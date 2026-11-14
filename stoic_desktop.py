"""Stoic Desktop: a transparent desktop widget that cycles Stoic quotes and gives you a fresh,
dark grayscale classical-art wallpaper every day.

Right-click the quote for the menu. Drag it with the left mouse button to move it.
"""
import ctypes
import gc
import json
import os
import random
import re
# Only to run Windows' own PowerShell, with fixed arguments.
import subprocess  # nosec B404
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

from PyQt6.QtCore import QBuffer, QByteArray, QIODevice, QPoint, QSettings, QSize, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QFont, QImage, QImageReader, QPainter
from PyQt6.QtWidgets import QApplication, QGraphicsDropShadowEffect, QLabel, QMenu, QVBoxLayout, QWidget

# --- Settings you can change ---
QUOTE_MINUTES = 1             # a new quote this often
WALLPAPER_HOURS = 24          # a new wallpaper this often (checked hourly, so restarts don't skip or repeat it)
WALLPAPER_DIM = 70            # 0-255: how much darker the art is made, so the quote stays readable
# Epic fantasy art (warriors, battles, castles, landscapes) and classical art and sculpture.
SUBREDDITS = ["ImaginaryWarriors", "ImaginaryBattlefields", "ImaginaryKnights", "ImaginaryCastles",
              "ClassicalArt", "Sculpture"]

APP_NAME = "Stoic Desktop"
USER_AGENT = "windows:stoic-desktop:1.2 (desktop wallpaper widget)"
TEMP_DIR = Path(os.environ.get("TEMP") or Path.home())
WP_A = TEMP_DIR / "stoic_wallpaper_A.jpg"   # two files, used in turn, so Windows always sees a new path
WP_B = TEMP_DIR / "stoic_wallpaper_B.jpg"
MAX_DOWNLOAD = 40 * 1024 * 1024               # never read more than 40 MB from the internet
MAX_PIXELS = 100_000_000                      # and never decode a picture bigger than 100 megapixels
THUMB_WIDTHS = (1280, 1920, 2560, 3840)       # Wikimedia's standard copy sizes
# Images are only ever downloaded over HTTPS from these hosts.
ALLOWED_HOSTS = {"www.reddit.com", "i.redd.it", "commons.wikimedia.org", "upload.wikimedia.org", "thumb.wikimedia.org",
                 "openaccess-api.clevelandart.org", "openaccess-cdn.clevelandart.org",
                 "picsum.photos", "fastly.picsum.photos"}
COMMONS_API = "https://commons.wikimedia.org/w/api.php"

# Public-domain masterpieces about courage, struggle and endurance, from Wikimedia Commons:
# (title, artist, file name on Commons). Every one is checked to exist at a good size.
MASTERPIECES = [
    ("Wanderer above the Sea of Fog", "Caspar David Friedrich", "Caspar David Friedrich - Wanderer above the sea of fog.jpg"),
    ("Napoleon Crossing the Alps", "Jacques-Louis David", "David - Napoleon crossing the Alps - Malmaison1.jpg"),
    ("Leonidas at Thermopylae", "Jacques-Louis David", "Jacques-Louis David - Leonidas at Thermopylae - WGA6095.jpg"),
    ("The Death of Socrates", "Jacques-Louis David", "David - The Death of Socrates.jpg"),
    ("The Oath of the Horatii", "Jacques-Louis David", "Jacques-Louis David, Le Serment des Horaces.jpg"),
    ("The Course of Empire: Destruction", "Thomas Cole", "Cole Thomas The Course of Empire Destruction 1836.jpg"),
    ("Washington Crossing the Delaware", "Emanuel Leutze", "Washington Crossing the Delaware by Emanuel Leutze, MMA-NYC, 1851.jpg"),
    ("Liberty Leading the People", "Eugène Delacroix", "Eugène Delacroix - La liberté guidant le peuple.jpg"),
    ("The Raft of the Medusa", "Théodore Géricault",
     "JEAN LOUIS THÉODORE GÉRICAULT - La Balsa de la Medusa (Museo del Louvre, 1818-19).jpg"),
    ("The Fighting Temeraire", "J. M. W. Turner", "The Fighting Temeraire, JMW Turner, National Gallery.jpg"),
    ("Pollice Verso", "Jean-Léon Gérôme", "Jean-Leon Gerome Pollice Verso.jpg"),
    ("The Ninth Wave", "Ivan Aivazovsky", "Hovhannes Aivazovsky - The Ninth Wave - Google Art Project.jpg"),
    ("The Sea of Ice", "Caspar David Friedrich", "Caspar David Friedrich - Das Eismeer - Hamburger Kunsthalle - 02.jpg"),
    ("The Monk by the Sea", "Caspar David Friedrich", "Caspar David Friedrich - Der Mönch am Meer - Google Art Project.jpg"),
    ("The School of Athens", "Raphael", "\"The School of Athens\" by Raffaello Sanzio da Urbino.jpg"),
    ("The Night Watch", "Rembrandt", "The Night Watch - HD.jpg"),
    ("Among the Sierra Nevada", "Albert Bierstadt", "Albert Bierstadt - Among the Sierra Nevada, California - Google Art Project.jpg"),
    ("The Great Day of His Wrath", "John Martin", "John Martin - The Great Day of His Wrath - Google Art Project.jpg"),
    ("The Battle of Alexander at Issus", "Albrecht Altdorfer",
     "Albrecht Altdorfer - Schlacht bei Issus (Alte Pinakothek, München) - Google Art Project.jpg"),
    ("Laocoön and His Sons", "Vatican Museums", "Laocoon Pio-Clementino Inv1059-1064-1067.jpg"),
    ("Winged Victory of Samothrace", "The Louvre", "Nike of Samothrake Louvre Ma2369 n4.jpg"),
    ("The Dying Gaul", "Capitoline Museums", "Dying gaul.jpg"),
]
STARTUP_LINK = (Path(os.environ.get("APPDATA") or Path.home()) / "Microsoft" / "Windows" / "Start Menu" / "Programs"
                / "Startup" / f"{APP_NAME}.lnk")

