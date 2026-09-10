from flask import Flask, request, jsonify, send_from_directory
import urllib.request
import json
import os

app = Flask(__name__)

OLLAMA = "http://127.0.0.1:11434/api/chat"
MODEL = "felyxorine:latest"

@app.route("/")
def index():
    return send_from_directory(".", "index.html")


@app.route("/<path:path>")
def files(path):
    return send_from_directory(".", path)

@app.post("/api/chat")
def chat():

    data = request.json

    payload = json.dumps({
        "model": MODEL,
        "messages": data["messages"],
        "stream": False
    }).encode("utf-8")

    req = urllib.request.Request(
        OLLAMA,
        data=payload,
        headers={
            "Content-Type": "application/json"
        }
    )

    try:

        with urllib.request.urlopen(
            req,
            timeout=120
        ) as response:

            result = json.loads(
                response.read().decode("utf-8")
            )

        return jsonify({
            "reply": result["message"]["content"]
        })

    except Exception as error:

        return jsonify({
            "error": str(error)
        }), 500

@app.post("/api/launch")
def launch():

    data = request.json

    app_name = data.get("app")

    if not app_name:

        return jsonify({
            "error": "undefined app name"
        }), 400

    try:

        os.startfile(
            app_name
        )

        return jsonify({
            "success": True,
            "message": f"{app_name}"
        })

    except Exception as error:

        return jsonify({
            "success": False,
            "error": str(error)
        }), 400

if __name__ == "__main__":

    print("========================================")
    print(" Felyxorine Server")
    print("========================================")
    print("http://127.0.0.1:8079")
    print("Ollama:", MODEL)
    print("========================================")

    app.run(
        host="127.0.0.1",
        port=8079,
        debug=False
    )
