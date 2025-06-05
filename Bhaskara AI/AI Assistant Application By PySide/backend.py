import cv2
import pytesseract
from PIL import Image
import pyttsx3
import speech_recognition as sr
from llama_cpp import Llama
import numpy as np
import requests
import os
import sys
import datetime
import platform
import subprocess
import time
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtCore import QUrl, QEventLoop, QTimer
from PySide6.QtWidgets import QApplication
import contextlib
import io
import sys
import json
from PySide6.QtCore import QThread, Signal
from stable_diffusion_cpp import StableDiffusion
import pydub
from pydub import AudioSegment
import tempfile
import re
import hashlib
import threading
import contextlib
import time


# Modify to load from relative path if not found
model_path = os.path.join(os.path.dirname(__file__), "models", "mistral-7b-instruct-v0.2-q4_k_m.gguf")

if not os.path.exists(model_path):
    # If model not found in the bundled path, fall back to a relative directory
    model_path = os.path.join(sys._MEIPASS, "models", "mistral-7b-instruct-v0.2-q4_k_m.gguf")

Ilm = Llama(model_path)

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

# Tesseract path
if platform.system() == "Windows":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# API Keys
WEATHER_API_KEY = "WEATHER API Key"
NEWSDATA_API_KEY = "NEWSDATA API Key"

# Initialize LLM
llm = Llama(
    model_path = resource_path("models/mistral-7b-instruct-v0.2-q4_k_m.gguf"),
    n_ctx=1000,
    n_threads=4,
    verbose=False
)

# NEW: Initialize Stable Diffusion
stable_diffusion = StableDiffusion(
    model_path=resource_path("models/stable-diffusion-v1-5-pruned-emaonly-Q8_0.gguf"),
    wtype="Q8_0", # Match the model quantization
)
class ChatModelThread(QThread):
    finished = Signal(str)

    def __init__(self, prompt, speak_output=False):
        super().__init__()
        self.prompt = prompt
        self.speak_output = speak_output

    def run(self):
        from backend import chat_with_model  # Local import to avoid QApplication
        try:
            result = chat_with_model(self.prompt, speak_output=self.speak_output)
            if isinstance(result, tuple):
                response_text, _ = result
            else:
                response_text = result
            self.finished.emit(response_text)
        except Exception as e:
            self.finished.emit(f"Error: {str(e)}")

class NewsFetchThread(QThread):
    finished = Signal(list)

    def __init__(self, topic="technology, science"):
        super().__init__()
        self.topic = topic

    def run(self):
        from backend import get_news
        try:
            news_items = get_news(self.topic)
            self.finished.emit(news_items)
        except Exception as e:
            self.finished.emit([{"title": "Error", "snippet": str(e), "link": "#"}])

class WeatherFetchThread(QThread):
    finished = Signal(dict)

    def __init__(self, city):
        super().__init__()
        self.city = city

    def run(self):
        import requests
        try:
            url = f"https://wttr.in/{self.city}?format=j1"
            response = requests.get(url, timeout=8)
            if response.status_code != 200:
                self.finished.emit({"error": f"Failed: HTTP {response.status_code}"})
                return
            data = response.json()
            self.finished.emit({"data": data})
        except Exception as e:
            self.finished.emit({"error": str(e)})

class ImageGenerationThread(QThread):
    result_signal = Signal(str)

    def __init__(self, prompt):
        super().__init__()
        self.prompt = prompt

    def run(self):
        
        try:
            result = text_to_image(self.prompt)
            if "Error" in result:
                self.result_signal.emit(result)
            else:
                self.result_signal.emit(f"Image generated and saved at: {result.split('Image generated and saved at: ')[-1]}")
        except Exception as e:
            self.result_signal.emit(f"Error generating image: {str(e)}")

app = QApplication.instance() or QApplication([])  # Needed for QMediaPlayer

# Global media player and audio output
media_player = QMediaPlayer()
audio_output = QAudioOutput()
media_player.setAudioOutput(audio_output)
audio_output.setVolume(1.0)