# --- The quotes ---
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
    # --- WARHAMMER 40,000: motivational ---
    ('To admit defeat is to blaspheme against the Emperor.', 'Imperial Thought for the Day'),
    ('For those who seek perfection there can be no rest on this side of the grave.', 'Imperial Thought for the Day'),
    ('Success is commemorated; failure merely remembered.', 'Imperial Thought for the Day'),
    ('Even a man who has nothing can still offer his life.', 'Imperial Thought for the Day'),
    ('Only in death does duty end.', 'Imperial Thought for the Day'),
    ("Success is measured in blood; yours or your enemy's.", 'Imperial Thought for the Day'),
    ('Fear denies faith.', 'Imperial Thought for the Day'),
    ("Life is the Emperor's currency, spend it well.", 'Imperial Thought for the Day'),
    ('Faith without deeds is worthless.', 'Imperial Thought for the Day'),
    ('True happiness stems only from duty.', 'Imperial Thought for the Day'),
    ('Work earns salvation.', 'Imperial Thought for the Day'),
    ('Victory needs no explanation, defeat allows none.', 'Imperial Thought for the Day'),
    ('A moment of laxity spawns a lifetime of heresy.', 'Imperial Thought for the Day'),
    ('Knowledge is power, guard it well.', 'Imperial Thought for the Day'),
    ("Courage is the Emperor's gift: repay him with victory.", 'Imperial Thought for the Day'),
    ('A dedicated life may reach the end of infinity.', 'Imperial Thought for the Day'),
    ('A mind without purpose will wander in dark places.', 'Imperial Thought for the Day'),
    ("A warrior's faith in his commander is his best armour and his strongest weapon.",
     'Imperial Thought for the Day'),
    ('All men die, but a name can live forever.', 'Imperial Thought for the Day'),
    ('Anvils fear no hammer.', 'Imperial Thought for the Day'),
    ('Be courageous and bold, be humble before your masters, lead with valour!', 'Imperial Thought for the Day'),
    ('Bravery is stronger than Adamantium.', 'Imperial Thought for the Day'),
    ('Deeds are more eloquent than any speech.', 'Imperial Thought for the Day'),
    ('Defeat is never an option.', 'Imperial Thought for the Day'),
    ('Do not shy from the hopeless fight, for endeavour is its own reward.', 'Imperial Thought for the Day'),
    ('Do not waste your tears. I was not born to watch the world grow dim. Life is not measured in years, but by the deeds of men.',
     'Imperial Thought for the Day'),
    ('Drink deep of victory and remember the fallen.', 'Imperial Thought for the Day'),
    ('Duty prevails.', 'Imperial Thought for the Day'),
    ('Excuses are the refuge of the weak.', 'Imperial Thought for the Day'),
    ('Faith is the strongest shield.', 'Imperial Thought for the Day'),
    ('Fear not death, for the soul of the faithful man never dies.', 'Imperial Thought for the Day'),
    ('Fear runs as deep as the mind allows.', 'Imperial Thought for the Day'),
    ('For a warrior the only crime is cowardice.', 'Imperial Thought for the Day'),
    ('For he today that sheds his blood with me shall be my Battle-Brother eternal.', 'Imperial Thought for the Day'),
    ('Forward Brothers, with loyalty to victory and glory!', 'Imperial Thought for the Day'),
    ('Great courage cannot be denied.', 'Imperial Thought for the Day'),
    ('Guns and warriors are useful, but it is our indomitable will that promises the ultimate victory.',
     'Imperial Thought for the Day'),
    ('Harden your soul against decadence.', 'Imperial Thought for the Day'),
    ('Hesitation kills.', 'Imperial Thought for the Day'),
    ("If a job's worth doing it's worth dying for!", 'Imperial Thought for the Day'),
    ('If you believe you can win, you can win. Faith is necessary before any victory.',
     'Imperial Thought for the Day'),
    ('In courage we have no equals.', 'Imperial Thought for the Day'),
    ('In the blazing furnace of battle we shall forge anew the iron will of a yet stronger race.',
     'Imperial Thought for the Day'),
    ("In the darkest of moments, the Emperor's light shines brightest.", 'Imperial Thought for the Day'),
    ('Know your destination before you set out.', 'Imperial Thought for the Day'),
    ('Let my enemies cower at my advance and tremble at the sight of me.', 'Imperial Thought for the Day'),
    ('Losses are acceptable. Failure is not.', 'Imperial Thought for the Day'),
    ('Never forget you are the walls of steel and iron, between Mankind and a thousand horrors too unspeakable to name.',
     'Imperial Thought for the Day'),
    ('No barrier, no enemy will thwart my purpose.', 'Imperial Thought for the Day'),
    ('On the battlefield, valour is the lifeblood of victory.', 'Imperial Thought for the Day'),
    ('Over the faithful, fear has no dominion.', 'Imperial Thought for the Day'),
    ('Pain builds character.', 'Imperial Thought for the Day'),
    ('Pain is an illusion of the senses, despair an illusion of the mind.', 'Imperial Thought for the Day'),
    ('Perseverance and silence are the highest virtues.', 'Imperial Thought for the Day'),
    ('Power resides in the will of the righteous.', 'Imperial Thought for the Day'),
    ('Reach out to embrace the glories that will come.', 'Imperial Thought for the Day'),
    ('Scrutinize your enemies well for they will show you your flaws.', 'Imperial Thought for the Day'),
    ('Seek honour as you act, and you will know no fear.', 'Imperial Thought for the Day'),
    ('Strive harder.', 'Imperial Thought for the Day'),
    ('Survival is no birthright, but a prize wrested from an uncaring galaxy by forgotten heroes.',
     'Imperial Thought for the Day'),
    ('The burden of failure is the most terrible punishment of all.', 'Imperial Thought for the Day'),
    ('The Emperor will not judge you by your medals and diplomas, but by your scars.',
     'Imperial Thought for the Day'),
    ('The fear of death is more to be dreaded than death itself.', 'Imperial Thought for the Day'),
    ('The justice of your action is measured by the strength of your conviction.', 'Imperial Thought for the Day'),
    ('The light is within us.', 'Imperial Thought for the Day'),
    ('The moment you stop to count the cost, that is the moment you fail.', 'Imperial Thought for the Day'),
    ('The soul of a warrior is the shield of humanity.', 'Imperial Thought for the Day'),
    ('There is no fear in conviction.', 'Imperial Thought for the Day'),
    ('There is no greater glory than a lifetime of dutiful service.', 'Imperial Thought for the Day'),
    ('There is nothing to fear but failure.', 'Imperial Thought for the Day'),
    ('They achieved great things, because their courage was infinite and because they never knew their goal was impossible.',
     'Imperial Thought for the Day'),
    ('Those who act in honour cannot fail.', 'Imperial Thought for the Day'),
    ('Though my body die, I will remain.', 'Imperial Thought for the Day'),
    ('To strengthen the sword, you must first strengthen the shield.', 'Imperial Thought for the Day'),
    ('We must endure the present so that those who follow may continue our endeavours.',
     'Imperial Thought for the Day'),
    ('What fear of death have we who know there is immortality in the great and noble deeds of men?',
     'Imperial Thought for the Day'),
    ('What is the terror of death? That we die our work incomplete.', 'Imperial Thought for the Day'),
    ('While cowards ponder, the righteous act.', 'Imperial Thought for the Day'),
    ('Will is not enough. Act!', 'Imperial Thought for the Day'),
    ('Words do not win wars. Deeds do.', 'Imperial Thought for the Day'),
    ("Your armour is your soul, and your soul's dedication its armour.", 'Imperial Thought for the Day'),
    ('Your freedom must be bought in the currency of toil, tears, and blood; a price all men can pay.',
     'Imperial Thought for the Day'),
    ('Your honour is your life. Let none dispute it.', 'Imperial Thought for the Day'),
    ('Wisdom resides in knowing your duty.', 'Imperial Thought for the Day'),
    ("A coward's only reward is to live in fear another day.", 'Imperial Thought for the Day'),
    ('Luck is allied to the bold.', 'Imperial Thought for the Day'),
    ('They are my Space Marines... and they shall know no fear.', 'The Emperor of Mankind'),
    ('In those times of darkness, my noble sons will shine the brightest of all.', 'The Emperor of Mankind'),
    ('Even in death, I still serve.', 'Space Marine Dreadnought'),
    ('Courage and honour!', 'Ultramarines'),
    ('No pity! No remorse! No fear!', 'Black Templars'),
    ('Into the fires of battle, unto the anvil of war!', 'Salamanders'),
    ('The flesh is weak!', 'Iron Hands'),
    ('Iron within, iron without.', 'Iron Warriors'),
    ('Cadia stands!', 'Cadian Shock Troops'),
    ('He who stands with me shall be my brother.', 'Force Commander, Dawn of War'),
    ("We are the Space Marines! We are the Emperor's fury!", 'Indrick Boreale, Dawn of War'),
    ('I value life. That is why I fight to protect it.', "Ibram Gaunt, Gaunt's Ghosts"),
    ('Winning is everything, but the trick is to know where the winning really is.', "Delane Oktar, Gaunt's Ghosts"),
    ('To feel pain or fear or grief is to allow myself a luxury I cannot afford.', 'Gregor Eisenhorn, Xenos'),
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
    ("The impediment to action advances action. What stands in the way becomes the way.", "Marcus Aurelius"),
    ("Dwell on the beauty of life. Watch the stars, and see yourself running with them.", "Marcus Aurelius"),
    ("Loss is nothing else but change, and change is Nature's delight.", "Marcus Aurelius"),
    ("How much more grievous are the consequences of anger than the causes of it.", "Marcus Aurelius"),
    ("Never let the future disturb you. You will meet it, if you have to, with the same weapons of reason "
     "which today arm you against the present.", "Marcus Aurelius"),
    ("Do every act of your life as though it were the very last act of your life.", "Marcus Aurelius"),
    ("Look well into thyself; there is a source of strength which will always spring up if thou wilt always look.",
     "Marcus Aurelius"),
    ("If you are distressed by anything external, the pain is not due to the thing itself, but to your estimate "
     "of it; and this you have the power to revoke at any moment.", "Marcus Aurelius"),
    ("Confine yourself to the present.", "Marcus Aurelius"),
    ("Reject your sense of injury and the injury itself disappears.", "Marcus Aurelius"),
    ("The art of living is more like wrestling than dancing.", "Marcus Aurelius"),
    ("Be like the promontory against which the waves continually break, but it stands firm and tames the fury "
     "of the water around it.", "Marcus Aurelius"),
    ("Let not your mind run on what you lack as much as on what you have already.", "Marcus Aurelius"),
    ("You could leave life right now. Let that determine what you do and say and think.", "Marcus Aurelius"),
    ("Never esteem anything as of advantage to you that will make you break your word or lose your self-respect.",
     "Marcus Aurelius"),
    ("Today I escaped anxiety. Or no, I discarded it, because it was within me, in my own perceptions - not outside.",
     "Marcus Aurelius"),
    ("Choose not to be harmed - and you won't feel harmed. Don't feel harmed - and you haven't been.", "Marcus Aurelius"),
    ("Kindness is invincible, provided it is sincere.", "Marcus Aurelius"),
    ("Time is a sort of river of passing events, and strong is its current.", "Marcus Aurelius"),
    ("Everything is only for a day, both that which remembers and that which is remembered.", "Marcus Aurelius"),
    ("Whatever happens at all happens as it should.", "Marcus Aurelius"),
    # --- SENECA ---
    ("We suffer more often in imagination than in reality.", "Seneca"),
    ("Luck is what happens when preparation meets opportunity.", "Often credited to Seneca"),
    ("Sometimes even to live is an act of courage.", "Seneca"),
    ("If a man knows not to which port he sails, no wind is favorable.", "Seneca"),
    ("Difficulties strengthen the mind, as labor does the body.", "Seneca"),
    ("As is a tale, so is life: not how long it is, but how good it is, is what matters.", "Seneca"),
    ("Begin at once to live, and count each separate day as a separate life.", "Seneca"),
    ("It is not that we have a short time to live, but that we waste a lot of it.", "Seneca"),
    ("While we are postponing, life speeds by.", "Seneca"),
    ("He who is brave is free.", "Seneca"),
    ("No man was ever wise by chance.", "Seneca"),
    ("Wherever there is a human being, there is an opportunity for a kindness.", "Seneca"),
    ("True happiness is to enjoy the present, without anxious dependence upon the future.", "Seneca"),
    ("It is a rough road that leads to the heights of greatness.", "Seneca"),
    ("The greatest obstacle to living is expectancy, which hangs upon tomorrow and loses today.", "Seneca"),
    ("Associate with people who are likely to improve you.", "Seneca"),
    ("Fire tests gold, suffering tests brave men.", "Seneca"),
    ("Most powerful is he who has himself in his own power.", "Seneca"),
    ("It is not the man who has too little, but the man who craves more, that is poor.", "Seneca"),
    ("Life is long if you know how to use it.", "Seneca"),
    ("Until we have begun to go without them, we fail to realize how unnecessary many things are.", "Seneca"),
    ("Whatever can happen at any time can happen today.", "Seneca"),
    ("There is no easy way from the earth to the stars.", "Seneca"),
    ("Retire into yourself as much as you can.", "Seneca"),
    ("Nothing is a better proof of a well-ordered mind than a man's ability to stop just where he is and pass "
     "some time in his own company.", "Seneca"),
    # --- EPICTETUS ---
    ("Don't explain your philosophy. Embody it.", "Epictetus"),
    ("Difficulty shows what men are.", "Epictetus"),
    ("First say to yourself what you would be; and then do what you have to do.", "Epictetus"),
    ("It's not what happens to you, but how you react to it that matters.", "Epictetus"),
    ("Wealth consists not in having great possessions, but in having few wants.", "Epictetus"),
    ("He is a wise man who does not grieve for the things which he has not, but rejoices for those which he has.",
     "Epictetus"),
    ("No man is free who is not master of himself.", "Epictetus"),
    ("Men are disturbed not by things, but by the views which they take of them.", "Epictetus"),
    ("We have two ears and one mouth so that we can listen twice as much as we speak.", "Zeno of Citium"),
    ("Only the educated are free.", "Epictetus"),
    ("Make the best use of what is in your power, and take the rest as it happens.", "Epictetus"),
    ("If you want to improve, be content to be thought foolish and stupid.", "Epictetus"),
    ("No great thing is created suddenly.", "Epictetus"),
    ("It is impossible for a man to learn what he thinks he already knows.", "Epictetus"),
    ("Any person capable of angering you becomes your master.", "Epictetus"),
    ("Circumstances don't make the man, they only reveal him to himself.", "Epictetus"),
    ("Seek not that the things which happen should happen as you wish; but wish the things which happen to be "
     "as they are, and you will have a tranquil flow of life.", "Epictetus"),
    ("Know, first, who you are, and then adorn yourself accordingly.", "Epictetus"),
    ("First learn the meaning of what you say, and then speak.", "Epictetus"),
    ("Freedom is the only worthy goal in life. It is won by disregarding things that lie beyond our control.",
     "Epictetus"),
    # --- THE OLDER GREEKS ---
    ("Well-being is attained by little and little, and nevertheless is no little thing itself.", "Zeno of Citium"),
    ("The unexamined life is not worth living.", "Socrates"),
    ("No man ever steps in the same river twice.", "Heraclitus"),
    # --- WISDOM & MODERN STOICISM ---
    ("The obstacle is the way.", "Ryan Holiday"),
    ("Ego is the enemy.", "Ryan Holiday"),
    ("Stillness is the key.", "Ryan Holiday"),
    ("Do not pray for an easy life, pray for the strength to endure a difficult one.", "Bruce Lee"),
    ("Success is not final, failure is not fatal: it is the courage to continue that counts.",
     "Often credited to Winston Churchill"),
    ("Know thyself.", "Inscribed at the Temple of Apollo, Delphi"),
    ("The first and greatest victory is to conquer yourself.", "Plato"),
    ("Discipline is choosing between what you want now and what you want most.", "Often credited to Abraham Lincoln"),
    ("Pain is inevitable. Suffering is optional.", "Haruki Murakami"),
]


