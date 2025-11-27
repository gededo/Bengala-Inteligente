import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSystemTrayIcon, QStyle
)
from PyQt6.QtCore import pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6 import uic # Importa a biblioteca para carregar o .ui

class MainWindow(QMainWindow):
    """
    Janela Principal que carrega a interface do arquivo .ui
    """
    
    def __init__(self):
        super().__init__()
        
        # Carrega a interface do arquivo .ui
        # Esta linha substitui todo o código de "setup_ui()"
        uic.loadUi("main_window.ui", self)
        
        # O PyQt automaticamente encontra os widgets pelo 'objectName'
        # que você definiu no Designer (ex: self.history_list)
        
        # Nós só precisamos conectar os sinais (cliques) dos botões:
        self.simulate_weak_button.clicked.connect(self.simular_batida_fraca)
        self.simulate_medium_button.clicked.connect(self.simular_batida_media)
        self.simulate_strong_button.clicked.connect(self.simular_batida_forte)

        self.setup_tray_icon()
        
        # Mostra a janela que foi carregada
        self.show()

    def setup_tray_icon(self):
        """Configura o ícone da bandeja do sistema para notificações."""
        self.tray_icon = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Monitor de Bengala")
        self.tray_icon.show()

    @pyqtSlot()
    def simular_batida_forte(self):
        """Simula uma batida forte, gerando alerta visual e notificação."""
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - BATIDA FORTE (Simulada)"
        
        # Acessa o label 'last_impact_label' definido no .ui
        self.last_impact_label.setText(f"BATIDA FORTE! \n{timestamp}")
        self.last_impact_label.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #D32F2F; padding: 10px; border: 1px solid #D32F2F; border-radius: 5px; background-color: #FFEBEE;"
        )
        
        self.show_notification("Alerta de Bengala", "Batida forte detectada!")
        
        # Acessa a lista 'history_list' definida no .ui
        self.history_list.insertItem(0, log_entry)

    @pyqtSlot()
    def simular_batida_media(self):
        """Simula uma batida média, apenas registrando no histórico."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Batida Média (Simulada)"
        self.history_list.insertItem(0, log_entry)

    @pyqtSlot()
    def simular_batida_fraca(self):
        """Simula uma batida fraca, apenas registrando no histórico."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - Batida Fraca (Simulada)"
        self.history_list.insertItem(0, log_entry)

    def show_notification(self, title, message):
        """Mostra uma notificação de balão na bandeja do sistema."""
        self.tray_icon.showMessage(title, message, QSystemTrayIcon.MessageIcon.Warning, 3000)

    def closeEvent(self, event):
        """Garante que o ícone da bandeja seja fechado com o app."""
        self.tray_icon.hide()
        event.accept()

# Ponto de entrada da aplicação
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    app.setWindowIcon(QIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)))

    window = MainWindow()
    # A janela já é mostrada dentro do __init__
    
    sys.exit(app.exec())