import sys
import os
from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QColor, QPalette, QFont

# Tenta importar o módulo python-vlc
VLC_AVAILABLE = False
try:
    import vlc
    # Tenta criar uma instância para validar se as DLLs do VLC estão no path (principalmente no Windows)
    _test_instance = vlc.Instance()
    VLC_AVAILABLE = True
except Exception as e:
    print(f"Aviso: libVLC/python-vlc não está disponível. Usando modo de simulação. Detalhe: {e}")

class VideoStreamWidget(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Sunken)
        self.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333333; border-radius: 4px;")
        
        self.camera_name = "Câmera"
        self.stream_url = ""
        self.is_playing = False
        
        # Layout principal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Label de status / erro / simulação
        self.status_label = QLabel("Conectando...", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #aaaaaa; font-size: 12px; background: transparent;")
        self.layout.addWidget(self.status_label)
        
        # VLC Player
        self.vlc_instance = None
        self.vlc_player = None
        
        if VLC_AVAILABLE:
            # Configurações do VLC para ultra-baixa latência em CFTV/RTSP
            args = [
                '--quiet',
                '--no-xlib',
                '--network-caching=100',      # Reduz buffer de rede para 100ms (padrão é 1000ms+)
                '--live-caching=100',         # Reduz buffer de live streams para 100ms
                '--clock-synchro=0',          # Desativa sincronia de relógio rígida
                '--clock-jitter=0',
                '--no-audio',                 # Desativa áudio (remove buffer de sincronização A/V)
                '--no-video-title-show',      # Não exibe o título preto do stream sobre o vídeo
                '--drop-late-frames',         # Descarta quadros atrasados na decodificação
                '--skip-frames',              # Pula quadros se a CPU/GPU do PC atrasar
                '--rtsp-tcp'                  # Força RTSP via TCP (evita perda de pacotes e artefatos)
            ]
            self.vlc_instance = vlc.Instance(args)
            self.vlc_player = self.vlc_instance.media_player_new()
        else:
            # Timer de simulação (simula frames/movimento caso VLC não esteja disponível)
            self.sim_timer = QTimer(self)
            self.sim_timer.timeout.connect(self._update_simulation)
            self.sim_counter = 0

    def set_camera(self, name, url):
        self.camera_name = name
        self.stream_url = url
        self.status_label.setText(f"{self.camera_name}\nConectando stream...")
        
    def play(self):
        if self.is_playing:
            return
            
        if VLC_AVAILABLE and self.vlc_player and self.stream_url:
            try:
                # Carrega a mídia
                media = self.vlc_instance.media_new(self.stream_url)
                self.vlc_player.set_media(media)
                
                # Associa a renderização da janela ao ID deste widget do Qt
                # Windows
                if sys.platform.startswith('win'):
                    self.vlc_player.set_hwnd(int(self.winId()))
                # Linux
                elif sys.platform.startswith('linux'):
                    self.vlc_player.set_xwindow(int(self.winId()))
                # macOS
                elif sys.platform.startswith('darwin'):
                    self.vlc_player.set_nsobject(int(self.winId()))
                
                self.vlc_player.play()
                self.is_playing = True
                self.status_label.hide() # Esconde a label de texto para mostrar o vídeo
            except Exception as e:
                self.status_label.setText(f"Erro VLC:\n{e}")
                self.status_label.show()
        else:
            # Simula player ativo
            self.is_playing = True
            self.status_label.show()
            if not VLC_AVAILABLE:
                self.sim_timer.start(500) # atualiza a cada 500ms

    def stop(self):
        if not self.is_playing:
            return
            
        if VLC_AVAILABLE and self.vlc_player:
            self.vlc_player.stop()
        else:
            self.sim_timer.stop()
            
        self.is_playing = False
        self.status_label.setText(f"{self.camera_name}\nDesconectado")
        self.status_label.show()

    def _update_simulation(self):
        """Método apenas para fins de desenvolvimento se o VLC não estiver instalado."""
        self.sim_counter += 1
        dots = "." * (self.sim_counter % 4)
        self.status_label.setText(
            f"🎥 {self.camera_name}\n"
            f"[Modo Simulação - Sem libVLC]\n"
            f"Exibindo: {self.stream_url.split('/')[-1]}\n"
            f"Recebendo dados{dots}"
        )

    def mouseDoubleClickEvent(self, event):
        # Propaga o evento de duplo clique para a interface pai gerenciar o Zoom/Tela Cheia
        super().mouseDoubleClickEvent(event)
