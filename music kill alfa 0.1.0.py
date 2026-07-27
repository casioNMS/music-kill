import tkinter as tk
import pygame
from mutagen.mp3 import MP3
import os
import time
import random

pygame.mixer.init()

BASE_DIR = os.path.abspath("Music Kill")


def format_time(seconds):
    m = seconds // 60
    s = seconds % 60
    return f"{m:02}:{s:02}"


class MusicKill:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Kill alfa 0.1.0")
        self.root.geometry("780x470")
        self.root.resizable(False, False)

        os.makedirs(BASE_DIR, exist_ok=True)

        self.current_dir = BASE_DIR
        self.musics = []
        self.current_index = 0
        self.length = 0
        self.start_time = 0
        self.paused = False

        # ===== LAYOUT =====
        left = tk.Frame(root)
        left.pack(side="left", padx=10)

        right = tk.Frame(root)
        right.pack(side="right", padx=10)

        # ===== NAVEGADOR =====
        tk.Label(left, text="Pastas / Músicas").pack()

        self.listbox = tk.Listbox(left, width=30, height=18)
        self.listbox.pack()
        self.listbox.bind("<Double-Button-1>", self.open_item)

        tk.Button(left, text="⬅ Voltar", command=self.go_back).pack(pady=5)
        tk.Button(left, text="🔄 Atualizar", command=self.load_dir).pack()

        # ===== VISUALIZADOR =====
        self.canvas = tk.Canvas(right, width=380, height=110, bg="black")
        self.canvas.pack(pady=5)

        # Texto música
        self.text_music = self.canvas.create_text(
            190, 18,
            text="",
            fill="white",
            font=("Arial", 11, "bold")
        )

        # Texto tempo
        self.text_time = self.canvas.create_text(
            190, 38,
            text="",
            fill="gray",
            font=("Arial", 9)
        )

        # Barras (ondas)
        self.bars = []
        self.bar_count = 32
        self.center_y = 80
        bar_width = 380 // self.bar_count

        for i in range(self.bar_count):
            x1 = i * bar_width
            x2 = x1 + bar_width - 2
            bar = self.canvas.create_rectangle(
                x1,
                self.center_y,
                x2,
                self.center_y,
                fill="lime",
                outline=""
            )
            self.bars.append(bar)

        # ===== PROGRESSO =====
        self.scale = tk.Scale(
            right, from_=0, to=100,
            orient="horizontal", length=380
        )
        self.scale.pack()
        self.scale.bind("<ButtonRelease-1>", self.seek)

        # ===== CONTROLES =====
        controls = tk.Frame(right)
        controls.pack(pady=5)

        tk.Button(controls, text="Play", command=self.play).grid(row=0, column=0, padx=5)
        tk.Button(controls, text="Pause", command=self.pause).grid(row=0, column=1, padx=5)
        tk.Button(controls, text="Stop", command=self.stop).grid(row=0, column=2, padx=5)

        self.load_dir()
        self.update()

    # ===== NAVEGAÇÃO =====
    def load_dir(self):
        self.listbox.delete(0, tk.END)
        self.musics.clear()

        for item in sorted(os.listdir(self.current_dir)):
            path = os.path.join(self.current_dir, item)
            if os.path.isdir(path):
                self.listbox.insert(tk.END, f"📁 {item}")
            elif item.lower().endswith(".mp3"):
                self.listbox.insert(tk.END, f"🎵 {item}")
                self.musics.append(item)

    def open_item(self, event):
        if not self.listbox.curselection():
            return

        item = self.listbox.get(self.listbox.curselection())
        name = item[2:]
        path = os.path.join(self.current_dir, name)

        if item.startswith("📁"):
            self.current_dir = path
            self.load_dir()
        elif item.startswith("🎵"):
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
        self.scale.config(to=self.length)

        pygame.mixer.music.load(path)
        pygame.mixer.music.play()
        self.start_time = time.time()
        self.paused = False

        self.canvas.itemconfig(self.text_music, text=f"🎵 {music}")
        self.canvas.itemconfig(
            self.text_time,
            text=f"⏱ 00:00 / {format_time(self.length)}"
        )

    def pause(self):
        if self.paused:
            pygame.mixer.music.unpause()
            self.start_time = time.time() - self.scale.get()
            self.paused = False
        else:
            pygame.mixer.music.pause()
            self.paused = True

    def stop(self):
        pygame.mixer.music.stop()
        self.scale.set(0)
        self.canvas.itemconfig(self.text_time, text="")
        self.paused = False

    def seek(self, event):
        pos = self.scale.get()
        pygame.mixer.music.play(start=pos)
        self.start_time = time.time() - pos
        self.paused = False

    # ===== UPDATE =====
    def update(self):
        if pygame.mixer.music.get_busy() and not self.paused:
            current = int(time.time() - self.start_time)
            if current <= self.length:
                self.scale.set(current)
                self.canvas.itemconfig(
                    self.text_time,
                    text=f"⏱ {format_time(current)} / {format_time(self.length)}"
                )

            for bar in self.bars:
                height = random.randint(5, 35)
                x1, _, x2, _ = self.canvas.coords(bar)
                self.canvas.coords(
                    bar,
                    x1,
                    self.center_y - height,
                    x2,
                    self.center_y + height
                )

        self.root.after(150, self.update)


root = tk.Tk()
MusicKill(root)
root.mainloop()
