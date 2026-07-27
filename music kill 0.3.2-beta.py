import sys
import os
import time
import random
import pygame
import shutil
from mutagen.mp3 import MP3

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QListWidget, QPushButton, QLabel,
    QSlider, QHBoxLayout, QVBoxLayout, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPainter, QColor

pygame.mixer.init()

BASE_DIR = os.path.abspath("Music Kill")


def format_time(seconds):
    m = seconds // 60
    s = seconds % 60
    return f"{m:02}:{s:02}"


# ===== VISUALIZADOR =====
class Visualizer(QWidget):
    def __init__(self):
        super().__init__()
        self.bars = [0] * 32
        self.setMinimumHeight(100)

    def update_bars(self):
        self.bars = [random.randint(10, 45) for _ in self.bars]
        self.update()

    def clear(self):
        self.bars = [0] *len(self.bars)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("black"))

        w = self.width() // len(self.bars)
        center = self.height() // 2

        painter.setBrush(QColor("lime"))
        painter.setPen(Qt.NoPen)

        for i, h in enumerate(self.bars):
            x = i * w
            painter.drawRect(x, center - h // 2, w - 2, h)


# ===== APP PRINCIPAL =====
class MusicKill(QMainWindow):
    def __init__(self):
        super().__init__()


        self.setWindowTitle("Music Kill 0.3.2-beta")
        self.setFixedSize(800, 500)

        self.setAcceptDrops(True)
        os.makedirs(BASE_DIR, exist_ok=True)

        self.current_dir = BASE_DIR
        self.musics = []
        self.current_index = 0
        self.length = 0
        self.start_time = 0
        self.paused = False

        # controls = QHBoxLayout()
        # right.addLayout(controls)

        # ===== LAYOUT =====
        main = QWidget()
        self.setCentralWidget(main)

        layout = QHBoxLayout(main)

        # ===== ESQUERDA =====
        left = QVBoxLayout()
        layout.addLayout(left)

        left.addWidget(QLabel("Pastas / Músicas"))

        self.listbox = QListWidget()
        self.listbox.itemDoubleClicked.connect(self.open_item)
        left.addWidget(self.listbox)

        btn_back = QPushButton("⬅ Voltar")
        btn_back.clicked.connect(self.go_back)
        left.addWidget(btn_back)

        btn_refresh = QPushButton("🔄 Atualizar")
        btn_refresh.clicked.connect(self.load_dir)
        left.addWidget(btn_refresh)

        btn_mais = QPushButton("mais...")
        btn_mais.clicked.connect(self.openMORE)
        left.addWidget(btn_mais)

        btn_ex = QPushButton("🗑")
        btn_ex.clicked.connect(self.deleteMusic)
        left.addWidget(btn_ex)


        # ===== DIREITA =====
        right = QVBoxLayout()
        layout.addLayout(right)

        self.lbl_music = QLabel("")
        self.lbl_music.setAlignment(Qt.AlignCenter)
        right.addWidget(self.lbl_music)

        self.lbl_time = QLabel("")
        self.lbl_time.setAlignment(Qt.AlignCenter)
        right.addWidget(self.lbl_time)

        self.visualizer = Visualizer()
        right.addWidget(self.visualizer)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderReleased.connect(self.seek)
        right.addWidget(self.slider)

        controls = QHBoxLayout()
        right.addLayout(controls)

        btn_prev = QPushButton("⏮")
        btn_prev.clicked.connect(self.prevMusic)
        controls.addWidget(btn_prev)

        btn_play = QPushButton("▶/🔄")
        btn_play.clicked.connect(self.play)
        controls.addWidget(btn_play)

        btn_pause = QPushButton("⏺")
        btn_pause.clicked.connect(self.pause)
        controls.addWidget(btn_pause)

        # btn_stop = QPushButton("Stop")
        # btn_stop.clicked.connect(self.stop)
        # controls.addWidget(btn_stop)

        btn_next = QPushButton("⏭")
        btn_next.clicked.connect(self.next_music)
        controls.addWidget(btn_next)

        # ===== TIMER =====
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ui)
        self.timer.start(150)

        self.load_dir()

    def deleteMusic(self):
        item = self.listbox.currentItem()

        if not item:
            QMessageBox.warning(self, "Aviso", "Nenhuma música selecionada.")
            return

        text = item.text()

        # Só permite excluir músicas
        if not text.startswith("🎵"):
            QMessageBox.warning(self, "Aviso", "Selecione uma música.")
            return

        music_name = text[2:]
        path = os.path.join(self.current_dir, music_name)

        reply = QMessageBox.question(
            self,
            "Confirmar exclusão",
            f"Tem certeza que deseja excluir:\n\n{music_name} ?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                pygame.mixer.music.stop()
                os.remove(path)

                self.length = 0
                self.slider.setValue(0)
                self.lbl_music.setText("")
                self.lbl_time.setText("")

                self.load_dir()

            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Não foi possível excluir:\n{e}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        for url in event.mimeData().urls():
            path = url.toLocalFile()

            if path.lower().endswith(".mp3"):
                dest = os.path.join(self.current_dir, os.path.basename(path))

                if not os.path.exists(dest):
                    shutil.copy(path, dest)

        self.load_dir()

    def prevMusic(self):
        if not self.musics:
            return
        
        self.current_index -= 1
        if self.current_index <0:
            self.current_index = len(self.musics) -1

        self.play()
    def openMORE(self):
        if not hasattr(self, "volume_Window"):
            self.volume_Window = volumeWindow()
        self.volume_Window.show()

    # ===== NAVEGAÇÃO =====
    def load_dir(self):
        self.listbox.clear()
        self.musics.clear()

        for item in sorted(os.listdir(self.current_dir)):
            path = os.path.join(self.current_dir, item)
            if os.path.isdir(path):
                self.listbox.addItem(f"📁 {item}")
            elif item.lower().endswith(".mp3"):
                self.listbox.addItem(f"🎵 {item}")
                self.musics.append(item)

    def open_item(self, item):
        text = item.text()
        name = text[2:]
        path = os.path.join(self.current_dir, name)

        if text.startswith("📁"):
            self.current_dir = path
            self.load_dir()
        elif text.startswith("🎵"):
            self.current_index = self.musics.index(name)
            self.play()

    def go_back(self):
        if self.current_dir != BASE_DIR:
            self.current_dir = os.path.dirname(self.current_dir)
            self.load_dir()

    # ===== PLAYER =====
    def play(self):
        if not self.musics:
            return

        music = self.musics[self.current_index]
        path = os.path.join(self.current_dir, music)

        audio = MP3(path)
        self.length = int(audio.info.length)

        self.slider.setMaximum(self.length)

        pygame.mixer.music.load(path)
        pygame.mixer.music.play()

        self.start_time = time.time()
        self.paused = False

        self.lbl_music.setText(f"🎵 {music}")
        self.lbl_time.setText(f"⏱ 00:00 / {format_time(self.length)}")

    def pause(self):
        if self.paused:
            pygame.mixer.music.unpause()
            self.start_time = time.time() - self.slider.value()
            self.paused = False
        else:
            pygame.mixer.music.pause()
            self.paused = True

    def stop(self):
        pygame.mixer.music.stop()
        self.slider.setValue(0)
        self.lbl_time.setText("")
        self.paused = False

    def seek(self):
        pos = self.slider.value()
        pygame.mixer.music.play(start=pos)
        self.start_time = time.time() - pos
        self.paused = False

    # ===== UPDATE =====
    def update_ui(self):
        if not pygame.mixer.music.get_busy() and not self.paused and self.length >0:
            self.next_music()
            return


        if pygame.mixer.music.get_busy() and not self.paused:
            current = int(time.time() - self.start_time)
            if current <= self.length:
                self.slider.setValue(current)
                self.lbl_time.setText(
                    f"⏱ {format_time(current)} / {format_time(self.length)}"
                )
            self.visualizer.update_bars()

    def next_music(self):
        if not self.musics:
            return
        
        self.current_index +=1

        if self.current_index >= len(self.musics):
            self.current_index =0

        self.play()

class volumeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("mais op")
        self.setFixedSize(300, 100)

        layout = QVBoxLayout(self)

        label = QLabel("🔊 Volume")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(0, 100)
        self.slider.setValue(50)  # volume inicial
        self.slider.valueChanged.connect(self.change_volume)
        layout.addWidget(self.slider)

        pygame.mixer.music.set_volume(0.5)

    def change_volume(self, value):
        pygame.mixer.music.set_volume(value / 100)




# ===== RUN =====
app = QApplication(sys.argv)
app.setStyleSheet("""
QMainWindow {
    background-color: #0b0b0b;
}

QLabel {
    color: #00ff99;
    font-size: 14px;
}

QListWidget {
    background-color: #111;
    color: #00ff99;
    border: 1px solid #00ff99;
}

QPushButton {
    background-color: #111;
    color: #00ff99;
    border: 1px solid solid #00ff99;
    padding: 6px;
}

QPushButton:hover {
    background-color: #00ff99;
    color: black;
}

QSlider::groove:horizontal {
    background: #222;
    height: 6px;
}

QSlider::handle:horizontal {
    background: #00ff99;
    width: 12px;
}
""")

window = MusicKill()
window.show()
sys.exit(app.exec())
