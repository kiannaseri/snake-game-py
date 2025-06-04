import pygame
import random
import time
import sys
import json
import os
from pygame import mixer
import math
import numpy as np

# Initialize pygame
pygame.init()
mixer.init()

# Game constants
WINDOW_WIDTH, WINDOW_HEIGHT = 800, 700
GAME_WIDTH, GAME_HEIGHT = 600, 600
GRID_SIZE = 20
GRID_WIDTH = GAME_WIDTH // GRID_SIZE
GRID_HEIGHT = GAME_HEIGHT // GRID_SIZE

# Directions
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GOLD = (255, 215, 0)
PURPLE = (128, 0, 128)
BORDER_COLOR = (70, 70, 70)
ICE_COLOR = (200, 230, 255)
DARK_NIGHT = (10, 10, 30)
BUTTON_COLOR = (50, 50, 50)
BUTTON_HOVER = (70, 70, 70)
SPECIAL_FOOD_COLOR = (255, 100, 100)
PLAYER2_COLOR = (255, 165, 0)  # رنگ نارنجی برای بازیکن دوم
AI_COLOR = (0, 200, 200)  # رنگ فیروزه‌ای برای هوش مصنوعی
DISABLED_COLOR = (100, 100, 100)  # رنگ برای گزینه غیرفعال

# Game states
MENU = 0
PLAYING = 1
PAUSED = 2
GAME_OVER = 3
SETTINGS = 4
NAME_INPUT = 5  # حالت دریافت نام بازیکنان
AI_PLAYING = 6  # حالت تماشای بازی هوش مصنوعی

# Game modes
NORMAL = 0
DEAD_OF_NIGHT = 1
WINTER = 2
MULTIPLAYER = 3  # حالت چند نفره
AI_MODE = 4  # حالت هوش مصنوعی


class Button:
    def __init__(self, x, y, width, height, text, font, color=BUTTON_COLOR, hover_color=BUTTON_HOVER, enabled=True):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color if enabled else DISABLED_COLOR
        self.hover_color = hover_color if enabled else DISABLED_COLOR
        self.is_hovered = False
        self.enabled = enabled

    def draw(self, surface):
        color = self.hover_color if (self.is_hovered and self.enabled) else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)

        text_surf = self.font.render(self.text, True, WHITE if self.enabled else (150, 150, 150))
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos) and self.enabled
        return self.is_hovered

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos) and self.enabled
        return False


class TextInputBox:
    def __init__(self, x, y, width, height, font, text=''):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = BUTTON_COLOR
        self.text = text
        self.font = font
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                if len(self.text) < 12:  # محدودیت طول نام
                    self.text += event.unicode
        return False

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)

        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)


