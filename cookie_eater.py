import pygame
import sys
import random

# Configuration for grid and difficulty via in-game menu.
config_grid_width = 20
config_grid_height = 20
config_is_hard = False

# Menu window dimensions (for config phase)
MENU_WIDTH = 600
MENU_HEIGHT = 400

pygame.init()
pygame.mixer.init()
try:
    pygame.mixer.music.load("gameover.mp3")
except Exception as e:
    print("Error loading game over sound:", e)
screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT), pygame.RESIZABLE)
pygame.display.set_caption("Cookie Eater Configuration")
clock = pygame.time.Clock()
CELL_SIZE = 20
grid_width = config_grid_width
grid_height = config_grid_height
is_hard = config_is_hard

grid_width_input = str(config_grid_width)
grid_height_input = str(config_grid_height)
active_input = None  # Can be "width" or "height"

# Colors
BACKGROUND_COLOR = (240, 248, 255)  # Light background (AliceBlue)
SNAKE_COLOR = (0, 255, 0)
COOKIE_COLOR = (255, 215, 0)
OBSTACLE_COLOR = (128, 128, 128)
BOUNDARY_COLOR = (128, 128, 128)
SCORE_TEXT_COLOR = (0, 0, 0)    # Dark text (opposite to the light background)
UPGRADE_TEXT_COLOR = (0, 0, 0)

# Global variables for water ripple effect
ripples = []

# Load sound effect for eating a cookie.
try:
    yum_sound = pygame.mixer.Sound("yum.wav")
    yum_sound.set_volume(1.0)
    pygame.time.set_timer(pygame.USEREVENT, 1000)  # Set timer for 1 second
    yum_sound.play()
except Exception as e:
    yum_sound = None

# Global variable for "Yum" ephemeral messages.
yum_messages = []

# Global variable for "Yum" ephemeral messages.
yum_messages = []

# Upgrade system globals
upgrades = [
    {"name": "Yellow Star", "cost": 5, "color": (255, 255, 0), "effect": "slow_20"},
    {"name": "Red Star",    "cost": 10, "color": (255, 0, 0),   "effect": "slow_50"},
    {"name": "Blue Star",   "cost": 15, "color": (0, 0, 255),   "effect": "shorten_5"},
    {"name": "Green Star",  "cost": 20, "color": (0, 255, 0),   "effect": "shorten_10"},
    {"name": "Gold Star",   "cost": 30, "color": (255, 215, 0), "effect": "wall_pass"},
]
active_speed_upgrade = None  # either "slow_20" or "slow_50" when active
speed_upgrade_end = 0        # pygame time when slowing effect expires
base_move_interval = 150     # base timer interval in milliseconds

# Global variable to store purchased upgrades for display.
purchased_upgrades = []

# Define application menu button for difficulty selection.
app_menu_difficulty_rect = pygame.Rect(10, 10, 180, 30)

