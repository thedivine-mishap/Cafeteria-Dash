import pygame
import numpy as np

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

# --- HELPER FUNCTIONS FOR BUTTONS ---
def buy_rice(): game_inventory.buy("Rice", INGREDIENT_PRICES["Rice"])
def buy_egg():  game_inventory.buy("Egg", INGREDIENT_PRICES["Egg"])
def buy_veg():  game_inventory.buy("Veggie", INGREDIENT_PRICES["Veggie"])
def buy_chk():  game_inventory.buy("Chicken", INGREDIENT_PRICES["Chicken"])

def cook_rice(): game_kitchen.start_cooking("Fried Rice")
def cook_chk():  game_kitchen.start_cooking("Chicken Rice")
def cook_ome():  game_kitchen.start_cooking("Omelet")

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
while running:
    dt = clock.tick(FPS) / 1000  # Delta time in seconds

    # ==========================
    # 1. INPUT HANDLING
    # ==========================
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Only process controls if Game is NOT Over
        if not game_over:
            # Handle Button Clicks
            for btn in buttons:
                btn.handle_event(event)
            
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
                            front_customer.kill() 
                            print(f"Served {dish_wanted}! +${MENU_PRICES[dish_wanted]}")
                        else:
                            print(f"You don't have {dish_wanted}!")

    # Handle Button Hover (Outside event loop)
    if not game_over:
        mouse_pos = pygame.mouse.get_pos()
        for btn in buttons:
            btn.check_hover(mouse_pos)

    # ==========================
    # 2. UPDATE LOGIC
    # ==========================
    
    # Check Game Over Condition
    if lost_customers >= MAX_LOST:
        game_over = True

    if not game_over:
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
        lost_this_frame = len(customer_queue) - len(survivors)
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
    if not game_over:
        screen.fill((40, 40, 40))
        
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

        # Show Lives
        lives_text = font.render(f"Lost: {lost_customers}/{MAX_LOST}", True, (255, 50, 50))
        screen.blit(lives_text, (WIDTH//2 - 50, 20))

    else:
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

    # Flip happens every frame regardless of state
    pygame.display.flip()

pygame.quit()