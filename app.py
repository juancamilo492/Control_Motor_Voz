import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import paho.mqtt.client as paho
import json

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
client1 = paho.Client("MOTOR_WEB_APP_VOICE")  # Cambiar
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

# Campo de texto para enviar mensajes manualmente
user_input = st.text_input("Escribe tu mensaje aquí:", "")

# Botón para enviar el mensaje escrito
if st.button("Enviar mensaje"):
    if user_input:
        client1.on_publish = on_publish                            
        client1.connect(broker, port)  
        message = json.dumps({"Act1": user_input.strip()})
        ret = client1.publish("CONTROL_VOZ", message)
        st.success("Mensaje enviado: " + user_input)  # Muestra el mensaje enviado
    else:
        st.warning("Por favor, escribe un mensaje antes de enviar.")  # Aviso si el campo está vacío

result = streamlit_bokeh_events(
    stt_button,
    events="GET_TEXT",
    key="listen",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0)

if result:
    if "GET_TEXT" in result:
        recognized_text = result.get("GET_TEXT").strip()
        st.write("Texto reconocido:", recognized_text)
        client1.on_publish = on_publish                            
        client1.connect(broker, port)  
        message = json.dumps({"Act1": recognized_text})
        ret = client1.publish("CONTROL_VOZ", message)

    try:
        os.mkdir("temp")
    except:
        pass
