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

# Back button for dialogs
back_button = Button(20, HEIGHT-60, 100, 40, "Back", (100,100,100), (150,150,150), lambda: set_game_state('START'))

# Game Over -> Main Menu button
game_over_button = Button(WIDTH//2 - 100, HEIGHT//2 + 80, 200, 50, "Main Menu", (100,100,200), (150,150,250), lambda: set_game_state('START'))

# --- QUEUE SYSTEM SETTINGS ---
customer_queue = []  # Python list to track order (FIFO)
QUEUE_START_X = 100
QUEUE_Y = 300        # Middle of screen vertically
SPACING = 60         # Pixels between customers

# --- GAME STATS ---
lost_customers = 0
MAX_LOST = 5
game_over = False

# --- POISSON ARRIVAL LOGIC ---
def get_next_arrival_time():
    # Exponential distribution = Poisson process for arrivals
    return np.random.exponential(1 / ARRIVAL_RATE)

spawn_timer = get_next_arrival_time()

# --- GAME LOOP ---
running = True
def reset_game():
    global lost_customers, game_over, customer_queue, all_sprites, customers, game_inventory, game_kitchen
    # reset minimal state
    lost_customers = 0
    game_over = False
    # remove existing customers
    for c in customers:
        c.kill()
    customer_queue = []
    # reset inventory and kitchen
    game_inventory.items = {k:0 for k in game_inventory.items}
    game_inventory.cooked_food = {k:0 for k in game_inventory.cooked_food}
    game_inventory.money = 100
    game_kitchen.slots = []


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
                btn.handle_event(event)

        elif GAME_STATE == 'HELP' or GAME_STATE == 'HIGHSCORES':
            back_button.handle_event(event)

        elif GAME_STATE == 'PLAYING':
            # Handle Button Clicks
            for btn in buttons:
                btn.handle_event(event)
            pause_button.handle_event(event)

            # Handle Keyboard
            if event.type == pygame.KEYDOWN:
                # --- SHOPPING CONTROLS ---
                if event.key == pygame.K_1:
                    game_inventory.buy("Rice", INGREDIENT_PRICES["Rice"])
                elif event.key == pygame.K_2:
                    game_inventory.buy("Egg", INGREDIENT_PRICES["Egg"])
                elif event.key == pygame.K_3:
                    game_inventory.buy("Veggie", INGREDIENT_PRICES["Veggie"])
                elif event.key == pygame.K_4:
                    game_inventory.buy("Chicken", INGREDIENT_PRICES["Chicken"])
                
                # --- COOKING CONTROLS ---
                elif event.key == pygame.K_r: # R for Rice (Fried Rice)
                    game_kitchen.start_cooking("Fried Rice")
                elif event.key == pygame.K_c: # C for Chicken Rice
                    game_kitchen.start_cooking("Chicken Rice")
                elif event.key == pygame.K_o: # O for Omelet
                    game_kitchen.start_cooking("Omelet")
                
                # --- SERVING CONTROLS ---
                elif event.key == pygame.K_SPACE:
                    # 1. Check if there is anyone in line
                    if len(customer_queue) > 0:
                        # Get the person at the front
                        front_customer = customer_queue[0]
                        dish_wanted = front_customer.order
                        
                        # 2. Check if we have the food
                        if game_inventory.cooked_food.get(dish_wanted, 0) > 0:
                            # --- SUCCESSFUL SERVE ---
                            game_inventory.cooked_food[dish_wanted] -= 1
                            game_inventory.money += MENU_PRICES[dish_wanted]
                            # Mark the customer as served so they don't count as "lost"
                            front_customer.served = True
                            front_customer.kill()
                            print(f"Served {dish_wanted}! +${MENU_PRICES[dish_wanted]}")
                        else:
                            print(f"You don't have {dish_wanted}!")

        elif GAME_STATE == 'PAUSED':
            # handle pause menu clicks via mouse
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Resume
                if WIDTH//2 - 100 <= mx <= WIDTH//2 + 100 and HEIGHT//2 - 60 <= my <= HEIGHT//2 - 10:
                    set_game_state('PLAYING')
                # Restart
                if WIDTH//2 - 100 <= mx <= WIDTH//2 + 100 and HEIGHT//2 - 0 <= my <= HEIGHT//2 + 50:
                    # notify player score won't be saved
                    print("Restarting game. Score won't be saved.")
                    reset_game()
                    set_game_state('PLAYING')
                # Finish
                if WIDTH//2 - 100 <= mx <= WIDTH//2 + 100 and HEIGHT//2 + 60 <= my <= HEIGHT//2 + 110:
                    set_game_state('FINISH_CONFIRM')

        elif GAME_STATE == 'FINISH_CONFIRM':
            if event.type == pygame.MOUSEBUTTONDOWN:
                mx, my = pygame.mouse.get_pos()
                # Yes
                if WIDTH//2 - 100 <= mx <= WIDTH//2 - 20 and HEIGHT//2 + 40 <= my <= HEIGHT//2 + 90:
                    # Finish game: check highscore
                    pending_score = game_inventory.money
                    if is_highscore(pending_score):
                        pending_name = ""
                        set_game_state('ENTER_NAME')
                    else:
                        game_over = True
                        set_game_state('GAME_OVER')
                # No
                if WIDTH//2 + 20 <= mx <= WIDTH//2 + 100 and HEIGHT//2 + 40 <= my <= HEIGHT//2 + 90:
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
                else:
                    if len(pending_name) < 10 and event.unicode.isprintable():
                        pending_name += event.unicode

        elif GAME_STATE == 'GAME_OVER' or game_over:
            # handle clicks on the Main Menu button
            game_over_button.handle_event(event)

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
    elif GAME_STATE == 'GAME_OVER' or game_over:
        game_over_button.check_hover(mouse_pos)

    # ==========================
    # 2. UPDATE LOGIC
    # ==========================
    
    # Check Game Over Condition
    if lost_customers >= MAX_LOST:
        game_over = True

    # Tick message timer
    if message_timer > 0:
        message_timer -= dt
        if message_timer <= 0:
            pending_message = None

    if GAME_STATE == 'PLAYING' and not game_over:
        # Spawning Logic (Poisson)
        spawn_timer -= dt
        if spawn_timer <= 0:
            queue_pos_x = QUEUE_START_X + (len(customer_queue) * SPACING)
            
            # Only spawn if the line isn't going off the screen
            if queue_pos_x < WIDTH - 50:
                new_customer = Customer((queue_pos_x, QUEUE_Y))
                all_sprites.add(new_customer)
                customers.add(new_customer)
                customer_queue.append(new_customer)
            
            spawn_timer = get_next_arrival_time()

        # Update Systems
        all_sprites.update(dt)
        game_kitchen.update(dt)

        # Queue Maintenance
        survivors = [c for c in customer_queue if c.alive()]
        # Only count customers who died from running out of patience (not served)
        lost_this_frame = sum(1 for c in customer_queue if not c.alive() and not getattr(c, 'served', False))
        lost_customers += lost_this_frame
        customer_queue = survivors

        # Slide Animation for Queue
        for index, customer in enumerate(customer_queue):
            target_x = QUEUE_START_X + (index * SPACING)
            if customer.rect.x > target_x:
                customer.rect.x -= 100 * dt
                if customer.rect.x < target_x:
                    customer.rect.x = target_x
            else:
                customer.rect.x = target_x

    # ==========================
    # 3. DRAWING
    # ==========================
    screen.fill((40, 40, 40))

    if GAME_STATE == 'START':
        # Title
        title_font = pygame.font.SysFont("Arial", 48, bold=True)
        title = title_font.render("Cafeteria Dash", True, (255, 215, 0))
        screen.blit(title, title.get_rect(center=(WIDTH//2, 100)))
        for btn in start_buttons:
            btn.draw(screen)

    elif GAME_STATE == 'HELP':
        # Draw help dialog
        dlg_rect = pygame.Rect(80, 80, WIDTH-160, HEIGHT-160)
        pygame.draw.rect(screen, (30,30,30), dlg_rect)
        pygame.draw.rect(screen, (200,200,200), dlg_rect, 2)
        help_font = pygame.font.SysFont("Arial", 20)
        lines = [
            "Help:",
            "- Buy ingredients and cook dishes.",
            "- Press SPACE to serve the front customer.",
            "- Pause to Resume/Restart/Finish the game.",
        ]
        y = dlg_rect.y + 20
        for l in lines:
            screen.blit(help_font.render(l, True, (255,255,255)), (dlg_rect.x+20, y))
            y += 30
        back_button.draw(screen)

    elif GAME_STATE == 'HIGHSCORES':
        dlg_rect = pygame.Rect(80, 80, WIDTH-160, HEIGHT-160)
        pygame.draw.rect(screen, (20,20,40), dlg_rect)
        pygame.draw.rect(screen, (200,200,200), dlg_rect, 2)
        hf = pygame.font.SysFont("Arial", 28, bold=True)
        screen.blit(hf.render("High Scores", True, (255,215,0)), (dlg_rect.x+20, dlg_rect.y+10))
        y = dlg_rect.y + 60
        entry_font = pygame.font.SysFont("Arial", 22)
        hs_sorted = sorted(highscores, key=lambda x: x["score"], reverse=True)[:5]
        for i, e in enumerate(hs_sorted, start=1):
            screen.blit(entry_font.render(f"{i}. {e['name']} - ${e['score']}", True, (255,255,255)), (dlg_rect.x+40, y))
            y += 32
        back_button.draw(screen)

    elif GAME_STATE in ('PLAYING',):
        # Draw Sprites
        all_sprites.draw(screen)
        # Draw Custom Customer UI
        for customer in customers:
            customer.draw_patience_bar(screen)
            customer.draw_order_text(screen, font)

        # Draw UI Systems
        game_hud.draw(screen)
        game_kitchen.draw(screen)
        # Draw Buttons
        for btn in buttons:
            btn.draw(screen)
        pause_button.draw(screen)
        # Show Lives
        lives_text = font.render(f"Lost: {lost_customers}/{MAX_LOST}", True, (255, 50, 50))
        screen.blit(lives_text, (WIDTH//2 - 50, 20))

    elif GAME_STATE == 'PAUSED':
        # draw the paused game behind (static)
        all_sprites.draw(screen)
        game_hud.draw(screen)
        game_kitchen.draw(screen)
        # overlay
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,150))
        screen.blit(overlay, (0,0))
        pf = pygame.font.SysFont("Arial", 36, bold=True)
        screen.blit(pf.render("Paused", True, (255,255,255)), (WIDTH//2 - 60, HEIGHT//2 - 120))
        # Simple buttons as rectangles
        pygame.draw.rect(screen, (80,120,80), (WIDTH//2 - 100, HEIGHT//2 - 60, 200, 50))
        screen.blit(font.render("Resume", True, (255,255,255)), (WIDTH//2 - 30, HEIGHT//2 - 45))
        pygame.draw.rect(screen, (120,80,80), (WIDTH//2 - 100, HEIGHT//2 - 0, 200, 50))
        screen.blit(font.render("Restart", True, (255,255,255)), (WIDTH//2 - 30, HEIGHT//2 + 15))
        pygame.draw.rect(screen, (100,100,140), (WIDTH//2 - 100, HEIGHT//2 + 60, 200, 50))
        screen.blit(font.render("Finish", True, (255,255,255)), (WIDTH//2 - 30, HEIGHT//2 + 75))

    elif GAME_STATE == 'FINISH_CONFIRM':
        # Confirmation dialog
        rect = pygame.Rect(WIDTH//2 - 180, HEIGHT//2 - 80, 360, 200)
        pygame.draw.rect(screen, (30,30,30), rect)
        pygame.draw.rect(screen, (200,200,200), rect, 2)
        tf = pygame.font.SysFont("Arial", 22)
        screen.blit(tf.render("Are you sure you want to finish?", True, (255,255,255)), (rect.x+20, rect.y+30))
        # Yes / No buttons
        pygame.draw.rect(screen, (80,120,80), (WIDTH//2 - 100, HEIGHT//2 + 40, 80, 50))
        screen.blit(font.render("Yes", True, (255,255,255)), (WIDTH//2 - 70, HEIGHT//2 + 55))
        pygame.draw.rect(screen, (120,80,80), (WIDTH//2 + 20, HEIGHT//2 + 40, 80, 50))
        screen.blit(font.render("No", True, (255,255,255)), (WIDTH//2 + 45, HEIGHT//2 + 55))

    elif GAME_STATE == 'ENTER_NAME':
        # Prompt for name
        rect = pygame.Rect(WIDTH//2 - 220, HEIGHT//2 - 80, 440, 160)
        pygame.draw.rect(screen, (25,25,40), rect)
        pygame.draw.rect(screen, (200,200,200), rect, 2)
        tf = pygame.font.SysFont("Arial", 20)
        screen.blit(tf.render(f"You made the High Scores! Enter name (max 10):", True, (255,255,255)), (rect.x+20, rect.y+20))
        pygame.draw.rect(screen, (255,255,255), (rect.x+20, rect.y+60, 400, 40), 2)
        name_surf = tf.render(pending_name, True, (255,255,255))
        screen.blit(name_surf, (rect.x+30, rect.y+70))

    elif GAME_STATE == 'GAME_OVER' or game_over:
        # --- GAME OVER SCREEN ---
        screen.fill((0, 0, 0)) # Black background
        # "GAME OVER" Text
        go_font = pygame.font.SysFont("Arial", 60, bold=True)
        text = go_font.render("GAME OVER", True, (255, 0, 0))
        text_rect = text.get_rect(center=(WIDTH//2, HEIGHT//2 - 50))
        screen.blit(text, text_rect)
        # Score Text
        score_font = pygame.font.SysFont("Arial", 40)
        score_text = score_font.render(f"Final Money: ${game_inventory.money}", True, (255, 255, 255))
        score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 20))
        screen.blit(score_text, score_rect)
        # Main Menu button
        game_over_button.draw(screen)

    # Pending message overlay (temporary)
    if pending_message and message_timer > 0:
        msg_surf = font.render(pending_message, True, (255, 255, 255))
        rect = msg_surf.get_rect(center=(WIDTH//2, 80))
        pygame.draw.rect(screen, (0,0,0), rect.inflate(20,10))
        screen.blit(msg_surf, rect)

    # Flip happens every frame regardless of state
    pygame.display.flip()

pygame.quit()