class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Ultimate Snake Game")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont('Arial', 48, bold=True)
        self.font_medium = pygame.font.SysFont('Arial', 32)
        self.font_small = pygame.font.SysFont('Arial', 24)

        # Game positioning
        self.game_x = (WINDOW_WIDTH - GAME_WIDTH) // 2
        self.game_y = (WINDOW_HEIGHT - GAME_HEIGHT) // 2 + 20

        # Game state
        self.state = MENU
        self.difficulty = "MEDIUM"  # EASY/MEDIUM/HARD
        self.snake_color = GREEN
        self.high_score = 0
        self.load_high_score()
        self.game_mode = NORMAL
        self.flashlight_radius = 5
        self.slip_chance = 0.3
        self.special_food = None
        self.special_food_timer = 0
        self.player_names = ["Player 1", "Player 2"]  # نام‌های پیش‌فرض بازیکنان
        self.name_inputs = [
            TextInputBox(WINDOW_WIDTH // 2 - 150, 250, 300, 50, self.font_medium),
            TextInputBox(WINDOW_WIDTH // 2 - 150, 350, 300, 50, self.font_medium)
        ]
        self.current_input = 0
        self.ai_active = False  # آیا حالت هوش مصنوعی فعال است؟

        # Game Over buttons
        button_width = 200
        button_height = 50
        self.restart_button = Button(
            WINDOW_WIDTH // 2 - button_width - 20,
            WINDOW_HEIGHT // 2 + 150,
            button_width, button_height,
            "Restart", self.font_medium
        )
        self.menu_button = Button(
            WINDOW_WIDTH // 2 + 20,
            WINDOW_HEIGHT // 2 + 150,
            button_width, button_height,
            "Main Menu", self.font_medium
        )
        self.ai_button = Button(
            WINDOW_WIDTH // 2 - button_width // 2,
            WINDOW_HEIGHT // 2 + 220,
            button_width, button_height,
            "Watch AI", self.font_medium
        )

        # Initialize sound system with dummy sounds
        self.sounds = {
            'eat': self.create_beep_sound(440, 0.2),
            'crash': self.create_beep_sound(220, 0.5),
            'click': self.create_beep_sound(660, 0.1),
            'slip': self.create_beep_sound(330, 0.3),
            'special': self.create_beep_sound(880, 0.3)
        }

        # Initialize game elements
        self.reset_game()

    def create_beep_sound(self, frequency, duration):
        """Generate simple beep sounds programmatically"""
        sample_rate = 44100
        samples = int(duration * sample_rate)
        buffer = numpy.zeros((samples, 2), dtype=numpy.int16)

        for s in range(samples):
            t = float(s) / sample_rate
            val = int(32767 * math.sin(2 * math.pi * frequency * t))
            buffer[s][0] = val  # Left channel
            buffer[s][1] = val  # Right channel

        sound = pygame.mixer.Sound(buffer)
        return sound

    def reset_game(self):
        # Snake for player 1
        self.snake = [(GRID_WIDTH // 3, GRID_HEIGHT // 2)]
        self.direction = RIGHT
        self.next_direction = RIGHT

        # Snake for player 2 or AI
        if self.game_mode == MULTIPLAYER:
            self.snake2 = [(GRID_WIDTH * 2 // 3, GRID_HEIGHT // 2)]
            self.direction2 = LEFT
            self.next_direction2 = LEFT
        elif self.game_mode == AI_MODE:
            self.snake2 = [(GRID_WIDTH * 2 // 3, GRID_HEIGHT // 2)]
            self.direction2 = LEFT
            self.next_direction2 = LEFT
        else:
            self.snake2 = []

        self.obstacles = self.create_obstacles()
        self.food = self.create_food()
        self.special_food = None
        self.special_food_timer = 0
        self.score = 0
        self.score2 = 0 if self.game_mode in [MULTIPLAYER, AI_MODE] else 0
        self.game_over = False
        self.paused = False
        self.speed = self.get_speed()
        self.base_speed = self.speed
        self.last_move = time.time()
        self.last_ai_move = time.time()
        self.particles = []
        self.ice_blocks = []
        self.slipping = False

        # Initialize ice blocks for WINTER mode
        if self.game_mode == WINTER:
            self.ice_blocks = self.create_ice_blocks(10)

        # Difficulty settings
        if self.difficulty == "EASY":
            self.obstacles = []
            self.speed = 8
            self.base_speed = 8
        elif self.difficulty == "HARD":
            self.speed = 15
            self.base_speed = 15
            self.obstacles = self.create_obstacles(10)

    def ai_move(self):
        """هوش مصنوعی برای کنترل مار دوم"""
        if not self.snake2 or len(self.snake2) == 0:
            return

        head_x, head_y = self.snake2[0]
        food_x, food_y = self.food

        # مسیرهای ممکن
        possible_directions = []

        # چک کردن مسیرهای ممکن بدون برخورد
        for dir in [UP, DOWN, LEFT, RIGHT]:
            new_head = ((head_x + dir[0]) % GRID_WIDTH, (head_y + dir[1]) % GRID_HEIGHT)

            # جلوگیری از حرکت به عقب
            if (dir[0] * -1, dir[1] * -1) == self.direction2:
                continue

            # چک کردن برخورد با خودش
            if new_head in self.snake2[1:]:
                continue

            # چک کردن برخورد با موانع
            if new_head in self.obstacles:
                continue

            # چک کردن برخورد با دیوارها (در صورت غیر فعال بودن حالت عبور از دیوار)
            if (new_head[0] == 0 or new_head[0] == GRID_WIDTH - 1 or
                    new_head[1] == 0 or new_head[1] == GRID_HEIGHT - 1):
                continue

            possible_directions.append(dir)

        if not possible_directions:
            return  # اگر هیچ مسیری ایمن نبود، همان جهت را ادامه دهد

        # انتخاب مسیری که به غذا نزدیکتر می‌شود
        best_dir = possible_directions[0]
        min_distance = float('inf')

        for dir in possible_directions:
            new_head = ((head_x + dir[0]) % GRID_WIDTH, (head_y + dir[1]) % GRID_HEIGHT)
            dist = abs(new_head[0] - food_x) + abs(new_head[1] - food_y)  # فاصله منهتن

            if dist < min_distance:
                min_distance = dist
                best_dir = dir

        self.next_direction2 = best_dir

    def create_ice_blocks(self, count=5):
        ice_blocks = []
        for _ in range(count):
            while True:
                ice = (random.randint(1, GRID_WIDTH - 2),
                       random.randint(1, GRID_HEIGHT - 2))
                if (ice not in self.snake and
                        ice not in self.obstacles and
                        ice != self.food and
                        (not hasattr(self, 'snake2') or ice not in self.snake2)):
                    ice_blocks.append(ice)
                    break
        return ice_blocks

    def get_speed(self):
        if self.difficulty == "EASY": return 8
        if self.difficulty == "MEDIUM": return 12
        return 15

    def create_food(self):
        while True:
            food = (random.randint(1, GRID_WIDTH - 2),
                    random.randint(1, GRID_HEIGHT - 2))
            if (food not in self.snake and
                    food not in self.obstacles and
                    (self.game_mode != WINTER or food not in self.ice_blocks) and
                    food != self.special_food and
                    (not hasattr(self, 'snake2') or food not in self.snake2)):
                return food

    def create_special_food(self):
        while True:
            food = (random.randint(1, GRID_WIDTH - 2),
                    random.randint(1, GRID_HEIGHT - 2))
            if (food not in self.snake and
                    food not in self.obstacles and
                    (self.game_mode != WINTER or food not in self.ice_blocks) and
                    food != self.food and
                    (not hasattr(self, 'snake2') or food not in self.snake2)):
                return food

    def create_obstacles(self, count=5):
        obstacles = []
        for _ in range(count):
            while True:
                obstacle = (random.randint(1, GRID_WIDTH - 2),
                            random.randint(1, GRID_HEIGHT - 2))
                if obstacle not in self.snake and (not hasattr(self, 'snake2') or obstacle not in self.snake2):
                    obstacles.append(obstacle)
                    break
        return obstacles

    def load_high_score(self):
        try:
            with open('highscore.dat', 'r') as f:
                self.high_score = int(f.read())
        except:
            self.high_score = 0

    def save_high_score(self):
        with open('highscore.dat', 'w') as f:
            f.write(str(self.high_score))

    def save_game(self):
        game_state = {
            "snake": self.snake,
            "snake2": self.snake2 if hasattr(self, 'snake2') else [],
            "direction": self.direction,
            "direction2": self.direction2 if hasattr(self, 'direction2') else RIGHT,
            "food": self.food,
            "special_food": self.special_food,
            "obstacles": self.obstacles,
            "score": self.score,
            "score2": self.score2 if hasattr(self, 'score2') else 0,
            "difficulty": self.difficulty,
            "speed": self.speed,
            "base_speed": self.base_speed,
            "game_mode": self.game_mode,
            "player_names": self.player_names,
            "ai_active": self.ai_active
        }

        try:
            with open('snake_save.json', 'w') as f:
                json.dump(game_state, f)
            return True
        except:
            return False

    def load_game(self):
        try:
            with open('snake_save.json', 'r') as f:
                data = json.load(f)

            self.snake = [tuple(pos) for pos in data["snake"]]
            self.snake2 = [tuple(pos) for pos in data.get("snake2", [])]
            self.direction = tuple(data["direction"])
            self.direction2 = tuple(data.get("direction2", LEFT))
            self.next_direction = tuple(data["direction"])
            self.next_direction2 = tuple(data.get("direction2", LEFT))
            self.food = tuple(data["food"])
            self.special_food = tuple(data["special_food"]) if data["special_food"] else None
            self.obstacles = [tuple(obs) for obs in data["obstacles"]]
            self.score = data["score"]
            self.score2 = data.get("score2", 0)
            self.difficulty = data["difficulty"]
            self.speed = data["speed"]
            self.base_speed = data.get("base_speed", self.speed)
            self.game_mode = data.get("game_mode", NORMAL)
            self.player_names = data.get("player_names", ["Player 1", "Player 2"])
            self.ai_active = data.get("ai_active", False)
            self.state = PLAYING
            return True
        except:
            return False

    def add_particles(self, pos, color, count=5):
        for _ in range(count):
            self.particles.append({
                'pos': [pos[0] * GRID_SIZE + self.game_x,
                        pos[1] * GRID_SIZE + self.game_y],
                'color': color,
                'size': random.randint(2, 5),
                'speed': [random.uniform(-2, 2), random.uniform(-2, 2)],
                'life': 30
            })

    def update_particles(self):
        for p in self.particles[:]:
            p['pos'][0] += p['speed'][0]
            p['pos'][1] += p['speed'][1]
            p['life'] -= 1
            if p['life'] <= 0:
                self.particles.remove(p)

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if self.state == PLAYING and not self.game_over:
                    # Player 1 controls (WASD)
                    if event.key == pygame.K_w:
                        if self.direction != DOWN:
                            self.next_direction = UP
                    elif event.key == pygame.K_s:
                        if self.direction != UP:
                            self.next_direction = DOWN
                    elif event.key == pygame.K_a:
                        if self.direction != RIGHT:
                            self.next_direction = LEFT
                    elif event.key == pygame.K_d:
                        if self.direction != LEFT:
                            self.next_direction = RIGHT

                    # Player 2 controls (Arrow keys) - only in MULTIPLAYER mode
                    if self.game_mode == MULTIPLAYER and not self.ai_active:
                        if event.key == pygame.K_UP:
                            if self.direction2 != DOWN:
                                self.next_direction2 = UP
                        elif event.key == pygame.K_DOWN:
                            if self.direction2 != UP:
                                self.next_direction2 = DOWN
                        elif event.key == pygame.K_LEFT:
                            if self.direction2 != RIGHT:
                                self.next_direction2 = LEFT
                        elif event.key == pygame.K_RIGHT:
                            if self.direction2 != LEFT:
                                self.next_direction2 = RIGHT

                    # Common controls
                    if event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                        self.sounds['click'].play()
                    elif event.key == pygame.K_p:
                        if self.save_game():
                            self.sounds['click'].play()
                    elif event.key == pygame.K_l:
                        if self.load_game():
                            self.sounds['click'].play()

                elif self.state == MENU:
                    if event.key == pygame.K_1:
                        self.difficulty = "EASY"
                        self.state = PLAYING
                        self.reset_game()
                        self.sounds['click'].play()
                    elif event.key == pygame.K_2:
                        self.difficulty = "MEDIUM"
                        self.state = PLAYING
                        self.reset_game()
                        self.sounds['click'].play()
                    elif event.key == pygame.K_3:
                        self.difficulty = "HARD"
                        self.state = PLAYING
                        self.reset_game()
                        self.sounds['click'].play()
                    elif event.key == pygame.K_s:
                        self.state = SETTINGS
                        self.sounds['click'].play()

                elif self.state == SETTINGS:
                    if event.key == pygame.K_ESCAPE:
                        self.state = MENU
                        self.sounds['click'].play()
                    elif event.key == pygame.K_1:
                        self.snake_color = GREEN
                        self.sounds['click'].play()
                    elif event.key == pygame.K_2:
                        self.snake_color = GOLD
                        self.sounds['click'].play()
                    elif event.key == pygame.K_3:
                        self.snake_color = PURPLE
                        self.sounds['click'].play()
                    elif event.key == pygame.K_4:
                        self.game_mode = NORMAL
                        self.ai_active = False
                        self.sounds['click'].play()
                    elif event.key == pygame.K_5:
                        self.game_mode = DEAD_OF_NIGHT
                        self.ai_active = False
                        self.sounds['click'].play()
                    elif event.key == pygame.K_6:
                        self.game_mode = WINTER
                        self.ai_active = False
                        self.sounds['click'].play()
                    elif event.key == pygame.K_7 and not self.ai_active:  # فقط اگر هوش مصنوعی فعال نباشد
                        self.game_mode = MULTIPLAYER
                        self.state = NAME_INPUT
                        self.sounds['click'].play()
                    elif event.key == pygame.K_8:
                        self.game_mode = AI_MODE
                        self.ai_active = True
                        self.state = AI_PLAYING
                        self.reset_game()
                        self.sounds['click'].play()

                elif self.state == NAME_INPUT:
                    if event.key == pygame.K_RETURN:
                        # ذخیره نام‌ها و شروع بازی
                        self.player_names[0] = self.name_inputs[0].text or "Player 1"
                        self.player_names[1] = self.name_inputs[1].text or "Player 2"
                        self.state = PLAYING
                        self.reset_game()
                        self.sounds['click'].play()
                    elif event.key == pygame.K_TAB:
                        # جابجایی بین فیلدهای ورودی
                        self.current_input = (self.current_input + 1) % 2
                    elif event.key == pygame.K_ESCAPE:
                        self.state = SETTINGS
                        self.sounds['click'].play()

                elif self.state == GAME_OVER:
                    if event.key == pygame.K_r:
                        self.state = PLAYING
                        self.reset_game()
                        self.sounds['click'].play()

                elif self.state == AI_PLAYING:
                    if event.key == pygame.K_ESCAPE:
                        self.state = SETTINGS
                        self.sounds['click'].play()

            elif event.type == pygame.MOUSEMOTION:
                if self.state == GAME_OVER:
                    self.restart_button.check_hover(mouse_pos)
                    self.menu_button.check_hover(mouse_pos)
                    if self.game_mode == AI_MODE:
                        self.ai_button.check_hover(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.state == GAME_OVER:
                    if self.restart_button.is_clicked(mouse_pos, event):
                        self.state = PLAYING
                        self.reset_game()
                        self.sounds['click'].play()
                    elif self.menu_button.is_clicked(mouse_pos, event):
                        self.state = MENU
                        self.sounds['click'].play()
                    elif self.game_mode == AI_MODE and self.ai_button.is_clicked(mouse_pos, event):
                        self.state = AI_PLAYING
                        self.reset_game()
                        self.sounds['click'].play()

            # Handle name input
            if self.state == NAME_INPUT:
                for i, input_box in enumerate(self.name_inputs):
                    if input_box.handle_event(event):
                        if i == 0:
                            self.current_input = 1
                        else:
                            self.player_names[0] = self.name_inputs[0].text or "Player 1"
                            self.player_names[1] = self.name_inputs[1].text or "Player 2"
                            self.state = PLAYING
                            self.reset_game()
                            self.sounds['click'].play()

    def update(self):
        if self.state not in [PLAYING, AI_PLAYING] or self.paused or self.game_over:
            return

        current_time = time.time()

        # حرکت هوش مصنوعی با سرعت کمتر برای قابل مشاهده بودن
        if (self.state == AI_PLAYING or (
                self.game_mode == MULTIPLAYER and self.ai_active)) and current_time - self.last_ai_move > 0.2:
            self.ai_move()
            self.last_ai_move = current_time

        if current_time - self.last_move < 1.0 / self.speed:
            return

        self.last_move = current_time

        # Handle slipping in WINTER mode
        if self.game_mode == WINTER and not self.slipping:
            head = self.snake[0]
            if head in self.ice_blocks and random.random() < self.slip_chance:
                self.slipping = True
                self.sounds['slip'].play()
                # Continue in same direction when slipping
                self.next_direction = self.direction
            else:
                self.direction = self.next_direction
        else:
            if self.slipping:
                self.slipping = False
            self.direction = self.next_direction

        # Generate special food randomly (5% chance every move)
        if self.special_food is None and random.random() < 0.05:
            self.special_food = self.create_special_food()
            self.special_food_timer = time.time()

        # Remove special food after 10 seconds if not eaten
        if (self.special_food and
                time.time() - self.special_food_timer > 10):
            self.special_food = None

        # Move player 1 snake
        head_x, head_y = self.snake[0]
        dir_x, dir_y = self.direction
        new_head = ((head_x + dir_x) % GRID_WIDTH,
                    (head_y + dir_y) % GRID_HEIGHT)

        # Move player 2 or AI snake
        if self.game_mode in [MULTIPLAYER, AI_MODE]:
            head2_x, head2_y = self.snake2[0]
            dir2_x, dir2_y = self.direction2
            new_head2 = ((head2_x + dir2_x) % GRID_WIDTH,
                         (head2_y + dir2_y) % GRID_HEIGHT)
            self.direction2 = self.next_direction2

        # Check collisions for player 1
        player1_collision = (
                new_head in self.snake[1:] or
                new_head in self.obstacles or
                new_head[0] == 0 or new_head[0] == GRID_WIDTH - 1 or
                new_head[1] == 0 or new_head[1] == GRID_HEIGHT - 1 or
                (self.game_mode in [MULTIPLAYER, AI_MODE] and new_head in self.snake2)
        )

        # Check collisions for player 2 or AI
        player2_collision = False
        if self.game_mode in [MULTIPLAYER, AI_MODE]:
            player2_collision = (
                    new_head2 in self.snake2[1:] or
                    new_head2 in self.obstacles or
                    new_head2[0] == 0 or new_head2[0] == GRID_WIDTH - 1 or
                    new_head2[1] == 0 or new_head2[1] == GRID_HEIGHT - 1 or
                    new_head2 in self.snake
            )

        # Handle game over conditions
        if player1_collision or (self.game_mode in [MULTIPLAYER, AI_MODE] and player2_collision):
            self.game_over = True
            self.state = GAME_OVER
            max_score = max(self.score, self.score2 if self.game_mode in [MULTIPLAYER, AI_MODE] else 0)
            if max_score > self.high_score:
                self.high_score = max_score
                self.save_high_score()
            self.sounds['crash'].play()
            if player1_collision:
                self.add_particles(new_head, RED, 15)
            if self.game_mode in [MULTIPLAYER, AI_MODE] and player2_collision:
                self.add_particles(new_head2, RED, 15)
            return

        # Update player 1 snake position
        self.snake.insert(0, new_head)

        # Update player 2 or AI snake position
        if self.game_mode in [MULTIPLAYER, AI_MODE]:
            self.snake2.insert(0, new_head2)

        # Check if food eaten by player 1
        if new_head == self.food:
            self.score += 10
            self.sounds['eat'].play()
            self.add_particles(new_head, GOLD, 8)
            self.food = self.create_food()

            # Increase speed every 3 foods
            if self.score % 30 == 0 and self.base_speed < 20:
                self.base_speed += 1
                self.speed = self.base_speed
        elif new_head == self.special_food:
            self.score += 20
            self.sounds['special'].play()
            self.add_particles(new_head, SPECIAL_FOOD_COLOR, 12)
            self.special_food = None

            # Decrease speed when eating special food
            if self.speed > 5:
                self.speed -= 1
        else:
            self.snake.pop()

        # Check if food eaten by player 2 or AI
        if self.game_mode in [MULTIPLAYER, AI_MODE]:
            if new_head2 == self.food:
                self.score2 += 10
                self.sounds['eat'].play()
                self.add_particles(new_head2, GOLD, 8)
                self.food = self.create_food()

                # Increase speed every 3 foods (for both players)
                if self.score2 % 30 == 0 and self.base_speed < 20:
                    self.base_speed += 1
                    self.speed = self.base_speed
            elif new_head2 == self.special_food:
                self.score2 += 20
                self.sounds['special'].play()
                self.add_particles(new_head2, SPECIAL_FOOD_COLOR, 12)
                self.special_food = None

                # Decrease speed when eating special food
                if self.speed > 5:
                    self.speed -= 1
            else:
                self.snake2.pop()

        self.update_particles()

    def draw_menu(self):
        self.screen.fill(BLACK)

        # Title
        title = self.font_large.render("ULTIMATE SNAKE GAME", True, GREEN)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 100))

        # Difficulty options
        easy = self.font_medium.render("1. Easy Mode", True, WHITE)
        medium = self.font_medium.render("2. Medium Mode", True, WHITE)
        hard = self.font_medium.render("3. Hard Mode", True, WHITE)
        settings = self.font_medium.render("S. Settings", True, WHITE)

        self.screen.blit(easy, (WINDOW_WIDTH // 2 - easy.get_width() // 2, 250))
        self.screen.blit(medium, (WINDOW_WIDTH // 2 - medium.get_width() // 2, 300))
        self.screen.blit(hard, (WINDOW_WIDTH // 2 - hard.get_width() // 2, 350))
        self.screen.blit(settings, (WINDOW_WIDTH // 2 - settings.get_width() // 2, 400))

        # High score
        hs_text = self.font_small.render(f"High Score: {self.high_score}", True, GOLD)
        self.screen.blit(hs_text, (WINDOW_WIDTH // 2 - hs_text.get_width() // 2, 500))

    def draw_settings(self):
        self.screen.fill(BLACK)

        title = self.font_large.render("SETTINGS", True, BLUE)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 100))

        # Snake color options
        green = self.font_medium.render("1. Green Snake", True, GREEN)
        gold = self.font_medium.render("2. Gold Snake", True, GOLD)
        purple = self.font_medium.render("3. Purple Snake", True, PURPLE)

        # Game mode options
        normal_mode = self.font_medium.render("4. Normal Mode", True, WHITE)
        night_mode = self.font_medium.render("5. Dead of Night", True, (100, 100, 255))
        winter_mode = self.font_medium.render("6. Winter Mode", True, ICE_COLOR)
        multiplayer_mode = self.font_medium.render("7. Multiplayer", True,
                                                   PLAYER2_COLOR if not self.ai_active else DISABLED_COLOR)
        ai_mode = self.font_medium.render("8. AI Mode", True, AI_COLOR)

        back = self.font_medium.render("ESC. Back to Menu", True, WHITE)

        self.screen.blit(green, (WINDOW_WIDTH // 2 - green.get_width() // 2, 200))
        self.screen.blit(gold, (WINDOW_WIDTH // 2 - gold.get_width() // 2, 250))
        self.screen.blit(purple, (WINDOW_WIDTH // 2 - purple.get_width() // 2, 300))
        self.screen.blit(normal_mode, (WINDOW_WIDTH // 2 - normal_mode.get_width() // 2, 350))
        self.screen.blit(night_mode, (WINDOW_WIDTH // 2 - night_mode.get_width() // 2, 400))
        self.screen.blit(winter_mode, (WINDOW_WIDTH // 2 - winter_mode.get_width() // 2, 450))
        self.screen.blit(multiplayer_mode, (WINDOW_WIDTH // 2 - multiplayer_mode.get_width() // 2, 500))
        self.screen.blit(ai_mode, (WINDOW_WIDTH // 2 - ai_mode.get_width() // 2, 550))
        self.screen.blit(back, (WINDOW_WIDTH // 2 - back.get_width() // 2, 620))

    def draw_name_input(self):
        self.screen.fill(BLACK)

        title = self.font_large.render("ENTER PLAYER NAMES", True, BLUE)
        self.screen.blit(title, (WINDOW_WIDTH // 2 - title.get_width() // 2, 100))

        player1_text = self.font_medium.render("Player 1 Name:", True, WHITE)
        player2_text = self.font_medium.render("Player 2 Name:", True, PLAYER2_COLOR)
        hint_text = self.font_small.render("Press TAB to switch, ENTER to confirm", True, WHITE)

        self.screen.blit(player1_text, (WINDOW_WIDTH // 2 - 200, 200))
        self.screen.blit(player2_text, (WINDOW_WIDTH // 2 - 200, 300))
        self.screen.blit(hint_text, (WINDOW_WIDTH // 2 - hint_text.get_width() // 2, 450))

        # Draw input boxes with highlight for active one
        for i, input_box in enumerate(self.name_inputs):
            input_box.color = (100, 100, 100) if i == self.current_input else BUTTON_COLOR
            input_box.draw(self.screen)

    def draw_game(self):
        # Background
        if self.game_mode == DEAD_OF_NIGHT:
            self.screen.fill(DARK_NIGHT)
        else:
            self.screen.fill(BLACK)

        # Game border with 3D effect
        border = pygame.Rect(self.game_x - 10, self.game_y - 10,
                             GAME_WIDTH + 20, GAME_HEIGHT + 20)
        pygame.draw.rect(self.screen, BORDER_COLOR, border)
        pygame.draw.rect(self.screen, (100, 100, 100), border, 3)

        # Game area
        game_area = pygame.Rect(self.game_x, self.game_y, GAME_WIDTH, GAME_HEIGHT)
        if self.game_mode == DEAD_OF_NIGHT:
            pygame.draw.rect(self.screen, DARK_NIGHT, game_area)
        else:
            pygame.draw.rect(self.screen, BLACK, game_area)

        # Draw obstacles
        for obs in self.obstacles:
            rect = pygame.Rect(
                self.game_x + obs[0] * GRID_SIZE,
                self.game_y + obs[1] * GRID_SIZE,
                GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(self.screen, BLUE, rect)
            pygame.draw.rect(self.screen, (0, 0, 100), rect, 2)

        # Draw ice blocks for WINTER mode
        if self.game_mode == WINTER:
            for ice in self.ice_blocks:
                rect = pygame.Rect(
                    self.game_x + ice[0] * GRID_SIZE,
                    self.game_y + ice[1] * GRID_SIZE,
                    GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(self.screen, ICE_COLOR, rect)
                pygame.draw.rect(self.screen, (150, 200, 255), rect, 1)

                # Draw ice pattern
                for i in range(3):
                    offset = i * 3
                    pygame.draw.line(self.screen, (220, 240, 255),
                                     (rect.left + offset, rect.top + offset),
                                     (rect.left + offset, rect.bottom - offset), 1)
                    pygame.draw.line(self.screen, (220, 240, 255),
                                     (rect.left + offset, rect.top + offset),
                                     (rect.right - offset, rect.top + offset), 1)

        # Draw food
        food_rect = pygame.Rect(
            self.game_x + self.food[0] * GRID_SIZE,
            self.game_y + self.food[1] * GRID_SIZE,
            GRID_SIZE, GRID_SIZE)
        pygame.draw.rect(self.screen, RED, food_rect)
        pygame.draw.rect(self.screen, (100, 0, 0), food_rect, 2)

        # Draw special food
        if self.special_food:
            food_rect = pygame.Rect(
                self.game_x + self.special_food[0] * GRID_SIZE,
                self.game_y + self.special_food[1] * GRID_SIZE,
                GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(self.screen, SPECIAL_FOOD_COLOR, food_rect)

            # Draw a star pattern on special food
            center_x = food_rect.centerx
            center_y = food_rect.centery
            radius = GRID_SIZE // 2 - 2

            # Draw a star
            points = []
            for i in range(5):
                angle = math.pi / 2 + 2 * math.pi * i / 5
                points.append((
                    center_x + radius * math.cos(angle),
                    center_y + radius * math.sin(angle)
                ))
                angle += math.pi / 5
                points.append((
                    center_x + radius * 0.4 * math.cos(angle),
                    center_y + radius * 0.4 * math.sin(angle)
                ))

            pygame.draw.polygon(self.screen, WHITE, points)
            pygame.draw.rect(self.screen, (150, 0, 0), food_rect, 2)

        # Draw snake with flashlight effect for DEAD_OF_NIGHT mode
        if self.game_mode == DEAD_OF_NIGHT:
            # Create a surface for the darkness
            darkness = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
            darkness.fill((0, 0, 0, 220))  # Semi-transparent black

            # Draw the flashlight around the snake's head
            head = self.snake[0]
            center = (head[0] * GRID_SIZE + GRID_SIZE // 2,
                      head[1] * GRID_SIZE + GRID_SIZE // 2)
########################################################
            # Draw gradient circle for flashlight
            for radius in range(self.flashlight_radius * GRID_SIZE, 0, -10):
                alpha = min(255, radius * 2)
                pygame.draw.circle(darkness, (0, 0, 0, alpha), center, radius)

            self.screen.blit(darkness, (self.game_x, self.game_y))

        # Draw player 1 snake
        for i, segment in enumerate(self.snake):
            color = self.snake_color
            # Make head slightly different
            if i == 0:
                color = (min(self.snake_color[0] + 50, 255),
                         min(self.snake_color[1] + 50, 255),
                         min(self.snake_color[2] + 50, 255))

            segment_rect = pygame.Rect(
                self.game_x + segment[0] * GRID_SIZE,
                self.game_y + segment[1] * GRID_SIZE,
                GRID_SIZE, GRID_SIZE)
            pygame.draw.rect(self.screen, color, segment_rect)
            pygame.draw.rect(self.screen, BLACK, segment_rect, 1)

        # Draw player 2 or AI snake
        if self.game_mode in [MULTIPLAYER, AI_MODE]:
            snake_color = PLAYER2_COLOR if self.game_mode == MULTIPLAYER else AI_COLOR
            for i, segment in enumerate(self.snake2):
                color = snake_color
                # Make head slightly different
                if i == 0:
                    color = (min(snake_color[0] + 50, 255),
                             min(snake_color[1] + 50, 255),
                             min(snake_color[2] + 50, 255))

                segment_rect = pygame.Rect(
                    self.game_x + segment[0] * GRID_SIZE,
                    self.game_y + segment[1] * GRID_SIZE,
                    GRID_SIZE, GRID_SIZE)
                pygame.draw.rect(self.screen, color, segment_rect)
                pygame.draw.rect(self.screen, BLACK, segment_rect, 1)

        # Draw particles
        for p in self.particles:
            pygame.draw.circle(self.screen, p['color'],
                               (int(p['pos'][0]), int(p['pos'][1])),
                               p['size'])

        # Draw UI
        # Player 1 score
        score_text = self.font_medium.render(f"{self.player_names[0]}: {self.score}", True, self.snake_color)
        self.screen.blit(score_text, (20, 20))

        # Player 2 or AI score
        if self.game_mode == MULTIPLAYER:
            score2_text = self.font_medium.render(f"{self.player_names[1]}: {self.score2}", True, PLAYER2_COLOR)
            self.screen.blit(score2_text, (20, 60))
        elif self.game_mode == AI_MODE:
            score2_text = self.font_medium.render(f"AI: {self.score2}", True, AI_COLOR)
            self.screen.blit(score2_text, (20, 60))
        else:
            hs_text = self.font_small.render(f"High Score: {self.high_score}", True, GOLD)
            self.screen.blit(hs_text, (20, 60))

        diff_text = self.font_small.render(f"Difficulty: {self.difficulty}", True, WHITE)
        self.screen.blit(diff_text, (WINDOW_WIDTH - diff_text.get_width() - 20, 20))

        # Show current speed
        speed_text = self.font_small.render(f"Speed: {self.speed}", True, WHITE)
        self.screen.blit(speed_text, (WINDOW_WIDTH - speed_text.get_width() - 20, 100))

        # Show current mode
        if self.game_mode == DEAD_OF_NIGHT:
            mode_text = self.font_small.render("Mode: Dead of Night", True, (100, 100, 255))
        elif self.game_mode == WINTER:
            mode_text = self.font_small.render("Mode: Winter", True, ICE_COLOR)
        elif self.game_mode == MULTIPLAYER:
            mode_text = self.font_small.render("Mode: Multiplayer", True, PLAYER2_COLOR)
        elif self.game_mode == AI_MODE:
            mode_text = self.font_small.render("Mode: AI", True, AI_COLOR)
        else:
            mode_text = self.font_small.render("Mode: Normal", True, WHITE)
        self.screen.blit(mode_text, (WINDOW_WIDTH - mode_text.get_width() - 20, 60))

        # Pause text
        if self.paused:
            pause_text = self.font_large.render("PAUSED", True, WHITE)
            self.screen.blit(pause_text,
                             (WINDOW_WIDTH // 2 - pause_text.get_width() // 2,
                              WINDOW_HEIGHT // 2 - pause_text.get_height() // 2))

        # Controls help
        if self.game_mode == MULTIPLAYER:
            controls = self.font_small.render(
                f"{self.player_names[0]}: WASD | {self.player_names[1]}: Arrows | SPACE: Pause", True, WHITE)
        elif self.game_mode == AI_MODE:
            controls = self.font_small.render("WASD: Move | SPACE: Pause | ESC: Exit", True, WHITE)
        else:
            controls = self.font_small.render("WASD/Arrows: Move | SPACE: Pause | P: Save | L: Load", True, WHITE)
        self.screen.blit(controls, (WINDOW_WIDTH // 2 - controls.get_width() // 2, WINDOW_HEIGHT - 30))

    def draw_ai_playing(self):
        self.draw_game()

        # Dark overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        self.screen.blit(overlay, (0, 0))

        # AI playing text
        ai_text = self.font_large.render("AI IS PLAYING...", True, AI_COLOR)
        self.screen.blit(ai_text, (WINDOW_WIDTH // 2 - ai_text.get_width() // 2, 50))

        # Controls help
        controls = self.font_medium.render("Press ESC to return to settings", True, WHITE)
        self.screen.blit(controls, (WINDOW_WIDTH // 2 - controls.get_width() // 2, WINDOW_HEIGHT - 50))

    def draw_game_over(self):
        self.draw_game()

        # Dark overlay
        overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Game over text
        game_over = self.font_large.render("GAME OVER", True, RED)
        self.screen.blit(game_over,
                         (WINDOW_WIDTH // 2 - game_over.get_width() // 2,
                          WINDOW_HEIGHT // 2 - 100))

        # Score text
        if self.game_mode == MULTIPLAYER:
            score_text = self.font_medium.render(f"{self.player_names[0]}: {self.score}", True, self.snake_color)
            score2_text = self.font_medium.render(f"{self.player_names[1]}: {self.score2}", True, PLAYER2_COLOR)

            self.screen.blit(score_text,
                             (WINDOW_WIDTH // 2 - score_text.get_width() // 2,
                              WINDOW_HEIGHT // 2 - 30))
            self.screen.blit(score2_text,
                             (WINDOW_WIDTH // 2 - score2_text.get_width() // 2,
                              WINDOW_HEIGHT // 2 + 10))

            # Determine winner
            if self.score > self.score2:
                winner_text = self.font_medium.render(f"{self.player_names[0]} Wins!", True, self.snake_color)
            elif self.score2 > self.score:
                winner_text = self.font_medium.render(f"{self.player_names[1]} Wins!", True, PLAYER2_COLOR)
            else:
                winner_text = self.font_medium.render("It's a Tie!", True, WHITE)

            self.screen.blit(winner_text,
                             (WINDOW_WIDTH // 2 - winner_text.get_width() // 2,
                              WINDOW_HEIGHT // 2 + 50))
        elif self.game_mode == AI_MODE:
            score_text = self.font_medium.render(f"You: {self.score}", True, self.snake_color)
            score2_text = self.font_medium.render(f"AI: {self.score2}", True, AI_COLOR)

            self.screen.blit(score_text,
                             (WINDOW_WIDTH // 2 - score_text.get_width() // 2,
                              WINDOW_HEIGHT // 2 - 30))
            self.screen.blit(score2_text,
                             (WINDOW_WIDTH // 2 - score2_text.get_width() // 2,
                              WINDOW_HEIGHT // 2 + 10))

            # Determine winner
            if self.score > self.score2:
                winner_text = self.font_medium.render("You Win!", True, self.snake_color)
            elif self.score2 > self.score:
                winner_text = self.font_medium.render("AI Wins!", True, AI_COLOR)
            else:
                winner_text = self.font_medium.render("It's a Tie!", True, WHITE)

            self.screen.blit(winner_text,
                             (WINDOW_WIDTH // 2 - winner_text.get_width() // 2,
                              WINDOW_HEIGHT // 2 + 50))
        else:
            score_text = self.font_medium.render(f"Final Score: {self.score}", True, WHITE)
            self.screen.blit(score_text,
                             (WINDOW_WIDTH // 2 - score_text.get_width() // 2,
                              WINDOW_HEIGHT // 2 - 30))

            # High score text if new record
            if self.score == self.high_score and self.score > 0:
                hs_text = self.font_medium.render("NEW HIGH SCORE!", True, GOLD)
                self.screen.blit(hs_text,
                                 (WINDOW_WIDTH // 2 - hs_text.get_width() // 2,
                                  WINDOW_HEIGHT // 2 + 20))

        # Draw buttons
        self.restart_button.draw(self.screen)
        self.menu_button.draw(self.screen)

        # Add AI button in AI mode
        if self.game_mode == AI_MODE:
            self.ai_button.draw(self.screen)

    def draw(self):
        if self.state == MENU:
            self.draw_menu()
        elif self.state == SETTINGS:
            self.draw_settings()
        elif self.state == NAME_INPUT:
            self.draw_name_input()
        elif self.state == AI_PLAYING:
            self.draw_ai_playing()
        elif self.state == GAME_OVER:
            self.draw_game_over()
        else:
            self.draw_game()

        pygame.display.flip()

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(60)  # 60 FPS for smooth animations


if __name__ == "__main__":
    # We need numpy for sound generation
    try:
        import numpy
    except ImportError:
        print("Installing required numpy package...")
        import subprocess

        subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy"])
        import numpy

    game = SnakeGame()
    game.run()