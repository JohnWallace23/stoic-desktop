# Stoic Desktop

A lightweight, transparent Windows desktop widget that cycles Stoic quotes and gives you a fresh,
dark grayscale wallpaper of epic art every day.

I built this to put a clean quote on my desktop and swap my background for something worth looking
at each day: masterpieces about courage and struggle, and epic fantasy art of warriors and battles.
It turns them dark grayscale so they aren't distracting, and sets them as your Windows wallpaper.
No accounts, no API keys, no subscriptions.

## Install (about 2 minutes)

1. On this page, click the green **Code** button, then **Download ZIP**.
2. Open your **Downloads** folder, right-click **stoic-desktop-main.zip**, and choose **Extract All…**, then **Extract**.
3. In the folder that opens, double-click **install.cmd**.
   - If Windows says "Windows protected your PC", click **More info**, then **Run anyway**.
     That message appears for any script downloaded from the internet.
4. A window shows each step. When it says **Done!**, press any key to close it.

The quote appears on your desktop, and a new wallpaper follows a few seconds later. From then on, it
starts by itself whenever you sign in to Windows.

You don't need to install anything first. If Python isn't on your PC, the installer installs it for
you (Windows 10 or 11). Everything goes into your own user folder, so it needs no administrator rights.

## Using it

- **Move the quote:** drag it with the left mouse button. It stays where you put it.
- **Right-click the quote** for the menu:
  - 🔄 **Force Refresh Wallpaper**: a new picture now.
  - 📜 **Next Quote**: skip to another quote.
  - 🚀 **Start with Windows**: tick or untick whether it starts when you sign in.
  - ❌ **Exit App**: closes it. To open it again: Start menu → **Stoic Desktop**.

## Features

- **210 quotes:** Stoic philosophers like Marcus Aurelius, Seneca and Epictetus; 100 motivational
  lines from Warhammer 40,000 (Imperial Thoughts for the Day on courage, duty and endurance, Space
  Marine battle cries, Gaunt's Ghosts and more); and voice lines from Aatrox and Pantheon from League of Legends. You see every quote once
  before any repeat, and never the same one twice in a row.
- **The quote changes every minute.**
- **The wallpaper changes every 24 hours,** half the time from each of these:
  - **Masterpieces:** 22 famous public-domain works about courage, struggle and endurance, in full
    resolution from Wikimedia Commons. *Wanderer above the Sea of Fog*, *Leonidas at Thermopylae*,
    *Washington Crossing the Delaware*, *The Death of Socrates*, *The Ninth Wave*, *Winged Victory of
    Samothrace* and more. It won't repeat one within ten days.
  - **Epic art from Reddit:** r/ImaginaryWarriors, r/ImaginaryBattlefields, r/ImaginaryKnights and
    r/ImaginaryCastles, plus r/ClassicalArt and r/Sculpture.
  - If one is down, it uses the other, then the Cleveland Museum of Art's open collection, then a
    moody landscape photo. Restarting your PC doesn't skip or repeat a day.
- **Made to fit your screen:** wide art fills it; a tall painting is shown whole over a dark, blurred
  copy of itself, instead of being cropped. Bright art is darkened more, so the quote always reads.
- **A small notice** in the top-right corner while it finds and applies a new picture, then it disappears.
- **Light on your PC:** it uses no CPU between changes and about 30 MB of memory. A wallpaper change
  takes a fraction of a second: pictures are decoded straight at your screen's size, it downloads the
  smallest copy that fills your screen, and it hands the memory back afterwards.
- **Tidy:** it uses only two image files in your Windows Temp folder and reuses them.
- **Only one copy runs**, however many times you open it.

## Updating

Download the ZIP again, extract it, and double-click **install.cmd**. It replaces the old version and
keeps your settings.

## Uninstalling

Start menu → **Stoic Desktop** → **Uninstall Stoic Desktop**. Or double-click **uninstall.cmd** in the
downloaded folder.

Your current wallpaper stays as it is. To change it: Settings → Personalization → Background.

## Changing the settings

Open `%LOCALAPPDATA%\StoicDesktop\stoic_desktop.py` in Notepad. Near the top, change:

- `QUOTE_MINUTES`: how often the quote changes.
- `WALLPAPER_HOURS`: how often the wallpaper changes.
- `WALLPAPER_DIM`: how much darker the art is made (0 = not at all, 255 = black).
- `SUBREDDITS`: which subreddits the art comes from.
- `MASTERPIECES`: the paintings and sculpture it picks from (any image on Wikimedia Commons works:
  add its title, artist and file name).

Save, then right-click the quote → **Exit App**, and start it again from the Start menu.

To add your own quotes, add lines like these to the `STOIC_QUOTES` list in the same file:

```python
    ("Your quote here.", "Who said it"),
```

## Safety

- The only package it installs is PyQt6, pinned to exact versions with no known vulnerabilities
  (checked with `pip-audit`). The installer checks each download against its official fingerprint
  and refuses anything that doesn't match.
- It installs into its own private Python environment, so it can't change or break other Python
  programs on your PC.
- It downloads only over HTTPS, and only from Reddit, Wikimedia Commons, the Cleveland Museum of Art
  and Picsum. It refuses any other address, any redirect to one, and any download over 40 MB.
  Pictures are only read as images; nothing downloaded is ever run.
- It collects nothing about you and sends nothing anywhere.

## Running it by hand (for developers)

```
python -m pip install -r requirements.txt
pythonw stoic_desktop.py
```

Requires Windows and Python 3.10 or newer.

## License

MIT. See [LICENSE](LICENSE).
