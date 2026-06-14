import sys

from PySide6.QtCore import QTimer
from PySide6.QtGui import QShortcut
from PySide6.QtGui import QKeySequence

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QTextEdit,
    QLabel,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout
)

from translator import translate
from save_manager import save_documents


class DualScribe(QWidget):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("DualScribe")
        self.resize(1400, 800)

        self.ko_editor = QTextEdit()
        self.en_editor = QTextEdit()

        self.en_editor.setReadOnly(True)

        layout = QHBoxLayout()

        left = QVBoxLayout()
        right = QVBoxLayout()

        left.addWidget(QLabel("한국어"))
        left.addWidget(self.ko_editor)

        right.addWidget(QLabel("English"))
        right.addWidget(self.en_editor)

        layout.addLayout(left)
        layout.addLayout(right)

        self.setLayout(layout)

        self.timer = QTimer()

        self.timer.setSingleShot(True)

        self.timer.timeout.connect(
            self.perform_translation
        )

        self.ko_editor.textChanged.connect(
            self.schedule_translation
        )

        save_shortcut = QShortcut(
            QKeySequence("Ctrl+S"),
            self
        )

        save_shortcut.activated.connect(
            self.save_files
        )

    def schedule_translation(self):

        self.timer.start(800)

    def perform_translation(self):

        text = self.ko_editor.toPlainText()

        result = translate(text)

        self.en_editor.setPlainText(result)

    def save_files(self):

        korean = self.ko_editor.toPlainText()

        english = self.en_editor.toPlainText()

        ko_file, en_file = save_documents(
            korean,
            english
        )

        QMessageBox.information(
            self,
            "Saved",
            f"{ko_file.name}\n{en_file.name}"
        )


app = QApplication(sys.argv)

window = DualScribe()

window.show()

sys.exit(app.exec())
