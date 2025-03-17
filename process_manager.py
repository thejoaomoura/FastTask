# process_manager.py
# Módulo responsável pelo gerenciamento de processos

import os
import sys
import time
import psutil
from typing import List, Dict, Tuple, Optional, Any
from settings import CRITICAL_PROCESSES

class ProcessInfo:
    """Classe para armazenar informações de um processo"""
    
    def __init__(self, pid: int, name: str, cpu_percent: float, memory_mb: float, 
                status: str, priority: Optional[int] = None, threads: Optional[int] = None,
                command_line: Optional[str] = None):
        self.pid = pid
        self.name = name
        self.cpu_percent = cpu_percent
        self.memory_mb = memory_mb
        self.status = status
        self.priority = priority
        self.threads = threads
        self.command_line = command_line
        self.is_critical = name.lower() in [p.lower() for p in CRITICAL_PROCESSES]
        self.is_suspicious = False
        
    def __str__(self) -> str:
        return f"{self.name} (PID: {self.pid}) - CPU: {self.cpu_percent:.1f}% - RAM: {self.memory_mb:.1f} MB"
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte o objeto em um dicionário para facilitar o uso na UI"""
        return {
            "pid": self.pid,
            "name": self.name,
            "cpu_percent": self.cpu_percent,
            "memory_mb": self.memory_mb,
            "status": self.status,
            "priority": self.priority,
            "threads": self.threads,
            "command_line": self.command_line,
            "is_critical": self.is_critical,
            "is_suspicious": self.is_suspicious
        }

def get_process_list(detailed: bool = False) -> List[ProcessInfo]:
    """
    Obtém lista de processos ativos no sistema
    
    Args:
        detailed: Se True, inclui informações adicionais como prioridade e linha de comando
        
    Returns:
        Uma lista de objetos ProcessInfo
    """
    processes = []
    
    # Obtém lista de todos os processos
    for proc in psutil.process_iter(['pid', 'name', 'status']):
        try:
            # Informações básicas do processo
            proc_info = proc.info
            pid = proc_info['pid']
            name = proc_info['name']
            status_raw = proc_info['status']
            
            # Mapeamento do status para formato legível
            status_map = {
                psutil.STATUS_RUNNING: "Ativo",
                psutil.STATUS_SLEEPING: "Inativo",
                psutil.STATUS_DISK_SLEEP: "Disco",
                psutil.STATUS_STOPPED: "Parado",
                psutil.STATUS_ZOMBIE: "Zumbi",
                psutil.STATUS_DEAD: "Morto",
            }
            status = status_map.get(status_raw, "Desconhecido")
            
            # Cálculo de uso de CPU e memória
            with proc.oneshot():  # Melhora a performance consultando tudo de uma vez
                try:
                    cpu_percent = proc.cpu_percent(interval=0.1)
                    memory_info = proc.memory_info()
                    memory_mb = memory_info.rss / (1024 * 1024)  # Converte para MB
                    
                    # Informações adicionais para o modo detalhado
                    if detailed:
                        priority = proc.nice()
                        threads = proc.num_threads()
                        try:
                            command_line = " ".join(proc.cmdline())
                        except:
                            command_line = "N/A"
                    else:
                        priority = None
                        threads = None
                        command_line = None
                    
                    # Cria objeto com as informações do processo
                    process = ProcessInfo(
                        pid=pid,
                        name=name,
                        cpu_percent=cpu_percent,
                        memory_mb=memory_mb,
                        status=status,
                        priority=priority,
                        threads=threads,
                        command_line=command_line
                    )
                    
                    processes.append(process)
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return processes

def terminate_process(pid: int) -> Tuple[bool, str]:
    """
    Encerra um processo pelo PID
    
    Args:
        pid: ID do processo a ser finalizado
        
    Returns:
        Tupla (sucesso, mensagem)
    """
    try:
        process = psutil.Process(pid)
        
        # Verifica se é um processo crítico
        process_name = process.name()
        if process_name.lower() in [p.lower() for p in CRITICAL_PROCESSES]:
            return False, f"Atenção: {process_name} é um processo crítico do sistema."
            
        # Tenta encerrar o processo
        process.terminate()
        
        # Espera até 3 segundos para confirmar que o processo foi encerrado
        gone, still_alive = psutil.wait_procs([process], timeout=3)
        
        if process in still_alive:
            # Se ainda estiver vivo, força o encerramento
            process.kill()
            return True, f"Processo {process_name} (PID: {pid}) foi forçadamente encerrado."
        
        return True, f"Processo {process_name} (PID: {pid}) foi encerrado com sucesso."
    
    except psutil.NoSuchProcess:
        return False, f"Processo com PID {pid} não existe."
    except psutil.AccessDenied:
        return False, f"Acesso negado ao tentar encerrar o processo PID {pid}. Execute como administrador."
    except Exception as e:
        return False, f"Erro ao encerrar processo: {str(e)}"

def change_process_priority(pid: int, priority_level: str) -> Tuple[bool, str]:
    """
    Altera a prioridade de um processo
    
    Args:
        pid: ID do processo
        priority_level: Nível de prioridade ('baixa', 'normal', 'alta', 'tempo_real')
        
    Returns:
        Tupla (sucesso, mensagem)
    """
    # Mapeamento de níveis de prioridade para valores do sistema
    priority_map = {
        "baixa": psutil.BELOW_NORMAL_PRIORITY_CLASS if hasattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS') else -10,
        "normal": psutil.NORMAL_PRIORITY_CLASS if hasattr(psutil, 'NORMAL_PRIORITY_CLASS') else 0,
        "alta": psutil.HIGH_PRIORITY_CLASS if hasattr(psutil, 'HIGH_PRIORITY_CLASS') else 10,
        "tempo_real": psutil.REALTIME_PRIORITY_CLASS if hasattr(psutil, 'REALTIME_PRIORITY_CLASS') else 20
    }
    
    if priority_level not in priority_map:
        return False, f"Nível de prioridade inválido: {priority_level}"
    
    try:
        process = psutil.Process(pid)
        if sys.platform == 'win32':
            # Windows
            process.nice(priority_map[priority_level])
        else:
            # Unix/Linux/macOS
            os.setpriority(os.PRIO_PROCESS, pid, priority_map[priority_level])
        
        return True, f"Prioridade do processo (PID: {pid}) alterada para {priority_level}."
    
    except psutil.NoSuchProcess:
        return False, f"Processo com PID {pid} não existe."
    except psutil.AccessDenied:
        return False, f"Acesso negado ao tentar alterar a prioridade do processo. Execute como administrador."
    except Exception as e:
        return False, f"Erro ao alterar prioridade: {str(e)}"

def start_new_process(command: str) -> Tuple[bool, str, Optional[int]]:
    """
    Inicia um novo processo
    
    Args:
        command: Comando ou caminho para o executável
        
    Returns:
        Tupla (sucesso, mensagem, pid)
    """
    try:
        if sys.platform == 'win32' and not command.endswith(('.exe', '.bat', '.cmd')):
            # No Windows, tenta abrir qualquer arquivo com o aplicativo padrão
            import subprocess
            process = subprocess.Popen(['start', '', command], shell=True)
            return True, f"Processo iniciado: {command}", None
        else:
            # Inicia o processo usando psutil
            process = psutil.Popen(command.split())
            return True, f"Processo iniciado: {command} (PID: {process.pid})", process.pid
    
    except Exception as e:
        return False, f"Erro ao iniciar processo: {str(e)}", None

def find_process_by_name(name: str) -> List[ProcessInfo]:
    """
    Busca processos pelo nome
    
    Args:
        name: Nome ou parte do nome do processo
        
    Returns:
        Lista de processos encontrados
    """
    all_processes = get_process_list()
    return [p for p in all_processes if name.lower() in p.name.lower()]

def get_system_info() -> Dict[str, Any]:
    """
    Obtém informações gerais do sistema
    
    Returns:
        Dicionário com informações do sistema
    """
    # CPU
    cpu_percent = psutil.cpu_percent(interval=0.5)
    cpu_count = psutil.cpu_count(logical=True)
    cpu_physical = psutil.cpu_count(logical=False)
    
    # Memória
    memory = psutil.virtual_memory()
    memory_total = memory.total / (1024 * 1024 * 1024)  # GB
    memory_used = memory.used / (1024 * 1024 * 1024)    # GB
    memory_percent = memory.percent
    
    # Disco
    disk = psutil.disk_usage('/')
    disk_total = disk.total / (1024 * 1024 * 1024)      # GB
    disk_used = disk.used / (1024 * 1024 * 1024)        # GB
    disk_percent = disk.percent
    
    # Rede (apenas conexões ativas)
    net_connections = len(psutil.net_connections())
    
    # Tempo de atividade do sistema
    boot_time = psutil.boot_time()
    uptime_seconds = time.time() - boot_time
    uptime_days = uptime_seconds // (24 * 3600)
    uptime_hours = (uptime_seconds % (24 * 3600)) // 3600
    uptime_minutes = (uptime_seconds % 3600) // 60
    uptime = f"{int(uptime_days)}d {int(uptime_hours)}h {int(uptime_minutes)}m"
    
    return {
        "cpu": {
            "percent": cpu_percent,
            "cores_logical": cpu_count,
            "cores_physical": cpu_physical
        },
        "memory": {
            "total_gb": memory_total,
            "used_gb": memory_used,
            "percent": memory_percent
        },
        "disk": {
            "total_gb": disk_total,
            "used_gb": disk_used,
            "percent": disk_percent
        },
        "network": {
            "connections": net_connections
        },
        "system": {
            "platform": sys.platform,
            "uptime": uptime,
            "python_version": sys.version.split()[0]
        }
    }
