import os
import base64
import subprocess
import whisper
from TTS.api import TTS
import torch
import requests
from dotenv import load_dotenv

# Set your system-installed FFmpeg path
FFMPEG_BIN = r"C:\ffmpeg\ffmpeg-7.1.1-essentials_build\bin"
os.environ["PATH"] += os.pathsep + FFMPEG_BIN

# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "llama-3-8b-instruct")

# Initialize models
whisper_model = None
tts_model = None

def initialize_models():
    global whisper_model, tts_model
    try:
        print("Loading Whisper model...")
        whisper_model = whisper.load_model("base")
        print("Whisper model loaded.")

        print("Loading TTS model...")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        tts_model = TTS("tts_models/en/ljspeech/tacotron2-DDC").to(device)
        print(f"TTS model loaded on {device}")
    except Exception as e:
        print("Model initialization error:", e)

# Call on import
initialize_models()

def convert_webm_to_mp3(webm_path, mp3_path):
    try:
        command = [
            "ffmpeg", "-y",
            "-i", webm_path,
            "-vn",
            "-ar", "16000",
            "-ac", "1",
            "-b:a", "128k",
            mp3_path
        ]
        subprocess.run(command, check=True)
        
        if not os.path.exists(mp3_path):
            raise FileNotFoundError(f"MP3 file was not created: {mp3_path}")
        
        print(f"Converted to MP3: {os.path.getsize(mp3_path)} bytes")
    except Exception as e:
        print("Error converting WebM to MP3:", e)
        raise

def transcribe_audio(audio_path):
    try:
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        print(f"Transcribing file: {audio_path}")
        result = whisper_model.transcribe(audio_path)
        return result.get("text", "").strip()
    except Exception as e:
        print("Error in transcription:", e)
        return ""

def generate_response(history, user_message):
    try:
        if not GROQ_API_KEY:
            raise EnvironmentError("GROQ_API_KEY not found in environment")

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        messages = [{"role": "system", "content": "You are a helpful AI assistant."}]
        messages += history[-10:] + [{"role": "user", "content": user_message}]

        data = {
            "model": MODEL_NAME,
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7
        }

        res = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers, timeout=30)
        res.raise_for_status()

        return res.json()["choices"][0]["message"]["content"]

    except Exception as e:
        print("Error generating response:", e)
        return "Sorry, I couldn't generate a response."

def synthesize_speech(text, output_path="audio/response.wav"):
    try:
        if not text.strip():
            raise ValueError("Empty text provided for TTS.")

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        tts_model.tts_to_file(text=text.strip(), file_path=output_path)

        with open(output_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")

    except Exception as e:
        print("TTS error:", e)
        return ""
