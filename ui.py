# ui.py
# Módulo responsável pela interface gráfica

import sys
import os
import time
from typing import Dict, List, Any, Optional, Tuple, Callable

# Tenta importar PySide6
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit, 
        QComboBox, QCheckBox, QTabWidget, QSlider, QMessageBox, 
        QMenu, QStatusBar, QSplitter, QFrame, QFileDialog, QDialogButtonBox
    )
    from PySide6.QtCore import Qt, QTimer, Signal, Slot, QSize, QThread
    from PySide6.QtGui import QIcon, QAction, QFont, QPixmap, QColor
except ImportError as e:
    print(f"Erro ao importar PySide6: {e}")
    print("Tente reinstalar a biblioteca com: pip install PySide6==6.5.2")
    sys.exit(1)

# Importa módulos do projeto
import process_manager
import monitoring
import utils
from settings import (
    APP_NAME, APP_VERSION, DEFAULT_UPDATE_INTERVAL, 
    DEFAULT_THEME, COLORS, WINDOW_SIZE, CRITICAL_PROCESSES,
    DEFAULT_VIEW_MODE, PROCESS_FETCH_LIMIT, ENABLE_GRAPHS, LAZY_LOADING
)

# Configurações de estilo
FONT_FAMILY = "Segoe UI" if sys.platform == "win32" else "Arial"
FONT_SIZE = 10
ICON_SIZE = 16

