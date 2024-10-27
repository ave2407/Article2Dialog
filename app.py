import streamlit as st
import tempfile
import os
import sqlite3
import validators
from gpt_api import create_dialog_gtp04mini, create_ssml_gpt04mini, dialog_promt, ssml_promt
from voice_api import voice_synth
from parser import pdf_to_txt, url_to_txt
from nltk import download
from nltk.corpus import stopwords
from newspaper.article import ArticleException

# Загрузка необходимых ресурсов для nltk
download('stopwords')
download('punkt')
stop_words = stopwords.words('russian')

# Инициализация базы данных для хранения истории
conn = sqlite3.connect('dialog_history.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS history 
             (id INTEGER PRIMARY KEY, source TEXT, dialog TEXT, audio_path TEXT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')
conn.commit()


# Функция для сохранения истории диалогов
def save_to_history(source, dialog, audio_path):
    c.execute("INSERT INTO history (source, dialog, audio_path) VALUES (?, ?, ?)", (source, dialog, audio_path))
    conn.commit()


# Описание проекта
st.title("👨‍👧 Преобразование текста в диалог с синтезом речи")
st.write(
    "Этот сервис предназначен для автоматического преобразования новостных и обзорных текстов в "
    "диалоговый формат между отцом и дочерью. Тексты сложных тем преобразуются в понятный диалог, "
    "который затем озвучивается, чтобы подростки могли лучше понимать важные темы. "
    "Вы можете загрузить текстовый файл, PDF, или указать URL-адрес статьи."
)

# Секция для загрузки файла или ввода URL
file = st.file_uploader("📄 Загрузите файл (.txt или .pdf)", type=["txt", "pdf"])
url = st.text_input("🌐 Или введите URL статьи")

# Размещаем кнопки в ряд
col1, col2 = st.columns(2)

# Кнопка генерации диалога
with col1:
    generate_button = st.button("Создать диалог")

# Кнопка для просмотра истории
with col2:
    history_button = st.button("Показать историю диалогов")

# Логика кнопки генерации диалога с прогресс-баром и аудио
if generate_button:
    if file or url:
        st.info("⏳ Идет обработка...")
        progress = st.progress(0)

        with tempfile.TemporaryDirectory() as temp_dir:
            text_path = None
            # Этап 1: Обработка файла или URL
            st.text("📂 Обработка файла или URL")
            progress.progress(0.25)

            # Проверка и обработка файла или URL
            if file:
                if file.type == "application/pdf":
                    pdf_path = os.path.join(temp_dir, file.name)
                    with open(pdf_path, "wb") as f:
                        f.write(file.read())
                    text_path = os.path.join(temp_dir, "uploaded_text.txt")
                    pdf_to_txt(pdf_path, text_path)
                elif file.type == "text/plain":
                    text_path = os.path.join(temp_dir, file.name)
                    with open(text_path, "w", encoding='utf-8') as f:
                        f.write(file.read().decode('utf-8'))
            elif url:
                if validators.url(url):
                    text_path = os.path.join(temp_dir, "url_text.txt")
                    try:
                        url_to_txt(url, text_path)
                    except ArticleException as e:
                        st.error(f"Ошибка загрузки статьи: {e}. Проверьте корректность URL.")
                        text_path = None  # Сбрасываем text_path при ошибке

            # Этап 2: Генерация диалога
            if text_path:
                st.text("🗣️ Генерация диалога")
                progress.progress(0.5)

                dialog_text = create_dialog_gtp04mini(dialog_promt, dialog_input_path=text_path)
                ssml_text = create_ssml_gpt04mini(ssml_promt, ssml_text=dialog_text)

                # Отображение диалога, даже если синтез речи не удается
                st.success("✅ Диалог успешно создан!")
                st.subheader("Сгенерированный диалог")
                st.write(dialog_text)

                # Этап 3: Синтез речи с обработкой ошибок
                audio_path = os.path.join(temp_dir, "output_audio.wav")
                try:
                    st.text("🎙️ Синтез речи")
                    progress.progress(0.75)
                    voice_synth(wav_output_path=audio_path, prompt_text=ssml_text)
                    st.text("✅ Завершение обработки")
                    progress.progress(1.0)

                    # Воспроизведение аудио на сайте
                    st.subheader("Прослушать диалог")
                    st.audio(audio_path, format="audio/wav")

                    # Кнопка для скачивания аудиофайла
                    with open(audio_path, "rb") as f:
                        st.download_button(label="📥 Скачать аудио", data=f, file_name="dialog_audio.wav",
                                           mime="audio/wav")

                except Exception as e:
                    # Если синтез не удается, выводим сообщение об ошибке
                    st.error(f"Ошибка синтеза речи: {e}")
                    st.warning("Диалог отображен, но синтез речи недоступен.")

                # Сохранение диалога в историю, независимо от успеха синтеза
                source = file.name if file else url
                save_to_history(source, dialog_text, audio_path if os.path.exists(audio_path) else None)

# Логика кнопки истории
if history_button:
    c.execute("SELECT * FROM history ORDER BY timestamp DESC")
    rows = c.fetchall()
    for row in rows:
        st.write(f"Источник: {row[1]}, Дата: {row[4]}")
        st.write("Диалог:")
        st.write(row[2])
        audio_path = row[3]
        if audio_path and os.path.exists(audio_path):
            # Воспроизведение и скачивание аудио из истории
            st.subheader("Прослушать диалог")
            st.audio(audio_path, format="audio/wav")
            with open(audio_path, "rb") as f:
                st.download_button(label="📥 Скачать аудио", data=f, file_name="dialog_audio.wav", mime="audio/wav")
        st.divider()