# TTS
tts_engine = pyttsx3.init()
tts_engine.setProperty('volume', 1.0)

def speak(text, voice_mode=True):
    if not voice_mode:
        return None

    os.makedirs("voice_responses", exist_ok=True)
    filename = f"voice_responses/response_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    temp_filename = tempfile.mktemp(suffix=".wav")  # Temporary file for raw TTS output

    # Configure pyttsx3 for female voice
    tts_engine.setProperty('voice', get_female_voice_id())  # Select female voice
    tts_engine.setProperty('rate', 180)  # Slightly faster for energetic delivery
    tts_engine.setProperty('pitch', 1.2)  # Slightly higher pitch (if supported)
    tts_engine.setProperty('volume', 0.9)  # High volume for clarity

    # Save raw TTS to temporary file
    tts_engine.save_to_file(text, temp_filename)
    tts_engine.runAndWait()

    # Wait for file to be written
    timeout = 5
    start_time = time.time()
    while not (os.path.exists(temp_filename) and os.path.getsize(temp_filename) > 1024):
        if time.time() - start_time > timeout:
            print("⚠️ Timed out waiting for audio file.")
            return None
        time.sleep(0.1)

    # Post-process with pydub for radio effect
    try:
        audio = AudioSegment.from_wav(temp_filename)
        audio = apply_radio_effect(audio)
        audio.export(filename, format="wav")  # Save processed audio
        os.remove(temp_filename)  # Clean up temp file
    except Exception as e:
        print(f"⚠️ Error processing audio: {e}")
        return None

    # Play audio with QMediaPlayer
    try:
        media_player.setSource(QUrl.fromLocalFile(os.path.abspath(filename)))
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            media_player.play()
        loop = QEventLoop()
        media_player.mediaStatusChanged.connect(
            lambda status: loop.quit() if status == QMediaPlayer.MediaStatus.EndOfMedia else None
        )
        QTimer.singleShot(15000, loop.quit)  # Max wait: 15s
        loop.exec()
    except Exception as e:
        print(f"⚠️ Error playing audio: {e}")
        return None

    return filename

def get_female_voice_id():
    """Select a female voice from available system voices."""
    voices = tts_engine.getProperty('voices')
    for voice in voices:
        # Look for female voices (names often include 'Female' or specific names like 'Zira')
        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():  # Microsoft Zira is a common female voice
            return voice.id
    return voices[0].id  # Fallback to default voice

def apply_radio_effect(audio):
    """Apply lightweight radio-like effects using pydub."""
    # Normalize volume
    audio = audio.normalize()

    # Apply EQ: Boost mid frequencies (1-4 kHz) for clarity, reduce low-end
    audio = audio.low_pass_filter(6000).high_pass_filter(200)

    # Add slight compression for broadcast feel
    audio = audio.compress_dynamic_range(threshold=-20.0, ratio=4.0)

    # Add subtle distortion for radio texture
    audio = audio + 2  # Slight gain boost for clipping effect

    # Add mild reverb (approximated with overlay)
    reverb = audio.fade_in(100).fade_out(100).reverse()
    audio = audio.overlay(reverb - 20, times=1)

    return audio


def suppress_console_output(func, *args, **kwargs):
    """Temporarily suppress low-level stdout/stderr (including Qt/FFmpeg)."""
    with open(os.devnull, 'w') as devnull:
        old_stdout_fd = os.dup(1)
        old_stderr_fd = os.dup(2)
        os.dup2(devnull.fileno(), 1)
        os.dup2(devnull.fileno(), 2)
        try:
            return func(*args, **kwargs)
        finally:
            os.dup2(old_stdout_fd, 1)
            os.dup2(old_stderr_fd, 2)
            os.close(old_stdout_fd)
            os.close(old_stderr_fd)

def format_prompt(user_input: str) -> str:
    return f"### Instruction:\n{user_input}\n\n### Response:\n"