# Initialize snake
snake = [(config_grid_width // 2, config_grid_height // 2)]
direction = (1, 0)  # start moving to the right

score = 0
allow_wrap = False  # Upgrade: when True, snake will wrap around the grid

# Generate obstacles if in hard mode
obstacles = []
if config_is_hard:
    # Amount proportional to grid size (at least 1 obstacle)
    obstacles_count = max(1, int(0.05 * (config_grid_width * config_grid_height)))
    for _ in range(obstacles_count):
        while True:
            pos = (random.randint(0, config_grid_width - 1), random.randint(0, config_grid_height - 1))
            # Ensure the obstacle does not overlap with the snake or another obstacle
            if pos not in snake and pos not in obstacles:
                obstacles.append(pos)
                break

# Function for generating a new cookie position (not on snake or obstacles)
def new_cookie():
    while True:
        pos = (random.randint(0, grid_width - 1), random.randint(0, grid_height - 1))
        if pos not in snake and pos not in obstacles:
            return pos

cookie = new_cookie()

# Upgrade menu state (still used during gameplay)
upgrade_menu = False

# New game state: "menu", "start", "running", "paused", "gameover"
game_state = "menu"
space_press_start = None

# Set up a timer event to move the snake every 150ms
MOVE_EVENT = pygame.USEREVENT + 1
pygame.time.set_timer(MOVE_EVENT, 150)

## Fonts (using an old-school game font and larger sizes)
font = pygame.font.SysFont("Press Start 2P", 24)
upgrade_font = pygame.font.SysFont("Press Start 2P", 36)

# Function to restart the game by resetting key variables.
def restart_game():
    global snake, direction, score, allow_wrap, cookie, obstacles, upgrade_menu, game_over_sound_played
    snake = [(grid_width // 2, grid_height // 2)]
    direction = (1, 0)
    score = 0
    allow_wrap = False
    upgrade_menu = False
    obstacles = []
    if is_hard:
        obstacles_count = max(1, int(0.05 * (grid_width * grid_height)))
        for _ in range(obstacles_count):
            while True:
                pos = (random.randint(0, grid_width - 1), random.randint(0, grid_height - 1))
                if pos not in snake and pos not in obstacles:
                    obstacles.append(pos)
                    break
    cookie = new_cookie()
    game_over_sound_played = False

running = True
while running:
    if game_state == "menu":
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Application menu item for difficulty selection.
                if app_menu_difficulty_rect.collidepoint(event.pos):
                    # Toggle difficulty.
                    config_is_hard = not config_is_hard
                    is_hard = config_is_hard
                    # If not in the menu state, restart game to apply new difficulty.
                    if game_state != "menu":
                        restart_game()
                        game_state = "start"
                    continue

                pos = event.pos
                # Define button and text box rectangles.
                grid_width_minus_rect = pygame.Rect(200, 100, 40, 40)
                grid_width_plus_rect  = pygame.Rect(360, 100, 40, 40)
                grid_height_minus_rect = pygame.Rect(200, 160, 40, 40)
                grid_height_plus_rect  = pygame.Rect(360, 160, 40, 40)
                grid_width_val_rect = pygame.Rect(250, 100, 100, 40)
                grid_height_val_rect = pygame.Rect(250, 160, 100, 40)
                difficulty_easy_rect = pygame.Rect(200, 220, 80, 40)
                difficulty_hard_rect = pygame.Rect(300, 220, 80, 40)
                start_button_rect = pygame.Rect(MENU_WIDTH//2 - 50, 300, 100, 50)

                # Check if user clicks in a text box for grid size.
                if grid_width_val_rect.collidepoint(pos):
                    active_input = "width"
                elif grid_height_val_rect.collidepoint(pos):
                    active_input = "height"
                else:
                    active_input = None

                # Process plus/minus and difficulty buttons.
                if grid_width_minus_rect.collidepoint(pos):
                    config_grid_width = max(5, config_grid_width - 1)
                    grid_width_input = str(config_grid_width)
                elif grid_width_plus_rect.collidepoint(pos):
                    config_grid_width = min(100, config_grid_width + 1)
                    grid_width_input = str(config_grid_width)
                elif grid_height_minus_rect.collidepoint(pos):
                    config_grid_height = max(5, config_grid_height - 1)
                    grid_height_input = str(config_grid_height)
                elif grid_height_plus_rect.collidepoint(pos):
                    config_grid_height = min(100, config_grid_height + 1)
                    grid_height_input = str(config_grid_height)
                elif difficulty_easy_rect.collidepoint(pos):
                    config_is_hard = False
                elif difficulty_hard_rect.collidepoint(pos):
                    config_is_hard = True
                elif start_button_rect.collidepoint(pos):
                    # Commit any active text input.
                    if active_input == "width":
                        try:
                            value = int(grid_width_input)
                            config_grid_width = min(100, max(5, value))
                        except:
                            pass
                        active_input = None
                    if active_input == "height":
                        try:
                            value = int(grid_height_input)
                            config_grid_height = min(100, max(5, value))
                        except:
                            pass
                        active_input = None
                    # Use chosen configuration and reinitialize game window.
                    grid_width = config_grid_width
                    grid_height = config_grid_height
                    is_hard = config_is_hard
                    WINDOW_WIDTH = grid_width * CELL_SIZE
                    WINDOW_HEIGHT = grid_height * CELL_SIZE
                    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
                    new_font_size = max(16, WINDOW_WIDTH // 40)
                    new_upgrade_font_size = max(24, WINDOW_WIDTH // 30)
                    font = pygame.font.SysFont("Press Start 2P", new_font_size)
                    upgrade_font = pygame.font.SysFont("Press Start 2P", new_upgrade_font_size)
                    restart_game()
                    game_state = "start"
            elif event.type == pygame.KEYDOWN:
                if active_input == "width":
                    if event.key == pygame.K_BACKSPACE:
                        grid_width_input = grid_width_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        try:
                            value = int(grid_width_input)
                            config_grid_width = min(100, max(5, value))
                        except:
                            pass
                        active_input = None
                    else:
                        if event.unicode.isdigit():
                            grid_width_input += event.unicode
                elif active_input == "height":
                    if event.key == pygame.K_BACKSPACE:
                        grid_height_input = grid_height_input[:-1]
                    elif event.key == pygame.K_RETURN:
                        try:
                            value = int(grid_height_input)
                            config_grid_height = min(100, max(5, value))
                        except:
                            pass
                        active_input = None
                    else:
                        if event.unicode.isdigit():
                            grid_height_input += event.unicode
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    space_press_start = pygame.time.get_ticks()
                elif not upgrade_menu:
                    if event.key == pygame.K_UP and direction != (0, 1) and game_state in ("running", "paused"):
                        direction = (0, -1)
                    elif event.key == pygame.K_DOWN and direction != (0, -1) and game_state in ("running", "paused"):
                        direction = (0, 1)
                    elif event.key == pygame.K_LEFT and direction != (1, 0) and game_state in ("running", "paused"):
                        direction = (-1, 0)
                    elif event.key == pygame.K_RIGHT and direction != (-1, 0) and game_state in ("running", "paused"):
                        direction = (1, 0)
                    elif event.key == pygame.K_u:
                        upgrade_menu = True
                elif upgrade_menu:
                    if event.key == pygame.K_ESCAPE:
                        upgrade_menu = False
                    elif event.key == pygame.K_w:
                        if not allow_wrap and score >= 50:
                            score -= 50
                            allow_wrap = True
                        upgrade_menu = False
            elif event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    if space_press_start is not None:
                        press_duration = pygame.time.get_ticks() - space_press_start
                        space_press_start = None
                        if press_duration < 300:
                            # Short press: in "start", begin game; in "running", pause; in "paused", resume; in "gameover", restart.
                            if game_state == "start":
                                game_state = "running"
                            elif game_state == "running":
                                game_state = "paused"
                                upgrade_menu = True       # Show upgrade menu when paused.
                            elif game_state == "paused":
                                game_state = "running"
                                upgrade_menu = False      # Hide upgrade menu when resuming.
                            elif game_state == "gameover":
                                restart_game()
                                game_state = "start"
                        elif press_duration < 1000:
                            # Medium press: Restart the game (reset to start state)
                            restart_game()
                            game_state = "start"
                        else:
                            # Long press: Quit game.
                            running = False

        # Draw the menu UI.
        screen.fill(BACKGROUND_COLOR)
        # Title
        title_surface = upgrade_font.render("Cookie Eater", True, SCORE_TEXT_COLOR)
        screen.blit(title_surface, (MENU_WIDTH//2 - title_surface.get_width()//2, 20))

        # Grid Width controls.
        grid_width_minus_rect = pygame.Rect(200, 100, 40, 40)
        grid_width_plus_rect  = pygame.Rect(360, 100, 40, 40)
        grid_width_val_rect = pygame.Rect(250, 100, 100, 40)
        width_label = font.render("Grid Width:", True, SCORE_TEXT_COLOR)
        screen.blit(width_label, (100, 110))
        pygame.draw.rect(screen, (100,100,100), grid_width_minus_rect)
        minus_label = font.render("-", True, (255,255,255))
        screen.blit(minus_label, (grid_width_minus_rect.centerx - minus_label.get_width()/2, grid_width_minus_rect.centery - minus_label.get_height()/2))
        pygame.draw.rect(screen, (100,100,100), grid_width_plus_rect)
        plus_label = font.render("+", True, (255,255,255))
        screen.blit(plus_label, (grid_width_plus_rect.centerx - plus_label.get_width()/2, grid_width_plus_rect.centery - plus_label.get_height()/2))
        pygame.draw.rect(screen, (50,50,50), grid_width_val_rect)
        width_val = font.render(grid_width_input, True, SCORE_TEXT_COLOR)
        screen.blit(width_val, (grid_width_val_rect.centerx - width_val.get_width()/2, grid_width_val_rect.centery - width_val.get_height()/2))

        # Grid Height controls.
        grid_height_minus_rect = pygame.Rect(200, 160, 40, 40)
        grid_height_plus_rect  = pygame.Rect(360, 160, 40, 40)
        grid_height_val_rect = pygame.Rect(250, 160, 100, 40)
        height_label = font.render("Grid Height:", True, SCORE_TEXT_COLOR)
        screen.blit(height_label, (100, 170))
        pygame.draw.rect(screen, (100,100,100), grid_height_minus_rect)
        screen.blit(minus_label, (grid_height_minus_rect.centerx - minus_label.get_width()/2, grid_height_minus_rect.centery - minus_label.get_height()/2))
        pygame.draw.rect(screen, (100,100,100), grid_height_plus_rect)
        screen.blit(plus_label, (grid_height_plus_rect.centerx - plus_label.get_width()/2, grid_height_plus_rect.centery - plus_label.get_height()/2))
        pygame.draw.rect(screen, (50,50,50), grid_height_val_rect)
        height_val = font.render(grid_height_input, True, SCORE_TEXT_COLOR)
        screen.blit(height_val, (grid_height_val_rect.centerx - height_val.get_width()/2, grid_height_val_rect.centery - height_val.get_height()/2))

        # Difficulty selection.
        difficulty_easy_rect = pygame.Rect(200, 220, 80, 40)
        difficulty_hard_rect = pygame.Rect(300, 220, 80, 40)
        diff_label = font.render("Difficulty:", True, SCORE_TEXT_COLOR)
        screen.blit(diff_label, (100, 230))
        pygame.draw.rect(screen, (100,100,100), difficulty_easy_rect)
        pygame.draw.rect(screen, (100,100,100), difficulty_hard_rect)
        easy_label = font.render("Easy", True, (255,255,255))
        hard_label = font.render("Hard", True, (255,255,255))
        screen.blit(easy_label, (difficulty_easy_rect.centerx - easy_label.get_width()/2, difficulty_easy_rect.centery - easy_label.get_height()/2))
        screen.blit(hard_label, (difficulty_hard_rect.centerx - hard_label.get_width()/2, difficulty_hard_rect.centery - hard_label.get_height()/2))
        if config_is_hard:
            pygame.draw.rect(screen, (255,255,255), difficulty_hard_rect, 3)
        else:
            pygame.draw.rect(screen, (255,255,255), difficulty_easy_rect, 3)

        # Start button.
        start_button_rect = pygame.Rect(MENU_WIDTH//2 - 50, 300, 100, 50)
        pygame.draw.rect(screen, (0,150,0), start_button_rect)
        start_label = font.render("Start", True, (255,255,255))
        screen.blit(start_label, (start_button_rect.centerx - start_label.get_width()/2, start_button_rect.centery - start_label.get_height()/2))

        # Draw application menu button for difficulty selection.
        difficulty_text = "Difficulty: Hard" if config_is_hard else "Difficulty: Easy"
        pygame.draw.rect(screen, (200,200,200), app_menu_difficulty_rect)
        diff_text_surface = font.render(difficulty_text, True, (0,0,0))
        screen.blit(diff_text_surface, (app_menu_difficulty_rect.x + 5, app_menu_difficulty_rect.y + 5))

        pygame.display.flip()
        clock.tick(60)
        continue

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if app_menu_difficulty_rect.collidepoint(event.pos):
                # Toggle difficulty.
                config_is_hard = not config_is_hard
                is_hard = config_is_hard
                # Restart game to apply new difficulty when not in config menu.
                if game_state != "menu":
                    restart_game()
                    game_state = "start"
                continue
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                space_press_start = pygame.time.get_ticks()
            elif not upgrade_menu:
                if event.key == pygame.K_UP and direction != (0, 1) and game_state in ("running", "paused"):
                    direction = (0, -1)
                elif event.key == pygame.K_DOWN and direction != (0, -1) and game_state in ("running", "paused"):
                    direction = (0, 1)
                elif event.key == pygame.K_LEFT and direction != (1, 0) and game_state in ("running", "paused"):
                    direction = (-1, 0)
                elif event.key == pygame.K_RIGHT and direction != (-1, 0) and game_state in ("running", "paused"):
                    direction = (1, 0)
                elif event.key == pygame.K_u:
                    upgrade_menu = True
            elif upgrade_menu:
                if event.key == pygame.K_ESCAPE:
                    upgrade_menu = False
                elif event.key == pygame.K_w:
                    if not allow_wrap and score >= 50:
                        score -= 50
                        allow_wrap = True
                    upgrade_menu = False
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                if space_press_start is not None:
                    press_duration = pygame.time.get_ticks() - space_press_start
                    space_press_start = None
                    if press_duration < 300:
                        # Short press: in "start", begin game; in "running", pause; in "paused", resume; in "gameover", restart.
                        if game_state == "start":
                            game_state = "running"
                        elif game_state == "running":
                            game_state = "paused"
                            upgrade_menu = True       # Show upgrade menu when paused.
                        elif game_state == "paused":
                            game_state = "running"
                            upgrade_menu = False      # Hide upgrade menu when resuming.
                        elif game_state == "gameover":
                            restart_game()
                            game_state = "start"
                    elif press_duration < 1000:
                        # Medium press: Restart the game (reset to start state)
                        restart_game()
                        game_state = "start"
                    else:
                        # Long press: Quit game.
                        running = False

        elif event.type == MOVE_EVENT and game_state == "running" and not upgrade_menu:
            # Calculate new head position.
            head_x, head_y = snake[0]
            dx, dy = direction
            new_head = (head_x + dx, head_y + dy)

            # If wall pass is active, wrap around; otherwise check for out-of-bounds.
            if allow_wrap:
                new_head = (new_head[0] % grid_width, new_head[1] % grid_height)
            else:
                if new_head[0] < 0 or new_head[0] >= grid_width or new_head[1] < 0 or new_head[1] >= grid_height:
                    game_state = "gameover"
                    continue

            # Check for collisions with self and obstacles.
            if new_head in snake or new_head in obstacles:
                game_state = "gameover"
                continue

            snake.insert(0, new_head)  # Add new head

            # Check if cookie is eaten.
            if new_head == cookie:
                yum_sound = pygame.mixer.Sound("yum.wav")
                yum_sound.set_volume(1.0)
                yum_sound.fadeout(500)  # Fade out after 500 milliseconds (0.5 seconds)
                score += 1
                # Trigger water ripple effect at the cookie location.
                ripple_center = (cookie[0]*CELL_SIZE + CELL_SIZE//2, cookie[1]*CELL_SIZE + CELL_SIZE//2)
                ripples.append({"center": ripple_center, "radius": 0, "max_radius": CELL_SIZE*3, "alpha": 150})
                # Show "Yum" message at the cookie location.
                yum_messages.append({"center": ripple_center, "alpha": 255, "lifetime": 60})
                # Play the yum sound effect if loaded.
                if yum_sound:
                    yum_sound.play()
                cookie = new_cookie()
                # Snake grows: do not remove tail segment.
            else:
                snake.pop()  # Remove tail

        elif event.type == pygame.VIDEORESIZE:
            if game_state != "menu":
                # Get new window dimensions
                new_width = event.w
                new_height = event.h
                # Update screen with new size
                screen = pygame.display.set_mode((new_width, new_height), pygame.RESIZABLE)
                # Recalculate cell size to fit new window
                CELL_SIZE = min(new_width // grid_width, new_height // grid_height)
                # Update font sizes based on new window size
                new_font_size = max(16, min(new_width, new_height) // 40)
                new_upgrade_font_size = max(24, min(new_width, new_height) // 30)
                font = pygame.font.SysFont("Press Start 2P", new_font_size)
                upgrade_font = pygame.font.SysFont("Press Start 2P", new_upgrade_font_size)

        elif event.type == pygame.MOUSEBUTTONDOWN and upgrade_menu:
            pos = event.pos
            cur_width = screen.get_width()
            cur_height = screen.get_height()
            # Layout upgrades horizontally.
            num_upgrades = len(upgrades)
            icon_size = 50
            spacing = 20
            total_width = num_upgrades * icon_size + (num_upgrades - 1) * spacing
            start_x = cur_width // 2 - total_width // 2
            upgrade_rects = []
            for i, upg in enumerate(upgrades):
                rect = pygame.Rect(start_x + i * (icon_size + spacing), cur_height // 2 + 100, icon_size, icon_size)
                upgrade_rects.append(rect)
            # Check which upgrade is clicked.
            for i, rect in enumerate(upgrade_rects):
                if rect.collidepoint(pos):
                    selected_upgrade = upgrades[i]
                    if score >= selected_upgrade["cost"]:
                        score -= selected_upgrade["cost"]
                        # Add purchased upgrade for display.
                        duration = 30000 if selected_upgrade["effect"] in ["slow_20", "slow_50", "wall_pass"] else 3000
                        purchased_upgrades.append({
                            "name": selected_upgrade["name"],
                            "effect": selected_upgrade["effect"],
                            "color": selected_upgrade["color"],
                            "expire": pygame.time.get_ticks() + duration
                        })
                        effect = selected_upgrade["effect"]
                        if effect == "slow_20":
                            active_speed_upgrade = "slow_20"
                            speed_upgrade_end = pygame.time.get_ticks() + 30000
                            new_interval = int(base_move_interval * 1.2)
                            pygame.time.set_timer(MOVE_EVENT, new_interval)
                        elif effect == "slow_50":
                            active_speed_upgrade = "slow_50"
                            speed_upgrade_end = pygame.time.get_ticks() + 30000
                            new_interval = int(base_move_interval * 1.5)
                            pygame.time.set_timer(MOVE_EVENT, new_interval)
                        elif effect == "shorten_5":
                            if len(snake) > 5:
                                snake = snake[:-5]
                        elif effect == "shorten_10":
                            if len(snake) > 10:
                                snake = snake[:-10]
                        elif effect == "wall_pass":
                            allow_wrap = True
                    break

    # Check if a slowing upgrade has expired.
    if active_speed_upgrade and pygame.time.get_ticks() > speed_upgrade_end:
        active_speed_upgrade = None
        pygame.time.set_timer(MOVE_EVENT, base_move_interval)

    # Fill background with light color
    screen.fill(BACKGROUND_COLOR)

    # Draw application menu button for difficulty selection.
    difficulty_text = "Difficulty: Hard" if config_is_hard else "Difficulty: Easy"
    pygame.draw.rect(screen, (200,200,200), app_menu_difficulty_rect)
    diff_text_surface = font.render(difficulty_text, True, (0,0,0))
    screen.blit(diff_text_surface, (app_menu_difficulty_rect.x + 5, app_menu_difficulty_rect.y + 5))

    # Draw grid boundary with same color as obstacles
    boundary_rect = pygame.Rect(0, 0, grid_width * CELL_SIZE, grid_height * CELL_SIZE)
    pygame.draw.rect(screen, OBSTACLE_COLOR, boundary_rect, 4)  # Increased thickness to 4

    # Update and draw water ripple effects.
    for ripple in ripples[:]:
        ripple["radius"] += 2
        ripple["alpha"] = max(0, ripple["alpha"] - 5)
        temp_surface = pygame.Surface((ripple["max_radius"]*2, ripple["max_radius"]*2), pygame.SRCALPHA)
        pygame.draw.circle(temp_surface, (0, 191, 255, ripple["alpha"]),
                         (ripple["max_radius"], ripple["max_radius"]), int(ripple["radius"]), 2)
        screen.blit(temp_surface, (ripple["center"][0] - ripple["max_radius"],
                                   ripple["center"][1] - ripple["max_radius"]))
        if ripple["radius"] >= ripple["max_radius"]:
            ripples.remove(ripple)

    # Update and draw "Yum" messages.
    for yum in yum_messages[:]:
        # Update the lifetime and fade out.
        yum["lifetime"] -= 1
        yum["alpha"] = max(0, yum["alpha"] - 5)
        # Optionally move the message upward slightly.
        yum["center"] = (yum["center"][0], yum["center"][1] - 1)
        # Render "Yum" text using the upgrade_font.
        yum_surface = upgrade_font.render("Yum", True, SCORE_TEXT_COLOR)
        yum_surface.set_alpha(yum["alpha"])
        screen.blit(yum_surface, (yum["center"][0] - yum_surface.get_width()//2,
                                  yum["center"][1] - yum_surface.get_height()//2))
        if yum["lifetime"] <= 0 or yum["alpha"] <= 0:
            yum_messages.remove(yum)

    # Draw cookie as a circle with dots.
    cookie_center = (cookie[0]*CELL_SIZE + CELL_SIZE//2, cookie[1]*CELL_SIZE + CELL_SIZE//2)
    pygame.draw.circle(screen, COOKIE_COLOR, cookie_center, CELL_SIZE//2 - 2)
    # Draw two small dots on the cookie.
    COOKIE_DOT_COLOR = (139,69,19)
    pygame.draw.circle(screen, COOKIE_DOT_COLOR, (cookie_center[0] - 4, cookie_center[1] - 4), 2)
    pygame.draw.circle(screen, COOKIE_DOT_COLOR, (cookie_center[0] + 4, cookie_center[1] - 4), 2)

    # Draw obstacles.
    for obs in obstacles:
        obs_rect = pygame.Rect(obs[0] * CELL_SIZE, obs[1] * CELL_SIZE, CELL_SIZE, CELL_SIZE)
        pygame.draw.rect(screen, OBSTACLE_COLOR, obs_rect)

    # Draw continuous snake.
    if len(snake) > 0:
        snake_thickness = int(CELL_SIZE * 0.6)
        # Compute center positions for each snake segment.
        centers = [(seg[0]*CELL_SIZE + CELL_SIZE//2, seg[1]*CELL_SIZE + CELL_SIZE//2) for seg in snake]

        # Draw continuous body using a polyline.
        if len(centers) > 1:
            pygame.draw.lines(screen, SNAKE_COLOR, False, centers, snake_thickness)
            # For each internal point, check for a turn and add a round join.
            for i in range(1, len(centers)-1):
                # Compute vectors from the previous segment to current and from current to next segment.
                prev = centers[i-1]
                curr = centers[i]
                nex = centers[i+1]
                v1 = (curr[0]-prev[0], curr[1]-prev[1])
                v2 = (nex[0]-curr[0], nex[1]-curr[1])
                # If the cross product of v1 and v2 is non-zero, there is a turn.
                if (v1[0]*v2[1] - v1[1]*v2[0]) != 0:
                    pygame.draw.circle(screen, SNAKE_COLOR, curr, snake_thickness//2)
        else:
            pygame.draw.circle(screen, SNAKE_COLOR, centers[0], snake_thickness//2)

        # Draw head as a rounded circle with two eye dots.
        head_center = centers[0]
        pygame.draw.circle(screen, SNAKE_COLOR, head_center, snake_thickness//2)
        DOT_COLOR = (255, 255, 255)
        if direction == (1, 0):
            eye1 = (head_center[0] + snake_thickness//4, head_center[1] - snake_thickness//4)
            eye2 = (head_center[0] + snake_thickness//4, head_center[1] + snake_thickness//4)
        elif direction == (-1, 0):
            eye1 = (head_center[0] - snake_thickness//4, head_center[1] - snake_thickness//4)
            eye2 = (head_center[0] - snake_thickness//4, head_center[1] + snake_thickness//4)
        elif direction == (0, -1):
            eye1 = (head_center[0] - snake_thickness//4, head_center[1] - snake_thickness//4)
            eye2 = (head_center[0] + snake_thickness//4, head_center[1] - snake_thickness//4)
        elif direction == (0, 1):
            eye1 = (head_center[0] - snake_thickness//4, head_center[1] + snake_thickness//4)
            eye2 = (head_center[0] + snake_thickness//4, head_center[1] + snake_thickness//4)
        else:
            eye1 = head_center
            eye2 = head_center
        pygame.draw.circle(screen, DOT_COLOR, eye1, 2)
        pygame.draw.circle(screen, DOT_COLOR, eye2, 2)

        # Cap the tail with a rounded circle.
        tail_center = centers[-1]
        pygame.draw.circle(screen, SNAKE_COLOR, tail_center, snake_thickness//2)

    # Display Cookies Eaten and snake Length centered at the top.
    cur_width = screen.get_width()
    info_text = "Cookies: " + str(score) + " | Length: " + str(len(snake))
    info_surface = font.render(info_text, True, SCORE_TEXT_COLOR)
    screen.blit(info_surface, (cur_width // 2 - info_surface.get_width() // 2, 10))

    # Draw active purchased upgrade icons in the top-right corner.
    upg_x = cur_width - 60
    upg_y = 10
    for upg in purchased_upgrades[:]:
         if pygame.time.get_ticks() > upg["expire"]:
             purchased_upgrades.remove(upg)
         else:
             icon_rect = pygame.Rect(upg_x, upg_y, 40, 40)
             pygame.draw.ellipse(screen, upg["color"], icon_rect)
             upg_y += 50

    # Display overlay messages based on game state.
    cur_width = screen.get_width()
    cur_height = screen.get_height()
    if game_state == "start":
        start_surface = upgrade_font.render("Press SPACE to start", True, SCORE_TEXT_COLOR)
        screen.blit(start_surface, (cur_width // 2 - start_surface.get_width() // 2, cur_height // 2 - 50))
    elif game_state == "paused":
        paused_surface = upgrade_font.render("Paused", True, SCORE_TEXT_COLOR)
        instructions = font.render("SHORT: Resume | MEDIUM: Restart | LONG: Quit", True, SCORE_TEXT_COLOR)
        screen.blit(paused_surface, (cur_width // 2 - paused_surface.get_width() // 2, cur_height // 2 - 70))
        screen.blit(instructions, (cur_width // 2 - instructions.get_width() // 2, cur_height // 2 - 30))
    elif game_state == "gameover":
        over_surface = upgrade_font.render("Game Over", True, SCORE_TEXT_COLOR)
        instructions = font.render("SHORT/MEDIUM: Restart | LONG: Quit", True, SCORE_TEXT_COLOR)
        screen.blit(over_surface, (cur_width // 2 - over_surface.get_width() // 2, cur_height // 2 - 70))
        screen.blit(instructions, (cur_width // 2 - instructions.get_width() // 2, cur_height // 2 - 30))

    # If upgrade menu is open, display its instructions below the game state overlay.
    if upgrade_menu:
        upgrade_text = upgrade_font.render("Upgrade Menu", True, UPGRADE_TEXT_COLOR)
        screen.blit(upgrade_text, (cur_width // 2 - upgrade_text.get_width() // 2, cur_height // 2 + 20))
        # Draw upgrade icons.
        num_upgrades = len(upgrades)
        icon_size = 50
        spacing = 20
        total_width = num_upgrades * icon_size + (num_upgrades - 1) * spacing
        start_x = cur_width // 2 - total_width // 2
        for i, upg in enumerate(upgrades):
            rect = pygame.Rect(start_x + i*(icon_size + spacing), cur_height // 2 + 100, icon_size, icon_size)
            if score < upg["cost"]:
                # Draw grayed-out icon if not enough cookies.
                gray_color = (upg["color"][0]//2, upg["color"][1]//2, upg["color"][2]//2)
                pygame.draw.ellipse(screen, gray_color, rect)
            else:
                pygame.draw.ellipse(screen, upg["color"], rect)
            cost_text = font.render(str(upg["cost"]), True, SCORE_TEXT_COLOR)
            screen.blit(cost_text, (rect.centerx - cost_text.get_width()//2, rect.bottom))
        instruction = font.render("Click on an upgrade to buy it.", True, UPGRADE_TEXT_COLOR)
        screen.blit(instruction, (cur_width // 2 - instruction.get_width() // 2, cur_height // 2 + 170))

    # If the game is over and the game over sound has not been played, play it.
    if game_state == "gameover" and not game_over_sound_played:
        pygame.mixer.music.play()
        game_over_sound_played = True

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit() 