class ProcessTableWidget(QTableWidget):
    """Widget de tabela personalizada para processos"""
    
    # Sinais
    processSelected = Signal(int)  # Sinal emitido quando um processo é selecionado
    
    def __init__(self, parent=None):
        """Inicializa a tabela de processos"""
        super().__init__(parent)
        
        # Configuração inicial
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Nome", "PID", "Status", "CPU %", "Memória", "Usuário"
        ])
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setShowGrid(True)
        self.setSortingEnabled(True)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(True)
        
        # Configura dimensões das colunas
        self.setColumnWidth(0, 200)  # Nome
        self.setColumnWidth(1, 60)   # PID
        self.setColumnWidth(2, 80)   # Status
        self.setColumnWidth(3, 80)   # CPU
        self.setColumnWidth(4, 100)  # Memória
        
        # Conecta sinais
        self.itemSelectionChanged.connect(self._on_selection_changed)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Estado interno
        self.processes = []
        self.detailed_mode = False
        self.pid_row_map = {}
        
    def update_processes(self, processes: List[process_manager.ProcessInfo], detailed_mode: bool = False):
        """
        Atualiza a lista de processos exibida
        
        Args:
            processes: Lista de objetos ProcessInfo
            detailed_mode: Se True, exibe informações detalhadas
        """
        # Armazena dados
        self.processes = processes
        self.detailed_mode = detailed_mode
        
        # Armazena seleção atual
        selected_pid = None
        selected_items = self.selectedItems()
        if selected_items:
            selected_row = selected_items[0].row()
            selected_pid = int(self.item(selected_row, 1).text())
        
        # Desativa ordenação temporariamente
        sorting_enabled = self.isSortingEnabled()
        self.setSortingEnabled(False)
        
        # Limpa tabela e atualiza número de linhas
        self.clearContents()
        self.setRowCount(len(processes))
        
        # Atualiza cabeçalhos se necessário
        if detailed_mode and self.columnCount() < 8:
            self.setColumnCount(8)
            self.setHorizontalHeaderLabels([
                "Nome", "PID", "Status", "CPU %", "Memória", "Usuário", 
                "Threads", "Prioridade"
            ])
        elif not detailed_mode and self.columnCount() > 6:
            self.setColumnCount(6)
            self.setHorizontalHeaderLabels([
                "Nome", "PID", "Status", "CPU %", "Memória", "Usuário"
            ])
        
        # Cria mapeamento de PID para linha para seleção posterior
        self.pid_row_map = {}
        
        # Preenche tabela
        for row, proc in enumerate(processes):
            # Guarda mapeamento entre PID e linha
            self.pid_row_map[proc.pid] = row
            
            # Nome do processo
            name_item = QTableWidgetItem(proc.name)
            name_item.setToolTip(proc.exe_path if hasattr(proc, 'exe_path') and proc.exe_path else proc.name)
            if proc.is_critical:
                name_item.setForeground(QColor(COLORS["critical"]))
            self.setItem(row, 0, name_item)
            
            # PID
            pid_item = QTableWidgetItem(str(proc.pid))
            pid_item.setTextAlignment(Qt.AlignCenter)
            self.setItem(row, 1, pid_item)
            
            # Status
            status_item = QTableWidgetItem(proc.status)
            status_item.setTextAlignment(Qt.AlignCenter)
            if proc.status == "Ativo":
                status_item.setForeground(QColor("green"))
            elif proc.status == "Parado":
                status_item.setForeground(QColor("red"))
            self.setItem(row, 2, status_item)
            
            # CPU
            cpu_item = QTableWidgetItem(f"{proc.cpu_percent:.1f}%")
            cpu_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            if proc.cpu_percent > 80:
                cpu_item.setBackground(QColor(255, 150, 150))
            elif proc.cpu_percent > 50:
                cpu_item.setBackground(QColor(255, 220, 150))
            self.setItem(row, 3, cpu_item)
            
            # Memória
            memory_str = utils.format_size(proc.memory_bytes if hasattr(proc, 'memory_bytes') else proc.memory_mb * 1024 * 1024)
            memory_item = QTableWidgetItem(memory_str)
            memory_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row, 4, memory_item)
            
            # Usuário
            user_item = QTableWidgetItem(proc.username if hasattr(proc, 'username') else "-")
            self.setItem(row, 5, user_item)
            
            # Campos adicionais para modo detalhado
            if detailed_mode:
                # Threads
                thread_item = QTableWidgetItem(str(proc.num_threads if hasattr(proc, 'num_threads') else proc.threads))
                thread_item.setTextAlignment(Qt.AlignCenter)
                self.setItem(row, 6, thread_item)
                
                # Prioridade
                priority_item = QTableWidgetItem(str(proc.priority) if proc.priority is not None else "N/A")
                priority_item.setTextAlignment(Qt.AlignCenter)
                self.setItem(row, 7, priority_item)
        
        # Restaura ordenação
        self.setSortingEnabled(sorting_enabled)
        
        # Restaura seleção
        if selected_pid in self.pid_row_map:
            self.selectRow(self.pid_row_map[selected_pid])
    
    def _on_selection_changed(self):
        """Manipula mudança na seleção de linha"""
        selected = self.selectedItems()
        if selected:
            row = selected[0].row()
            pid_item = self.item(row, 1)  # Coluna do PID
            if pid_item:
                pid = int(pid_item.text())
                self.processSelected.emit(pid)
    
    def _show_context_menu(self, position):
        """Exibe menu de contexto para a linha selecionada"""
        selected = self.selectedItems()
        if not selected:
            return
            
        row = selected[0].row()
        pid_item = self.item(row, 1)
        name_item = self.item(row, 0)
        
        if not pid_item or not name_item:
            return
            
        pid = int(pid_item.text())
        process_name = name_item.text()
        
        # Cria menu de contexto
        context_menu = QMenu(self)
        
        # Adiciona ações
        terminate_action = QAction("Finalizar Processo", self)
        terminate_action.triggered.connect(lambda: self._terminate_process(pid, process_name))
        
        priority_menu = QMenu("Alterar Prioridade", self)
        for priority_name in ["Baixa", "Normal", "Alta", "Tempo Real"]:
            priority_action = QAction(priority_name, self)
            priority_level = priority_name.lower().replace(" ", "_")
            priority_action.triggered.connect(
                lambda checked, p=priority_level, pid=pid: self._change_priority(pid, p)
            )
            priority_menu.addAction(priority_action)
        
        # Adiciona ações ao menu
        context_menu.addAction(terminate_action)
        context_menu.addMenu(priority_menu)
        
        # Exibe o menu
        context_menu.exec_(self.mapToGlobal(position))
    
    def _terminate_process(self, pid: int, name: str):
        """Confirma e encerra o processo"""
        # Verifica se é um processo crítico
        is_critical = name.lower() in [p.lower() for p in CRITICAL_PROCESSES]
        
        # Define a mensagem de confirmação
        if is_critical:
            msg = f"ATENÇÃO: {name} é um processo crítico do sistema!\n\nFinalizar este processo pode causar instabilidade ou travamento do sistema.\n\nDeseja realmente finalizar?"
            icon = QMessageBox.Warning
        else:
            msg = f"Deseja finalizar o processo {name} (PID: {pid})?"
            icon = QMessageBox.Question
        
        # Mostra diálogo de confirmação
        reply = QMessageBox.question(
            self, "Confirmar Finalização", msg, 
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            success, message = process_manager.terminate_process(pid)
            
            # Mostra resultado
            if success:
                QMessageBox.information(self, "Processo Finalizado", message)
            else:
                QMessageBox.warning(self, "Erro", message)
    
    def _change_priority(self, pid: int, priority_level: str):
        """Altera a prioridade do processo"""
        success, message = process_manager.change_process_priority(pid, priority_level)
        
        # Mostra resultado
        if success:
            QMessageBox.information(self, "Prioridade Alterada", message)
        else:
            QMessageBox.warning(self, "Erro", message)

class SystemInfoWidget(QWidget):
    """Widget para exibir informações do sistema"""
    
    def __init__(self, parent=None):
        """Inicializa o widget de informações do sistema"""
        super().__init__(parent)
        
        # Cria layout principal
        layout = QVBoxLayout(self)
        
        # Título
        title_label = QLabel("Informações do Sistema")
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title_label)
        
        # Layout para CPU e RAM
        resource_layout = QHBoxLayout()
        
        # CPU Info
        self.cpu_label = QLabel("CPU: 0%")
        self.cpu_label.setStyleSheet("font-size: 12px;")
        resource_layout.addWidget(self.cpu_label)
        
        # RAM Info
        self.ram_label = QLabel("RAM: 0 / 0 GB (0%)")
        self.ram_label.setStyleSheet("font-size: 12px;")
        resource_layout.addWidget(self.ram_label)
        
        layout.addLayout(resource_layout)
        
        # Informações adicionais
        info_layout = QVBoxLayout()
        
        # Processos
        self.process_count_label = QLabel("Processos: 0")
        info_layout.addWidget(self.process_count_label)
        
        # Tempo de atividade
        self.uptime_label = QLabel("Tempo de Atividade: 0m")
        info_layout.addWidget(self.uptime_label)
        
        # Plataforma
        self.platform_label = QLabel(f"Sistema: {sys.platform}")
        info_layout.addWidget(self.platform_label)
        
        layout.addLayout(info_layout)
        
        # Adiciona espaçador
        layout.addStretch()
        
        # Define estilo
        self.setStyleSheet("""
            QLabel {
                margin-bottom: 5px;
            }
        """)
    
    def update_info(self, system_info: Dict[str, Any], process_count: int):
        """
        Atualiza as informações do sistema
        
        Args:
            system_info: Dicionário com informações do sistema
            process_count: Número de processos ativos
        """
        # Atualiza CPU
        cpu_percent = system_info['cpu']['percent']
        cpu_cores = system_info['cpu']['cores_logical']
        self.cpu_label.setText(f"CPU: {cpu_percent:.1f}% ({cpu_cores} cores)")
        
        # Define cor baseada no uso de CPU
        if cpu_percent > 80:
            self.cpu_label.setStyleSheet("font-size: 12px; color: red; font-weight: bold;")
        elif cpu_percent > 50:
            self.cpu_label.setStyleSheet("font-size: 12px; color: orange;")
        else:
            self.cpu_label.setStyleSheet("font-size: 12px;")
        
        # Atualiza RAM
        ram_total = system_info['memory']['total_gb']
        ram_used = system_info['memory']['used_gb']
        ram_percent = system_info['memory']['percent']
        self.ram_label.setText(f"RAM: {ram_used:.1f} / {ram_total:.1f} GB ({ram_percent:.1f}%)")
        
        # Define cor baseada no uso de RAM
        if ram_percent > 80:
            self.ram_label.setStyleSheet("font-size: 12px; color: red; font-weight: bold;")
        elif ram_percent > 50:
            self.ram_label.setStyleSheet("font-size: 12px; color: orange;")
        else:
            self.ram_label.setStyleSheet("font-size: 12px;")
        
        # Atualiza contagem de processos
        self.process_count_label.setText(f"Processos: {process_count}")
        
        # Atualiza tempo de atividade
        self.uptime_label.setText(f"Tempo de Atividade: {system_info['system']['uptime']}")

