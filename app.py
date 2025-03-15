import os
import streamlit as st
import time
import json
import paho.mqtt.client as mqtt
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image

# Configuración de MQTT
broker = "broker.emqx.io"
port = 1883
topic = "mensajeUsuario"  # Tema MQTT que coincide con el código de Wokwi

# Callback de publicación
def on_publish(client, userdata, result):
    print("Mensaje publicado correctamente")
    pass

# Callback de recepción de mensajes
def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received = str(message.payload.decode("utf-8"))
    st.write("Mensaje recibido:", message_received)

# Configuración del cliente MQTT
client = mqtt.Client("AppServoVoz")
client.on_publish = on_publish
client.on_message = on_message
client.connect(broker, port)

# Interfaz de Streamlit
st.title("Control de Servo y Luces")
st.subheader("Control por Voz y Manual")

image = Image.open('voice_ctrl.jpg')
st.image(image, width=200)

st.write("Presiona el botón y habla para enviar comandos.")

# Botón de reconocimiento de voz
stt_button = Button(label="Inicio", width=200)

stt_button.js_on_event("button_click", CustomJS(code="""
    var recognition = new webkitSpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
 
    recognition.onresult = function (e) {
        var value = "";
        for (var i = e.resultIndex; i < e.results.length; ++i) {
            if (e.results[i].isFinal) {
                value += e.results[i][0].transcript;
            }
        }
        if (value != "") {
            document.dispatchEvent(new CustomEvent("GET_TEXT", { detail: value }));
        }
    }
    recognition.start();
"""))

# Variable para el texto reconocido
recognized_text = ""

# Ejecuta el reconocimiento de voz y obtiene el texto
result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0
)

if result:
    if "GET_TEXT" in result:
        recognized_text = result.get("GET_TEXT").strip()
        st.write("Texto reconocido:", recognized_text)

        # Publica el comando en MQTT
        message = json.dumps({"Act1": recognized_text})
        client.publish(topic, message)
        st.success(f"Comando enviado: {recognized_text}")

# Controles manuales
col1, col2 = st.columns(2)

with col1:
    st.subheader("Control de Puerta")
    if st.button("Abrir Puerta"):
        message = json.dumps({"Act1": "abre la puerta"})
        client.publish(topic, message)
        st.success("Mensaje enviado: abre la puerta")
    if st.button("Cerrar Puerta"):
        message = json.dumps({"Act1": "cierra la puerta"})
        client.publish(topic, message)
        st.success("Mensaje enviado: cierra la puerta")

with col2:
    st.subheader("Control de Luces")
    if st.button("Encender Luces"):
        message = json.dumps({"Act1": "enciende las luces"})
        client.publish(topic, message)
        st.success("Mensaje enviado: enciende las luces")
    if st.button("Apagar Luces"):
        message = json.dumps({"Act1": "apaga las luces"})
        client.publish(topic, message)
        st.success("Mensaje enviado: apaga las luces")

# Verificación de carpeta temporal
try:
    os.mkdir("temp")
except:
    pass
