# stoic-desktop
A lightweight, transparent Windows desktop widget that cycles Stoic quotes and automatically updates your wallpaper with grayscale classical art from Reddit.


Stoic Desktop Quote and Wallpaper App

I built this script to put a clean, transparent text widget on my desktop that cycles through quotes and automatically updates my background with classical art every day. It scrapes high-res images directly from art subreddits, converts them to a dark grayscale so they aren't distracting, and sets them as your Windows wallpaper.

It runs completely in the background without needing any paid API keys or subscriptions.

Features

Cycles through over 200 quotes. Mostly Stoic philosophers like Marcus Aurelius and Seneca, but also includes voice lines from Aatrox and Pantheon from League of Legends.

The quote updates every minute.

The wallpaper updates every 24 hours. It pulls randomly from subreddits like r/ClassicalArt, r/Sculpture, and r/museum.

Built-in fallback system that grabs a moody landscape image if Reddit happens to be down.

Right-click menu on the quote text lets you force refresh the wallpaper, skip to the next quote, or cleanly exit the app.

A small popup notification in the top right corner lets you know when it's searching for and applying a new image, then disappears.

Self-cleaning. It only uses two image files in your Windows Temp folder and overwrites them, so it won't clutter your hard drive.

Requirements
You just need Python installed, along with PyQt6 for the UI elements.

You can install the dependency via command prompt:
pip install PyQt6

How to run on startup (Windows)
To have this run silently in the background every time you turn on your PC, you can use a simple batch script.

Press Win + R, type shell:startup, and hit Enter.

Create a new text file in that folder and name it dailyquotes.cmd

Open it in Notepad and paste the following code. Just make sure the folder path and python filename match wherever you actually saved the script.

@echo off
cd /d "C:\Users\Mafia\OneDrive\Desktop"
start "" pyw motivational_quotes.py
exit

Using pyw instead of python ensures the app runs completely invisibly without leaving a command prompt window open on your taskbar.

Usage
Once it's running, the text will appear on your screen. You can right-click the text at any time to open a small menu where you can force a new wallpaper download, skip the current quote, or close the program completely.