class MonitoringGraphWidget(QWidget):
    """Widget para exibir gráficos de monitoramento"""
    
    def __init__(self, parent=None):
        """Inicializa o widget de gráficos"""
        super().__init__(parent)
        
        # Cria layout principal
        layout = QVBoxLayout(self)
        
        try:
            # Tenta importar matplotlib
            import matplotlib
            matplotlib.use('Qt5Agg')  # Tenta com Qt5Agg primeiro
            try:
                from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
            except ImportError:
                # Se falhar, tenta com Qt6Agg
                matplotlib.use('Qt6Agg')
                from matplotlib.backends.backend_qt6agg import FigureCanvasQTAgg as FigureCanvas
            from matplotlib.figure import Figure
            
            # Configuração inicial do matplotlib
            self.use_matplotlib = True
            
            # Cria figura e canvas
            self.figure = Figure(figsize=(5, 3), dpi=70)
            self.canvas = FigureCanvas(self.figure)
            
            # Cria dois subplots (CPU e RAM)
            self.cpu_ax = self.figure.add_subplot(211)
            self.ram_ax = self.figure.add_subplot(212)
            
            # Configuração dos gráficos
            self.cpu_line, = self.cpu_ax.plot([], [], 'b-', label='CPU %')
            self.ram_line, = self.ram_ax.plot([], [], 'g-', label='RAM %')
            
            self.cpu_ax.set_ylabel('CPU %')
            self.cpu_ax.set_ylim(0, 100)
            self.cpu_ax.grid(True)
            self.cpu_ax.legend(loc='upper right')
            
            self.ram_ax.set_ylabel('RAM %')
            self.ram_ax.set_ylim(0, 100)
            self.ram_ax.grid(True)
            self.ram_ax.legend(loc='upper right')
            
            # Ajusta layout
            self.figure.tight_layout()
            
            # Adiciona canvas ao layout
            layout.addWidget(self.canvas)
            
        except (ImportError, AttributeError, Exception) as e:
            # Fallback para mensagem de erro
            self.use_matplotlib = False
            error_msg = QLabel(f"Não foi possível carregar os gráficos.\nErro: {str(e)}")
            error_msg.setAlignment(Qt.AlignCenter)
            layout.addWidget(error_msg)
            
            # Adiciona um texto explicativo
            info_label = QLabel("Instale o matplotlib com: pip install matplotlib==3.8.0")
            info_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(info_label)
    
    def update_graph(self, monitor_data: Dict[str, Any]):
        """
        Atualiza os gráficos com novos dados
        
        Args:
            monitor_data: Dicionário com histórico de CPU e RAM
        """
        if not hasattr(self, 'use_matplotlib') or not self.use_matplotlib:
            return
            
        try:
            # Obtém histórico
            cpu_history = monitor_data['history']['cpu']
            ram_history = monitor_data['history']['ram']
            
            # Define limite de pontos a exibir
            max_points = 60
            if len(cpu_history) > max_points:
                cpu_history = cpu_history[-max_points:]
                ram_history = ram_history[-max_points:]
            
            # Cria array de pontos no eixo X
            x_data = list(range(len(cpu_history)))
            
            # Atualiza dados
            self.cpu_line.set_data(x_data, cpu_history)
            self.ram_line.set_data(x_data, ram_history)
            
            # Ajusta limites do eixo X
            self.cpu_ax.set_xlim(0, len(x_data))
            self.ram_ax.set_xlim(0, len(x_data))
            
            # Redesenha o canvas
            self.canvas.draw()
        except Exception:
            # Ignora erros na atualização dos gráficos
            pass