# --- Downloading, safely ---
def allowed(url):
    parts = urllib.parse.urlsplit(url)
    return parts.scheme == "https" and parts.hostname in ALLOWED_HOSTS


def fetch(url, limit=MAX_DOWNLOAD):
    """Bytes from an HTTPS address on the allowed list, never more than `limit`."""
    if not allowed(url):
        raise ValueError(f"not an allowed address: {url[:80]}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    # Https and allowed hosts only, checked above.
    with urllib.request.urlopen(req, timeout=20) as res:  # nosec B310
        if not allowed(res.geturl()):   # a redirect must stay on the list too
            raise ValueError("redirected to an address that isn't allowed")
        data = res.read(limit + 1)
    if len(data) > limit:
        raise ValueError("download too large")
    return data


def reddit_images(sub):
    """Image links from a subreddit's hot posts (its RSS feed: Reddit refuses unsigned JSON requests)."""
    feed = fetch(f"https://www.reddit.com/r/{sub}/hot.rss?limit=50", limit=5 * 1024 * 1024).decode("utf-8", "replace")
    return list(dict.fromkeys(re.findall(r"https://i\.redd\.it/[A-Za-z0-9_-]+\.(?:jpg|jpeg|png)", feed)))


def museum_image():
    """A random public-domain (CC0) painting or sculpture from the Cleveland Museum of Art."""
    # Picking art, not security.
    kind = random.choice(["Painting", "Sculpture"])  # nosec B311
    base = f"https://openaccess-api.clevelandart.org/api/artworks/?cc0=1&has_image=1&type={kind}"
    total = json.loads(fetch(base + "&limit=1", limit=1024 * 1024)).get("info", {}).get("total") or 1
    # Picking art, not security.
    skip = random.randrange(min(int(total), 5000))  # nosec B311
    data = json.loads(fetch(base + f"&limit=1&skip={skip}", limit=1024 * 1024))
    art = (data.get("data") or [{}])[0]
    url = ((art.get("images") or {}).get("print") or {}).get("url")
    if not url:
        raise ValueError("no image")
    return url, str(art.get("title") or "the Cleveland Museum of Art")


def masterpiece(avoid=(), screen_width=1920):
    """A masterpiece (not one of `avoid`, the titles shown lately): (image address, title, artist), in
    the smallest copy Wikimedia has that's still as wide as the screen."""
    choices = [m for m in MASTERPIECES if m[0] not in avoid] or MASTERPIECES
    title, artist, file = random.choice(choices)  # nosec B311
    query = urllib.parse.urlencode({"action": "query", "titles": "File:" + file, "prop": "imageinfo",
                                    "iiprop": "url", "format": "json",
                                    "iiurlwidth": next((w for w in THUMB_WIDTHS if w >= screen_width), THUMB_WIDTHS[-1])})
    data = json.loads(fetch(f"{COMMONS_API}?{query}", limit=1024 * 1024))
    page = next(iter((data.get("query") or {}).get("pages", {}).values()), {})
    info = (page.get("imageinfo") or [{}])[0]
    url = info.get("thumburl") or info.get("url")
    if not url:
        raise ValueError("not on Wikimedia Commons")
    return url, title, artist


def load_image(data, size=(1920, 1080)):
    """The picture, decoded straight at the size the screen needs (never bigger), which takes a fraction
    of the memory and time of decoding a huge one in full. Refuses broken, tiny or enormous pictures."""
    buffer = QBuffer()
    buffer.setData(QByteArray(data))
    buffer.open(QIODevice.OpenModeFlag.ReadOnly)
    reader = QImageReader(buffer)
    reader.setAutoTransform(True)
    full = reader.size()
    if not full.isValid() or full.width() < 800 or full.height() < 500:
        raise ValueError("not a usable picture")
    if full.width() * full.height() > MAX_PIXELS:
        raise ValueError("picture too large")
    # Enough pixels to cover the screen either way it's shown; only ever smaller, never bigger.
    scale = min(1.0, max(size[0] / full.width(), size[1] / full.height()))
    if scale < 1.0:
        reader.setScaledSize(QSize(max(1, round(full.width() * scale)), max(1, round(full.height() * scale))))
    image = reader.read()
    if image.isNull():
        raise ValueError("not a usable picture")
    return image


def compose(image, width, height):
    """The art in grayscale at exactly the screen's size, darkened so the quote stays readable. A picture
    near the screen's shape fills it; a tall or very wide one is shown whole, over a dark, blurred copy
    of itself, instead of being cropped."""
    gray = image.convertToFormat(QImage.Format.Format_Grayscale8).convertToFormat(QImage.Format.Format_RGB32)
    out = QImage(width, height, QImage.Format.Format_RGB32)
    out.fill(QColor(0, 0, 0))
    smooth, keep = Qt.TransformationMode.SmoothTransformation, Qt.AspectRatioMode
    painter = QPainter(out)
    painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

    def centred(img):
        painter.drawImage((width - img.width()) // 2, (height - img.height()) // 2, img)

    shape, screen = gray.width() / gray.height(), width / height
    if abs(shape - screen) / screen <= 0.2:
        centred(gray.scaled(width, height, keep.KeepAspectRatioByExpanding, smooth))
    else:
        tiny = gray.scaled(max(1, width // 32), max(1, height // 32), keep.KeepAspectRatioByExpanding, smooth)
        centred(tiny.scaled(width, height, keep.KeepAspectRatioByExpanding, smooth))   # blurred
        painter.fillRect(out.rect(), QColor(0, 0, 0, 150))
        centred(gray.scaled(int(width * 0.96), int(height * 0.96), keep.KeepAspectRatio, smooth))
    painter.end()
    # Darken: at least WALLPAPER_DIM, and more for a bright picture, so the white quote always reads on it.
    sample = out.scaled(32, 18, Qt.AspectRatioMode.IgnoreAspectRatio, smooth)
    mean = sum(sample.pixelColor(x, y).red() for x in range(32) for y in range(18)) / (32 * 18)
    target = 80   # the most the finished wallpaper's average brightness (0-255) should be
    dim = WALLPAPER_DIM if mean <= target else max(WALLPAPER_DIM, round(255 * (1 - target / mean)))
    painter = QPainter(out)
    painter.fillRect(out.rect(), QColor(0, 0, 0, min(dim, 200)))
    painter.end()
    return out


def save_wallpaper(image, path, size):
    if not compose(image, *size).save(str(path), "JPG", 92):
        raise OSError("couldn't save the wallpaper")


# --- Start with Windows (a shortcut in the Startup folder) ---
def pythonw():
    exe = Path(sys.executable)
    windowless = exe.with_name("pythonw.exe")
    return windowless if windowless.exists() else exe


def set_start_with_windows(on):
    if not on:
        STARTUP_LINK.unlink(missing_ok=True)
        return
    # The paths go in through environment variables, never pasted into the command, so no folder
    # name can ever be run as a command.
    env = dict(os.environ, SD_LINK=str(STARTUP_LINK), SD_EXE=str(pythonw()),
               SD_SCRIPT=str(Path(__file__).resolve()), SD_DIR=str(Path(__file__).resolve().parent))
    script = ("$s = (New-Object -ComObject WScript.Shell).CreateShortcut($env:SD_LINK); "
              "$s.TargetPath = $env:SD_EXE; $s.Arguments = '\"' + $env:SD_SCRIPT + '\"'; "
              "$s.WorkingDirectory = $env:SD_DIR; $s.Description = 'Stoic Desktop'; $s.Save()")
    # The full path, so nothing named powershell.exe elsewhere on the PATH can stand in for it.
    powershell = Path(os.environ.get("SystemRoot") or r"C:\Windows") / "System32" / "WindowsPowerShell" / "v1.0" / "powershell.exe"
    # Fixed program and arguments; the paths arrive as environment variables, never as command text.
    subprocess.run([str(powershell), "-NoProfile", "-NonInteractive", "-Command", script], env=env, check=True,  # nosec B603
                   capture_output=True, timeout=30, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


class Notification(QWidget):
    def __init__(self, message):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        layout = QVBoxLayout()
        self.label = QLabel(message)
        self.label.setStyleSheet("background-color: rgba(20,20,20,230); color: white; border: 1px solid #555; "
                                 "border-radius: 8px; padding: 12px; font-family: 'Segoe UI';")
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.setFixedWidth(340)
        self.update_status(message)
        self.show()

    def update_status(self, text, delay=0):
        self.label.setText(text)
        self.adjustSize()
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 20, screen.top() + 40)
        if delay > 0:
            QTimer.singleShot(delay, self.close)


class WallpaperWorker(QThread):
    finished = pyqtSignal(str)
    status_signal = pyqtSignal(str, int)

    def __init__(self):
        super().__init__()
        self.toggle = True
        self.size = (1920, 1080)   # the screen, in real pixels: set before each run

    def from_reddit(self, target):
        sub = random.choice(SUBREDDITS)  # nosec B311
        self.status_signal.emit(f"Scanning r/{sub}...", 0)
        images = reddit_images(sub)
        random.shuffle(images)
        for url in images[:4]:
            try:
                save_wallpaper(load_image(fetch(url), self.size), target, self.size)
                return f"🔥 New art from r/{sub}!"
            # That picture failed: try the next one.
            except Exception:  # nosec B112
                continue
        raise ValueError("no usable picture")

    def from_masterpieces(self, target):
        self.status_signal.emit("Choosing a masterpiece...", 0)
        settings = QSettings("StoicDesktop", "StoicDesktop")
        recent = settings.value("recent_art") or []
        recent = [recent] if isinstance(recent, str) else list(recent)
        url, title, artist = masterpiece(avoid=recent, screen_width=self.size[0])
        save_wallpaper(load_image(fetch(url), self.size), target, self.size)
        settings.setValue("recent_art", (recent + [title])[-10:])   # not again for the next 10
        return f"🏛️ {title}, {artist}"

    def from_museum(self, target):
        url, title = museum_image()
        save_wallpaper(load_image(fetch(url), self.size), target, self.size)
        return f"🏛️ New art: {title[:60]}"

    def from_photo(self, target):
        save_wallpaper(load_image(fetch("https://picsum.photos/1920/1080?grayscale"), self.size), target, self.size)
        return "🛡️ Fallback engaged."

    def run(self):
        target = WP_A if self.toggle else WP_B
        self.toggle = not self.toggle
        first = [self.from_masterpieces, self.from_reddit]
        random.shuffle(first)
        for source in first + [self.from_museum, self.from_photo]:
            try:
                message = source(target)
            # That source failed: the next one.
            except Exception:  # nosec B112
                continue
            self.status_signal.emit(message, 5000)
            self.finished.emit(str(target))
            return
        self.status_signal.emit("❌ Update failed. Trying again later.", 4000)


class StoicDesktop(QWidget):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("StoicDesktop", "StoicDesktop")
        self.deck = []      # every quote once, in random order, before any repeats
        self.notif = None
        self.drag_from = None

        # Frameless, see-through, kept down at desktop level and off the taskbar.
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool | Qt.WindowType.WindowStaysOnBottomHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.resize(900, 350)
        self.place()

        layout = QVBoxLayout()
        self.label = QLabel("Summoning Stoicism...")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setWordWrap(True)
        self.label.setFont(QFont("Arial", 28, QFont.Weight.Bold, True))
        self.label.setStyleSheet("color: white;")
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(15)
        shadow.setOffset(2, 2)
        shadow.setColor(QColor(0, 0, 0, 240))
        self.label.setGraphicsEffect(shadow)
        layout.addWidget(self.label)
        self.setLayout(layout)

        self.update_quote()
        self.q_timer = QTimer(self)
        self.q_timer.timeout.connect(self.update_quote)
        self.q_timer.start(QUOTE_MINUTES * 60_000)

        self.worker = WallpaperWorker()
        self.worker.finished.connect(self.apply_wp)
        self.worker.status_signal.connect(self.show_notif)
        self.wp_timer = QTimer(self)
        self.wp_timer.timeout.connect(self.wallpaper_if_due)
        self.wp_timer.start(3_600_000)
        QTimer.singleShot(3000, self.wallpaper_if_due)
        QTimer.singleShot(15000, release_memory)   # start-up's one-off memory, handed back

    # -- position: wherever it was dragged last time, if that's still on a screen --
    def place(self):
        saved = self.settings.value("pos")
        screens = [s.availableGeometry() for s in QApplication.screens()]
        if isinstance(saved, QPoint) and any(g.contains(saved) for g in screens):
            self.move(saved)
        else:
            g = QApplication.primaryScreen().availableGeometry()
            self.move(g.center().x() - self.width() // 2, g.center().y() - self.height() // 2)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_from = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self.drag_from is not None and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_from)

    def mouseReleaseEvent(self, event):
        if self.drag_from is not None:
            self.drag_from = None
            self.settings.setValue("pos", self.pos())

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("background-color: #222; color: white; border: 1px solid #555;")
        refresh_action = QAction("🔄 Force Refresh Wallpaper", self)
        refresh_action.triggered.connect(self.refresh_wallpaper)
        next_quote_action = QAction("📜 Next Quote", self)
        next_quote_action.triggered.connect(self.update_quote)
        startup_action = QAction("🚀 Start with Windows", self)
        startup_action.setCheckable(True)
        startup_action.setChecked(STARTUP_LINK.exists())
        startup_action.toggled.connect(self.toggle_startup)
        exit_action = QAction("❌ Exit App", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        menu.addAction(refresh_action)
        menu.addAction(next_quote_action)
        menu.addAction(startup_action)
        menu.addSeparator()
        menu.addAction(exit_action)
        menu.exec(event.globalPos())

    def toggle_startup(self, on):
        try:
            set_start_with_windows(on)
            self.show_notif("Starts with Windows ✓" if on else "Won't start with Windows", 3000)
        except Exception:
            self.show_notif("❌ Couldn't change that setting.", 4000)

    def show_notif(self, msg, delay):
        if not self.notif:
            self.notif = Notification(msg)
        if delay > 0:
            self.notif.update_status(msg, delay)
            self.notif = None
        else:
            self.notif.update_status(msg)

    def update_quote(self):
        if not self.deck:
            # Shuffling quotes, not security.
            self.deck = random.sample(STOIC_QUOTES, len(STOIC_QUOTES))  # nosec B311
            if len(self.deck) > 1 and self.deck[-1] == getattr(self, "shown", None):
                self.deck[0], self.deck[-1] = self.deck[-1], self.deck[0]   # never the same quote twice in a row
        self.shown = self.deck.pop()
        text, author = self.shown
        self.label.setText(f'"{text}"\n\n— {author}')

    def wallpaper_if_due(self):
        try:
            last = float(self.settings.value("last_wallpaper", 0) or 0)
        except (TypeError, ValueError):
            last = 0.0
        if time.time() - last >= WALLPAPER_HOURS * 3600:
            self.refresh_wallpaper()

    def refresh_wallpaper(self):
        if not self.worker.isRunning():
            screen = QApplication.primaryScreen()
            size, ratio = screen.size(), screen.devicePixelRatio()
            self.worker.size = (max(800, round(size.width() * ratio)), max(600, round(size.height() * ratio)))
            self.worker.start()

    def apply_wp(self, path):
        ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)   # SPI_SETDESKWALLPAPER, kept after sign-out
        self.settings.setValue("last_wallpaper", time.time())
        QTimer.singleShot(2000, release_memory)


def release_memory():
    """Give back the memory a wallpaper change borrowed, so the app idles small."""
    gc.collect()
    try:
        kernel32, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p   # a full-size handle, or the call misses
        psapi.EmptyWorkingSet.argtypes = [ctypes.c_void_p]
        psapi.EmptyWorkingSet(kernel32.GetCurrentProcess())
    except (AttributeError, OSError):
        pass


def already_running():
    """One widget at a time, however many times it's started."""
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW(None, False, "Local\\StoicDesktopSingleInstance")   # held until the app exits
    return ctypes.get_last_error() == 183   # ERROR_ALREADY_EXISTS


if __name__ == "__main__":
    if already_running():
        sys.exit(0)
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setQuitOnLastWindowClosed(False)   # a notification closing must not close the app
    ex = StoicDesktop()
    ex.show()
    sys.exit(app.exec())
