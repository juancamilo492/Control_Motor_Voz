import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import paho.mqtt.client as paho
import json
import torch
from transformers import pipeline

# Configuración del modelo de NLP
classifier = pipeline("zero-shot-classification")

def on_publish(client, userdata, result):  # Callback
    print("El dato ha sido publicado \n")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received = str(message.payload.decode("utf-8"))
    st.write(message_received)

broker = "broker.mqttdashboard.com"
port = 1883
client1 = paho.Client("AppServoVoz")
client1.on_message = on_message

st.title("Interfaces Multimodales")
st.subheader("CONTROL POR VOZ")

image = Image.open('voice_ctrl.jpg')
st.image(image, width=200)

st.write("Toca el Botón y habla ")

# Botón para reconocimiento de voz
stt_button = Button(label=" Inicio ", width=200)

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

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0)

# Categorías para clasificar los mensajes
categories = ["abre la puerta", "cierra la puerta", "enciende las luces", "apaga las luces"]

if result:
    if "GET_TEXT" in result:
        recognized_text = result.get("GET_TEXT").strip()  # Almacena el texto reconocido
        st.write("Texto reconocido:", recognized_text)

        # Usar el clasificador para predecir el comando
        predictions = classifier(recognized_text, categories)
        predicted_label = predictions['labels'][0]  # Obtener la etiqueta más probable

        # Si la confianza es suficientemente alta, enviar el mensaje
        if predictions['scores'][0] > 0.7:  # Ajusta el umbral de confianza según sea necesario
            message = json.dumps({"Act1": predicted_label})
            client1.publish("mensajeUsuario", message)
            st.success(f"Mensaje enviado: {predicted_label}")
        else:
            st.warning("No se reconoció ningún comando válido.")

# Crear columnas para los controles manuales
col1, col2 = st.columns(2)

# Columna para Control de puerta manual
with col1:
    st.subheader("Control de puerta manual")
    if st.button("Abrir"):
        message = json.dumps({"Act1": "abre la puerta"})
        client1.publish("mensajeUsuario", message)
        st.success("Mensaje enviado: abre la puerta")
    if st.button("Cerrar"):
        message = json.dumps({"Act1": "cierra la puerta"})
        client1.publish("mensajeUsuario", message)
        st.success("Mensaje enviado: cierra la puerta")

# Columna para Control de luz manual
with col2:
    st.subheader("Control de luz manual")
    if st.button("Encender"):
        message = json.dumps({"Act1": "enciende las luces"})
        client1.publish("mensajeUsuario", message)
        st.success("Mensaje enviado: enciende las luces")
    if st.button("Apagar"):
        message = json.dumps({"Act1": "apaga las luces"})
        client1.publish("mensajeUsuario", message)
        st.success("Mensaje enviado: apaga las luces")

try:
    os.mkdir("temp")
except:
    pass
