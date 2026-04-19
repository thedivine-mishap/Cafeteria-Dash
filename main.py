import pygame
import numpy as np
import sys
import json
import os

from settings import WIDTH, HEIGHT, FPS, ARRIVAL_RATE, INGREDIENT_PRICES, MENU_PRICES, SimConfig, BG_COLOR, WHITE, BLACK, GREEN_ACCENT, RED_ACCENT, TERRACOTTA, GRAY
from entities.player import Player
from entities.customer import Customer
from systems.inventory import Inventory
from systems.game_stats import GameStats
from ui.hud import HUD
from systems.kitchen import Kitchen
from ui.button import Button
from ui.strategy_screen import StrategyScreen
from simulation.simulator import CafeteriaSimulator
from simulation.experiment import build_configs, PARAM_GRID, RUNS_PER_CONFIG
from simulation.analysis import add_efficiency_scores, print_summary_table, plot_results
import pandas as pd
from systems.sound_manager import SoundManager, sound_manager as global_sm
import systems.sound_manager

# bug fixed

# --- INITIALIZATION ---
pygame.mixer.pre_init(44100, -16, 2, 512) # Pre-init for better latency
pygame.init()
pygame.mixer.init()

# Start window in fullscreen and don't allow resizable/half-screen modes
info = pygame.display.Info()
# Use a borderless window at desktop resolution (borderless windowed)
screen = pygame.display.set_mode((info.current_w, info.current_h), pygame.NOFRAME)
pygame.display.set_caption("Cafeteria Dash")
clock = pygame.time.Clock()

# --- AUDIO SETUP ---
assets_dir = os.path.join(os.path.dirname(__file__), "assets")
systems.sound_manager.sound_manager = SoundManager(assets_dir)
sm = systems.sound_manager.sound_manager

# Attempt to load placeholder sounds (will fail silently if files don't exist yet)
sm.load_sound("click", "click.mp3")
sm.load_sound("buy", "buy.mp3")
sm.load_sound("cook", "cook.mp3")
sm.load_sound("serve", "serve.mp3")
sm.load_sound("error", "error.mp3")
sm.load_sound("gameover", "gameover.mp3")

# Start background music
sm.play_music("bgm.mp3", volume=0.3)

# Current window size (fullscreen)
cur_width, cur_height = screen.get_size()
is_fullscreen = True

# UI Font
font = pygame.font.SysFont("trebuchetms", 16, bold=True)

# Background image for menus (used when not in SIMULATION or PLAYING)
bg_image = None
bg_path = os.path.join(assets_dir, "images", "background.png")
try:
    if os.path.exists(bg_path):
        bg_image = pygame.image.load(bg_path).convert()
        # scale to current fullscreen size
        try:
            bg_scaled = pygame.transform.smoothscale(bg_image, (cur_width, cur_height))
        except Exception:
            bg_scaled = bg_image
    else:
        bg_image = None
        bg_scaled = None
except Exception:
    bg_image = None
    bg_scaled = None
# Floor image for gameplay/simulation background
floor_image = None
floor_path = os.path.join(assets_dir, "images", "floor.png")
try:
    if os.path.exists(floor_path):
        floor_image = pygame.image.load(floor_path).convert()
        try:
            floor_scaled = pygame.transform.smoothscale(floor_image, (cur_width, cur_height))
        except Exception:
            floor_scaled = floor_image
    else:
        floor_image = None
        floor_scaled = None
except Exception:
    floor_image = None
    floor_scaled = None

# --- SPRITES & GROUPS ---
player = None
# Groups
all_sprites = pygame.sprite.Group()
customers = pygame.sprite.Group()

# --- SYSTEMS ---
game_inventory = Inventory()
game_stats = GameStats()
game_hud = HUD(game_inventory)
game_kitchen = Kitchen(game_inventory, stats=game_stats)
strategy_screen = StrategyScreen(WIDTH, HEIGHT)

# --- GAME TIMER ---
GAME_TIMER_MAX = 300.0  # 5 minutes per session (0 = no timer)
game_elapsed = 0.0

# --- GAME STATE ---
GAME_STATE = "START"  # START, PLAYING, HELP, HIGHSCORES, PAUSED, ENTER_NAME, GAME_OVER, STRATEGY_SUMMARY
STOVE_COST = 50
pending_message = None
message_timer = 0.0
active_simulator = None
active_experiment = None

# --- Simulation settings (user-configurable) ---
sim_num_queues = 1
sim_num_stoves = 4
sim_speed_multiplier = 8
sim_runs_per_config = 2
sim_compare = False
sim_initial_inventory = {"Rice": 5, "Egg": 5, "Veggie": 5, "Chicken": 5}
sim_restock_threshold = 3
sim_setting_rows = ["Queues", "Stoves", "Speed", "Runs", "Rice", "Egg", "Veggie", "Chicken", "Restock"]

sim_setting_buttons = []

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
# Caret / text input UI
CARET_BLINK_INTERVAL = 0.5
caret_timer = CARET_BLINK_INTERVAL
caret_visible = True

# --- HELPER FUNCTIONS FOR BUTTONS ---
def _buy_helper(item):
    cost = INGREDIENT_PRICES[item]
    if game_inventory.buy(item, cost):
        game_stats.record_ingredient_bought(item, cost)
        systems.sound_manager.sound_manager.play_sound("buy")
    else:
        systems.sound_manager.sound_manager.play_sound("error")

def buy_rice(): _buy_helper("Rice")
def buy_egg():  _buy_helper("Egg")
def buy_veg():  _buy_helper("Veggie")
def buy_chk():  _buy_helper("Chicken")

def _cook_helper(dish):
    ok, info = game_kitchen.start_cooking(dish)
    if ok:
        game_stats.record_cook_started(dish)
        systems.sound_manager.sound_manager.play_sound("cook")
    else:
        global pending_message, message_timer
        systems.sound_manager.sound_manager.play_sound("error")
        if info == "full":
            pending_message = "Kitchen is full!"
        else:
            parts = [f"{k} x{v}" for k, v in info.items()]
            pending_message = "Missing: " + ", ".join(parts)
        message_timer = 3.0

def cook_rice(): _cook_helper("Fried Rice")

def cook_chk(): _cook_helper("Chicken Rice")
def cook_ome(): _cook_helper("Omelet")

def buy_stove():
    global pending_message, message_timer
    if game_kitchen.buy_stove(STOVE_COST):
        game_stats.record_stove_bought(STOVE_COST)
        systems.sound_manager.sound_manager.play_sound("buy")
        pending_message = f"New stove! Total: {game_kitchen.max_slots}"
    else:
        systems.sound_manager.sound_manager.play_sound("error")
        pending_message = f"Need ${STOVE_COST} for a stove!"
    message_timer = 3.0

