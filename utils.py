# Módulo com funções auxiliares diversas

import os
import sys
import datetime
import platform
from typing import Dict, List, Any, Optional, Tuple

def format_size(size_bytes: float) -> str:
    """
    Formata tamanho em bytes para formato legível
    
    Args:
        size_bytes: Tamanho em bytes
        
    Returns:
        String formatada (ex: "2.5 MB", "1.2 GB")
    """
    # Constantes para conversão
    KB = 1024
    MB = KB * 1024
    GB = MB * 1024
    TB = GB * 1024
    
    if size_bytes < KB:
        return f"{size_bytes:.0f} Bytes"
    elif size_bytes < MB:
        return f"{size_bytes/KB:.1f} KB"
    elif size_bytes < GB:
        return f"{size_bytes/MB:.1f} MB"
    elif size_bytes < TB:
        return f"{size_bytes/GB:.2f} GB"
    else:
        return f"{size_bytes/TB:.2f} TB"

def format_time(seconds: float) -> str:
    """
    Formata tempo em segundos para formato legível
    
    Args:
        seconds: Tempo em segundos
        
    Returns:
        String formatada (ex: "2h 15m", "45s")
    """
    if seconds < 60:
        return f"{int(seconds)}s"
    
    minutes = seconds // 60
    seconds = seconds % 60
    
    if minutes < 60:
        return f"{int(minutes)}m {int(seconds)}s"
    
    hours = minutes // 60
    minutes = minutes % 60
    
    if hours < 24:
        return f"{int(hours)}h {int(minutes)}m"
    
    days = hours // 24
    hours = hours % 24
    
    return f"{int(days)}d {int(hours)}h {int(minutes)}m"

def format_timestamp(timestamp: float) -> str:
    """
    Formata timestamp para string no formato local
    
    Args:
        timestamp: Timestamp Unix
        
    Returns:
        String formatada com data e hora local
    """
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%d/%m/%Y %H:%M:%S")

def get_process_icon_name(process_name: str) -> str:
    """
    Determina o ícone a ser usado para o processo baseado no nome
    
    Args:
        process_name: Nome do processo
        
    Returns:
        Nome do arquivo de ícone a ser usado
    """
    # Mapeamento de processos comuns para ícones
    icon_map = {
        "chrome": "browser",
        "firefox": "browser",
        "edge": "browser",
        "explorer": "folder",
        "cmd": "terminal",
        "powershell": "terminal",
        "notepad": "text",
        "word": "document",
        "excel": "spreadsheet",
        "python": "code",
        "code": "code",
    }
    
    # Verifica se o nome do processo corresponde a algum dos mapeamentos
    process_lower = process_name.lower()
    for key, icon in icon_map.items():
        if key in process_lower:
            return f"icons/{icon}.png"
    
    # Ícone genérico para processos desconhecidos
    return "icons/generic.png"

def is_admin() -> bool:
    """
    Verifica se o aplicativo está sendo executado como administrador
    
    Returns:
        True se estiver sendo executado como administrador
    """
    try:
        if sys.platform == 'win32':
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        else:
            # No Unix, verifica se o UID é 0 (root)
            return os.geteuid() == 0
    except:
        return False

def create_directory_if_not_exists(directory_path: str) -> bool:
    """
    Cria um diretório se ele não existir
    
    Args:
        directory_path: Caminho para o diretório
        
    Returns:
        True se o diretório foi criado ou já existia
    """
    try:
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
        return True
    except Exception:
        return False

def get_system_info_string() -> str:
    """
    Obtém informações do sistema em formato de string
    
    Returns:
        String com informações do sistema
    """
    os_info = platform.platform()
    python_version = platform.python_version()
    cpu_info = platform.processor()
    
    return f"Sistema: {os_info}\nPython: {python_version}\nProcessador: {cpu_info}"

def safe_division(a: float, b: float, default: float = 0.0) -> float:
    """
    Divisão segura que retorna um valor padrão em caso de divisão por zero
    
    Args:
        a: Numerador
        b: Denominador
        default: Valor padrão para retornar em caso de divisão por zero
        
    Returns:
        Resultado da divisão ou valor padrão
    """
    return a / b if b != 0 else default

def log_error(error_message: str, exception: Optional[Exception] = None) -> None:
    """
    Registra um erro em arquivo de log
    
    Args:
        error_message: Mensagem de erro
        exception: Exceção ocorrida (opcional)
    """
    log_dir = "logs"
    create_directory_if_not_exists(log_dir)
    
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = os.path.join(log_dir, f"error_{datetime.datetime.now().strftime('%Y%m%d')}.log")
    
    error_text = f"[{timestamp}] {error_message}"
    if exception:
        error_text += f"\nException: {str(exception)}"
    
    try:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(error_text + "\n\n")
    except:
        # Se não conseguir gravar o log, ignora silenciosamente
        pass

def truncate_text(text: str, max_length: int = 50) -> str:
    """
    Trunca um texto para o tamanho máximo especificado
    
    Args:
        text: Texto a ser truncado
        max_length: Tamanho máximo permitido
        
    Returns:
        Texto truncado com "..." se necessário
    """
    if len(text) <= max_length:
        return text
    
    # Trunca o texto e adiciona "..." no final
    return text[:max_length-3] + "..."
