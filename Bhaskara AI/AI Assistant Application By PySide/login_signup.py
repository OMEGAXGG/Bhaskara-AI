import sqlite3
from PySide6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QMessageBox, QApplication
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt, Signal, QTimer, QProcess
import json
from utils.session_manager import save_session, clear_session
import sys

class LoginSignupPage(QWidget):
    login_successful = Signal(str)  # signal that passes username on success

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Account")
        self.setFixedSize(320, 280)
        self.setStyleSheet("background-color: #2c2f33; color: white;")
        self.init_ui()
        self.init_db()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Account Login / Signup")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #23272a; color: white;")

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("padding: 8px; border-radius: 5px; background-color: #23272a; color: white;")

        self.login_btn = QPushButton("Login")
        self.signup_btn = QPushButton("Signup")
        self.logout_btn = QPushButton("Logout")  # 🔘 Added logout button

        for btn in [self.login_btn, self.signup_btn]:
            btn.setStyleSheet("""
                QPushButton {
                    padding: 10px; font-size: 13px;
                    background-color: #7289da; color: white;
                    border: none; border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #5b6eae;
                }
            """)
        
        # Style Logout button (red)
        self.logout_btn.setStyleSheet("""
            QPushButton {
                padding: 10px; font-size: 13px;
                background-color: #e74c3c; color: white;
                border: none; border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)

        self.login_btn.clicked.connect(self.login_user)
        self.signup_btn.clicked.connect(self.signup_user)
        self.logout_btn.clicked.connect(self.logout_user)  # 🧹 Connected to logout method

        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_btn)
        layout.addWidget(self.signup_btn)
        layout.addSpacing(10)
        layout.addWidget(self.logout_btn)  # 👇 Placed below login/signup
        layout.addStretch()

    def init_db(self):
        self.conn = sqlite3.connect("users.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT
            )
        """)
        self.conn.commit()

    def signup_user(self):
        username = self.username_input.text()
        password = self.password_input.text()
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            self.conn.commit()
            QMessageBox.information(self, "Success", "User registered successfully!")
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Error", "Username already exists.")

    def login_user(self):
        username = self.username_input.text()
        password = self.password_input.text()
        self.cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = self.cursor.fetchone()
        if user:
            QMessageBox.information(self, "Login Successful", f"Welcome back, {username}!")
            with open("user_login_status.json", "w") as f:
                json.dump({"username": username, "click_count": 0}, f)
            
            save_session(username)
            self.login_successful.emit(username)
            self.close()
        else:
            QMessageBox.warning(self, "Login Failed", "Incorrect username or password.")

    def logout_user(self):
        clear_session()
        QMessageBox.information(self, "Logout", "You have been logged out.")
        QTimer.singleShot(500, self.restart_app)

    def restart_app(self):
        QApplication.quit()
        QProcess.startDetached(sys.executable, sys.argv)
