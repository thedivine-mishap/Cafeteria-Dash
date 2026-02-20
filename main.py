import pygame
import numpy as np
import sys
import json
import os

from settings import WIDTH, HEIGHT, FPS, ARRIVAL_RATE, INGREDIENT_PRICES, MENU_PRICES
from entities.player import Player
from entities.customer import Customer
from systems.inventory import Inventory
from ui.hud import HUD
from systems.kitchen import Kitchen
from ui.button import Button

# --- INITIALIZATION ---
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Restaurant Game")
clock = pygame.time.Clock()

# UI Font
font = pygame.font.SysFont("Arial", 16, bold=True)

# --- SPRITES & GROUPS ---
player = Player((WIDTH // 2, HEIGHT // 2))

# Groups
all_sprites = pygame.sprite.Group(player)
customers = pygame.sprite.Group()

# --- SYSTEMS ---
game_inventory = Inventory()
game_hud = HUD(game_inventory)
game_kitchen = Kitchen(game_inventory)

# --- GAME STATE ---
GAME_STATE = "START"  # START, PLAYING, HELP, HIGHSCORES, PAUSED, ENTER_NAME, GAME_OVER
pending_message = None
message_timer = 0.0

# Highscore file
HIGHSCORE_FILE = os.path.join(os.path.dirname(__file__), "highscores.json")

def load_highscores():
    if not os.path.exists(HIGHSCORE_FILE):
        return []
    try:
        with open(HIGHSCORE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_highscores(hs):
    try:
        with open(HIGHSCORE_FILE, "w", encoding="utf-8") as f:
            json.dump(hs, f, indent=2)
    except Exception as e:
        print("Failed to save highscores:", e)

highscores = load_highscores()

def is_highscore(score):
    hs = sorted(highscores, key=lambda x: x["score"], reverse=True)
    if len(hs) < 5:
        return True
    return score > hs[-1]["score"]

pending_score = None
pending_name = ""

# --- HELPER FUNCTIONS FOR BUTTONS ---
def buy_rice(): game_inventory.buy("Rice", INGREDIENT_PRICES["Rice"])
def buy_egg():  game_inventory.buy("Egg", INGREDIENT_PRICES["Egg"])
def buy_veg():  game_inventory.buy("Veggie", INGREDIENT_PRICES["Veggie"])
def buy_chk():  game_inventory.buy("Chicken", INGREDIENT_PRICES["Chicken"])

def cook_rice():
    ok, info = game_kitchen.start_cooking("Fried Rice")
    if not ok:
        global pending_message, message_timer
        if info == "full":
            pending_message = "Kitchen is full!"
        else:
            # info is missing dict
            parts = [f"{k} x{v}" for k, v in info.items()]
            pending_message = "Missing: " + ", ".join(parts)
        message_timer = 3.0

def cook_chk():
    ok, info = game_kitchen.start_cooking("Chicken Rice")
    if not ok:
        global pending_message, message_timer
        if info == "full":
            pending_message = "Kitchen is full!"
        else:
            parts = [f"{k} x{v}" for k, v in info.items()]
            pending_message = "Missing: " + ", ".join(parts)
        message_timer = 3.0

def cook_ome():
    ok, info = game_kitchen.start_cooking("Omelet")
    if not ok:
        global pending_message, message_timer
        if info == "full":
            pending_message = "Kitchen is full!"
        else:
            parts = [f"{k} x{v}" for k, v in info.items()]
            pending_message = "Missing: " + ", ".join(parts)
        message_timer = 3.0

# --- CREATE BUTTON OBJECTS ---
buttons = []

# Shop Buttons (Left side)
buttons.append(Button(20, 400, 80, 40, "Buy Rice", (100, 100, 200), (150, 150, 250), buy_rice))
buttons.append(Button(110, 400, 80, 40, "Buy Egg", (100, 100, 200), (150, 150, 250), buy_egg))
buttons.append(Button(200, 400, 80, 40, "Buy Veg", (100, 100, 200), (150, 150, 250), buy_veg))
buttons.append(Button(290, 400, 80, 40, "Buy Chk", (100, 100, 200), (150, 150, 250), buy_chk))

# Cooking Buttons (Right side)
buttons.append(Button(400, 400, 100, 40, "Cook Rice", (200, 100, 100), (250, 150, 150), cook_rice))
buttons.append(Button(510, 400, 100, 40, "Cook Chk", (200, 100, 100), (250, 150, 150), cook_chk))
buttons.append(Button(620, 400, 100, 40, "Cook Omelet", (200, 100, 100), (250, 150, 150), cook_ome))

# Pause Button (top-right)
pause_button = Button(WIDTH-110, 10, 100, 40, "Pause", (150,50,50), (200,80,80), lambda: set_game_state('PAUSED'))

# --- START MENU BUTTONS ---
start_buttons = []
def start_play():
    reset_game()
    set_game_state('PLAYING')

def set_game_state(s):
    global GAME_STATE
    GAME_STATE = s

def start_help():
    set_game_state('HELP')

def start_highscores():
    set_game_state('HIGHSCORES')

def start_exit():
    pygame.quit()
    sys.exit()

start_buttons.append(Button(WIDTH//2 - 100, 200, 200, 50, "Play", (50,150,50), (80,200,80), start_play))
start_buttons.append(Button(WIDTH//2 - 100, 270, 200, 50, "Help", (50,50,150), (80,80,200), start_help))
start_buttons.append(Button(WIDTH//2 - 100, 340, 200, 50, "High Score", (150,100,50), (200,140,80), start_highscores))
start_buttons.append(Button(WIDTH//2 - 100, 410, 200, 50, "Exit", (150,50,50), (200,80,80), start_exit))