# --- CREATE BUTTON OBJECTS ---
buttons = []

# Shop Buttons (Left side) - Hovering over the bins
buttons.append(Button(0, 0, 50, 30, "+$2", GREEN_ACCENT, (160, 180, 140), buy_rice))
buttons.append(Button(0, 0, 50, 30, "+$1", GREEN_ACCENT, (160, 180, 140), buy_egg))
buttons.append(Button(0, 0, 50, 30, "+$2", GREEN_ACCENT, (160, 180, 140), buy_veg))
buttons.append(Button(0, 0, 50, 30, "+$5", GREEN_ACCENT, (160, 180, 140), buy_chk))

# Cooking Buttons (Right side) - 2x2 grid
buttons.append(Button(0, 0, 120, 40, "Cook Rice", TERRACOTTA, RED_ACCENT, cook_rice))
buttons.append(Button(0, 0, 120, 40, "Cook Chk", TERRACOTTA, RED_ACCENT, cook_chk))
buttons.append(Button(0, 0, 120, 40, "Cook Omelet", TERRACOTTA, RED_ACCENT, cook_ome))
buttons.append(Button(0, 0, 120, 40, f"Buy Stove ${STOVE_COST}", GRAY, (230, 215, 200), buy_stove))

# Pause Button (top-right)
pause_button = Button(WIDTH-110, 10, 100, 40, "Pause", RED_ACCENT, (245, 180, 165), lambda: set_game_state('PAUSED'))

# --- START MENU BUTTONS ---
start_buttons = []
def start_play():
    reset_game()
    set_game_state('PLAYING')

def start_simulation():
    """Open simulation settings screen where user customizes parameters."""
    global active_experiment
    # prepare a blank experiment state; actual configs created when user starts
    active_experiment = None
    set_game_state('SIMULATION_SETTINGS')

def set_game_state(s):
    global GAME_STATE
    # Enable/disable SDL text input when entering/exiting name entry
    try:
        if s == 'ENTER_NAME':
            pygame.key.start_text_input()
        elif GAME_STATE == 'ENTER_NAME' and s != 'ENTER_NAME':
            pygame.key.stop_text_input()
    except Exception:
        pass
    GAME_STATE = s
    # Support automated test mode: auto-save name if provided in env
    try:
        if s == 'ENTER_NAME':
            auto_name = os.environ.get('AUTOSAVE_NAME')
            if auto_name:
                # mimic the save flow used in ENTER_NAME
                nm = auto_name[:10] if auto_name else "Player"
                highscores.append({"name": nm, "score": pending_score})
                hs_sorted = sorted(highscores, key=lambda x: x["score"], reverse=True)[:5]
                save_highscores(hs_sorted)
                highscores[:] = hs_sorted
                # move to game over
                try:
                    globals()['game_over'] = True
                except Exception:
                    pass
                GAME_STATE = 'GAME_OVER'
    except Exception:
        pass

def start_help():
    set_game_state('HELP')

def start_highscores():
    set_game_state('HIGHSCORES')

def start_exit():
    pygame.quit()
    sys.exit()


# --- Simulation Settings actions ---
def inc_num_queues():
    global sim_num_queues
    sim_num_queues = min(8, sim_num_queues + 1)

def dec_num_queues():
    global sim_num_queues
    sim_num_queues = max(1, sim_num_queues - 1)

def inc_num_stoves():
    global sim_num_stoves
    sim_num_stoves = min(12, sim_num_stoves + 1)

def dec_num_stoves():
    global sim_num_stoves
    sim_num_stoves = max(1, sim_num_stoves - 1)

def inc_speed():
    global sim_speed_multiplier
    sim_speed_multiplier = min(50, sim_speed_multiplier + 1)

def dec_speed():
    global sim_speed_multiplier
    sim_speed_multiplier = max(1, sim_speed_multiplier - 1)

def inc_runs():
    global sim_runs_per_config
    sim_runs_per_config = min(20, sim_runs_per_config + 1)

def dec_runs():
    global sim_runs_per_config
    sim_runs_per_config = max(1, sim_runs_per_config - 1)

def inc_rice():
    sim_initial_inventory["Rice"] = min(100, sim_initial_inventory["Rice"] + 1)

def dec_rice():
    sim_initial_inventory["Rice"] = max(0, sim_initial_inventory["Rice"] - 1)

def inc_egg():
    sim_initial_inventory["Egg"] = min(100, sim_initial_inventory["Egg"] + 1)

def dec_egg():
    sim_initial_inventory["Egg"] = max(0, sim_initial_inventory["Egg"] - 1)

def inc_veg():
    sim_initial_inventory["Veggie"] = min(100, sim_initial_inventory["Veggie"] + 1)

def dec_veg():
    sim_initial_inventory["Veggie"] = max(0, sim_initial_inventory["Veggie"] - 1)

def inc_chk():
    sim_initial_inventory["Chicken"] = min(100, sim_initial_inventory["Chicken"] + 1)

def dec_chk():
    sim_initial_inventory["Chicken"] = max(0, sim_initial_inventory["Chicken"] - 1)

def inc_restock():
    global sim_restock_threshold
    sim_restock_threshold = min(20, sim_restock_threshold + 1)

def dec_restock():
    global sim_restock_threshold
    sim_restock_threshold = max(0, sim_restock_threshold - 1)

def start_experiment_with_params():
    """Create experiment configs from user params and begin orchestration."""
    global active_experiment, active_simulator
    try:
        # Build grid depending on compare flag
        if sim_compare:
            nq_list = list(range(1, sim_num_queues + 1))
            ns_list = list(range(1, sim_num_stoves + 1))
        else:
            nq_list = [sim_num_queues]
            ns_list = [sim_num_stoves]

        grid = {
            "num_queues": nq_list,
            "num_stoves": ns_list,
            "arrival_rate": PARAM_GRID.get("arrival_rate", [ARRIVAL_RATE]),
            "initial_ingredients": PARAM_GRID.get("initial_ingredients", [{"Rice":5,"Egg":5,"Veggie":5,"Chicken":5}]),
        }
        configs = build_configs(grid)
        total_configs = len(configs)
        total_runs = total_configs * sim_runs_per_config

        active_experiment = {
            "configs": configs,
            "ci": 0,
            "ri": 0,
            "rows": [],
            "total_configs": total_configs,
            "total_runs": total_runs,
            "runs_per_config": sim_runs_per_config,
            "speed_multiplier": sim_speed_multiplier,
            "initial_ingredients": sim_initial_inventory.copy(),
            "restock_threshold": sim_restock_threshold,
        }

        active_simulator = None
        set_game_state('SIMULATION')
        print(f"Starting experiment: {total_configs} configs × {sim_runs_per_config} runs = {total_runs} simulations @ {sim_speed_multiplier}x")
    except Exception as e:
        print("Failed to start experiment with params:", e)

