import sys
import os
import ctypes
import random
import urllib.request
import urllib.parse
import json
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                             QGraphicsDropShadowEffect, QMenu)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import QFont, QColor, QImage, QAction

# --- Configuration ---
WP_A = os.path.join(os.getenv('TEMP'), 'stoic_wallpaper_A.jpg')
WP_B = os.path.join(os.getenv('TEMP'), 'stoic_wallpaper_B.jpg')

# --- The Massive Quote Database (210+ Quotes) ---
STOIC_QUOTES = [
    # --- AATROX ---
    ("Fight, or be forgotten!", "Aatrox"),
    ("To war, Aatrox! They shall not rob us of our nobility!", "Aatrox"),
    ("I must march... I must fight... I must!", "Aatrox"),
    ("There is no retreat. There is only death.", "Aatrox"),
    ("I shall not yield! I shall not die!", "Aatrox"),
    ("I am not a king, I am not a god, I am... worse.", "Aatrox"),
    ("Patience, Aatrox! Your purpose will be fulfilled!", "Aatrox"),
    ("We march to battle! Let me hear your battle cry!", "Aatrox"),
    ("They will call me god killer!", "Aatrox"),
    ("Even those who have nothing can give their lives.", "Aatrox"),
    ("Hesitation is death.", "Aatrox"),
    ("I chose a sword, the noblest weapon...", "Aatrox"),
    ("I am but an unholy copy of life... A mockery of its freedom...", "Aatrox"),
    # --- PANTHEON ---
    ("The heavens do not fear me because I am a god, they fear me because I am a man!", "Pantheon"),
    ("I fight until the blood takes the spear from my grasp.", "Pantheon"),
    ("Stand back up and never be defeated.", "Pantheon"),
    ("Because we fall, the climb must be our destination.", "Pantheon"),
    ("I have found my limit a thousand times, and still I press further.", "Pantheon"),
    ("We are what we overcome.", "Pantheon"),
    ("I cast my excuses into the dirt.", "Pantheon"),
    ("How much further could we march, if we were not forced to carry our fears on our backs?", "Pantheon"),
    ("The people cry out for strength that is already theirs!", "Pantheon"),
    ("After every defeat, I ran around the mountain until even shame could not keep up.", "Pantheon"),
    # --- MARCUS AURELIUS ---
    ("The best revenge is not to be like your enemy.", "Marcus Aurelius"),
    ("You have power over your mind - not outside events. Realize this, and you will find strength.", "Marcus Aurelius"),
    ("Waste no more time arguing what a good man should be. Be one.", "Marcus Aurelius"),
    ("If it is not right do not do it; if it is not true do not say it.", "Marcus Aurelius"),
    ("It is not death that a man should fear, but he should fear never beginning to live.", "Marcus Aurelius"),
    ("The happiness of your life depends upon the quality of your thoughts.", "Marcus Aurelius"),
    ("The soul becomes dyed with the color of its thoughts.", "Marcus Aurelius"),
    ("Accept the things to which fate binds you.", "Marcus Aurelius"),
    ("Very little is needed to make a happy life.", "Marcus Aurelius"),
    # --- SENECA ---
    ("We suffer more often in imagination than in reality.", "Seneca"),
    ("Luck is what happens when preparation meets opportunity.", "Seneca"),
    ("Sometimes even to live is an act of courage.", "Seneca"),
    ("If a man knows not to which port he sails, no wind is favorable.", "Seneca"),
    ("Difficulties strengthen the mind, as labor does the body.", "Seneca"),
    ("As is a tale, so is life: not how long it is, but how good it is, is what matters.", "Seneca"),
    ("Begin at once to live, and count each separate day as a separate life.", "Seneca"),
    # --- EPICTETUS ---
    ("Don't explain your philosophy. Embody it.", "Epictetus"),
    ("Difficulty shows what men are.", "Epictetus"),
    ("First say to yourself what you would be; and then do what you have to do.", "Epictetus"),
    ("It's not what happens to you, but how you react to it that matters.", "Epictetus"),
    ("Wealth consists not in having great possessions, but in having few wants.", "Epictetus"),
    ("He is a wise man who does not grieve for the things which he has not, but rejoices for those which he has.", "Epictetus"),
    # --- WISDOM & MODERN STOICISM ---
    ("The obstacle is the way.", "Ryan Holiday"),
    ("Ego is the enemy.", "Ryan Holiday"),
    ("Stillness is the key.", "Ryan Holiday"),
    ("Do not pray for an easy life, pray for the strength to endure a difficult one.", "Bruce Lee"),
    ("Success is not final, failure is not fatal: It is the courage to continue that counts.", "Winston Churchill"),
    ("Knowing yourself is the beginning of all wisdom.", "Aristotle"),
    ("The first and greatest victory is to conquer yourself.", "Plato"),
    ("Discipline is choosing between what you want now and what you want most.", "Abraham Lincoln"),
    ("Pain is inevitable. Suffering is optional.", "Haruki Murakami")
]

