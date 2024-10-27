# file: app.py
import streamlit as st
import tempfile
import os
import requests
from gpt_api import create_dialog_gtp04mini, create_ssml_gpt04mini, dialog_promt, ssml_promt
from voice_api import voice_synth
from parser import pdf_to_txt, url_to_txt

# Заголовок страницы
st.title("Обработчик текста и аудио")

# Основной текст
st.write("Загрузите файл или укажите URL для обработки. После обработки результат будет выведен в виде текста и аудио.")

# Форма для ввода файла и URL
file = st.file_uploader("Загрузите файл (.txt или .pdf)", type=["txt", "pdf"])
url = st.text_input("Или введите URL")

# Кнопка отправить
if st.button("Отправить"):
    if file or url:
        with tempfile.TemporaryDirectory() as temp_dir:
            text_path = None

            # Сохранение файла во временную директорию
            if file:
                if file.type == "application/pdf":
                    # Сохраняем PDF файл во временную директорию
                    pdf_path = os.path.join(temp_dir, file.name)
                    with open(pdf_path, "wb") as f:
                        f.write(file.read())

                    # Конвертируем PDF в текст
                    text_path = os.path.join(temp_dir, "uploaded_text.txt")
                    pdf_to_txt(pdf_path, text_path)

                elif file.type == "text/plain":
                    # Сохраняем текстовый файл
                    text_path = os.path.join(temp_dir, file.name)
                    with open(text_path, "wb") as f:
                        f.write(file.read())

            elif url:
                # Скачиваем текст по URL и сохраняем во временный файл
                response = requests.get(url)
                if response.status_code == 200:
                    text_path = os.path.join(temp_dir, "url_text.txt")
                    with open(text_path, "w") as f:
                        f.write(response.text)
                else:
                    st.error("Не удалось загрузить данные с указанного URL")

            # Если текст успешно сохранен
            if text_path:
                dialog_text = create_dialog_gtp04mini(dialog_promt, dialog_input_path=text_path)
                ssml_text = create_ssml_gpt04mini(ssml_promt, ssml_text=dialog_text)

                # Генерация аудио файла
                audio_path = os.path.join(temp_dir, "output_audio.wav")
                voice_synth(wav_output_path=audio_path, prompt_text=ssml_text)

                # Отображение результата на сайте
                st.subheader("Результат обработки текста:")
                st.write(dialog_text)

                st.subheader("Результат в аудио формате:")
                st.audio(audio_path, format="audio/wav")
    else:
        st.warning("Пожалуйста, загрузите файл или введите URL для обработки.")
