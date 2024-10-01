import os
import streamlit as st
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events
from PIL import Image
import time
import paho.mqtt.client as paho
import json
from googletrans import Translator

def on_publish(client, userdata, result):  # create function for callback
    print("el dato ha sido publicado \n")
    pass

def on_message(client, userdata, message):
    global message_received
    time.sleep(2)
    message_received = str(message.payload.decode("utf-8"))
    st.write(message_received)

broker = "broker.mqttdashboard.com"
port = 1883
client1 = paho.Client("MOTOR_WEB_APP_VOICE")  # CAMBIAR
client1.on_message = on_message

st.title("Interfaces Multimodales")
st.subheader("CONTROL POR VOZ")

image = Image.open('voice_ctrl.jpg')
st.image(image, width=200)

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
            document.dispatchEvent(new CustomEvent("GET_TEXT", {detail: value}));
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

        # Language detection
        translator = Translator()
        detected_language = translator.detect(recognized_text)

        # Mapping of language codes to full names
        language_map = {
            'en': 'Inglés',
            'es': 'Español',
            'fr': 'Francés',
            'de': 'Alemán',
            'it': 'Italiano',
            'pt': 'Portugués',
            'zh-cn': 'Chino Simplificado',
            'ja': 'Japonés',
            'ru': 'Ruso',
            # Add more languages as needed
        }

        # Get the full language name
        language_name = language_map.get(detected_language.lang, detected_language.lang)
        confidence_percentage = detected_language.confidence * 100  # Convert to percentage

        st.write(f"Idioma reconocido: {language_name} (Confianza: {confidence_percentage:.2f}%)")

        # If the recognized language is not Spanish, translate the text
        if detected_language.lang != 'es':
            translated_text = translator.translate(recognized_text, src=detected_language.lang, dest='es').text
            st.write("Texto traducido:", translated_text)

        client1.on_publish = on_publish
        client1.connect(broker, port)
        message = json.dumps({"Act1": recognized_text})
        ret = client1.publish("CONTROL_VOZ", message)

    try:
        os.mkdir("temp")
    except:
        pass
