import json
import paho.mqtt.client as mqtt
from PyQt6.QtCore import QObject, pyqtSignal


class MqttClient(QObject):
    batida_recebida = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._client = mqtt.Client(client_id="MonitorBengalaDesktop")
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message

    def conectar(self, host: str = "localhost", port: int = 1883):
        self._client.connect(host, port, keepalive=60)
        self._client.loop_start()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[MQTT] Conectado ao broker")
            client.subscribe("bengala/+/+/batidas")
            print("[MQTT] Assinado tópico: bengala/+/+/batidas")
        else:
            print(f"[MQTT] Falha na conexão, código: {rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)
            print("[MQTT] Mensagem recebida:", data)
            self.batida_recebida.emit(data)
        except Exception as e:
            print("[MQTT] Erro ao decodificar mensagem:", e)