class ProcessFilterWidget(QWidget):
    """Widget para filtrar processos"""
    
    # Sinal emitido quando o filtro é alterado
    filterChanged = Signal(str, str)
    
    def __init__(self, parent=None):
        """Inicializa o widget de filtro"""
        super().__init__(parent)
        
        # Cria layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Campo de busca
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar processo...")
        self.search_input.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self.search_input)
        
        # Combobox para ordenação
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Nome", "PID", "CPU", "RAM"])
        self.sort_combo.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(QLabel("Ordenar por:"))
        layout.addWidget(self.sort_combo)
    
    def _on_filter_changed(self, *args):
        """Emite sinal quando o filtro ou ordenação mudam"""
        search_text = self.search_input.text()
        sort_by = self.sort_combo.currentText().lower()
        self.filterChanged.emit(search_text, sort_by)

class StartProcessDialog(QWidget):
    """Diálogo para iniciar um novo processo"""
    
    # Sinal emitido quando um processo é iniciado
    processStarted = Signal(bool, str)
    
    def __init__(self, parent=None):
        """Inicializa o diálogo"""
        super().__init__(parent)
        
        # Configura a janela
        self.setWindowTitle("Iniciar Novo Processo")
        self.setMinimumWidth(400)
        
        # Cria layout principal
        layout = QVBoxLayout(self)
        
        # Campo para comando
        form_layout = QHBoxLayout()
        form_layout.addWidget(QLabel("Comando:"))
        
        self.command_input = QLineEdit()
        self.command_input.setPlaceholderText("Digite o comando ou caminho do executável...")
        form_layout.addWidget(self.command_input)
        
        # Botão para selecionar arquivo
        browse_button = QPushButton("Procurar...")
        browse_button.clicked.connect(self._browse_file)
        form_layout.addWidget(browse_button)
        
        layout.addLayout(form_layout)
        
        # Botões de ação
        button_layout = QHBoxLayout()
        
        # Botão para executar
        run_button = QPushButton("Executar")
        run_button.clicked.connect(self._start_process)
        button_layout.addWidget(run_button)
        
        # Botão para cancelar
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.close)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
    
    def _browse_file(self):
        """Abre diálogo para selecionar arquivo executável"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Executável", "",
            "Executáveis (*.exe);;Todos os arquivos (*.*)"
        )
        
        if file_path:
            self.command_input.setText(file_path)
    
    def _start_process(self):
        """Inicia o processo com o comando especificado"""
        command = self.command_input.text().strip()
        
        if not command:
            QMessageBox.warning(self, "Erro", "Digite um comando ou selecione um executável.")
            return
        
        # Tenta iniciar o processo
        success, message, _ = process_manager.start_new_process(command)
        
        # Emite sinal com o resultado
        self.processStarted.emit(success, message)
        
        if success:
            self.close()
        else:
            QMessageBox.warning(self, "Erro", message)

class MainWindow(QMainWindow):
    """Janela principal da aplicação"""
    
    def __init__(self):
        """Inicializa a janela principal"""
        super().__init__()
        
        # Configura janela
        self.setWindowTitle(f"{APP_NAME} v{APP_VERSION}")
        self.resize(*WINDOW_SIZE)
        self.setMinimumSize(800, 600)
        
        # Define estado inicial
        self.is_updating = False
        self.view_mode = DEFAULT_VIEW_MODE
        self.detailed_mode = self.view_mode == "detalhado"
        self.search_text = ""
        self.monitor = monitoring.SystemMonitor()
        self.update_interval = DEFAULT_UPDATE_INTERVAL
        self.selected_pid = None
        self.processes = []
        
        # Interface principal
        self._create_layout()
        self._create_menu()
        self._create_status_bar()
        
        # Timer de atualização
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_data)
        self.set_update_interval(DEFAULT_UPDATE_INTERVAL)
        
        # Atualização inicial
        if not LAZY_LOADING:
            self.update_data()
        else:
            # Em modo de carregamento preguiçoso, apenas busca dados básicos primeiro
            self.status_bar.showMessage("Carregando processos...", 2000)
            QTimer.singleShot(100, self._initial_load)
    
    def _initial_load(self):
        """Realiza carregamento inicial com menos processos"""
        try:
            # Carrega apenas processos mais importantes primeiro
            processes = process_manager.get_process_list(detailed=False, limit=PROCESS_FETCH_LIMIT)
            self.process_table.update_processes(processes)
            
            # Inicia o timer de atualização após o carregamento inicial
            QTimer.singleShot(1000, lambda: self.update_timer.start())
            
            self.status_bar.showMessage("Pronto", 2000)
        except Exception as e:
            self.status_bar.showMessage(f"Erro ao carregar processos: {str(e)}", 5000)
    
    def _create_layout(self):
        """Cria o layout principal e widgets"""
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Barra de ferramentas com filtros e controles
        toolbar_layout = QHBoxLayout()
        
        # Widget de filtro
        self.filter_widget = ProcessFilterWidget()
        self.filter_widget.filterChanged.connect(self._on_filter_changed)
        toolbar_layout.addWidget(self.filter_widget)
        
        # Checkbox para modo de visualização
        self.detail_checkbox = QCheckBox("Modo Detalhado")
        self.detail_checkbox.setChecked(self.view_mode == "detalhado")
        self.detail_checkbox.toggled.connect(self._toggle_view_mode)
        toolbar_layout.addWidget(self.detail_checkbox)
        
        # Botão para atualizar manualmente
        refresh_button = QPushButton("Atualizar")
        refresh_button.clicked.connect(self.update_data)
        toolbar_layout.addWidget(refresh_button)
        
        main_layout.addLayout(toolbar_layout)
        
        # Layout central com splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Painel esquerdo: Tabela de processos
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabela de processos
        self.process_table = ProcessTableWidget()
        self.process_table.processSelected.connect(self._on_process_selected)
        left_layout.addWidget(self.process_table)
        
        # Botões de ação para processos
        button_layout = QHBoxLayout()
        
        # Botão para finalizar processo
        terminate_button = QPushButton("Finalizar Processo")
        terminate_button.clicked.connect(self._terminate_selected_process)
        button_layout.addWidget(terminate_button)
        
        # Botão para iniciar novo processo
        new_process_button = QPushButton("Novo Processo")
        new_process_button.clicked.connect(self._show_new_process_dialog)
        button_layout.addWidget(new_process_button)
        
        left_layout.addLayout(button_layout)
        
        # Painel direito: Informações e gráficos
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Widget de informações do sistema
        self.system_info = SystemInfoWidget()
        right_layout.addWidget(self.system_info)
        
        # Widget de gráficos
        self.graphs = MonitoringGraphWidget()
        right_layout.addWidget(self.graphs)
        
        # Adiciona painéis ao splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        
        # Define proporção inicial do splitter (70% esquerda, 30% direita)
        splitter.setSizes([700, 300])
        
        main_layout.addWidget(splitter)
    
    def _create_menu(self):
        """Cria menus e ações"""
        # Barra de menu
        menu_bar = self.menuBar()
        
        # Menu Arquivo
        file_menu = menu_bar.addMenu("Arquivo")
        
        # Ação: Atualizar
        refresh_action = QAction("Atualizar", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self.update_data)
        file_menu.addAction(refresh_action)
        
        # Ação: Iniciar Processo
        new_process_action = QAction("Iniciar Novo Processo", self)
        new_process_action.triggered.connect(self._show_new_process_dialog)
        file_menu.addAction(new_process_action)
        
        file_menu.addSeparator()
        
        # Ação: Sair
        exit_action = QAction("Sair", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menu Visualização
        view_menu = menu_bar.addMenu("Visualização")
        
        # Ação: Modo Detalhado
        self.detail_action = QAction("Modo Detalhado", self)
        self.detail_action.setCheckable(True)
        self.detail_action.setChecked(self.view_mode == "detalhado")
        self.detail_action.toggled.connect(self._toggle_view_mode)
        view_menu.addAction(self.detail_action)
        
        # Submenu: Intervalo de Atualização
        update_menu = view_menu.addMenu("Intervalo de Atualização")
        
        # Opções de intervalo
        for interval in [0.5, 1, 2, 5, 10]:
            interval_action = QAction(f"{interval} segundos", self)
            interval_action.setCheckable(True)
            interval_action.setChecked(self.update_interval == interval)
            interval_action.triggered.connect(
                lambda checked, i=interval: self.set_update_interval(i)
            )
            update_menu.addAction(interval_action)
        
        # Menu Ações
        actions_menu = menu_bar.addMenu("Ações")
        
        # Ação: Finalizar Processo
        terminate_action = QAction("Finalizar Processo Selecionado", self)
        terminate_action.triggered.connect(self._terminate_selected_process)
        actions_menu.addAction(terminate_action)
        
        # Menu Ajuda
        help_menu = menu_bar.addMenu("Ajuda")
        
        # Ação: Sobre
        about_action = QAction("Sobre", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """Cria barra de status"""
        self.status_bar = QStatusBar()
        self.admin_label = QLabel()
        self.status_bar.addPermanentWidget(self.admin_label)
        self.setStatusBar(self.status_bar)
        
        # Verifica se está sendo executado como administrador
        if utils.is_admin():
            self.admin_label.setText("Administrador")
            self.admin_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.admin_label.setText("Usuário Normal")
            self.admin_label.setStyleSheet("color: orange;")
            self.status_bar.showMessage("Execute como administrador para acesso completo", 5000)
    
    def update_data(self):
        """Atualiza todos os dados exibidos"""
        if self.is_updating:
            return
            
        self.is_updating = True
        try:
            # Obtém lista de processos com base no modo de visualização
            detailed = self.detailed_mode
            self.processes = process_manager.get_process_list(detailed=detailed, limit=None)
            
            # Filtra processos de acordo com o texto de busca
            if self.search_text:
                search_text = self.search_text.lower()
                self.processes = [p for p in self.processes if search_text in p.name.lower()]
            
            # Atualiza tabela de processos
            self.process_table.update_processes(self.processes)
            
            # Atualiza informações do sistema
            monitor_data = self.monitor.update()
            self.system_info.update_info(monitor_data['current'])
            
            # Atualiza gráficos se estiverem habilitados
            if ENABLE_GRAPHS:
                self.graphs.update_graph(monitor_data)
            
            # Atualiza barra de status
            self.status_bar.showMessage(
                f"Última atualização: {utils.format_timestamp(time.time())} | "
                f"Processos: {len(self.processes)} | "
                f"CPU: {monitor_data['current']['cpu']:.1f}% | "
                f"RAM: {monitor_data['current']['ram']:.1f}%", 
                5000
            )
        except Exception as e:
            utils.log_error(f"Erro na atualização de dados: {str(e)}")
        finally:
            self.is_updating = False
    
    def _apply_filter(self, processes: List[process_manager.ProcessInfo]) -> List[process_manager.ProcessInfo]:
        """
        Aplica filtro e ordenação à lista de processos
        
        Args:
            processes: Lista de processos original
            
        Returns:
            Lista filtrada e ordenada
        """
        # Obtém valores atuais do filtro
        search_text = self.filter_widget.search_input.text().lower()
        sort_by = self.filter_widget.sort_combo.currentText().lower()
        
        # Filtra por texto de busca
        if search_text:
            processes = [p for p in processes if search_text in p.name.lower()]
        
        # Ordena conforme selecionado
        if sort_by == "nome":
            processes.sort(key=lambda p: p.name.lower())
        elif sort_by == "pid":
            processes.sort(key=lambda p: p.pid)
        elif sort_by == "cpu":
            processes.sort(key=lambda p: p.cpu_percent, reverse=True)
        elif sort_by == "ram":
            processes.sort(key=lambda p: p.memory_mb, reverse=True)
        
        return processes
    
    def _on_filter_changed(self, search_text: str, sort_by: str):
        """Callback quando o filtro é alterado"""
        # Reaplica filtros e atualiza a tabela
        filtered_processes = self._apply_filter(self.processes)
        self.process_table.update_processes(filtered_processes)
    
    def _on_process_selected(self, pid: int):
        """Callback quando um processo é selecionado"""
        self.selected_pid = pid
    
    def _toggle_view_mode(self, checked: bool):
        """Alterna entre modos de visualização detalhado e compacto"""
        # Atualiza checkbox e action do menu para ficarem sincronizados
        self.detail_checkbox.setChecked(checked)
        self.detail_action.setChecked(checked)
        
        # Atualiza modo de visualização
        self.view_mode = "detalhado" if checked else "compacto"
        
        # Atualiza dados para refletir o novo modo
        self.update_data()
    
    def set_update_interval(self, interval: float):
        """Altera o intervalo de atualização"""
        self.update_interval = interval
        
        # Reinicia o timer com novo intervalo
        self.update_timer.stop()
        self.update_timer.start(int(self.update_interval * 1000))
        
        self.status_bar.showMessage(f"Intervalo de atualização alterado para {interval} segundos", 3000)
    
    def _terminate_selected_process(self):
        """Finaliza o processo selecionado"""
        if self.selected_pid is None:
            QMessageBox.warning(self, "Aviso", "Nenhum processo selecionado.")
            return
        
        # Busca o processo na lista
        process_info = None
        for proc in self.processes:
            if proc.pid == self.selected_pid:
                process_info = proc
                break
        
        if not process_info:
            return
        
        # Chama o método de finalização da tabela de processos
        self.process_table._terminate_process(self.selected_pid, process_info.name)
        
        # Atualiza dados após uma pequena pausa para permitir que o sistema atualize
        QTimer.singleShot(500, self.update_data)
    
    def _show_new_process_dialog(self):
        """Mostra diálogo para iniciar novo processo"""
        dialog = StartProcessDialog(self)
        dialog.processStarted.connect(self._on_process_started)
        dialog.show()
    
    def _on_process_started(self, success: bool, message: str):
        """Callback quando um processo é iniciado"""
        if success:
            self.status_bar.showMessage(message, 5000)
            # Atualiza dados após uma pequena pausa
            QTimer.singleShot(500, self.update_data)
        else:
            QMessageBox.warning(self, "Erro", message)
    
    def _show_about(self):
        """Mostra diálogo de informações sobre o aplicativo"""
        about_text = f"""
        <h2>{APP_NAME} v{APP_VERSION}</h2>
        <p>Um gerenciador de tarefas simplificado desenvolvido em Python.</p>
        <p><b>Recursos:</b>
        <ul>
            <li>Visualização e gerenciamento de processos</li>
            <li>Monitoramento de CPU e RAM</li>
            <li>Finalização de processos</li>
            <li>Alteração de prioridade</li>
            <li>Gráficos de desempenho</li>
        </ul>
        <p><b>Informações do Sistema:</b><br>
        {utils.get_system_info_string()}</p>
        """
        
        QMessageBox.about(self, f"Sobre {APP_NAME}", about_text)
    
    def closeEvent(self, event):
        """Manipula evento de fechamento da janela"""
        # Para o timer antes de fechar
        self.update_timer.stop()
        event.accept()