def cancel_sim_settings():
    set_game_state('START')

# Create setting buttons (positions relative to center)
cx = WIDTH // 2 - 120
cy = 200
# Rows in order: queues, stoves, speed, runs, rice, egg, veg, chicken, restock
handlers = [
    (dec_num_queues, inc_num_queues),
    (dec_num_stoves, inc_num_stoves),
    (dec_speed, inc_speed),
    (dec_runs, inc_runs),
    (dec_rice, inc_rice),
    (dec_egg, inc_egg),
    (dec_veg, inc_veg),
    (dec_chk, inc_chk),
    (dec_restock, inc_restock),
]

for i, (dec_fn, inc_fn) in enumerate(handlers):
    y = cy + i * 60
    sim_setting_buttons.append(Button(cx + 220, y, 40, 32, "-", RED_ACCENT, (245, 180, 165), dec_fn))
    sim_setting_buttons.append(Button(cx + 260, y, 40, 32, "+", GREEN_ACCENT, (160, 180, 140), inc_fn))

# Compare toggle (checkbox-like) and action buttons (moved down to avoid overlap)
def toggle_compare():
    global sim_compare, compare_button
    sim_compare = not sim_compare
    try:
        compare_button.text = f"Compare: {'On' if sim_compare else 'Off'}"
    except Exception:
        pass

