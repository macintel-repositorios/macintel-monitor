import math
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QListWidget, QListWidgetItem,
    QGridLayout, QLabel, QPushButton, QFrame, QStackedWidget, QScrollArea
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QIcon
from src.config import ConfigManager
from src.ui.camera_widget import CameraWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Macintel Monitor - Mosaico de Câmeras")
        self.resize(1280, 720)
        self.setMinimumSize(960, 540)
        
        # Gerenciador de Configurações
        self.config = ConfigManager()
        self.active_condominio_id = None
        self.active_cameras = []
        self.active_widgets = []
        self.fullscreen_widget = None
        
        # Paginação e Layout da Grade
        self.current_page = 0
        self.grid_rows = 2
        self.grid_cols = 2
        self.cameras_per_page = self.grid_rows * self.grid_cols
        
        self.init_ui()
        self.load_condominios()

    def init_ui(self):
        # Estilo Global (Dark Theme Premium)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
            }
            QWidget {
                color: #e0e0e0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QFrame#Sidebar {
                background-color: #1a1a1a;
                border-right: 1px solid #282828;
            }
            QListWidget {
                background-color: transparent;
                border: none;
                outline: 0;
            }
            QListWidget::item {
                background-color: #242424;
                border: 1px solid #2d2d2d;
                border-radius: 6px;
                padding: 12px;
                margin-bottom: 6px;
                font-weight: 500;
            }
            QListWidget::item:hover {
                background-color: #2a2a2a;
                border: 1px solid #00aaff;
            }
            QListWidget::item:selected {
                background-color: #0088cc;
                color: #ffffff;
                border: 1px solid #00aaff;
            }
            QPushButton {
                background-color: #242424;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                border-color: #00aaff;
            }
            QPushButton:pressed {
                background-color: #0088cc;
                border-color: #00aaff;
            }
            QPushButton#ActiveGridBtn {
                background-color: #0088cc;
                border-color: #00aaff;
                color: white;
            }
            QFrame#Header {
                background-color: #1a1a1a;
                border-bottom: 1px solid #282828;
            }
        """)

        # Layout Principal (Sidebar + Main Area)
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- SIDEBAR (Lista de Condomínios) ---
        sidebar = QFrame()
        self.sidebar = sidebar
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(260)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 12, 12, 12)
        
        logo_label = QLabel("MACINTEL MONITOR")
        logo_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #00aaff; letter-spacing: 1px; margin-bottom: 15px;")
        logo_label.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo_label)
        
        cond_title = QLabel("CONDOMÍNIOS")
        cond_title.setStyleSheet("font-size: 10px; font-weight: bold; color: #777777; margin-bottom: 5px;")
        sidebar_layout.addWidget(cond_title)
        
        self.condo_list = QListWidget()
        self.condo_list.itemClicked.connect(self.on_condominio_changed)
        sidebar_layout.addWidget(self.condo_list)
        
        sidebar_layout.addStretch()
        
        # Info rodapé sidebar
        sys_info = QLabel("Status: Online\nEngine: PySide6 + VLC")
        sys_info.setStyleSheet("color: #555555; font-size: 10px; line-height: 14px;")
        sys_info.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(sys_info)
        
        main_layout.addWidget(sidebar)
        
        # --- ÁREA PRINCIPAL (Header + Mosaico/Câmeras) ---
        main_content = QWidget()
        content_layout = QVBoxLayout(main_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Header (Barra Superior)
        header = QFrame()
        header.setObjectName("Header")
        header.setFixedHeight(60)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 0, 20, 0)
        
        # Botão Hamburger para recolher/expandir sidebar
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setToolTip("Ocultar/Mostrar Menu")
        self.menu_btn.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                background-color: transparent;
                border: none;
                color: #00aaff;
                padding: 5px 10px;
            }
            QPushButton:hover {
                background-color: #242424;
                border-radius: 4px;
            }
        """)
        self.menu_btn.clicked.connect(self.toggle_sidebar)
        header_layout.addWidget(self.menu_btn)
        
        self.condo_title_label = QLabel("Selecione um Condomínio")
        self.condo_title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff; margin-left: 10px;")
        header_layout.addWidget(self.condo_title_label)
        
        header_layout.addStretch()
        
        # Layout / Controles da Grade
        grid_ctrl_layout = QHBoxLayout()
        grid_ctrl_layout.setSpacing(5)
        
        self.grid_2x2_btn = QPushButton("Grade 2x2")
        self.grid_2x2_btn.setObjectName("ActiveGridBtn") # 2x2 padrão
        self.grid_2x2_btn.clicked.connect(lambda: self.change_grid_layout(2, 2))
        
        self.grid_3x3_btn = QPushButton("Grade 3x3")
        self.grid_3x3_btn.clicked.connect(lambda: self.change_grid_layout(3, 3))
        
        self.grid_4x4_btn = QPushButton("Grade 4x4")
        self.grid_4x4_btn.clicked.connect(lambda: self.change_grid_layout(4, 4))
        
        self.grid_8x8_btn = QPushButton("Grade 8x8 (64 Cams)")
        self.grid_8x8_btn.clicked.connect(lambda: self.change_grid_layout(8, 8))
        
        # Botão para abrir o Gerenciador de Dispositivos (Interface Gráfica)
        self.devices_btn = QPushButton("⚙️ Dispositivos")
        self.devices_btn.setToolTip("Cadastrar e editar condomínios, DVRs e câmeras")
        self.devices_btn.setStyleSheet("""
            QPushButton {
                background-color: #2e2e2e;
                border: 1px solid #444;
                color: #00aaff;
            }
            QPushButton:hover {
                background-color: #383838;
                border-color: #00aaff;
            }
        """)
        self.devices_btn.clicked.connect(self.open_device_manager)
        
        grid_ctrl_layout.addWidget(self.grid_2x2_btn)
        grid_ctrl_layout.addWidget(self.grid_3x3_btn)
        grid_ctrl_layout.addWidget(self.grid_4x4_btn)
        grid_ctrl_layout.addWidget(self.grid_8x8_btn)
        grid_ctrl_layout.addWidget(self.devices_btn)
        
        header_layout.addLayout(grid_ctrl_layout)
        
        content_layout.addWidget(header)
        
        # Visualizador de Páginas de Grade (Stacked Widget)
        # Permite alternar facilmente entre o modo grade e o modo tela cheia de uma câmera
        self.stacked_display = QStackedWidget()
        
        # Tela da Grade / Mosaico
        self.grid_view_widget = QWidget()
        self.grid_view_layout = QVBoxLayout(self.grid_view_widget)
        self.grid_view_layout.setContentsMargins(12, 12, 12, 12)
        
        # O Mosaico real de Grid
        self.grid_layout_area = QGridLayout()
        self.grid_layout_area.setSpacing(8)
        self.grid_view_layout.addLayout(self.grid_layout_area)
        
        # Controles de Paginação (Inferior)
        self.pagination_layout = QHBoxLayout()
        self.prev_page_btn = QPushButton("◀ Página Anterior")
        self.prev_page_btn.clicked.connect(self.show_prev_page)
        self.page_info_label = QLabel("Página 1 de 1")
        self.page_info_label.setAlignment(Qt.AlignCenter)
        self.page_info_label.setStyleSheet("font-weight: bold; font-size: 12px; color: #888888;")
        self.next_page_btn = QPushButton("Próxima Página ▶")
        self.next_page_btn.clicked.connect(self.show_next_page)
        
        self.pagination_layout.addWidget(self.prev_page_btn)
        self.pagination_layout.addWidget(self.page_info_label)
        self.pagination_layout.addWidget(self.next_page_btn)
        self.grid_view_layout.addLayout(self.pagination_layout)
        
        self.stacked_display.addWidget(self.grid_view_widget)
        
        # Tela Cheia (Exibição de Câmera Única Ampliada)
        self.fullscreen_container = QWidget()
        self.fullscreen_layout = QVBoxLayout(self.fullscreen_container)
        self.fullscreen_layout.setContentsMargins(10, 10, 10, 10)
        self.stacked_display.addWidget(self.fullscreen_container)
        
        content_layout.addWidget(self.stacked_display)
        
        main_layout.addWidget(main_content)

    def load_condominios(self):
        condos = self.config.get_condominios()
        for c in condos:
            item = QListWidgetItem(c.get("nome", "Sem Nome"))
            item.setData(Qt.UserRole, c.get("id"))
            self.condo_list.addItem(item)
            
        if self.condo_list.count() > 0:
            # Seleciona o primeiro condomínio por padrão
            self.condo_list.setCurrentRow(0)
            self.on_condominio_changed(self.condo_list.item(0))

    def on_condominio_changed(self, item):
        cond_id = item.data(Qt.UserRole)
        if self.active_condominio_id == cond_id:
            return
            
        self.active_condominio_id = cond_id
        self.condo_title_label.setText(item.text())
        self.current_page = 0
        
        # Para todos os streams ativos antes de limpar
        self.clear_active_streams()
        
        # Carrega a lista de câmeras do novo condomínio
        self.active_cameras = self.config.get_cameras_for_condominio(cond_id)
        self.update_grid_view()

    def clear_active_streams(self):
        for w in self.active_widgets:
            w.stop_stream()
            w.deleteLater()
        self.active_widgets.clear()
        
        # Limpa o grid layout
        for i in reversed(range(self.grid_layout_area.count())):
            self.grid_layout_area.itemAt(i).widget().setParent(None)

    def change_grid_layout(self, rows, cols):
        self.grid_rows = rows
        self.grid_cols = cols
        self.cameras_per_page = rows * cols
        self.current_page = 0
        
        # Atualiza a marcação dos botões de grade
        self.grid_2x2_btn.setObjectName("")
        self.grid_3x3_btn.setObjectName("")
        self.grid_4x4_btn.setObjectName("")
        self.grid_8x8_btn.setObjectName("")
        
        if rows == 2:
            self.grid_2x2_btn.setObjectName("ActiveGridBtn")
        elif rows == 3:
            self.grid_3x3_btn.setObjectName("ActiveGridBtn")
        elif rows == 4:
            self.grid_4x4_btn.setObjectName("ActiveGridBtn")
        elif rows == 8:
            self.grid_8x8_btn.setObjectName("ActiveGridBtn")
            
        # Força atualização do estilo
        self.grid_2x2_btn.style().unpolish(self.grid_2x2_btn)
        self.grid_2x2_btn.style().polish(self.grid_2x2_btn)
        self.grid_3x3_btn.style().unpolish(self.grid_3x3_btn)
        self.grid_3x3_btn.style().polish(self.grid_3x3_btn)
        self.grid_4x4_btn.style().unpolish(self.grid_4x4_btn)
        self.grid_4x4_btn.style().polish(self.grid_4x4_btn)
        self.grid_8x8_btn.style().unpolish(self.grid_8x8_btn)
        self.grid_8x8_btn.style().polish(self.grid_8x8_btn)
        
        self.update_grid_view()

    def update_grid_view(self):
        self.clear_active_streams()
        
        total_cams = len(self.active_cameras)
        total_pages = max(1, math.ceil(total_cams / self.cameras_per_page))
        
        # Corrige página corrente se necessário
        if self.current_page >= total_pages:
            self.current_page = total_pages - 1
            
        self.page_info_label.setText(f"Página {self.current_page + 1} de {total_pages}")
        
        # Habilita/Desabilita botões de paginação
        self.prev_page_btn.setEnabled(self.current_page > 0)
        self.next_page_btn.setEnabled(self.current_page < total_pages - 1)
        
        # Calcula as câmeras deste intervalo de página
        start_idx = self.current_page * self.cameras_per_page
        end_idx = min(start_idx + self.cameras_per_page, total_cams)
        
        page_cameras = self.active_cameras[start_idx:end_idx]
        
        # Cria e popula os widgets no grid
        for idx, camera in enumerate(page_cameras):
            row = idx // self.grid_cols
            col = idx % self.grid_cols
            
            cam_widget = CameraWidget()
            resolved_url = self.config.resolve_camera_url(self.active_condominio_id, camera)
            cam_widget.set_camera_data(self.active_condominio_id, camera, resolved_url)
            cam_widget.double_clicked.connect(self.on_camera_double_clicked)
            
            self.grid_layout_area.addWidget(cam_widget, row, col)
            self.active_widgets.append(cam_widget)
            cam_widget.start_stream()

    def show_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_grid_view()

    def show_next_page(self):
        total_cams = len(self.active_cameras)
        total_pages = math.ceil(total_cams / self.cameras_per_page)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_grid_view()

    def on_camera_double_clicked(self, widget):
        """Alterna entre modo mosaico e tela cheia de uma câmera específica."""
        if self.stacked_display.currentIndex() == 0:
            # --- Mosaico -> Tela Cheia ---
            # Para todos os streams do mosaico para economizar banda
            for w in self.active_widgets:
                if w != widget:
                    w.stop_stream()
            
            # Remove o widget selecionado do grid do mosaico
            self.grid_layout_area.removeWidget(widget)
            
            # Adiciona ao container de tela cheia
            self.fullscreen_layout.addWidget(widget)
            self.fullscreen_widget = widget
            
            # Atualiza para Main Stream (Maior resolução)
            widget.set_fullscreen_mode(True)
            
            # Se for modo simulação ou VLC, recarrega o fluxo
            widget.stop_stream()
            
            # Se tivermos um DVR real, recalcula a URL para Main Stream (resolução principal)
            # e reconecta
            main_camera_data = widget.camera_data.copy()
            main_camera_data["stream_tipo"] = "main"
            resolved_url_main = self.config.resolve_camera_url(self.active_condominio_id, main_camera_data)
            widget.video_player.set_camera(main_camera_data.get("nome"), resolved_url_main)
            
            widget.start_stream()
            
            # Muda a tela
            self.stacked_display.setCurrentIndex(1)
        else:
            # --- Tela Cheia -> Mosaico ---
            if self.fullscreen_widget:
                # Remove o widget do container de tela cheia
                self.fullscreen_layout.removeWidget(self.fullscreen_widget)
                
                # Reseta para Sub-Stream (Menor resolução)
                self.fullscreen_widget.set_fullscreen_mode(False)
                self.fullscreen_widget.stop_stream()
                
                # Restaura a URL do sub-stream
                sub_url = self.config.resolve_camera_url(self.active_condominio_id, self.fullscreen_widget.camera_data)
                self.fullscreen_widget.video_player.set_camera(self.fullscreen_widget.camera_data.get("nome"), sub_url)
                
                self.fullscreen_widget = None
                
            # Restaura todos os widgets de volta no mosaico e religa os streams
            self.stacked_display.setCurrentIndex(0)
            self.update_grid_view()

    def open_device_manager(self):
        """Abre o diálogo de configuração e cadastro de dispositivos."""
        # Para todos os streams ativos temporariamente para evitar concorrência de leitura de arquivo
        self.clear_active_streams()
        
        from src.ui.device_manager import DeviceManagerDialog
        dialog = DeviceManagerDialog(self.config, self)
        dialog.exec()
        
        # Recarrega a configuração modificada
        self.config.load_config()
        
        # Atualiza a sidebar de condomínios
        self.condo_list.clear()
        self.load_condominios()

    def toggle_sidebar(self):
        """Alterna a visibilidade da barra lateral (sidebar) de condomínios."""
        self.sidebar.setVisible(not self.sidebar.isVisible())

    def closeEvent(self, event):
        # Garante a desconexão de todos os players antes de encerrar o programa
        self.clear_active_streams()
        super().closeEvent(event)
