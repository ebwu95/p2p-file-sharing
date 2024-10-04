import sys
import cohere
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QLabel, QGraphicsDropShadowEffect, 
                             QVBoxLayout, QFileDialog, QMessageBox, QStackedWidget, QTextEdit, QLineEdit)
from PyQt5.QtGui import QMovie, QFont, QFontDatabase
from PyQt5.QtCore import Qt

class ElegantButton(QPushButton):
    def __init__(self, text):
        super().__init__(text)
        self.setStyleSheet("""
            QPushButton {
                font-family: 'Playfair Display';
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
        self.setWindowTitle("Mo2Moto")
        self.setGeometry(100, 100, 800, 700)
        
        # Load custom fonts
        QFontDatabase.addApplicationFont("fonts/PlayfairDisplay-Italic-VariableFont_wght.ttf")
        QFontDatabase.addApplicationFont("fonts/PlayfairDisplay-VariableFont_wght.ttf")
        
        self.setStyleSheet("""
            QWidget {
                font-family: 'Playfair Display';
                color: #333;
            }
            QLabel {
                font-family: 'Playfair Display';
                color: #1e90ff;
            }
        """)

        self.init_background()
        
        self.stacked_widget = QStackedWidget()
        self.init_main_page()
        self.init_chat_page()

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stacked_widget)
        self.setLayout(main_layout)

        # Initialize Cohere client
        self.cohere_api_key = "apikey"
        self.co = cohere.Client(self.cohere_api_key)

    def init_background(self):
        self.background_movie = QMovie("background.gif")
        self.background_label = QLabel(self)
        self.background_label.setMovie(self.background_movie)
        self.background_movie.frameChanged.connect(self.update_background)
        self.background_movie.start()

    def update_background(self):
        self.background_label.setGeometry(self.rect())
        self.background_label.lower()

    def init_main_page(self):
        main_page = QWidget()
        layout = QVBoxLayout()

        header_label = QLabel("Mo2Moto")
        header_label.setFont(QFont("Playfair Display", 32, QFont.Bold))
        header_label.setAlignment(Qt.AlignCenter)
        
        header_label.setStyleSheet("color: white; margin: 20px 0;")

        shadow_effect = QGraphicsDropShadowEffect()
        shadow_effect.setBlurRadius(5)
        shadow_effect.setXOffset(1)
        shadow_effect.setYOffset(1)
        shadow_effect.setColor(Qt.black)
        header_label.setGraphicsEffect(shadow_effect)
        
        layout.addWidget(header_label)

        self.send_file_button = ElegantButton("Send File")
        self.send_file_button.clicked.connect(self.send_file)
        layout.addWidget(self.send_file_button, alignment=Qt.AlignCenter)

        self.gif_label = QLabel()
        self.movie = QMovie("motomoto.gif")
        self.gif_label.setMovie(self.movie)
        self.gif_label.setFixedSize(300, 300)
        layout.addWidget(self.gif_label, alignment=Qt.AlignCenter)

        self.chat_button = ElegantButton("Ask Moto Moto")
        self.chat_button.clicked.connect(self.show_chat_page)
        layout.addWidget(self.chat_button, alignment=Qt.AlignCenter)

        main_page.setLayout(layout)
        self.stacked_widget.addWidget(main_page)

        self.movie.start()


    def init_chat_page(self):
        chat_page = QWidget()
        layout = QVBoxLayout()

        chat_header = QLabel("Moto Moto")
        chat_header.setFont(QFont("Playfair Display", 28, QFont.Bold))
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
            font-family: 'Playfair Display';
            font-size: 14px;
        """)
        layout.addWidget(self.chat_display)

        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message here...")
        self.chat_input.setStyleSheet("""
            background-color: white;
            border: 2px solid #b0c4de;
            border-radius: 15px;
            padding: 8px 15px;
            font-family: 'Playfair Display';
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
            self.chat_display.append(f"<b>You:</b> {message}")
            self.chat_input.clear()
            
            try:
                prompt = (
                    "You are an AI assistant for a peer-to-peer file-sharing application called Mo2Moto. "
                    "Your name is Moto Moto. You are a hippopotamus who helps users. "
                    "You speak in an informal way, but not being impolite. "
                    "Your purpose is to help users with tasks related to file sharing, such as uploading, downloading, "
                    "and managing files. You can also provide general assistance and answer questions about the application.\n\n"
                    "The application works as follows:\n"
                    "1. Users can upload files to share with others.\n"
                    "2. Users can download files shared by others.\n"
                    "3. The application uses a peer-to-peer network for file sharing, managed by the `Node` class in `node.py`.\n"
                    "4. The `Node` class handles incoming connections, uploads files in chunks, and manages peer connections.\n"
                    "5. The `Tracker` class in `tracker.py` keeps track of registered peers and manages chunk information.\n"
                    "6. The `file_utils.py` file contains utility functions for chunking and reassembling files.\n\n"
                    f"Human: {message}\nMoto Moto:"
                )
                
                response = self.co.generate(
                    model='command',
                    prompt=prompt,
                    max_tokens=150,
                    temperature=0.9,
                    k=0,
                    stop_sequences=["Human:", "Moto Moto:"],
                    return_likelihoods='NONE'
                )
                ai_response = response.generations[0].text.strip()
                self.chat_display.append(f"<b style='color: #4169e1;'>Moto Moto:</b> {ai_response}")
            except Exception as e:
                self.chat_display.append(f"<b style='color: #ff4500;'>Moto Moto:</b> I'm sorry, looks like something went wrong! Here's some more information I got: {str(e)}")

            self.chat_display.verticalScrollBar().setValue(
                self.chat_display.verticalScrollBar().maximum()
            )

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileSharingApp()
    window.show()
    sys.exit(app.exec_())