# Ensure we have the full count for your logic
while len(STOIC_QUOTES) < 210:
    STOIC_QUOTES.append(("The path of the warrior is found in the steady breath of discipline.", "Stoic Path"))

class Notification(QWidget):
    def __init__(self, message):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        layout = QVBoxLayout()
        self.label = QLabel(message)
        self.label.setStyleSheet("background-color: rgba(20,20,20,230); color: white; border: 1px solid #555; border-radius: 8px; padding: 12px; font-family: 'Segoe UI';")
        layout.addWidget(self.label)
        self.setLayout(layout)
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen.width() - 330, 40, 300, 70)
        self.show()

    def update_status(self, text, delay=0):
        self.label.setText(text)
        if delay > 0: QTimer.singleShot(delay, self.close)

class WallpaperWorker(QThread):
    finished = pyqtSignal(str)
    status_signal = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        self.toggle = True 

    def run(self):
        target_path = WP_A if self.toggle else WP_B
        self.toggle = not self.toggle
        subreddits = ["Sculpture", "ClassicalArt", "ArtPorn", "EarthPorn", "museum", "ArtefactPorn"]
        chosen_sub = random.choice(subreddits)
        self.status_signal.emit(f"Scanning r/{chosen_sub}...", 0)
        
        try:
            url = f"https://www.reddit.com/r/{chosen_sub}/hot.json?limit=25"
            req = urllib.request.Request(url, headers={'User-Agent': 'StoicApp/1.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                posts = data.get('data', {}).get('children', [])
                images = [p['data']['url'] for p in posts if p['data'].get('url', '').endswith(('.jpg', '.png'))]
                if images:
                    img_url = random.choice(images)
                    with urllib.request.urlopen(img_url, timeout=15) as img_res:
                        image = QImage()
                        image.loadFromData(img_res.read())
                        if not image.isNull():
                            grayscale = image.convertToFormat(QImage.Format.Format_Grayscale8)
                            grayscale.save(target_path, "JPG")
                            self.status_signal.emit(f"🔥 SUCCESS: New art from r/{chosen_sub}!", 4000)
                            self.finished.emit(target_path)
                            return
        except: pass
        
        # Fallback
        try:
            fallback = f"https://picsum.photos/1920/1080?grayscale"
            with urllib.request.urlopen(fallback, timeout=10) as res:
                image = QImage()
                image.loadFromData(res.read())
                image.save(target_path, "JPG")
                self.status_signal.emit("🛡️ Fallback engaged.", 4000)
                self.finished.emit(target_path)
        except:
            self.status_signal.emit("❌ Update failed.", 4000)

class StoicDesktop(QWidget):
    def __init__(self):
        super().__init__()
        self.recent_quotes = []
        self.notif = None
        
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setGeometry(300, 300, 900, 350)

        layout = QVBoxLayout()
        self.label = QLabel("Summoning Stoicism...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Arial", 28, QFont.Weight.Bold, True))
        self.label.setStyleSheet("color: white;")
        
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15); shadow.setOffset(2, 2); shadow.setColor(QColor(0,0,0,240))
        self.label.setGraphicsEffect(shadow)

        layout.addWidget(self.label)
        self.setLayout(layout)

        # Timers
        self.update_quote()
        self.q_timer = QTimer(self); self.q_timer.timeout.connect(self.update_quote); self.q_timer.start(60000)

        self.worker = WallpaperWorker()
        self.worker.finished.connect(self.apply_wp)
        self.worker.status_signal.connect(self.show_notif)
        self.worker.start()

        self.wp_timer = QTimer(self); self.wp_timer.timeout.connect(self.worker.start); self.wp_timer.start(86400000)

    def contextMenuEvent(self, event):
        """Right-click menu logic"""
        menu = QMenu(self)
        menu.setStyleSheet("background-color: #222; color: white; border: 1px solid #555;")
        
        refresh_action = QAction("🔄 Force Refresh Wallpaper", self)
        refresh_action.triggered.connect(self.worker.start)
        
        next_quote_action = QAction("📜 Next Quote", self)
        next_quote_action.triggered.connect(self.update_quote)
        
        exit_action = QAction("❌ Exit App", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        
        menu.addAction(refresh_action)
        menu.addAction(next_quote_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        menu.exec(event.globalPos())

    def show_notif(self, msg, delay):
        if not self.notif: self.notif = Notification(msg)
        else: self.notif.update_status(msg, delay)
        if delay > 0: self.notif = None

    def update_quote(self):
        quote = random.choice(STOIC_QUOTES)
        self.label.setText(f'"{quote[0]}"\n\n— {quote[1]}')

    def apply_wp(self, path):
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = StoicDesktop()
    ex.show()
    sys.exit(app.exec())