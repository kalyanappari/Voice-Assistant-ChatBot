from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from workers import transcribe_audio, generate_response, synthesize_speech, convert_webm_to_mp3

app = Flask(__name__, static_folder="../frontend", static_url_path="/")
CORS(app)

conversation_history = []

os.makedirs("audio", exist_ok=True)

@app.route("/")
def index():
    return send_from_directory("../frontend", "index.html")

@app.route("/<path:path>")
def static_files(path):
    return send_from_directory("../frontend", path)

@app.route("/process-text", methods=["POST"])
def process_text():
    global conversation_history
    try:
        data = request.get_json()
        user_message = data.get("message", "").strip()
        if not user_message:
            return jsonify({"error": "Empty message"}), 400

        response_text = generate_response(conversation_history, user_message)
        conversation_history.append({"role": "user", "content": user_message})
        conversation_history.append({"role": "assistant", "content": response_text})

        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        response_audio = synthesize_speech(response_text)
        return jsonify({
            "responseText": response_text,
            "responseAudio": response_audio
        })

    except Exception as e:
        print("Error in process_text:", e)
        return jsonify({"error": "Internal server error"}), 500

@app.route("/process-voice", methods=["POST"])
def process_voice():
    global conversation_history
    try:
        if "audio" not in request.files:
            return jsonify({"error": "No audio file provided"}), 400

        webm_file = request.files["audio"]
        webm_path = "audio/input.webm"
        mp3_path = "audio/input.mp3"

        webm_file.save(webm_path)
        print(f"Saved WebM file: {webm_path}, size: {os.path.getsize(webm_path)} bytes")

        print("Converting WebM to MP3...")
        convert_webm_to_mp3(webm_path, mp3_path)
        print(f"MP3 created? {os.path.exists(mp3_path)} - Size: {os.path.getsize(mp3_path) if os.path.exists(mp3_path) else 'Missing'}")


        user_text = transcribe_audio(mp3_path)
        if not user_text:
            return jsonify({"error": "Could not transcribe audio"}), 400

        response_text = generate_response(conversation_history, user_text)
        conversation_history.append({"role": "user", "content": user_text})
        conversation_history.append({"role": "assistant", "content": response_text})

        if len(conversation_history) > 20:
            conversation_history = conversation_history[-20:]

        response_audio = synthesize_speech(response_text)

        return jsonify({
            "userText": user_text,
            "responseText": response_text,
            "responseAudio": response_audio
        })

    except Exception as e:
        print("Error in process_voice:", e)
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
