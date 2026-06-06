import sys
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from src.ui.main_window import MainWindow

def main():
    # Garante suporte adequado a displays de alta densidade de pixels (High DPI)
    # No PySide6 isso é ativado por padrão, mas configuramos atributos para consistência
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    
    app = QApplication(sys.argv)
    
    # Aplica o estilo Fusion para obter um visual limpo e unificado em qualquer SO (Windows/Linux)
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    # Garante que o diretório de execução principal seja a pasta raiz do script
    # para que as importações e caminhos de arquivos relativos funcionem corretamente.
    script_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, script_dir)
    os.chdir(script_dir)
    
    main()
