import sys
import os
import csv
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QSystemTrayIcon, QStyle
)
from PyQt6.QtCore import pyqtSlot, QDateTime
from PyQt6.QtGui import QIcon
from PyQt6 import uic

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

from mqtt_client_qt import MqttClient  # garante que este arquivo existe


# ==========================
# INICIALIZAÇÃO DO FIREBASE
# ==========================

FIREBASE_KEY = "bengala-inteligente-firebase-adminsdk-fbsvc-a6724b6281.json"

if not os.path.exists(FIREBASE_KEY):
    print(f"[ERRO FATAL] Arquivo de chave Firebase NÃO encontrado: {FIREBASE_KEY}")
else:
    try:
        print("[Firebase] Carregando chave:", FIREBASE_KEY)

        cred = credentials.Certificate(FIREBASE_KEY)
        firebase_admin.initialize_app(cred, {
            "databaseURL": "https://bengala-inteligente-default-rtdb.firebaseio.com/"
        })

        print("[Firebase] Inicializado com sucesso!")

    except Exception as e:
        print("[Firebase] Falha ao inicializar:")
        print(">>> ERRO COMPLETO ABAIXO:")
        print(e)



# ==========================
# SALVAMENTOS LOCAL & ONLINE
# ==========================

def salvar_historico(intensidade: str, tipo: str = "Simulada"):
    """Tenta enviar registro ao Firebase."""
    ref = db.reference("bd_bengala/historico")
    ref.push().set({
        "intensidade": intensidade,
        "data": datetime.now().isoformat(),
        "tipo": tipo
    })
    print(f"[Firebase] Enviado: {intensidade} ({tipo})")


def salvar_offline_csv(intensidade: str, tipo: str):
    """Grava localmente quando offline."""
    caminho = "dados_offline.csv"
    existe = os.path.exists(caminho)

    with open(caminho, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not existe:
            writer.writerow(["data", "hora", "intensidade", "tipo"])

        agora = datetime.now()
        writer.writerow([
            agora.date().isoformat(),
            agora.time().strftime("%H:%M:%S"),
            intensidade,
            tipo
        ])

    print(f"[OFFLINE] Salvo em CSV: {intensidade} ({tipo})")



# ==========================
# JANELA PRINCIPAL
# ==========================

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        # Carregar interface
        uic.loadUi("main_window.ui", self)

        # Conectar botões de simulação
        self.simulate_weak_button.clicked.connect(
            lambda: self.registrar_batida("fraca", tipo="Simulada")
        )
        self.simulate_medium_button.clicked.connect(
            lambda: self.registrar_batida("media", tipo="Simulada")
        )
        self.simulate_strong_button.clicked.connect(
            lambda: self.registrar_batida("forte", tipo="Simulada")
        )

        # Botão de sincronizar CSV → Firebase
        if hasattr(self, "sync_button"):
            self.sync_button.clicked.connect(self.sincronizar_offline)

        # Tray icon
        self.setup_tray_icon()

        # MQTT
        self.mqtt = MqttClient(self)
        self.mqtt.batida_recebida.connect(self.on_batida_mqtt)

        # Conectar ao Mosquitto local
        print("[MQTT] Conectando ao broker localhost:1883...")
        self.mqtt.conectar(host="localhost", port=1883)

        self.show()



    # =============================
    # RECEBIMENTO MQTT
    # =============================

    @pyqtSlot(dict)
    def on_batida_mqtt(self, dados: dict):

        intensidade = (dados.get("intensidade") or "").lower()

        print(f"[MQTT] Recebido → {intensidade}")

        if intensidade not in ("fraca", "media", "forte"):
            intensidade = "desconhecida"

        self.registrar_batida(intensidade, tipo="MQTT")



    # =============================
    # REGISTRO UNIFICADO (UI + CSV + Firebase)
    # =============================

    def registrar_batida(self, intensidade_cod: str, tipo: str):

        ts = QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss")

        intensidade_cod = intensidade_cod.lower()

        mapa = {
            "fraca": ("Batida Fraca", "Fraca"),
            "media": ("Batida Média", "Média"),
            "forte": ("BATIDA FORTE!", "Forte")
        }

        texto_hist = mapa.get(intensidade_cod, ("Desconhecida", "Desconhecida"))[0]
        intensidade_fb = mapa.get(intensidade_cod, ("", ""))[1]

        # Atualização UI
        if intensidade_cod == "forte":
            self.last_impact_label.setText(f"{texto_hist}\n{ts}")
            self.last_impact_label.setStyleSheet(
                "font-size: 14pt; font-weight: bold; color: #D32F2F; padding: 10px;"
                "border: 1px solid #D32F2F; border-radius: 5px; background-color: #FFEBEE;"
            )
            self.show_notification("Bengala", "Batida Forte Detectada!")

        # Histórico visual
        self.history_list.insertItem(0, f"{ts} - {texto_hist} ({tipo})")

        # Sempre salvar offline
        if intensidade_fb:
            salvar_offline_csv(intensidade_fb, tipo)

            # Tentar enviar ao Firebase
            try:
                salvar_historico(intensidade_fb, tipo)
            except Exception as e:
                print("[Firebase] Falha ao enviar agora, ficará só no CSV.")
                print("Erro:", e)



    # =============================
    # NOTIFICAÇÕES
    # =============================

    def setup_tray_icon(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)
        self.tray_icon.setIcon(icon)
        self.tray_icon.show()

    def show_notification(self, title, msg):
        self.tray_icon.showMessage(title, msg, QSystemTrayIcon.MessageIcon.Warning, 3000)



    # =============================
    # SINCRONIZAÇÃO OFFLINE → FIREBASE
    # =============================

    def sincronizar_offline(self):

        caminho = "dados_offline.csv"

        if not os.path.exists(caminho):
            print("[SYNC] Nenhum arquivo CSV encontrado.")
            return

        print("[SYNC] Enviando dados do CSV → Firebase...")

        try:
            ref = db.reference("bd_bengala/historico")

            with open(caminho, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for linha in reader:
                    ref.push().set({
                        "intensidade": linha["intensidade"],
                        "data": f"{linha['data']}T{linha['hora']}",
                        "tipo": linha["tipo"]
                    })

            print("[SYNC] Dados enviados com sucesso!")
            os.remove(caminho)

        except Exception as e:
            print("[SYNC] ERRO AO SINCRONIZAR:")
            print(e)



# =============================
# PONTO DE ENTRADA
# =============================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(app.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxWarning)))

    window = MainWindow()
    sys.exit(app.exec())
