# settings.py
# Arquivo com configurações gerais da aplicação

# Configurações gerais do aplicativo
APP_NAME = "FastTask - Gerenciador de Processos"
APP_VERSION = "1.0.0"
ICON_PATH = "icons/app_icon.png"

# Configurações de atualização
DEFAULT_UPDATE_INTERVAL = 2  # Segundos
MIN_UPDATE_INTERVAL = 0.5    # Intervalo mínimo
MAX_UPDATE_INTERVAL = 10     # Intervalo máximo

# Configurações da interface
DEFAULT_THEME = "light"      # light ou dark
DEFAULT_VIEW_MODE = "compacto"  # compacto ou detalhado
WINDOW_SIZE = (1000, 700)    # Tamanho padrão da janela (largura, altura)

# Limites para alertas
CPU_ALERT_THRESHOLD = 80     # Alerta quando uso de CPU > 80%
RAM_ALERT_THRESHOLD = 80     # Alerta quando uso de RAM > 80%

# Cores para interface
COLORS = {
    "light": {
        "background": "#FFFFFF",
        "foreground": "#000000",
        "highlight": "#4285F4",
        "normal_process": "#333333",
        "high_usage": "#FF5252",
        "medium_usage": "#FFC107",
        "low_usage": "#4CAF50",
    },
    "dark": {
        "background": "#252525",
        "foreground": "#E0E0E0",
        "highlight": "#4285F4",
        "normal_process": "#E0E0E0",
        "high_usage": "#FF5252",
        "medium_usage": "#FFC107",
        "low_usage": "#4CAF50",
    }
}

# Lista de processos do sistema que são considerados críticos
CRITICAL_PROCESSES = [
    "explorer.exe",
    "winlogon.exe",
    "services.exe",
    "csrss.exe",
    "svchost.exe",
    "lsass.exe",
    "System"
]
