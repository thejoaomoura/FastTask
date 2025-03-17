# Módulo responsável pelo monitoramento do sistema

import time
import psutil
from typing import List, Dict, Tuple, Optional, Any
from collections import deque

class SystemMonitor:
    """Classe para monitoramento de recursos do sistema com histórico"""
    
    def __init__(self, history_length: int = 60):
        """
        Inicializa o monitor de sistema com histórico
        
        Args:
            history_length: Número de pontos de histórico a manter
        """
        self.history_length = history_length
        
        # Inicializa históricos com deques de tamanho fixo
        self.cpu_history = deque(maxlen=history_length)
        self.ram_history = deque(maxlen=history_length)
        self.timestamps = deque(maxlen=history_length)
        
        # Coleta inicial de dados
        self._collect_data_point()
    
    def _collect_data_point(self) -> None:
        """Coleta um ponto de dados atual e armazena no histórico"""
        timestamp = time.time()
        cpu_percent = psutil.cpu_percent(interval=0.1)  # Intervalo curto para não bloquear
        ram_percent = psutil.virtual_memory().percent
        
        self.timestamps.append(timestamp)
        self.cpu_history.append(cpu_percent)
        self.ram_history.append(ram_percent)
    
    def update(self) -> Dict[str, Any]:
        """
        Atualiza o histórico com novos dados
        
        Returns:
            Dicionário com dados atuais e histórico
        """
        self._collect_data_point()
        
        return {
            "current": {
                "cpu": self.cpu_history[-1],
                "ram": self.ram_history[-1],
                "timestamp": self.timestamps[-1]
            },
            "history": {
                "cpu": list(self.cpu_history),
                "ram": list(self.ram_history),
                "timestamps": list(self.timestamps)
            }
        }
    
    def get_history(self) -> Dict[str, List]:
        """
        Obtém o histórico completo
        
        Returns:
            Dicionário com históricos de CPU, RAM e timestamps
        """
        return {
            "cpu": list(self.cpu_history),
            "ram": list(self.ram_history),
            "timestamps": list(self.timestamps)
        }
    
    def get_current(self) -> Dict[str, float]:
        """
        Obtém apenas os valores atuais
        
        Returns:
            Dicionário com valores atuais de CPU e RAM
        """
        if not self.cpu_history:
            self._collect_data_point()
            
        return {
            "cpu": self.cpu_history[-1],
            "ram": self.ram_history[-1],
            "timestamp": self.timestamps[-1]
        }
    
    def get_average(self, minutes: int = 1) -> Dict[str, float]:
        """
        Calcula a média de uso no período especificado
        
        Args:
            minutes: Período em minutos para calcular a média
            
        Returns:
            Dicionário com médias de CPU e RAM
        """
        # Calcula quantos pontos representam o período solicitado
        points = min(len(self.cpu_history), minutes * 60)
        
        if points == 0:
            return {"cpu": 0.0, "ram": 0.0}
        
        # Calcula as médias dos últimos 'points' valores
        avg_cpu = sum(list(self.cpu_history)[-points:]) / points
        avg_ram = sum(list(self.ram_history)[-points:]) / points
        
        return {
            "cpu": avg_cpu,
            "ram": avg_ram
        }

class ProcessMonitor:
    """Classe para monitoramento de processos específicos"""
    
    def __init__(self, pid: int, history_length: int = 60):
        """
        Inicializa o monitor para um processo específico
        
        Args:
            pid: ID do processo a monitorar
            history_length: Número de pontos de histórico a manter
        """
        self.pid = pid
        self.history_length = history_length
        
        # Tenta acessar o processo
        try:
            self.process = psutil.Process(pid)
            self.valid = True
        except psutil.NoSuchProcess:
            self.valid = False
            return
        
        # Inicializa históricos
        self.cpu_history = deque(maxlen=history_length)
        self.ram_history = deque(maxlen=history_length)
        self.timestamps = deque(maxlen=history_length)
        
        # Coleta inicial de dados
        self._collect_data_point()
    
    def _collect_data_point(self) -> None:
        """Coleta um ponto de dados atual e armazena no histórico"""
        if not self.valid:
            return
            
        try:
            timestamp = time.time()
            with self.process.oneshot():
                cpu_percent = self.process.cpu_percent(interval=0.1)
                ram_mb = self.process.memory_info().rss / (1024 * 1024)
            
            self.timestamps.append(timestamp)
            self.cpu_history.append(cpu_percent)
            self.ram_history.append(ram_mb)
        except psutil.NoSuchProcess:
            self.valid = False
    
    def update(self) -> Optional[Dict[str, Any]]:
        """
        Atualiza o histórico com novos dados
        
        Returns:
            Dicionário com dados atuais e histórico ou None se o processo não existir
        """
        if not self.valid:
            return None
            
        self._collect_data_point()
        
        return {
            "current": {
                "cpu": self.cpu_history[-1],
                "ram": self.ram_history[-1],
                "timestamp": self.timestamps[-1]
            },
            "history": {
                "cpu": list(self.cpu_history),
                "ram": list(self.ram_history),
                "timestamps": list(self.timestamps)
            }
        }
    
    def get_history(self) -> Optional[Dict[str, List]]:
        """
        Obtém o histórico completo
        
        Returns:
            Dicionário com históricos de CPU, RAM e timestamps ou None se o processo não existir
        """
        if not self.valid:
            return None
            
        return {
            "cpu": list(self.cpu_history),
            "ram": list(self.ram_history),
            "timestamps": list(self.timestamps)
        }
    
    def get_current(self) -> Optional[Dict[str, float]]:
        """
        Obtém apenas os valores atuais
        
        Returns:
            Dicionário com valores atuais de CPU e RAM ou None se o processo não existir
        """
        if not self.valid:
            return None
            
        if not self.cpu_history:
            self._collect_data_point()
            
        return {
            "cpu": self.cpu_history[-1],
            "ram": self.ram_history[-1],
            "timestamp": self.timestamps[-1]
        }
    
    def is_suspicious(self, cpu_threshold: float = 80.0, ram_threshold_mb: float = 1000.0) -> bool:
        """
        Verifica se o processo está com uso suspeito de recursos
        
        Args:
            cpu_threshold: Limite de CPU para considerar suspeito (%)
            ram_threshold_mb: Limite de RAM para considerar suspeito (MB)
            
        Returns:
            True se o processo estiver usando recursos acima dos limiares
        """
        if not self.valid or not self.cpu_history:
            return False
            
        return self.cpu_history[-1] > cpu_threshold or self.ram_history[-1] > ram_threshold_mb