def text_to_image(prompt, output_path=None):
    sd = StableDiffusion(model_path= "models/stable-diffusion-v1-5-pruned-emaonly-Q8_0.gguf", wtype="Q8_0")  # instantiate here
    try:
        if output_path is None:
            os.makedirs("generated_images", exist_ok=True)
            output_path = f"generated_images/image_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # Generate image using Stable Diffusion
        result = stable_diffusion.txt_to_img(
            prompt=prompt,
            width=512,
            height=512
        )
        
        # Handle list output (extract first image if list)
        if isinstance(result, list):
            if not result:
                return "Error: No images generated."
            image = result[0]  # Take the first image
        else:
            image = result
        
        # Save the image
        image.save(output_path)
        return f"Image generated and saved at: {output_path}"
    except Exception as e:
        return f"Error generating image: {str(e)}"

def chat_with_model(user_input: str, speak_output=False) -> str:
    if "weather" in user_input.lower():
        city = input("Enter city for weather: ")
        response = get_weather(city)
    elif "news" in user_input.lower():
        topic = input("Enter topic for news: ")
        response = get_news(topic)
    elif "generate image" in user_input.lower():  # NEW: Handle image generation
        prompt = user_input.replace("generate image", "").strip()
        if not prompt:
            prompt = input("Enter a description for the image: ")
        response = text_to_image(prompt)
    else:
        try:
            prompt = format_prompt(user_input)
            result = llm(prompt, max_tokens=1100, temperature=0.6, top_p=0.8)
            response = result['choices'][0]['text'].strip()
        except Exception as e:
            response = f"Error: {str(e)}"

    if speak_output:
        _ = speak(response, voice_mode=True)
        return response
    return response

# Weather API Function
def get_weather(location="Dehradun"):
    cities = ["Dehradun", "Delhi", "Mumbai", "Bengaluru", "Kolkata"]
    weather_reports = []

    for city in cities:
        try:
            url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={city}"
            response = requests.get(url)
            data = response.json()
            condition = data["current"]["condition"]["text"]
            temp_c = data["current"]["temp_c"]
            city_name = data["location"]["name"]
            report = f"{city_name}: {condition}, {temp_c}°C"
            weather_reports.append(report)
        except Exception as e:
            weather_reports.append(f"{city}: Error fetching weather - {str(e)}")

    return "Weather updates for 5 Indian cities:\n" + "\n".join(weather_reports)

# News API Function
def get_news(topic="technology, science"):
    try:
        url = f"https://newsdata.io/api/1/news?apikey={NEWSDATA_API_KEY}&q={topic}&language=en"
        response = requests.get(url)
        articles = response.json().get("results", [])
        if not articles:
            return []

        news_items = []
        for article in articles[:3]:  # Limit to 3 news cards
            news_items.append({
                "title": article.get("title", "No Title"),
                "snippet": article.get("description", "No description available."),
                "link": article.get("link", "#")
            })

        return news_items

    except Exception as e:
        return [{"title": "Error", "snippet": str(e), "link": "#"}]

def capture_image():
    cam = cv2.VideoCapture(0)
    ret, frame = cam.read()
    if ret:
        path = "captured_image.jpg"
        cv2.imwrite(path, frame)
        cam.release()
        return path
    cam.release()
    return None

def preprocess_and_extract_text(image_path):
    image = cv2.imread(image_path)
    if image is None:
        return "Error: Could not read image."
    image = cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    sharp = cv2.filter2D(gray, -1, kernel)
    thresh = cv2.adaptiveThreshold(sharp, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2)
    custom_config = r'--oem 3 --psm 11 -c tessedit_char_whitelist=abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,.!?() '
    extracted_text = pytesseract.image_to_string(thresh, config=custom_config).strip()
    return extracted_text

def image_to_text_with_answer(image_path, speak_output=False):
    image = cv2.imread(image_path)
    if image is None:
        return "Error: Image not found or cannot be loaded."
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    config = r'--oem 3 --psm 6'
    extracted_text = pytesseract.image_to_string(gray, config=config).strip()
    if not extracted_text:
        return "No readable text found in the image."
    print("🔍 Extracted Text:\n", extracted_text)
    prompt = f"Explain this extracted text clearly:\n\n{extracted_text}"
    response = chat_with_model(prompt, speak_output=speak_output)
    return response

