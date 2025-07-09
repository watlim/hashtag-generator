import datetime
import json
import os

import functions_framework
from flask import jsonify, make_response
from google import genai
from google.cloud import pubsub


@functions_framework.http
def publish(request):
    # ✅ CORS Preflight
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    # ✅ CORS headers สำหรับ main request
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type'
    }

    try:
        request_json = request.get_json(silent=True)
        request_args = request.args

        publisher = pubsub.PublisherClient()
        topic_path = os.getenv("TOPIC")

        client = genai.Client(api_key=os.getenv("API_KEY"))

        # ✅ รับค่าจาก JSON หรือ args
        name = request_json.get("name") if request_json else request_args.get("name", "anonymous")
        message = request_json.get("message") if request_json else request_args.get("message")

        if not message:
            return make_response(jsonify({"error": "Missing message"}), 400, headers)

        # ✅ ประมวลผลข้อความ
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f'Please classify the message "{message}" into array of appropriate hashtags without hash symbol as concise as possible, no more than five. If the message is a question, please put "question" in the hashtag . The response should be strings delimited by comma without any other special character except comma, do not put new line symbol. Strictly as follow hashtag1,hashtag2,..',
        )

        data = {
            "timestamp": str(datetime.datetime.now()),
            "name": name,
            "message": message,
            "response": response.text,
        }

        # ✅ ส่งเข้า PubSub
        publisher.publish(topic_path, json.dumps(data).encode("utf-8"))

        # ✅ ส่งกลับพร้อม CORS
        return make_response(jsonify(data), 200, headers)

    except Exception as e:
        error_message = {"error": str(e)}
        return make_response(jsonify(error_message), 500, headers)