compare_button = Button(WIDTH//2 - 100, cy+320, 200, 40, "Compare: Off", GRAY, (230, 215, 200), toggle_compare)
sim_setting_buttons.append(compare_button)
sim_setting_buttons.append(Button(WIDTH//2 - 100, cy+380, 200, 50, "Start Experiment", GREEN_ACCENT, (160, 180, 140), start_experiment_with_params))
sim_setting_buttons.append(Button(WIDTH//2 - 100, cy+440, 200, 50, "Back", RED_ACCENT, (245, 180, 165), cancel_sim_settings))

start_buttons.append(Button(WIDTH//2 - 100, 200, 200, 50, "Play", GREEN_ACCENT, (160, 180, 140), start_play))
start_buttons.append(Button(WIDTH//2 - 100, 270, 200, 50, "Help", GRAY, (230, 215, 200), start_help))
start_buttons.append(Button(WIDTH//2 - 100, 340, 200, 50, "High Score", TERRACOTTA, (225, 146, 113), start_highscores))
start_buttons.append(Button(WIDTH//2 - 100, 410, 200, 50, "Simulation", GRAY, (230, 215, 200), start_simulation))
start_buttons.append(Button(WIDTH//2 - 100, 480, 200, 50, "Exit", RED_ACCENT, (245, 180, 165), start_exit))

# Back button for dialogs
back_button = Button(20, HEIGHT-60, 100, 40, "Back", GRAY, (230, 215, 200), lambda: set_game_state('START'))

# Game Over -> Main Menu button
def goto_main_menu():
    global game_over, pending_score, pending_name, pending_message, message_timer
    game_over = False
    pending_score = None
    pending_name = ""
    pending_message = None
    message_timer = 0.0
    reset_game()
    set_game_state('START')

game_over_button = Button(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 50, "Main Menu", GRAY, (230, 215, 200), goto_main_menu)

# --- QUEUE SYSTEM SETTINGS ---
customer_queue = []  # Python list to track order (FIFO)
# Vertical queue layout: fixed X coordinate, variable Y for each customer
QUEUE_X = 100
QUEUE_START_Y = 120  # Top of the queue
SPACING = 80         # Vertical pixels between customers (keeps names/sprites from overlapping)

# --- GAME STATS ---
lost_customers = 0
MAX_LOST = 5
game_over = False

# --- POISSON ARRIVAL LOGIC ---
def get_next_arrival_time():
    # Exponential distribution = Poisson process for arrivals
    return np.random.exponential(1 / ARRIVAL_RATE)

spawn_timer = get_next_arrival_time()

# Test hook: trigger immediate loss when AUTOTEST_LOSS=1 (non-interactive test)
if os.environ.get('AUTOTEST_LOSS') == '1':
    lost_customers = MAX_LOST

# --- GAME LOOP ---
running = True
def reset_game():
    global lost_customers, game_over, customer_queue, all_sprites, customers
    global game_inventory, game_kitchen, game_stats, game_elapsed
    global player
    # reset minimal state
    lost_customers = 0
    game_over = False
    game_elapsed = 0.0
    # remove existing customers
    for c in customers:
        c.kill()
    customer_queue = []
    # reset sprite groups (no static player by default)
    all_sprites.empty()
    customers.empty()
    player = None
    # reset inventory and kitchen
    game_inventory.items = {k:0 for k in game_inventory.items}
    game_inventory.cooked_food = {k:0 for k in game_inventory.cooked_food}
    game_inventory.money = 100
    game_kitchen.slots = []
    game_kitchen.max_slots = 4
    # reset stats
    game_stats = GameStats()
    game_kitchen.stats = game_stats


while running:
    dt = clock.tick(FPS) / 1000  # Delta time in seconds

    # ==========================
    # 1. INPUT HANDLING
    # ==========================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # global-level controls depend on GAME_STATE
        # Only process controls for various states
        if GAME_STATE == 'START':
            for btn in start_buttons:
                if btn.handle_event(event):
                    systems.sound_manager.sound_manager.play_sound("click")

        elif GAME_STATE == 'SIMULATION_SETTINGS':
            for btn in sim_setting_buttons:
                if btn.handle_event(event):
                    systems.sound_manager.sound_manager.play_sound("click")

        # Allow fullscreen toggle and window resize handling globally
        if event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
            # Fullscreen-only mode: ignore F11 toggle to prevent windowed/half-screen modes
            pass
        elif event.type == pygame.VIDEORESIZE:
            # Ignore resize events while running fullscreen; keep current fullscreen size
            try:
                cur_width, cur_height = screen.get_size()
            except Exception:
                pass

        elif GAME_STATE == 'SIMULATION':
            # Allow exiting simulation with ESC (returns to main menu)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                try:
                    if active_simulator:
                        active_simulator.cleanup()
                except Exception:
                    pass
                active_simulator = None
                set_game_state('START')
            elif active_simulator:
                # Route events to simulation for speed controls / pause
                action = active_simulator.handle_event(event)
                if action == 'PAUSE':
                    systems.sound_manager.sound_manager.play_sound("click")
                    set_game_state('PAUSED')

        elif GAME_STATE == 'HELP' or GAME_STATE == 'HIGHSCORES':
            if back_button.handle_event(event):
                systems.sound_manager.sound_manager.play_sound("click")

        elif GAME_STATE == 'PLAYING':
            # Handle Button Clicks
            for btn in buttons:
                if btn.handle_event(event):
                    systems.sound_manager.sound_manager.play_sound("click")
            if pause_button.handle_event(event):
                systems.sound_manager.sound_manager.play_sound("click")

            # Handle Keyboard
            if event.type == pygame.KEYDOWN:
                # --- SHOPPING CONTROLS ---
                if event.key == pygame.K_1:
                    _buy_helper("Rice")
                elif event.key == pygame.K_2:
                    _buy_helper("Egg")
                elif event.key == pygame.K_3:
                    _buy_helper("Veggie")
                elif event.key == pygame.K_4:
                    _buy_helper("Chicken")
                
                # --- COOKING CONTROLS ---
                elif event.key == pygame.K_r:
                    _cook_helper("Fried Rice")
                elif event.key == pygame.K_c:
                    _cook_helper("Chicken Rice")
                elif event.key == pygame.K_o:
                    _cook_helper("Omelet")
                elif event.key == pygame.K_b:
                    buy_stove()
                
                # --- SERVING CONTROLS ---
                elif event.key == pygame.K_SPACE:
                    if len(customer_queue) > 0:
                        front_customer = customer_queue[0]
                        dish_wanted = front_customer.order
                        if game_inventory.cooked_food.get(dish_wanted, 0) > 0:
                            game_inventory.cooked_food[dish_wanted] -= 1
                            revenue = MENU_PRICES[dish_wanted]
                            game_inventory.money += revenue
                            wait_time = game_elapsed - front_customer.arrival_time
                            game_stats.record_customer_served(wait_time, dish_wanted, revenue)
                            front_customer.served = True
                            front_customer.kill()
                            systems.sound_manager.sound_manager.play_sound("serve")
                            print(f"Served {dish_wanted}! +${revenue}")
                        else:
                            systems.sound_manager.sound_manager.play_sound("error")
                            print(f"You don't have {dish_wanted}!")

        elif GAME_STATE == 'PAUSED':
            # handle pause menu clicks via mouse
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Resume
                if cur_width//2 - 100 <= mx <= cur_width//2 + 100 and cur_height//2 - 60 <= my <= cur_height//2 - 10:
                    systems.sound_manager.sound_manager.play_sound("click")
                    set_game_state('PLAYING')
                # Restart
                if cur_width//2 - 100 <= mx <= cur_width//2 + 100 and cur_height//2 - 0 <= my <= cur_height//2 + 50:
                    systems.sound_manager.sound_manager.play_sound("click")
                    # notify player score won't be saved
                    print("Restarting game. Score won't be saved.")
                    reset_game()
                    set_game_state('PLAYING')
                # Finish
                if cur_width//2 - 100 <= mx <= cur_width//2 + 100 and cur_height//2 + 60 <= my <= cur_height//2 + 110:
                    systems.sound_manager.sound_manager.play_sound("click")
                    set_game_state('FINISH_CONFIRM')

        elif GAME_STATE == 'FINISH_CONFIRM':
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Yes — go to strategy summary first
                if cur_width//2 - 100 <= mx <= cur_width//2 - 20 and cur_height//2 + 40 <= my <= cur_height//2 + 90:
                    systems.sound_manager.sound_manager.play_sound("click")
                    game_stats.finalize(game_elapsed)
                    strategy_screen.reset()
                    set_game_state('STRATEGY_SUMMARY')
                # No
                if cur_width//2 + 20 <= mx <= cur_width//2 + 100 and cur_height//2 + 40 <= my <= cur_height//2 + 90:
                    systems.sound_manager.sound_manager.play_sound("click")
                    set_game_state('PLAYING')

        elif GAME_STATE == 'ENTER_NAME':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    pending_name = pending_name[:-1]
                elif event.key == pygame.K_RETURN:
                    # Save name (max 10 chars)
                    name = pending_name[:10] if pending_name else "Player"
                    highscores.append({"name": name, "score": pending_score})
                    hs_sorted = sorted(highscores, key=lambda x: x["score"], reverse=True)[:5]
                    save_highscores(hs_sorted)
                    # refresh
                    highscores[:] = hs_sorted
                    set_game_state('GAME_OVER')
                    game_over = True
            elif event.type == pygame.TEXTINPUT:
                # TEXTINPUT is the recommended way for text entry across platforms
                txt = getattr(event, 'text', '')
                if txt and len(pending_name) < 10 and txt.isprintable():
                    pending_name += txt

        elif GAME_STATE == 'STRATEGY_SUMMARY':
            if strategy_screen.handle_event(event):
                systems.sound_manager.sound_manager.play_sound("click")
                # Continue pressed — go to highscore/game over
                pending_score = game_inventory.money
                if is_highscore(pending_score):
                    pending_name = ""
                    set_game_state('ENTER_NAME')
                else:
                    game_over = True
                    set_game_state('GAME_OVER')

        elif GAME_STATE == 'GAME_OVER' or game_over:
            if game_over_button.handle_event(event):
                systems.sound_manager.sound_manager.play_sound("click")

    # Handle Button Hover (Outside event loop)
    mouse_pos = pygame.mouse.get_pos()
    if GAME_STATE == 'PLAYING' and not game_over:
        for btn in buttons:
            btn.check_hover(mouse_pos)
        pause_button.check_hover(mouse_pos)
    elif GAME_STATE == 'START':
        for btn in start_buttons:
            btn.check_hover(mouse_pos)
    elif GAME_STATE in ('HELP', 'HIGHSCORES'):
        back_button.check_hover(mouse_pos)
    elif GAME_STATE == 'STRATEGY_SUMMARY':
        strategy_screen.check_hover(mouse_pos)
    elif GAME_STATE == 'GAME_OVER' or game_over:
        game_over_button.check_hover(mouse_pos)
    elif GAME_STATE == 'SIMULATION_SETTINGS':
        for btn in sim_setting_buttons:
            btn.check_hover(mouse_pos)
    elif GAME_STATE == 'SIMULATION':
        if active_simulator:
            active_simulator.check_hover(mouse_pos)

    # ==========================
    # 2. UPDATE LOGIC
    # ==========================
    
    # Check Game Over Condition (lost too many OR timer expired)
    timer_expired = GAME_TIMER_MAX > 0 and game_elapsed >= GAME_TIMER_MAX
    if (lost_customers >= MAX_LOST or timer_expired) and GAME_STATE == 'PLAYING':
        systems.sound_manager.sound_manager.play_sound("gameover")
        game_over = True
        game_stats.finalize(game_elapsed)
        strategy_screen.reset()
        set_game_state('STRATEGY_SUMMARY')

    # Tick message timer
    if message_timer > 0:
        message_timer -= dt
        if message_timer <= 0:
            pending_message = None

    # Caret blink for name entry
    if GAME_STATE == 'ENTER_NAME':
        try:
            caret_timer -= dt
            if caret_timer <= 0:
                caret_timer = CARET_BLINK_INTERVAL
                caret_visible = not caret_visible
        except Exception:
            # ensure caret vars exist even if something odd happens
            caret_timer = CARET_BLINK_INTERVAL
            caret_visible = True

    if GAME_STATE == 'PLAYING' and not game_over:
        # Track elapsed game time
        game_elapsed += dt

        # Spawning Logic (Poisson)
        spawn_timer -= dt
        if spawn_timer <= 0:
            # Bottom-up vertical queue: place customers so their bottoms sit above the counter
            counter_y = cur_height - 160
            gap = 20  # vertical gap between stacked customers (increased for readability)

            # Create a new customer temporarily to measure sprite height
            tmp = Customer((0, 0), game_clock=game_elapsed)
            h = tmp.rect.height
            w = tmp.rect.width
            del tmp

            # Compute the final target y for the new customer so its bottom is just above the counter
            target_y = counter_y - 5 - h - (len(customer_queue) * (h + gap))

            # Only spawn if there's room above (don't spawn off the top of the screen)
            if target_y > 80:
                # center horizontally
                queue_x = (cur_width // 2) - (w // 2)
                # spawn slightly above final position for a small drop animation
                spawn_y = target_y - 40
                new_customer = Customer((queue_x, spawn_y), game_clock=game_elapsed)
                all_sprites.add(new_customer)
                customers.add(new_customer)
                customer_queue.append(new_customer)
                game_stats.record_customer_arrived()

            spawn_timer = get_next_arrival_time()

        # Update Systems
        all_sprites.update(dt)
        game_kitchen.update(dt)

        # Stats snapshots (every frame)
        game_stats.record_queue_snapshot(len(customer_queue))
        game_stats.record_stove_snapshot(len(game_kitchen.slots), game_kitchen.max_slots)
        game_stats.record_stock_snapshot(game_inventory.items)

        # Queue Maintenance
        survivors = [c for c in customer_queue if c.alive()]
        lost_this_frame = sum(1 for c in customer_queue if not c.alive() and not getattr(c, 'served', False))
        for _ in range(lost_this_frame):
            game_stats.record_customer_lost()
        lost_customers += lost_this_frame
        customer_queue = survivors

        # Slide Animation for bottom-up vertical Queue: compute per-customer targets using sprite heights
        counter_y = cur_height - 160
        gap = 20
        # For each customer compute stacked position so their bottoms sit above the counter
        for idx, customer in enumerate(customer_queue):
            # compute cumulative height of customers before this one
            offset = 0
            for prev in customer_queue[:idx]:
                offset += prev.rect.height + gap
            target_y = counter_y - 5 - customer.rect.height - offset
            if customer.rect.y > target_y:
                customer.rect.y -= 300 * dt
                if customer.rect.y < target_y:
                    customer.rect.y = target_y
            else:
                customer.rect.y = target_y

    # ==========================
    # 3. DRAWING
    # ==========================
    # Background selection:
    # - Use floor for PLAYING, SIMULATION, PAUSED, FINISH_CONFIRM
    # - Use decorative menu background for other states
    if GAME_STATE in ('PLAYING', 'SIMULATION', 'PAUSED', 'FINISH_CONFIRM'):
        if floor_image:
            try:
                if floor_scaled is None or floor_scaled.get_size() != (cur_width, cur_height):
                    floor_scaled = pygame.transform.smoothscale(floor_image, (cur_width, cur_height))
                screen.blit(floor_scaled, (0, 0))
            except Exception:
                screen.fill(BG_COLOR)
        else:
            screen.fill(BG_COLOR)
    else:
        # menus use decorative background
        if bg_image:
            try:
                if bg_scaled is None or bg_scaled.get_size() != (cur_width, cur_height):
                    bg_scaled = pygame.transform.smoothscale(bg_image, (cur_width, cur_height))
                screen.blit(bg_scaled, (0, 0))
            except Exception:
                screen.fill(BG_COLOR)
        else:
            screen.fill(BG_COLOR)

    if GAME_STATE == 'START':
        # Title
        title_font = pygame.font.SysFont("trebuchetms", 54, bold=True)
        title = title_font.render("Cafeteria Dash", True, BLACK)
        screen.blit(title, title.get_rect(center=(cur_width//2, 100)))
        
        # Reposition and draw main menu buttons
        start_y = 200
        for i, btn in enumerate(start_buttons):
            btn.set_position(cur_width//2 - 100, start_y + i * 70)
            btn.draw(screen)

    elif GAME_STATE == 'SIMULATION_SETTINGS':
        # Responsive panel centered on screen
        # Layout constants - make them scale to available screen height so content fits
        rows = len(sim_setting_rows)
        padding = max(12, int(cur_height * 0.03))

        # Start with a preferred row height then shrink if needed to fit
        preferred_row_h = 56
        min_row_h = 36

        # Action area (buttons) size scales with screen height
        action_h = min(220, int(cur_height * 0.22))

        # Compute maximum allowed panel height with margins
        max_panel_h = max(300, cur_height - 80)

        # Compute tentative content height and adjust row height to fit if necessary
        content_h = rows * preferred_row_h
        panel_h = padding * 2 + 40 + content_h + action_h
        if panel_h > max_panel_h:
            # reduce row height to fit available space
            avail_for_rows = max_panel_h - (padding * 2) - 40 - action_h
            row_h = max(min_row_h, int(avail_for_rows / max(1, rows)))
            content_h = rows * row_h
            panel_h = padding * 2 + 40 + content_h + action_h
        else:
            row_h = preferred_row_h

        # Button sizes scale with row height
        btn_h = max(24, min(40, row_h - 12))
        btn_w = max(32, int(btn_h * 1.25))
        btn_gap = max(8, int(btn_h * 0.35))

        # Panel width adapts to screen width
        panel_w = min(900, max(480, cur_width - 120))

        # Fonts scale with row height for readability on small screens
        labelf = pygame.font.SysFont("trebuchetms", max(12, int(row_h * 0.35)))
        titlef = pygame.font.SysFont("trebuchetms", max(18, int(row_h * 0.5) + 6), bold=True)

        dlg = pygame.Rect((cur_width - panel_w)//2, (cur_height - panel_h)//2, panel_w, panel_h)
        pygame.draw.rect(screen, WHITE, dlg, border_radius=15)
        pygame.draw.rect(screen, GRAY, dlg, 2, border_radius=15)

        # Title
        title_surf = titlef.render("Simulation Settings", True, TERRACOTTA)
        title_x = dlg.x + padding
        title_y = dlg.y + padding
        screen.blit(title_surf, (title_x, title_y))

        # content origin
        content_x = dlg.x + padding
        content_y = title_y + 40

        # compute areas: label column and button column
        label_col_w = int(panel_w * 0.55)
        value_col_x = content_x + label_col_w - 80
        buttons_col_right = dlg.x + dlg.width - padding
        button_left_x = buttons_col_right - (btn_w * 2 + btn_gap)

        # Draw each row: left-aligned label, value near label, right-aligned +/- buttons
        for i, name in enumerate(sim_setting_rows):
            row_y = content_y + i * row_h

            # get display label and value
            if name == 'Queues':
                label = "Number of Queues:"
                value = str(sim_num_queues)
            elif name == 'Stoves':
                label = "Number of Stoves:"
                value = str(sim_num_stoves)
            elif name == 'Speed':
                label = "Speed Multiplier:"
                value = f"{sim_speed_multiplier}x"
            elif name == 'Runs':
                label = "Runs per Config:"
                value = str(sim_runs_per_config)
            elif name == 'Rice':
                label = "Rice Stock:"
                value = str(sim_initial_inventory.get('Rice', 0))
            elif name == 'Egg':
                label = "Egg Stock:"
                value = str(sim_initial_inventory.get('Egg', 0))
            elif name == 'Veggie':
                label = "Veggie Stock:"
                value = str(sim_initial_inventory.get('Veggie', 0))
            elif name == 'Chicken':
                label = "Chicken Stock:"
                value = str(sim_initial_inventory.get('Chicken', 0))
            elif name == 'Restock':
                label = "Restock Threshold:"
                value = str(sim_restock_threshold)
            else:
                label = name
                value = ''

            # label (left-aligned)
            lbl_surf = labelf.render(label, True, BLACK)
            screen.blit(lbl_surf, (content_x, row_y + (row_h - lbl_surf.get_height())//2))

            # value (slightly to right of label, visually tied)
            val_surf = labelf.render(value, True, (140, 120, 110))
            screen.blit(val_surf, (value_col_x, row_y + (row_h - val_surf.get_height())//2))

            # position +/- buttons created earlier (pairs in same order)
            a = i * 2
            b = a + 1
            try:
                # vertical center inside row
                btn_y = row_y + (row_h - btn_h) // 2
                sim_setting_buttons[a].rect.topleft = (button_left_x, btn_y)
                sim_setting_buttons[b].rect.topleft = (button_left_x + btn_w + btn_gap, btn_y)
            except Exception:
                pass

        # Actions: Compare, Start, Back — stack centered horizontally inside panel
        actions_x = dlg.x + (dlg.width - 240) // 2
        action_base_y = content_y + content_h + 24
        try:
            # Compute maximum width available for action buttons inside the panel
            max_action_w = max(160, dlg.width - padding * 2 - 20)

            # Compare toggle (small)
            compare_w = min(220, max_action_w)
            compare_h = max(28, int(action_h * 0.18))
            compare_button.rect.size = (compare_w, compare_h)
            compare_button.rect.topleft = (dlg.x + (dlg.width - compare_w)//2, action_base_y)

            # spacing between action buttons
            spacing = max(12, int(action_h * 0.12))

            # Start Experiment (prominent) - placed below Compare with spacing
            start_w = min(280, max_action_w)
            start_h = max(40, int(action_h * 0.28))
            sim_setting_buttons[-2].rect.size = (start_w, start_h)
            start_y = action_base_y + compare_h + spacing
            sim_setting_buttons[-2].rect.topleft = (dlg.x + (dlg.width - start_w)//2, start_y)

            # Back button (smaller) - placed below Start with spacing
            back_w = min(240, max_action_w)
            back_h = max(36, int(action_h * 0.2))
            sim_setting_buttons[-1].rect.size = (back_w, back_h)
            back_y = start_y + start_h + spacing
            sim_setting_buttons[-1].rect.topleft = (dlg.x + (dlg.width - back_w)//2, back_y)
        except Exception:
            pass

        # finally draw all buttons
        for btn in sim_setting_buttons:
            btn.draw(screen)

    elif GAME_STATE == 'SIMULATION':
        # Experiment orchestration: either step a running simulator, or start
        # the next simulator for the next run/config.
        if active_simulator:
            running_sim = active_simulator.step(dt)
            if not running_sim:
                # Collect stats from the finished simulator
                try:
                    st = active_simulator.stats
                    cfg = active_experiment["configs"][active_experiment["ci"]]
                    row = {
                        "config_id": active_experiment["ci"],
                        "run": active_experiment["ri"] + 1,
                        "num_queues": cfg.num_queues,
                        "num_stoves": cfg.num_stoves,
                        "arrival_rate": cfg.arrival_rate,
                        "initial_stock": sum(cfg.initial_ingredients.values()),
                    }
                    # metrics: simulation.metrics.GameStats has a to_dict or similar
                    try:
                        row.update(st.to_dict())
                    except Exception:
                        # fallback — inspect common fields
                        row.update({
                            "profit": getattr(st, "total_revenue", 0) - getattr(st, "total_ingredient_cost", 0),
                            "customers_served": getattr(st, "customers_served", 0),
                            "customers_lost": getattr(st, "customers_lost", 0),
                            "avg_wait_time": getattr(st, "avg_wait_time", 0),
                            "throughput": getattr(st, "customers_served", 0),
                            "loss_rate": getattr(st, "customers_lost", 0) / max(1, cfg.sim_duration),
                        })
                except Exception as e:
                    print("Failed to collect stats from simulator:", e)
                    row = None

                # cleanup simulator and advance run indices
                try:
                    active_simulator.cleanup()
                except Exception:
                    pass
                active_simulator = None

                if row is not None:
                    active_experiment["rows"].append(row)

                # Advance run index; move to next config when runs exhausted
                active_experiment["ri"] += 1
                if active_experiment["ri"] >= active_experiment.get("runs_per_config", 1):
                    active_experiment["ri"] = 0
                    active_experiment["ci"] += 1
        else:
            # No active simulator: if there are remaining configs/runs, start next
            if active_experiment and active_experiment["ci"] < active_experiment["total_configs"]:
                cfg = active_experiment["configs"][active_experiment["ci"]]
                ri = active_experiment["ri"]
                # instantiate simulator for this config/run
                try:
                    active_simulator = CafeteriaSimulator(cfg, run_index=ri+1, total_runs=active_experiment.get("runs_per_config", 1), screen=screen, clock=clock)
                    # apply user speed multiplier
                    try:
                        active_simulator.SPEED_MULTIPLIER = active_experiment.get("speed_multiplier", active_simulator.SPEED_MULTIPLIER)
                    except Exception:
                        pass
                    # apply initial ingredients and restock threshold if provided
                    try:
                        if "initial_ingredients" in active_experiment:
                            # Update the simulator's inventory in-place so kitchen
                            # (which holds a reference) sees the changes.
                            new_items = active_experiment["initial_ingredients"].copy()
                            try:
                                # prefer in-place update
                                active_simulator.items.clear()
                                active_simulator.items.update(new_items)
                            except Exception:
                                # fallback: replace and also update kitchen reference
                                active_simulator.items = new_items
                                try:
                                    active_simulator.kitchen.items = active_simulator.items
                                except Exception:
                                    pass
                            # reset cooked food counts
                            if hasattr(active_simulator, 'cooked_food'):
                                for k in list(active_simulator.cooked_food.keys()):
                                    active_simulator.cooked_food[k] = 0
                        if "restock_threshold" in active_experiment:
                            active_simulator.RESTOCK_THRESHOLD = active_experiment["restock_threshold"]
                    except Exception:
                        pass
                    print(f"Running config {active_experiment['ci']} run {ri+1}/{active_experiment.get('runs_per_config',1)}")
                except Exception as e:
                    print("Failed to start simulator for config:", e)
                    # advance to next to avoid infinite loop
                    active_experiment["ri"] += 1
                    if active_experiment["ri"] >= active_experiment.get("runs_per_config", 1):
                        active_experiment["ri"] = 0
                        active_experiment["ci"] += 1
            else:
                # Experiment finished — build DataFrame and run analysis
                try:
                    df = pd.DataFrame(active_experiment["rows"]) if active_experiment["rows"] else pd.DataFrame()
                    if not df.empty:
                        df = add_efficiency_scores(df)
                        print_summary_table(df)
                        plot_results(df)
                        out_path = os.path.join(os.path.dirname(__file__), "experiment_results_embedded.csv")
                        df.to_csv(out_path, index=False)
                        print(f"Embedded experiment results saved to {out_path}")
                except Exception as e:
                    print("Failed to finalize experiment analysis:", e)

                active_experiment = None
                active_simulator = None
                set_game_state('START')

    elif GAME_STATE == 'HELP':
        # Draw help dialog
        dlg_rect = pygame.Rect((cur_width - 600)//2, (cur_height - 400)//2, 600, 400)
        pygame.draw.rect(screen, WHITE, dlg_rect, border_radius=15)
        pygame.draw.rect(screen, GRAY, dlg_rect, 2, border_radius=15)
        
        title_font = pygame.font.SysFont("trebuchetms", 28, bold=True)
        screen.blit(title_font.render("Help", True, BLACK), (dlg_rect.x+20, dlg_rect.y+20))
        
        help_font = pygame.font.SysFont("trebuchetms", 18)
        lines = [
            "- 1/2/3/4: Buy Rice/Egg/Veg/Chicken",
            "- R/C/O: Cook Fried Rice/Chicken Rice/Omelet",
            "- SPACE: Serve the front customer",
            "- B: Buy a new stove ($50)",
            "- Pause to Resume/Restart/Finish the game.",
            "- Game ends after 5 lost customers or 5 min timer.",
            "- Strategy summary shown at end of game.",
            "- Press ESC to exit the simulation experiment."
        ]
        y = dlg_rect.y + 70
        for l in lines:
            screen.blit(help_font.render(l, True, BLACK), (dlg_rect.x+20, y))
            y += 30
        
        back_button.set_position(dlg_rect.x + 20, dlg_rect.bottom - 60)
        back_button.draw(screen)

    elif GAME_STATE == 'HIGHSCORES':
        dlg_rect = pygame.Rect((cur_width - 400)//2, (cur_height - 400)//2, 400, 400)
        pygame.draw.rect(screen, WHITE, dlg_rect, border_radius=15)
        pygame.draw.rect(screen, GRAY, dlg_rect, 2, border_radius=15)
        hf = pygame.font.SysFont("trebuchetms", 28, bold=True)
        screen.blit(hf.render("High Scores", True, TERRACOTTA), (dlg_rect.x+20, dlg_rect.y+20))
        y = dlg_rect.y + 80
        entry_font = pygame.font.SysFont("trebuchetms", 22)
        hs_sorted = sorted(highscores, key=lambda x: x["score"], reverse=True)[:5]
        for i, e in enumerate(hs_sorted, start=1):
            screen.blit(entry_font.render(f"{i}. {e['name']} - ${e['score']}", True, BLACK), (dlg_rect.x+40, y))
            y += 40
        back_button.set_position(dlg_rect.x + 20, dlg_rect.bottom - 60)
        back_button.draw(screen)

    elif GAME_STATE in ('PLAYING',):
        # Draw UI Systems and kitchen first (so sprites render on top of the counter)
        game_hud.draw(screen, cur_width, cur_height, game_stats=game_stats, game_elapsed=game_elapsed, game_timer_max=GAME_TIMER_MAX)
        game_kitchen.draw(screen, cur_width, cur_height)

        # Draw Sprites after kitchen so they appear above the counter
        all_sprites.draw(screen)
        # Draw Custom Customer UI
        for customer in customers:
            customer.draw_patience_bar(screen)
            customer.draw_order_text(screen, font)
        
        # Reposition buttons dynamically
        # 1. Buy Buttons over the storage bins in kitchen.py
        bin_w = 70
        bin_y = cur_height - 120
        for i in range(4):
            bx = 20 + (i * (bin_w + 20)) + 10
            buttons[i].set_position(bx, bin_y + 65) # Hover just under the bin center
            
        # 2. Cook Buttons in a 2x2 grid bottom right
        grid_start_x = cur_width - 320
        grid_start_y = cur_height - 120
        buttons[4].set_position(grid_start_x, grid_start_y)           # Cook Rice
        buttons[5].set_position(grid_start_x + 140, grid_start_y)     # Cook Chk
        buttons[6].set_position(grid_start_x, grid_start_y + 60)      # Cook Omelet
        buttons[7].set_position(grid_start_x + 140, grid_start_y + 60)# Buy Stove
        
        # Anchor Pause button to the top-right with padding
        try:
            pause_button.set_position(cur_width - pause_button.rect.width - 20, 12)
        except Exception:
            pause_button.set_position(cur_width - 110, 10)
        
        # Draw Buttons
        for btn in buttons:
            btn.draw(screen)
        pause_button.draw(screen)


    elif GAME_STATE == 'PAUSED':
        # draw the paused game behind (static)
        all_sprites.draw(screen)
        game_hud.draw(screen, cur_width, cur_height, game_stats=game_stats, game_elapsed=game_elapsed, game_timer_max=GAME_TIMER_MAX)
        game_kitchen.draw(screen, cur_width, cur_height)
        
        # overlay
        overlay = pygame.Surface((cur_width, cur_height), pygame.SRCALPHA)
        overlay.fill((169, 194, 168, 180)) # Semi-transparent Sage Green
        screen.blit(overlay, (0,0))
        
        pf = pygame.font.SysFont("trebuchetms", 36, bold=True)
        screen.blit(pf.render("Paused", True, BLACK), (cur_width//2 - 60, cur_height//2 - 150))
        
        # Simple buttons as rectangles
        pygame.draw.rect(screen, WHITE, (cur_width//2 - 100, cur_height//2 - 60, 200, 50), border_radius=15)
        screen.blit(font.render("Resume", True, BLACK), (cur_width//2 - 35, cur_height//2 - 45))
        pygame.draw.rect(screen, WHITE, (cur_width//2 - 100, cur_height//2 + 0, 200, 50), border_radius=15)
        screen.blit(font.render("Restart", True, BLACK), (cur_width//2 - 35, cur_height//2 + 15))
        pygame.draw.rect(screen, WHITE, (cur_width//2 - 100, cur_height//2 + 60, 200, 50), border_radius=15)
        screen.blit(font.render("Finish", True, BLACK), (cur_width//2 - 35, cur_height//2 + 75))

    elif GAME_STATE == 'FINISH_CONFIRM':
        # Confirmation dialog
        rect = pygame.Rect(cur_width//2 - 180, cur_height//2 - 80, 360, 200)
        pygame.draw.rect(screen, WHITE, rect, border_radius=15)
        pygame.draw.rect(screen, GRAY, rect, 2, border_radius=15)
        tf = pygame.font.SysFont("trebuchetms", 22)
        screen.blit(tf.render("Are you sure you want to finish?", True, BLACK), (rect.x+20, rect.y+30))
        
        # Yes / No buttons
        pygame.draw.rect(screen, GREEN_ACCENT, (cur_width//2 - 100, cur_height//2 + 40, 80, 50), border_radius=10)
        screen.blit(font.render("Yes", True, WHITE), (cur_width//2 - 75, cur_height//2 + 55))
        pygame.draw.rect(screen, RED_ACCENT, (cur_width//2 + 20, cur_height//2 + 40, 80, 50), border_radius=10)
        screen.blit(font.render("No", True, WHITE), (cur_width//2 + 45, cur_height//2 + 55))

    elif GAME_STATE == 'ENTER_NAME':
        # Prompt for name
        rect = pygame.Rect(cur_width//2 - 220, cur_height//2 - 80, 440, 160)
        pygame.draw.rect(screen, WHITE, rect, border_radius=15)
        pygame.draw.rect(screen, GRAY, rect, 2, border_radius=15)
        tf = pygame.font.SysFont("trebuchetms", 20)
        screen.blit(tf.render(f"You made the High Scores!", True, TERRACOTTA), (rect.x+20, rect.y+20))
        # input box
        pygame.draw.rect(screen, GRAY, (rect.x+20, rect.y+60, 400, 40), 2, border_radius=8)
        name_surf = tf.render(pending_name, True, BLACK)
        screen.blit(name_surf, (rect.x+30, rect.y+70))
        # instruction and caret
        inst_font = pygame.font.SysFont("trebuchetms", 16)
        inst = inst_font.render("Type name (max 10) and press Enter to save", True, (140, 120, 110))
        screen.blit(inst, (rect.x+20, rect.y+110))
        try:
            if caret_visible:
                cx = rect.x+30 + name_surf.get_width()
                cy1 = rect.y+65
                cy2 = rect.y+95
                pygame.draw.line(screen, BLACK, (cx, cy1), (cx, cy2), 2)
        except Exception:
            pass

    elif GAME_STATE == 'STRATEGY_SUMMARY':
        strategy_screen.update(dt)
        strategy_screen.draw(screen, game_stats, cur_width, cur_height)

    elif GAME_STATE == 'GAME_OVER' or game_over:
        # --- GAME OVER SCREEN ---
        screen.fill(BG_COLOR)
        go_font = pygame.font.SysFont("trebuchetms", 60, bold=True)
        text = go_font.render("GAME OVER", True, RED_ACCENT)
        text_rect = text.get_rect(center=(cur_width//2, cur_height//2 - 50))
        screen.blit(text, text_rect)
        score_font = pygame.font.SysFont("trebuchetms", 40)
        score_text = score_font.render(f"Final Money: ${game_inventory.money}", True, BLACK)
        score_rect = score_text.get_rect(center=(cur_width//2, cur_height//2 + 20))
        screen.blit(score_text, score_rect)
        game_over_button.set_position(cur_width//2 - 100, cur_height//2 + 80)
        game_over_button.draw(screen)

    # Pending message overlay (temporary)
    if pending_message and message_timer > 0:
        msg_surf = font.render(pending_message, True, BLACK)
        rect = msg_surf.get_rect(center=(cur_width//2, 80))
        pygame.draw.rect(screen, WHITE, rect.inflate(20,10), border_radius=8)
        pygame.draw.rect(screen, RED_ACCENT, rect.inflate(20,10), 2, border_radius=8)
        screen.blit(msg_surf, rect)

    # Flip happens every frame regardless of state
    pygame.display.flip()

pygame.quit()