def main_menu():
    while True:
        mode = input("\nChoose Your Conversation Option:\n  1 Text-to-Text \n  2 Text-to-Voice \n  3 Voice-to-Voice \n  4 Image Processing (OCR & AI Answer) \n  5 Text-to-Image \n  6 Exit \n").strip()
        if mode == '6':
            print("Exiting program. Goodbye!")
            speak("Goodbye!", voice_mode=False)
            break
        elif mode == '5':  # NEW: Text-to-Image mode
            prompt = input("Enter a description for the image: ")
            response = text_to_image(prompt)
            print("AI Response:", response)
            interactive_chat()
        elif mode == '4':
            img_choice = input("Enter image file path or type 'camera' to capture: ").strip()
            if img_choice.lower() == "camera":
                img_choice = capture_image()
            if img_choice:
                response = image_to_text_with_answer(img_choice, speak_output=True)
                if isinstance(response, tuple):
                    response_text, _ = response
                else:
                    response_text = response
                print("AI Response:", response_text)
            interactive_chat()
        elif mode == '3':
            interactive_chat(voice_mode=True)
        elif mode == '2':
            interactive_chat(text_to_voice=True)
        elif mode == '1':
            interactive_chat(voice_mode=False)
        else:
            print("Invalid choice. Please select a valid option.")

def interactive_chat(voice_mode=False, text_to_voice=False):
    print("\nAI Assistant: Hello! Type or speak your message. Say 'menu' to return.")
    while True:
        user_input = listen() if voice_mode else input("You: ").strip()
        if user_input.lower() == "menu":
            break
        reply = chat_with_model(user_input, speak_output=(voice_mode or text_to_voice))

        # Unpack and print only response
        if isinstance(reply, tuple):
            response_text = extract_response_text(reply)
        else:
            response_text = reply

        print("AI Assistant:", extract_response_text(reply))

def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source)
        try:
            audio = recognizer.listen(source, timeout=10)
            return recognizer.recognize_google(audio)
        except:
            return "Sorry, I didn't catch that."
        
def extract_response_text(response):
    if isinstance(response, tuple):
        return response[0]
    return response

def generate_filename(content):
    """Generate a smart filename with .txt extension regardless of content."""
    # Always use .txt extension
    extension = ".txt"

    # Base name from first 3 words
    base = "file_" + hashlib.md5(content[:50].encode()).hexdigest()[:6]
    match = re.search(r"(?:a|an|the)?\s*(\w+)", content.lower())
    if match:
        base = match.group(1)

    # Append timestamp to ensure uniqueness
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    return f"{base}_{timestamp}{extension}"

def open_editor_background(file_path, editor="notepad"):
    try:
        if platform.system() == "Windows":
            if editor == "vscode":
                subprocess.Popen(["code", file_path], shell=True)
            else:
                subprocess.Popen(["notepad.exe", file_path], shell=True)
        elif platform.system() == "Linux":
            subprocess.Popen(["gedit", file_path])
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", "-a", "TextEdit", file_path])
    except Exception as e:
        print(f"Error launching editor: {e}")

def launch_editor(content, filename=None, editor="notepad"):
    """Save content and launch Notepad/VS Code in a non-blocking background thread."""
    target_dir = r"C:\Projects\Bhaskara AI\AI Assistant Application By PySide\generated_files"
    os.makedirs(target_dir, exist_ok=True)
    
    # Generate a unique filename if none provided
    if filename is None:
        filename = generate_filename(content)
    
    file_path = os.path.join(target_dir, filename)

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        # ✅ Run editor launch in a background thread
        threading.Thread(target=open_editor_background, args=(file_path, editor), daemon=True).start()

        return file_path
    except Exception as e:
        print(f"Error writing or launching file: {e}")
        return None

# Start the assistant
if __name__ == "__main__":
    main_menu()
