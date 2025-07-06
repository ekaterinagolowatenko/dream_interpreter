from flask import Flask, request, jsonify, render_template
from gigachat import GigaChat
import requests
import re
import base64

app = Flask(__name__)


GIGACHAT_TOKEN = "YmY0YzRjNGQtY2U2Mi00ZjA1LWFiZDMtNGI4ZTEwNDQyYjFlOjhhYjU5OTEwLTA3MzYtNDAyMS1hZmMwLWI0ZDliYTUzNGE4OA=="
APIHOST_API_KEY = "KtrRmz1MWWwBw09zmoHIblojtaz5xhvD"
DEEPSEEK_API_KEY = "sk-c37d56ce2f65428b8a410342b317c468"




def generate_image_and_interpretate(prompt):
    # giga = GigaChat(
    #     credentials=GIGACHAT_TOKEN,
    # )

    # response = giga.get_token()

    url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

    payload='scope=GIGACHAT_API_PERS'
    headers = {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Accept': 'application/json',
    'RqUID': '8a89284c-cb64-4568-9c70-ace867381fd3',
    'Authorization': f'Basic {GIGACHAT_TOKEN}'
    }

    response = requests.request("POST", url, headers=headers, data=payload, verify=False)
    token = response.json()['access_token']


    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions" 
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {
            "model": "GigaChat",
            "messages": [
                {
                "role": "system",
                "content": "Ты — Василий Кандинский"      
                },
                {
                "role": "user",
                "content": f"Нарисуй одно изображение по следующему описанию сна {prompt}."
                }
            ],
            "function_call": "auto"
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)
    if response.status_code != 200:
        raise Exception(f"Ошибка при генерации изображения: {response.text}")
    data = response.json()

    regexp_img_id = re.compile("<img src=\\\"(.+)\\\" fuse=\\\"true\\\"\/>")

    img_id = regexp_img_id.match(data['choices'][0]['message']['content']).group(1)

    url = f"https://gigachat.devices.sberbank.ru/api/v1/files/{img_id}/content"
    response = requests.request("GET", url, headers=headers, verify=False)
    print(token)
    print(img_id)
    with open('static/image.jpg', mode="wb") as fd:
        fd.write(response.content)

    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions" 
    payload = {
            "model": "GigaChat-Pro",
            "messages": [
                {
                "role": "user",
                "content": f"Что изображено на рисунке? Пиши без 'на картинке изображено', только описание картинки",
                "attachments": [img_id]
                }
            ],
            "temperature": 0.1
    }

    response = requests.post(url, headers=headers, json=payload, verify=False)
    data = response.json()
    image_description = data['choices'][0]['message']['content']
    url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions" 
    payload = {
            "model": "GigaChat",
            "messages": [
                {
                "role": "system",
                "content": "Ты — прорицатель, великий толкователь снов"      
                },
                {
                "role": "user",
                "content": f"Чтобы мог означать такой сон?: {data['choices'][0]['message']['content']}. Ответь только текстом и не вставляй картинок."
                }
            ],
            "function_call": "auto"
    }
    response = requests.post(url, headers=headers, json=payload, verify=False)
    data = response.json()
    dream_interpretation = data['choices'][0]['message']['content']
    return {
        'description': image_description,
        'interpretation': dream_interpretation
    }



def describe_image(image_url):
    url = "https://apihost.ru/api/vision" 
    headers = {
        "Authorization": f"Bearer {APIHOST_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "image_url": image_url,
        "tasks": ["caption"]
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Ошибка при описании изображения: {response.text}")
    return response.json()["results"]["caption"]



def interpret_dream(description):
    url = "https://api.deepseek.com/chat/completions" 
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "user", "content": f"Шуточно растолкуй мне этот сон: {description}"}
        ],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code != 200:
        raise Exception(f"Ошибка при толковании сна: {response.text}")
    return response.json()["choices"][0]["message"]["content"]



@app.route("/")
def index():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    dream_text = data.get("dream", "")

    if not dream_text:
        return jsonify({"error": "Нет текста сна"}), 400

    try:
       

        return jsonify(generate_image_and_interpretate(dream_text))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    from waitress import serve
    serve(app, host='192.168.0.13', port='8000')