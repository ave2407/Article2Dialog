from openai import OpenAI
import os

OPENAI_API_KEY = "sk-WtQcuu7ZV6tXfUOhapb2JzORObV42kRF"
# OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")


client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url="https://api.proxyapi.ru/openai/v1",
)


def send_request_to_gpt4_mini(text, file_path):
    with open(file_path, "r", encoding='utf-8') as file:
        file_content = file.read()  # Считываем текст файла

        # Выполняем запрос с текстом и файлом
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user",
                 "content": f"{text}\n\nСодержимое файла:\n{file_content}"}
            ]
        )

    # Возвращаем ответ
    return response.choices[0].message.content


# Пример использования функции
file_path = r'C:\Users\Vladimir\PycharmProjects\cueta_repo\parser\output_with_latex_clean.txt'
base_promt = """Преобразуй данную статью в формате диалога между отцом и дочерью-подростком. Отец должен объяснять суть текста простыми, понятными словами, избегая сложных терминов, а также отвечать на вопросы дочери, которые помогают раскрыть и уточнить основные идеи. Начинай с краткого объяснения темы, а затем используй диалог, чтобы глубже раскрыть содержание, акцентируя внимание на ключевых моментах. Диалог должен быть сбалансированным: дочери — вопросы, отцу — ответы, без потери важной информации.

Пример структуры диалога:

Дочь: "Пап, о чем эта статья?"
Отец: "Эта статья говорит о ...."
Дочь: "А что это за задача?"
Отец: "...".
Задача: Сделать объяснения короткими, но исчерпывающими. Заверши диалог, подытожив главные выводы статьи.
"""

response = send_request_to_gpt4_mini(base_promt, file_path)
print(response)
