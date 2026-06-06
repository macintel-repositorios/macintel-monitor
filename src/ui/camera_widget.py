from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QCursor
from src.video_stream import VideoStreamWidget

class CameraWidget(QWidget):
    # Sinal emitido ao dar duplo clique no widget, passa o próprio widget
    double_clicked = Signal(QWidget)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.camera_data = None
        self.condominio_id = None
        self.is_fullscreen = False
        self.stream_type = "sub" # Padrão inicial no mosaico é Sub-Stream
        
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(4, 4, 4, 4)
        
        # Container com borda e sombra
        self.container = QFrame(self)
        self.container.setObjectName("CameraContainer")
        self.container.setStyleSheet("""
            QFrame#CameraContainer {
                background-color: #1a1a1a;
                border: 2px solid #2e2e2e;
                border-radius: 8px;
            }
            QFrame#CameraContainer:hover {
                border: 2px solid #00aaff;
            }
        """)
        
        container_layout = QVBoxLayout(self.container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)
        
        # Header do Widget (Nome da câmera e Tipo de Stream)
        self.header = QFrame(self.container)
        self.header.setStyleSheet("background-color: #242424; border-top-left-radius: 6px; border-top-right-radius: 6px;")
        self.header.setFixedHeight(30)
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(10, 0, 10, 0)
        
        self.name_label = QLabel("Carregando...", self.header)
        self.name_label.setStyleSheet("color: #ffffff; font-weight: bold; font-size: 11px; border: none;")
        
        self.stream_badge = QLabel("SUB", self.header)
        self.stream_badge.setStyleSheet("""
            color: #121212;
            background-color: #00ff66;
            font-size: 9px;
            font-weight: bold;
            border-radius: 3px;
            padding: 1px 4px;
            border: none;
        """)
        self.stream_badge.setToolTip("Exibindo fluxo secundário otimizado para economia de recursos.")
        
        header_layout.addWidget(self.name_label)
        header_layout.addStretch()
        header_layout.addWidget(self.stream_badge)
        
        container_layout.addWidget(self.header)
        
        # Player de Vídeo
        self.video_player = VideoStreamWidget(self.container)
        container_layout.addWidget(self.video_player)
        
        self.layout.addWidget(self.container)
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def set_camera_data(self, condominio_id, camera_data, resolved_url):
        self.condominio_id = condominio_id
        self.camera_data = camera_data
        self.name_label.setText(camera_data.get("nome", "Câmera Sem Nome"))
        
        # Define o tipo de stream baseado no status
        self.stream_type = camera_data.get("stream_tipo", "sub")
        self.update_stream_badge()
        
        self.video_player.set_camera(camera_data.get("nome", "Câmera"), resolved_url)

    def update_stream_badge(self):
        if self.stream_type == "main":
            self.stream_badge.setText("MAIN")
            self.stream_badge.setStyleSheet("""
                color: #ffffff;
                background-color: #ff3b30;
                font-size: 9px;
                font-weight: bold;
                border-radius: 3px;
                padding: 1px 4px;
                border: none;
            """)
            self.stream_badge.setToolTip("Exibindo fluxo principal em alta resolução.")
        else:
            self.stream_badge.setText("SUB")
            self.stream_badge.setStyleSheet("""
                color: #121212;
                background-color: #00ff66;
                font-size: 9px;
                font-weight: bold;
                border-radius: 3px;
                padding: 1px 4px;
                border: none;
            """)
            self.stream_badge.setToolTip("Exibindo fluxo secundário otimizado para economia de recursos.")

    def start_stream(self):
        self.video_player.play()

    def stop_stream(self):
        self.video_player.stop()

    def set_fullscreen_mode(self, is_fs):
        self.is_fullscreen = is_fs
        if is_fs:
            self.stream_type = "main"
            # Se fosse um DVR real, aqui alteraríamos a URL para puxar o canal com subtype=0
        else:
            self.stream_type = "sub"
            # Retorna para subtype=1 (Sub-Stream)
            
        self.update_stream_badge()

    def mouseDoubleClickEvent(self, event):
        self.double_clicked.emit(self)
        super().mouseDoubleClickEvent(event)
