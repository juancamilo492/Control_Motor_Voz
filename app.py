import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
import paho.mqtt.client as paho
import json
from googletrans import Translator

# Mapeo de códigos de idiomas a nombres completos
language_names = {
    'es': 'Español',
    'en': 'Inglés',
    'fr': 'Francés',
    'de': 'Alemán',
    'pt': 'Portugués',
    'it': 'Italiano',
    'zh-cn': 'Chino Simplificado',
    'ja': 'Japonés',
    'ru': 'Ruso',
    # Agrega más idiomas según sea necesario
}

def on_publish(client, userdata, result):  # Callback
    print("El dato ha sido publicado \n")
    pass

def on_message(client, userdata, message):
    global message_received
    message_received = str(message.payload.decode("utf-8"))
    st.write(message_received)  # Muestra el mensaje en Streamlit

broker = "broker.mqttdashboard.com"
port = 1883
client1 = paho.Client("MOTOR_WEB_APP_VOICE")  # Cambiar
client1.on_message = on_message
client1.connect(broker, port)
client1.subscribe("CONTROL_VOZ")
client1.loop_start()  # Comienza el bucle del cliente MQTT

st.title("Interfaces Multimodales")
st.subheader("CONTROL POR VOZ")

st.write("Toca el Botón y habla ")

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

if result:
    if "GET_TEXT" in result:
        recognized_text = result.get("GET_TEXT").strip()
        st.write("Texto escuchado:", recognized_text)

        # Procesar el texto recibido y verificar el idioma y la confianza
        translator = Translator()
        detected_language = translator.detect(recognized_text)
        language_code = detected_language.lang
        confidence = detected_language.confidence * 100  # Convertir a porcentaje

        # Obtener el nombre completo del idioma
        language_name = language_names.get(language_code, language_code.capitalize())  # Usa el nombre del idioma, o el código si no se encuentra

        st.write(f"Idioma reconocido: {language_name}")  # Muestra el idioma reconocido
        st.write(f"Nivel de confianza: {confidence:.2f}%")  # Muestra el nivel de confianza

        # Si el idioma no es español, traducir el texto
        if language_code != 'es':
            translation = translator.translate(recognized_text, dest='es')  # Traduce al español
            translated_text = translation.text
            st.write(f"Traducción: {translated_text}")  # Muestra la traducción

            # Publicar la traducción en MQTT para el servo
            message = json.dumps({"Act1": translated_text.strip()})  # Envía la traducción al servo
            client1.publish("CONTROL_VOZ", message)
        else:
            # Publicar el texto original en MQTT para el servo si es español
            message = json.dumps({"Act1": recognized_text.strip()})
            client1.publish("CONTROL_VOZ", message)
