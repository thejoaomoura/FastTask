#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
FastTask - Gerenciador de Tarefas Simplificado

Este é o módulo principal que inicia a aplicação.
"""

import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon

# Importa a classe da janela principal
from ui import MainWindow

# Importa configurações
from settings import APP_NAME, ICON_PATH

def create_app_directories():
    """Cria diretórios necessários para a aplicação"""
    dirs = ["logs", "icons"]
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)

def main():
    """Função principal que inicia a aplicação"""
    # Cria diretórios necessários
    create_app_directories()
    
    # Cria a aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    
    # Configura o ícone da aplicação se existir
    if os.path.exists(ICON_PATH):
        app.setWindowIcon(QIcon(ICON_PATH))
    
    # Cria e exibe a janela principal
    window = MainWindow()
    window.show()
    
    # Inicia o loop de eventos
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
