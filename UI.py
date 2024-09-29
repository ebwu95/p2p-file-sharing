import sys
import cohere
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QVBoxLayout, 
                             QFileDialog, QMessageBox, QStackedWidget, QTextEdit, QLineEdit)
from PyQt5.QtGui import QMovie, QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer

class ElegantButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QPushButton {
                font-size: 18px;
                background-color: #6a5acd;
                color: white;
                padding: 12px 24px;
                border-radius: 25px;
                border: 2px solid #483d8b;
            }
            QPushButton:hover {
                background-color: #483d8b;
            }
            QPushButton:pressed {
                background-color: #322b5f;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)

class FileSharingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Elegant File Sharing & Chat")
        self.setGeometry(100, 100, 800, 700)
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f8ff;
                color: #333;
            }
            QLabel {
                color: #1e90ff;
            }
        """)

        self.stacked_widget = QStackedWidget()
        self.init_main_page()
        self.init_chat_page()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

        # Initialize Cohere client
        self.cohere_api_key = "eEWivonREXwcGxJiiRfiuOroHlTei6EmSar5LEEU"
        self.co = cohere.Client(self.cohere_api_key)

    def init_main_page(self):
        main_page = QWidget()
        layout = QVBoxLayout()

        header_label = QLabel("Elegant File Sharing & Chat")
        header_label.setFont(QFont("Arial", 28, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("color: #4169e1; margin: 20px 0;")
        layout.addWidget(header_label)

        self.send_file_button = ElegantButton("Send File")
        self.send_file_button.clicked.connect(self.send_file)
        layout.addWidget(self.send_file_button, alignment=Qt.AlignCenter)

        self.gif_label = QLabel()
        self.movie = QMovie("motomoto.gif")
        self.gif_label.setMovie(self.movie)
        self.gif_label.setFixedSize(300, 300)
        layout.addWidget(self.gif_label, alignment=Qt.AlignCenter)

        self.chat_button = ElegantButton("Open Chat")
        self.chat_button.clicked.connect(self.show_chat_page)
        layout.addWidget(self.chat_button, alignment=Qt.AlignCenter)

        main_page.setLayout(layout)
        self.stacked_widget.addWidget(main_page)

        self.movie.start()

    def init_chat_page(self):
        chat_page = QWidget()
        layout = QVBoxLayout()

        chat_header = QLabel("Intelligent Chat Assistant")
        chat_header.setFont(QFont("Arial", 24, QFont.Bold))
        chat_header.setAlignment(Qt.AlignCenter)
        chat_header.setStyleSheet("color: #4169e1; margin: 20px 0;")
        layout.addWidget(chat_header)

        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            background-color: white;
            border: 2px solid #b0c4de;
            border-radius: 10px;
            padding: 10px;
        """)
        layout.addWidget(self.chat_display)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message here...")
        self.chat_input.setStyleSheet("""
            background-color: white;
            border: 2px solid #b0c4de;
            border-radius: 15px;
            padding: 8px 15px;
            font-size: 16px;
        """)
        self.chat_input.returnPressed.connect(self.send_message)
        layout.addWidget(self.chat_input)

        send_button = ElegantButton("Send")
        send_button.clicked.connect(self.send_message)
        layout.addWidget(send_button, alignment=Qt.AlignRight)

        back_button = ElegantButton("Back to Main")
        back_button.clicked.connect(self.show_main_page)
        layout.addWidget(back_button, alignment=Qt.AlignCenter)

        chat_page.setLayout(layout)
        self.stacked_widget.addWidget(chat_page)

    def send_file(self):
        file_name, _ = QFileDialog.getOpenFileName(self, "Select File to Send")
        if file_name:
            QMessageBox.information(self, "File Sent", f"File '{file_name}' is being sent!")

    def show_chat_page(self):
        self.stacked_widget.setCurrentIndex(1)

    def show_main_page(self):
        self.stacked_widget.setCurrentIndex(0)

    def send_message(self):
        message = self.chat_input.text()
        if message:
            self.chat_display.append(f"You: {message}")
            self.chat_input.clear()
            
            # Use Cohere API to generate a response
            try:
                response = self.co.generate(
                    model='command',
                    prompt=f'Human: {message}\nAI:',
                    max_tokens=150,
                    temperature=0.9,
                    k=0,
                    stop_sequences=["Human:", "AI:"],
                    return_likelihoods='NONE'
                )
                ai_response = response.generations[0].text.strip()
                self.chat_display.append(f"Assistant: {ai_response}")
            except Exception as e:
                self.chat_display.append(f"Assistant: I'm sorry, I encountered an error: {str(e)}")

            # Scroll to the bottom of the chat display
            self.chat_display.verticalScrollBar().setValue(
                self.chat_display.verticalScrollBar().maximum()
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileSharingApp()
    window.show()
    sys.exit(app.exec_())