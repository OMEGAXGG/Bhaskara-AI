import sys
import math
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QListWidget, QListWidgetItem, QLabel,
    QFileDialog, QMessageBox, QInputDialog, QSizePolicy, QDialog, QFrame, QGraphicsDropShadowEffect, 
    QGraphicsView, QGraphicsScene, QGraphicsPolygonItem, QScrollArea, QStackedWidget, QLineEdit, 
    QFrame, QMenu, QGraphicsPathItem, QStyleOptionGraphicsItem, QStyle, QToolButton, QSpacerItem, 
    QSplashScreen, QGraphicsOpacityEffect
)
from PySide6.QtCore import Qt, QThread, Signal, QTimer, QPropertyAnimation, QEasingCurve, QRect, QUrl, QRectF, QPointF, QObject, Property, QTimer 
from PySide6.QtGui import QFont, QPixmap, QIcon, QPalette, QColor, QPolygonF, QBrush, QPainter, QPen, QPainterPath, QCursor, QAction, QMouseEvent
import itertools
import speech_recognition as sr
from PySide6.QtWebEngineWidgets import QWebEngineView
from backend import get_news, get_weather
import requests
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
import os
import datetime
import random
from login_signup import LoginSignupPage
from utils.session_manager import load_session
from backend import resource_path 
import json
import time
import uuid  # NEW: For generating unique chat IDs
from backend import ImageGenerationThread
# Backend imports
from backend import (
    chat_with_model,
    speak,
    capture_image,
    image_to_text_with_answer,
    listen,
    text_to_image

)

# Custom Splash Screen Widget
class CustomSplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(600, 400)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)
        layout.setContentsMargins(20, 20, 20, 20)

        frame = QFrame(self)
        frame.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:1,
                    stop:0 #2c2f33, stop:1 #1e1f22
                );
                border-radius: 20px;
            }
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setAlignment(Qt.AlignCenter)
        frame_layout.setContentsMargins(20, 20, 20, 20)

        logo_label = QLabel()
        logo_pixmap = QPixmap(resource_path("icons_and_assets/Bhaskara AI.png")).scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        logo_label.setPixmap(logo_pixmap)
        logo_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(logo_label)

        app_name_label = QLabel("Bhaskara AI")
        app_name_label.setFont(QFont("sans-serif", 22, QFont.Bold))
        app_name_label.setStyleSheet("color: white;")
        app_name_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(app_name_label)

        loading_label = QLabel("Loading...")
        loading_label.setFont(QFont("Arial", 12))
        loading_label.setStyleSheet("color: #7289da;")
        loading_label.setAlignment(Qt.AlignCenter)
        frame_layout.addWidget(loading_label)

        layout.addWidget(frame)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(0)
        shadow.setColor(QColor(0, 0, 0, 180))
        frame.setGraphicsEffect(shadow)

    def showEvent(self, event):
        screen = QApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move((screen.width() - size.width()) // 2, (screen.height() - size.height()) // 2)
        
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(4000)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(4.0)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.fade_animation.start()
        
        super().showEvent(event)

class HexBrick(QObject, QGraphicsPolygonItem):
    def __init__(self, size, color, parent=None):
        QObject.__init__(self, parent)
        QGraphicsPolygonItem.__init__(self)
        self._opacity = 0.0
        self.setPolygon(self.create_hexagon(size))
        self.setBrush(QBrush(color))
        self.setOpacity(self._opacity)

    def create_hexagon(self, size):
        points = []
        for i in range(6):
            angle = math.radians(60 * i)
            x = size * math.cos(angle)
            y = size * math.sin(angle)
            points.append(QPointF(x, y))
        return QPolygonF(points)

    def get_opacity(self):
        return self._opacity

    def set_opacity(self, value):
        self._opacity = value
        self.setOpacity(value)

    opacity = Property(float, get_opacity, set_opacity)

    def animate(self, delay):
        def start_animation():
            animation = QPropertyAnimation(self, b"opacity")
            animation.setStartValue(0.0)
            animation.setEndValue(1.0)
            animation.setDuration(1000)
            animation.setLoopCount(-1)
            animation.setEasingCurve(QEasingCurve.InOutQuad)
            animation.start()
            self._animation = animation

        QTimer.singleShot(delay, start_animation)

class LoaderScene(QGraphicsScene):
    def __init__(self):
        super().__init__(QRectF(-150, -100, 300, 200))
        self.init_hex_loader()

    def init_hex_loader(self):
        hex_size = 10
        radius = 30
        rows = 3
        cols = 6
        color = QColor("#ABF8FF")

        count = 0
        for row in range(rows):
            for col in range(cols):
                x_offset = col * radius * 0.75
                y_offset = row * radius + (col % 2) * (radius / 2)

                gel_x = x_offset - (cols * radius * 0.75) / 2
                gel_y = y_offset - (rows * radius) / 2

                for i in range(3):
                    brick = HexBrick(hex_size, color)
                    angle = [0, 60, -60][i]
                    brick.setRotation(angle)
                    brick.setPos(gel_x, gel_y)
                    self.addItem(brick)
                    brick.animate(delay=80 * count)
                count += 1

class LoaderView(QGraphicsView):
    def __init__(self):
        super().__init__()
        self.setScene(LoaderScene())
        self.setRenderHint(QPainter.Antialiasing)
        self.setFixedHeight(120)
        self.setStyleSheet("background-color: transparent; border: none;")
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

class NewsCard(QFrame):
    def __init__(self, title, snippet, link, parent=None):
        super().__init__(parent)
        self.setFixedSize(175, 140)
        self.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f5f9ff, stop:1 #e1ecff);
                border-radius: 15px;
                color: #333;
            }
            QLabel {
                color: #222;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        icon_label = QLabel("📰")
        icon_label.setFont(QFont("Arial", 11))
        icon_label.setAlignment(Qt.AlignLeft)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 8, QFont.Bold))
        title_label.setWordWrap(True)

        snippet_label = QLabel(snippet)
        snippet_label.setFont(QFont("Arial", 7))
        snippet_label.setStyleSheet("color: #444;")
        snippet_label.setWordWrap(True)

        link_label = QLabel(f'<a href="{link}">Read more →</a>')
        link_label.setFont(QFont("Arial", 5))
        link_label.setStyleSheet("color: #1a0dab;")
        link_label.setOpenExternalLinks(True)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(snippet_label)
        layout.addStretch()
        layout.addWidget(link_label)

class WeatherCard(QFrame):
    def __init__(self, city, temp, feels_like, humidity, description, parent=None):
        super().__init__(parent)
        self.setFixedSize(175, 140)
        self.setStyleSheet("""
            QFrame {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:0, y2:1,
                    stop:0 #fffce1, stop:1 #fff6c5);
                border-radius: 20px;
                color: #333;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(2)

        city_label = QLabel(city)
        city_label.setFont(QFont("Arial", 10, QFont.Bold))

        date_label = QLabel(datetime.date.today().strftime("%B %d"))
        date_label.setStyleSheet("color: gray; font-size: 11px;")

        temp_container = QWidget()
        temp_layout = QHBoxLayout(temp_container)
        temp_layout.setContentsMargins(0, 0, 0, 0)
        temp_container.setAttribute(Qt.WA_StyledBackground, True)
        temp_container.setStyleSheet("background: transparent;")
        
        temp_label = QLabel(f"{temp}°C")
        temp_label.setFont(QFont("Arial", 28, QFont.Bold))
        temp_label.setStyleSheet("color: #222222;")
        
        weather_icon = QLabel("⛅")
        weather_icon.setAlignment(Qt.AlignRight)
        weather_icon.setFont(QFont("Arial", 24))
        
        temp_layout.addWidget(temp_label)
        temp_layout.addStretch()
        temp_layout.addWidget(weather_icon)

        desc_label = QLabel(description)
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setStyleSheet("color: #222222;")
        desc_label.setWordWrap(True)
        
        feels_like_label = QLabel(f"Feels like {feels_like}°C")
        feels_like_label.setFont(QFont("Arial", 10))
        feels_like_label.setStyleSheet("color: #222222;")
        
        humidity_label = QLabel(f"Humidity {humidity}%")
        humidity_label.setFont(QFont("Arial"))
        humidity_label.setStyleSheet("color: #222222;")

        layout.addWidget(city_label)
        layout.addWidget(date_label)
        layout.addWidget(temp_container)
        layout.addWidget(desc_label)
        layout.addWidget(feels_like_label)
        layout.addWidget(humidity_label)
        
        layout.addStretch(1)

class VoiceListeningPopup(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet("background-color: #2f3136; color: white; border-radius: 15px;")
        self.setFixedSize(320, 180)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        self.loader = LoaderView()
        layout.addWidget(self.loader)

        self.transcription_label = QLabel("Listening...")
        self.transcription_label.setWordWrap(True)
        self.transcription_label.setStyleSheet("font-size: 14px; color: white; padding: 10px;")
        layout.addWidget(self.transcription_label)

    def update_transcription(self, text):
        self.transcription_label.setText(text)

class AudioPlayer:
    def __init__(self):
        self.player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.player.setAudioOutput(self.audio_output)
        self.player.errorOccurred.connect(self.handle_error)
        self.is_playing = False
        self.player.playbackStateChanged.connect(self.handle_state_change)
        
    def handle_state_change(self, state):
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.is_playing = True
        else:
            self.is_playing = False
            
    def play_audio(self, file_path):
        try:
            self.stop_audio()
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")
            self.player.setSource(QUrl.fromLocalFile(file_path))
            self.player.play()
            print(f"Playing audio: {file_path}")
        except Exception as e:
            print(f"Error in play_audio: {str(e)}")

    def stop_audio(self):
        try:
            if self.is_playing:
                print("Stopping audio playback")
                self.player.pause()
                self.player.stop()
                self.player.setSource(QUrl())
                self.audio_output = QAudioOutput()
                print("Audio output reset")
        except Exception as e:
            print(f"Error in stop_audio: {str(e)}")
            
    def handle_error(self, error):
        error_str = str(error)
        print(f"Media player error: {error_str}")
        error_string = self.player.errorString()
        print(f"Error details: {error_string}")

class VoiceChatThread(QThread):
    result_signal = Signal(str)
    partial_text = Signal(str)

    def run(self):
        recognizer = sr.Recognizer()
        mic = sr.Microphone()

        with mic as source:
            recognizer.adjust_for_ambient_noise(source)
            try:
                self.partial_text.emit("Listening...")
                audio_data = recognizer.listen(source, timeout=4, phrase_time_limit=5)
                self.partial_text.emit("Transcribing...")

                transcript = recognizer.recognize_google(audio_data)
                self.partial_text.emit(transcript)

                response = chat_with_model(transcript, speak_output=True)
                if isinstance(response, tuple):
                    response_text, audio_path = response
                else:
                    response_text = response
                    audio_path = None

                self.result_signal.emit(f"You: {transcript}")
                self.result_signal.emit(f"Bot: {response_text}")

                if audio_path:
                    self.result_signal.emit(f"AUDIO_PATH::{audio_path}")

            except sr.WaitTimeoutError:
                self.result_signal.emit("Bot: No speech detected. Try again.")
            except sr.UnknownValueError:
                self.result_signal.emit("Bot: Sorry, I couldn't understand you.")
            except sr.RequestError:
                self.result_signal.emit("Bot: Error accessing the speech service.")
            except Exception as e:
                full_message = f"Bot: Error occurred during voice-to-voice processing - {str(e)}"
                self.result_signal.emit(full_message)

class ImageProcessingThread(QThread):
    result_signal = Signal(str)

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        try:
            response = image_to_text_with_answer(self.image_path, speak_output=True)
            full_message = f"{response}"
            self.result_signal.emit(full_message)
        except Exception as e:
            self.result_signal.emit(f"Error processing image: {str(e)}")

class ChatBubble(QWidget):
    def __init__(self, text, is_user=True):
        super().__init__()
        self.is_user = is_user
        self.text = text
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.setFocusPolicy(Qt.NoFocus)

        layout = QHBoxLayout()
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(0)

        bubble = QLabel(text)
        bubble.setWordWrap(True)
        bubble.setTextInteractionFlags(Qt.NoTextInteraction)
        bubble.setFocusPolicy(Qt.NoFocus)
        bubble.setStyleSheet(f"""
            QLabel {{
                background-color: {'#7289da' if is_user else '#99aab5'};
                color: white;
                padding: 10px 15px;
                border-radius: 15px;
                font-size: 14px;
            }}
            QLabel:focus {{
                outline: none;
                background-color: {'#7289da' if is_user else '#99aab5'};
            }}
        """)
        bubble.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        bubble.setMaximumWidth(400)

        bubble.setContextMenuPolicy(Qt.CustomContextMenu)
        bubble.customContextMenuRequested.connect(self.show_context_menu)

        if is_user:
            layout.addStretch()
            layout.addWidget(bubble)
        else:
            layout.addWidget(bubble)
            layout.addStretch()

        self.setLayout(layout)

    def show_context_menu(self, pos):
        menu = QMenu()
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(self.copy_text)
        menu.addAction(copy_action)
        menu.exec(QCursor.pos())

    def copy_text(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text)

class CustomScrollArea(QScrollArea):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QScrollArea {
                background-color: #2f3136;
                border: none;
            }
            QScrollBar:horizontal {
                height: 0px;
                background: transparent;
            }
            QScrollBar::handle:horizontal {
                background: transparent;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                background: transparent;
            }
        """)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        scrollbar = self.horizontalScrollBar()
        if delta > 0:
            scrollbar.setValue(scrollbar.value() - 100)
        elif delta < 0:
            scrollbar.setValue(scrollbar.value() + 100)
        event.accept()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Bhaskara AI")
        self.setMinimumSize(1000, 600)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        self.main_layout = QVBoxLayout(main_widget)

        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("#2c2f33"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        def create_button(icon_text, label_text):
            btn = QPushButton(f"{icon_text}  {label_text}")
            btn.setFixedHeight(40)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #404249;
                    color: white;
                    padding: 8px 20px;
                    border-radius: 20px;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #5a5d63;
                }
            """)
            return btn

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_horizontal_layout = QHBoxLayout(central_widget)
        main_horizontal_layout.setContentsMargins(0, 0, 0, 0)
        main_horizontal_layout.setSpacing(0)

        self.sidebar = QFrame(central_widget)
        self.sidebar.setFixedWidth(0)
        self.sidebar.setStyleSheet("background-color: #2c2f33; border-right: 1px solid #444;")
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)

        self.sidebar_toggle_button = QPushButton("☰")
        self.sidebar_toggle_button.setFixedWidth(30)
        self.sidebar_toggle_button.clicked.connect(self.toggle_sidebar)

        self.sidebar_animation = QPropertyAnimation(self.sidebar, b"maximumWidth")
        self.sidebar_animation.setDuration(300)
        self.sidebar_animation.setEasingCurve(QEasingCurve.InOutCubic)

        main_horizontal_layout.addWidget(self.sidebar)

        main_content = QWidget(central_widget)
        main_content_layout = QVBoxLayout(main_content)
        main_content_layout.setContentsMargins(0, 0, 0, 0)
        main_content_layout.setSpacing(0)

        main_content_layout.insertWidget(0, self.sidebar_toggle_button, alignment=Qt.AlignLeft)

        self.audio_player = AudioPlayer()

        self.chat_display = QListWidget()
        self.chat_display.setStyleSheet("""
            QListWidget {
                background-color: #2f3136;
                color: white;
                border: none;
            }
            QListWidget::item {
                padding: 0px;
                margin: 0px;
                background-color: transparent;
            }
            QListWidget::item:selected {
                background-color: transparent;
                border: none;
            }
            QListWidget::item:focus {
                outline: none;
                background-color: transparent;
            }
        """)
        self.chat_display.setResizeMode(QListWidget.Adjust)
        self.chat_display.setWordWrap(True)
        self.chat_display.setSpacing(5)
        self.chat_display.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        main_content_layout.addWidget(self.chat_display, 0)

        main_horizontal_layout.addWidget(main_content)

        sidebar_label = QLabel("Bhaskara AI History")
        sidebar_label.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")
        self.sidebar_layout.addWidget(sidebar_label)

        # NEW: Add New Chat Button
        self.new_chat_btn = QPushButton("➕ New Chat")
        self.new_chat_btn.setFixedHeight(40)
        self.new_chat_btn.setStyleSheet("""
            QPushButton {
                background-color: #404249;
                color: white;
                padding: 8px 20px;
                border-radius: 20px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #5a5d63;
            }
        """)
        self.new_chat_btn.clicked.connect(self.start_new_chat)
        self.sidebar_layout.addWidget(self.new_chat_btn)

        self.history_list = QListWidget()
        self.history_list.setStyleSheet("background-color: #2c2c2c; color: white;")
        self.sidebar_layout.addWidget(self.history_list)

        input_container_bg = QWidget()
        input_container_bg.setObjectName("inputSection")
        input_container_bg.setFixedHeight(75)
        input_container_bg.setStyleSheet("""
            QWidget#inputSection {
                background-color: #1e1f22;
                border-radius: 35px;
            }
        """)
        input_container_bg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        input_container_layout = QHBoxLayout(input_container_bg)
        input_container_layout.setContentsMargins(0, 0, 0, 0)
        input_container_layout.setSpacing(0)

        input_bar = QWidget()
        input_bar.setStyleSheet("""
            background-color: rgba(47, 49, 54, 180);
            border-radius: 30px;
        """)
        input_bar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        input_bar.setMinimumHeight(60)

        input_bar_layout = QHBoxLayout(input_bar)
        input_bar_layout.setContentsMargins(15, 10, 15, 10)
        input_bar_layout.setSpacing(10)

        input_wrapper = QWidget()
        input_wrapper.setStyleSheet("""
            QWidget {
                background-color: rgba(40, 40, 40, 240);
                border-radius: 15px;
            }
        """)
        input_wrapper.setFixedHeight(45)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 180))
        input_wrapper.setGraphicsEffect(shadow)

        wrapper_layout = QHBoxLayout(input_wrapper)
        wrapper_layout.setContentsMargins(12, 5, 12, 5)
        wrapper_layout.setSpacing(0)

        self.user_input = QTextEdit()
        self.user_input.setPlaceholderText("Ask anything...")
        self.user_input.setStyleSheet("""
            QTextEdit {
                background: transparent;
                color: white;
                font-size: 14px;
                border: none;
                padding: 0px;
            }
        """)
        self.user_input.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.user_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.user_input.setFixedHeight(30)

        wrapper_layout.addWidget(self.user_input)
        
        input_bar_layout.addWidget(input_wrapper)

        self.voice_btn = create_button("🎙️", "Voice Chat")
        self.voice_btn.clicked.connect(self.handle_voice_chat)
        input_bar_layout.addWidget(self.voice_btn)

        self.tts_btn = create_button("🔊", "Speak Text")
        self.tts_btn.clicked.connect(self.handle_text_to_voice)
        input_bar_layout.addWidget(self.tts_btn)

        self.image_btn = create_button("📷", "Image to Text")
        self.image_btn.clicked.connect(self.handle_image_recognition)
        input_bar_layout.addWidget(self.image_btn)

        self.text_to_image_btn = create_button("🖼️", "Generate Image")
        self.text_to_image_btn.clicked.connect(self.handle_text_to_image)
        input_bar_layout.addWidget(self.text_to_image_btn)


        input_container_layout.addWidget(input_bar)
        main_content_layout.addWidget(input_container_bg, 0)

        self.user_input.textChanged.connect(self.check_enter_key)

        self.weather_scroll = CustomScrollArea()
        self.weather_scroll.setWidgetResizable(True)
        self.weather_scroll.setFixedHeight(200)
        self.weather_scroll.setStyleSheet("background-color: #2f3136; border: none;")
        self.weather_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.weather_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        weather_container = QWidget()
        self.weather_layout = QHBoxLayout(weather_container)
        self.weather_layout.setContentsMargins(10, 10, 10, 10)
        self.weather_layout.setSpacing(15)

        self.weather_scroll.setWidget(weather_container)
        self.sidebar_layout.addWidget(self.weather_scroll)

        self.fetch_weather_for_cities()

        self.news_scroll = CustomScrollArea()
        self.news_scroll.setWidgetResizable(True)
        self.news_scroll.setFixedHeight(200)
        self.news_scroll.setStyleSheet("background-color: #2f3136; border: none;")
        self.news_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.news_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        news_container = QWidget()
        self.news_layout = QHBoxLayout(news_container)
        self.news_layout.setContentsMargins(10, 10, 10, 10)
        self.news_layout.setSpacing(15)

        self.news_scroll.setWidget(news_container)
        self.sidebar_layout.addWidget(self.news_scroll)

        self.fetch_news()

        sidebar_footer = QFrame()
        sidebar_footer.setFixedHeight(40)
        sidebar_footer.setStyleSheet("background-color: #2c2c33;")

        footer_layout = QHBoxLayout(sidebar_footer)
        footer_layout.setContentsMargins(10, 5, 10, 5)

        self.user_label = QLabel("User")
        footer_layout.addWidget(self.user_label)
        self.user_label.setStyleSheet("color: white; font-weight: bold; font-size: 10px;")

        caret_label = QLabel()
        caret_label.setCursor(Qt.PointingHandCursor)
        caret_pixmap = QPixmap("caret.png").scaled(10, 10, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        caret_label.setPixmap(caret_pixmap)

        self.saved_chats = {}
        self.current_chat_id = None
        self.load_chats_from_file()
        self.history_list.itemClicked.connect(self.load_selected_chat)
        self.history_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.history_list.customContextMenuRequested.connect(self.show_history_context_menu)

        def open_login_signup(event):
            if event.type() == QMouseEvent.MouseButtonDblClick:
                self.login_window = LoginSignupPage()
                self.login_window.show()

        caret_label.mouseDoubleClickEvent = open_login_signup

        caret_menu = QMenu()
        caret_menu.setStyleSheet("""
            QMenu {
                background-color: #2c2c2c;
                color: white;
                border: 1px solid #444;
            }
            QMenu::item:selected {
                background-color: #444444;
            }
        """)
        caret_menu.addAction(QAction("Login"))
        caret_menu.addAction(QAction("Signup"))

        def show_sidebar_menu(event):
            caret_menu.exec(QCursor.pos())

        caret_label.mousePressEvent = show_sidebar_menu

        footer_layout.addWidget(self.user_label)
        footer_layout.addStretch()
        footer_layout.addWidget(caret_label)

        self.sidebar_layout.addWidget(sidebar_footer)

    def save_chats_to_file(self):
        try:
            with open("saved_chats.json", "w", encoding="utf-8") as f:
                json.dump(self.saved_chats, f, indent=4)
        except Exception as e:
            print(f"Error saving chats: {e}")

    def load_chats_from_file(self):
        self.history_list.clear()
        if os.path.exists("saved_chats.json"):
            try:
                with open("saved_chats.json", "r", encoding="utf-8") as f:
                    self.saved_chats = json.load(f)
                for chat_id, chat_data in sorted(
                    self.saved_chats.items(),
                    key=lambda x: x[1]["last_updated"],
                    reverse=True
                ):
                    item = QListWidgetItem(f"{chat_data['title']} ({chat_data['last_updated']})")
                    item.setData(Qt.UserRole, chat_id)  # Store chat_id in item
                    self.history_list.addItem(item)
            except Exception as e:
                print(f"Error loading chats: {e}")

    def start_new_chat(self):
        # Save current chat if it exists
        if self.current_chat_id:
            self.saved_chats[self.current_chat_id]["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.save_chats_to_file()
        
        # Create new chat
        chat_title, ok = QInputDialog.getText(self, "New Chat", "Enter chat title:", text=f"Chat {len(self.saved_chats) + 1}")
        if not ok or not chat_title.strip():
            chat_title = f"Chat {len(self.saved_chats) + 1}"
        
        self.current_chat_id = str(uuid.uuid4())
        self.saved_chats[self.current_chat_id] = {
            "title": chat_title,
            "messages": [],
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Update history list
        self.history_list.clear()
        for chat_id, chat_data in sorted(
            self.saved_chats.items(),
            key=lambda x: x[1]["last_updated"],
            reverse=True
        ):
            item = QListWidgetItem(f"{chat_data['title']} ({chat_data['last_updated']})")
            item.setData(Qt.UserRole, chat_id)
            self.history_list.addItem(item)
        
        self.chat_display.clear()
        self.user_input.clear()
        self.save_chats_to_file()

    def append_to_current_chat(self, message):
        if not self.current_chat_id:
            self.start_new_chat()
        
        self.saved_chats[self.current_chat_id]["messages"].append(message)
        self.saved_chats[self.current_chat_id]["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Update history list to reflect new timestamp
        self.history_list.clear()
        for chat_id, chat_data in sorted(
            self.saved_chats.items(),
            key=lambda x: x[1]["last_updated"],
            reverse=True
        ):
            item = QListWidgetItem(f"{chat_data['title']} ({chat_data['last_updated']})")
            item.setData(Qt.UserRole, chat_id)
            self.history_list.addItem(item)
        
        self.save_chats_to_file()

    def load_selected_chat(self, item):
        chat_id = item.data(Qt.UserRole)
        if chat_id in self.saved_chats:
            self.current_chat_id = chat_id
            self.chat_display.clear()
            for msg in self.saved_chats[chat_id]["messages"]:
                self.append_to_chat(msg)

    def show_history_context_menu(self, pos):
        menu = QMenu()
        rename_action = menu.addAction("Rename Chat")
        delete_action = menu.addAction("Delete Chat")
        action = menu.exec(QCursor.pos())
        
        item = self.history_list.itemAt(pos)
        if not item:
            return
        
        chat_id = item.data(Qt.UserRole)
        if action == rename_action:
            new_title, ok = QInputDialog.getText(
                self, "Rename Chat", "Enter new chat title:", text=self.saved_chats[chat_id]["title"]
            )
            if ok and new_title.strip():
                self.saved_chats[chat_id]["title"] = new_title
                self.saved_chats[chat_id]["last_updated"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.history_list.clear()
                for cid, chat_data in sorted(
                    self.saved_chats.items(),
                    key=lambda x: x[1]["last_updated"],
                    reverse=True
                ):
                    new_item = QListWidgetItem(f"{chat_data['title']} ({chat_data['last_updated']})")
                    new_item.setData(Qt.UserRole, cid)
                    self.history_list.addItem(new_item)
                self.save_chats_to_file()
        
        elif action == delete_action:
            reply = QMessageBox.question(
                self, "Delete Chat", "Are you sure you want to delete this chat?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                del self.saved_chats[chat_id]
                self.save_chats_to_file()
                self.history_list.takeItem(self.history_list.row(item))
                if self.current_chat_id == chat_id:
                    self.current_chat_id = None
                    self.chat_display.clear()

    def show_full_image(self, image_path):
        dialog = QDialog(self)
        dialog.setWindowTitle("Full Image")
        layout = QVBoxLayout(dialog)
        full_label = QLabel()
        full_pixmap = QPixmap(image_path)
        full_label.setPixmap(full_pixmap)
        full_label.setScaledContents(True)
        layout.addWidget(full_label)
        dialog.resize(full_pixmap.width(), full_pixmap.height())
        dialog.exec()

    def toggle_sidebar(self):
        is_open = self.sidebar.isVisible()
        if is_open:
            self.sidebar_animation.setStartValue(self.sidebar.width())
            self.sidebar_animation.setEndValue(0)
            self.sidebar_animation.start()
            QTimer.singleShot(300, lambda: self.sidebar.setVisible(False))
            self.sidebar_toggle_button.setText("☰")
        else:
            self.sidebar.setVisible(True)
            self.sidebar_animation.setStartValue(0)
            self.sidebar_animation.setEndValue(220)
            self.sidebar_animation.start()
            self.sidebar_toggle_button.setText("X")

    def closeEvent(self, event):
        if hasattr(self, 'audio_player'):
            try:
                self.audio_player.stop_audio()
            except Exception as e:
                print(f"Error stopping audio during close: {str(e)}")
        
        try:
            if hasattr(self, 'voice_thread') and self.voice_thread and self.voice_thread.isRunning():
                self.voice_thread.quit()
                if not self.voice_thread.wait(1000):
                    print("Voice thread did not terminate in time")
            if hasattr(self, 'image_thread') and self.image_thread and self.image_thread.isRunning():
                self.image_thread.quit()
                if not self.image_thread.wait(1000):
                    print("Image thread did not terminate in time")
        except Exception as e:
            print(f"Error during thread cleanup: {str(e)}")
        
        event.accept()

    def check_enter_key(self):
        cursor = self.user_input.textCursor()
        text = self.user_input.toPlainText()
        if text.endswith('\n'):
            self.user_input.setPlainText(text.rstrip('\n'))
            self.send_text_message()

    def append_to_chat(self, message):
        if message.startswith("You: "):
            bubble = ChatBubble(message[5:], is_user=True)
            alignment = Qt.AlignRight
        elif message.startswith("Bot: "):
            bubble = ChatBubble(message[5:], is_user=False)
            alignment = Qt.AlignLeft
        else:
            bubble = ChatBubble(message, is_user=False)
            alignment = Qt.AlignLeft

        item = QListWidgetItem()
        item.setSizeHint(bubble.sizeHint())
        item.setTextAlignment(alignment)

        self.chat_display.addItem(item)
        self.chat_display.setItemWidget(item, bubble)
        self.chat_display.scrollToBottom()

    def send_text_message(self):
        user_msg = self.user_input.toPlainText().strip()
        if not user_msg:
            return
        self.append_to_chat(f"You: {user_msg}")
        self.append_to_current_chat(f"You: {user_msg}")
        self.user_input.clear()
    
        response = chat_with_model(user_msg, speak_output=False)
        if isinstance(response, tuple):
            response_text, _ = response
        else:
            response_text = response
        self.append_to_chat(f"Bot: {response_text}")
        self.append_to_current_chat(f"Bot: {response_text}")

    def handle_text_to_voice(self):
        user_input = self.user_input.toPlainText().strip()
        if not user_input:
            user_input, ok = QInputDialog.getText(self, "Text-to-Voice", "Enter text:")
            if not (ok and user_input.strip()):
                return
        else:
            self.user_input.clear()

        self.append_to_chat(f"You: {user_input}")
        self.append_to_current_chat(f"You: {user_input}")

    # Stop any ongoing audio
        self.audio_player.stop_audio()

        response = chat_with_model(user_input, speak_output=True)
        if isinstance(response, tuple):
            response_text, audio_path = response
        else:
            response_text = response
            audio_path = None

        self.append_to_chat(f"Bot: {response_text}")
        self.append_to_current_chat(f"Bot: {response_text}")

        if audio_path and os.path.exists(audio_path):
            self.audio_player.play_audio(audio_path)

    def handle_voice_chat(self):
        if hasattr(self, 'voice_thread') and self.voice_thread and self.voice_thread.isRunning():
            print("Voice thread already running")
            return
        
        self.voice_btn.setText("🎙️ Listening...")
        self.voice_btn.setEnabled(False)

        self.popup = VoiceListeningPopup()
        self.popup.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.popup.show()

        self.voice_thread = VoiceChatThread()
        
        def safe_connect(signal, slot):
            try:
                signal.connect(slot)
            except Exception as e:
                print(f"Error connecting signal: {str(e)}")
        
        safe_connect(self.voice_thread.partial_text, self.popup.update_transcription)
        safe_connect(self.voice_thread.result_signal, self.on_voice_response)
        safe_connect(self.voice_thread.finished, lambda: (
            self.popup.close(),
            self.reset_voice_btn()
        ))
        
        self.voice_thread.start()

    def on_voice_response(self, response):
        if response.startswith("AUDIO_PATH::"):
            audio_path = response.split("AUDIO_PATH::")[1].strip()
            if os.path.exists(audio_path):
                self.audio_player.play_audio(audio_path)
        else:
            self.append_to_chat(response)
            self.append_to_current_chat(response)

    def reset_voice_btn(self):
        self.voice_btn.setText("🎙️ Voice Chat")
        self.voice_btn.setEnabled(True)

    def handle_image_recognition(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Choose Input Method")
        msg.setText("Use Camera or Select Image File?")
        cam_btn = msg.addButton("Camera", QMessageBox.AcceptRole)
        file_btn = msg.addButton("Image File", QMessageBox.AcceptRole)
        msg.addButton("Cancel", QMessageBox.RejectRole)
        msg.exec()

        if msg.clickedButton() == cam_btn:
            image_path = capture_image()
            if not image_path:
                self.append_to_chat("Bot: Failed to capture image from camera.")
                self.append_to_current_chat("Bot: Failed to capture image from camera.")
                return
        elif msg.clickedButton() == file_btn:
            image_path, _ = QFileDialog.getOpenFileName(self, "Open Image", "", "Images (*.png *.jpg *.jpeg)")
            if not image_path:
                return
        else:
            return

        filename = image_path.split('/')[-1] if '/' in image_path else image_path.split('\\')[-1]
        self.append_to_chat(f"You: Processing image {filename}")
        self.append_to_current_chat(f"You: Processing image {filename}")
        
        self.image_thread = ImageProcessingThread(image_path)
        self.show_image_preview(image_path)
        self.image_thread.result_signal.connect(lambda msg: (
            self.append_to_chat(msg),
            self.append_to_current_chat(msg)
        ))
        self.image_thread.start()

    def show_image_preview(self, image_path):
        try:
            label = QLabel()
            pixmap = QPixmap(image_path)
            if pixmap.isNull():
                self.append_to_chat(f"Bot: Error loading image from {image_path}")
                self.append_to_current_chat(f"Bot: Error loading image from {image_path}")
                return

            max_width = 200
            max_height = 300
            scaled_pixmap = pixmap.scaled(max_width, max_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            label.setPixmap(scaled_pixmap)
            label.setFixedSize(scaled_pixmap.size())
            label.setAlignment(Qt.AlignCenter)

            container = QWidget()
            container_layout = QHBoxLayout(container)
            container_layout.setContentsMargins(10, 5, 10, 5)
            container_layout.addStretch()
            container_layout.addWidget(label)
            container_layout.addStretch()

            list_item = QListWidgetItem()
            list_item.setSizeHint(container.sizeHint())

            self.chat_display.addItem(list_item)
            self.chat_display.setItemWidget(list_item, container)
            self.chat_display.scrollToBottom()
        except Exception as e:
            self.append_to_chat(f"Bot: Error displaying image: {str(e)}")
            self.append_to_current_chat(f"Bot: Error displaying image: {str(e)}")

    def fetch_news(self):
        news_items = get_news()
        while self.news_layout.count():
            item = self.news_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for item in news_items:
            card = NewsCard(
                title=item.get("title", "No Title"),
                snippet=item.get("snippet", "No Description"),
                link=item.get("link", "#")
            )
            self.news_layout.addWidget(card)

        self.news_layout.addStretch()

    def fetch_weather_for_cities(self):
        cities = ["Dehradun", "Delhi", "Mumbai", "Bengaluru", "Kolkata"]
        while self.weather_layout.count():
            item = self.weather_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for city in cities:
            try:
                url = f"https://wttr.in/{city}?format=j1"
                response = requests.get(url)
                if response.status_code != 200:
                    self.show_error(f"{city}: Failed to fetch weather. HTTP {response.status_code}")
                    continue

                try:
                    data = response.json()
                except ValueError:
                    self.show_error(f"{city}: Invalid JSON response.")
                    continue

                if "current_condition" in data:
                    current = data["current_condition"][0]
                    temp = current["temp_C"]
                    feels_like = current["FeelsLikeC"]
                    humidity = current["humidity"]
                    weather_desc = current["weatherDesc"][0]["value"]

                    card = WeatherCard(city, temp, feels_like, humidity, weather_desc)
                    self.weather_layout.addWidget(card)
                else:
                    self.show_error(f"{city}: No weather data found.")
            except requests.RequestException as e:
                self.show_error(f"{city}: Failed to fetch weather.\n{str(e)}")
            except Exception as e:
                self.show_error(f"{city}: Failed to fetch weather.\n{str(e)}")

            self.weather_layout.addStretch()

    def show_error(self, message):
        QMessageBox.warning(self, "Weather Error", message)

    def set_username(self, username):
        self.user_label.setText(f"👤 {username}")

    from backend import ImageGenerationThread

    def handle_text_to_image(self):
        prompt = self.user_input.toPlainText().strip()
        if not prompt:
            prompt, ok = QInputDialog.getText(self, "Text-to-Image", "Enter a description for the image:")
            if not (ok and prompt.strip()):
                return
        else:
            self.user_input.clear()

        self.append_to_chat(f"You: {prompt}")
        self.append_to_current_chat(f"You: {prompt}")
        self.append_to_chat("Bot: Generating image...")

        self.image_gen_thread = ImageGenerationThread(prompt)
        self.image_gen_thread.finished.connect(self.handle_image_result)
        self.image_gen_thread.start()

    def handle_image_result(self, response):
        self.append_to_current_chat(f"Bot: {response}")
        if response.startswith("Image generated and saved at:"):
            image_path = response.split("Image generated and saved at: ")[-1].strip()
            self.append_to_chat("Bot: Image generated successfully!")
            self.show_image_preview(image_path)
        else:
            self.append_to_chat(f"Bot: {response}")

if __name__ == "__main__":
    print("Launching Bhaskara AI...")
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("fusion")

    splash = CustomSplashScreen()
    splash.show()

    main_window = MainWindow()
    icon = QIcon(resource_path("assets/Bhaskara AI.png"))
    main_window.setWindowIcon(icon)

    def show_main_window():
        saved_username = load_session()
        if saved_username:
            main_window.set_username(saved_username)
            main_window.show()
            splash.close()
        else:
            main_window.login_page = LoginSignupPage()
            main_window.login_page.login_successful.connect(main_window.set_username)
            main_window.login_page.login_successful.connect(main_window.show)
            main_window.login_page.login_successful.connect(splash.close)
            main_window.login_page.show()
            splash.close()
        
    QTimer.singleShot(6000, show_main_window)
    sys.exit(app.exec())