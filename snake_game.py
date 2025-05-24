import pygame
import random
import time
import sys
import json
import os
from pygame import mixer
import math

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

# Game states
MENU = 0
PLAYING = 1
PAUSED = 2
GAME_OVER = 3
SETTINGS = 4

# Game modes
NORMAL = 0
DEAD_OF_NIGHT = 1
WINTER = 2


class Button:
    def __init__(self, x, y, width, height, text, font, color=BUTTON_COLOR, hover_color=BUTTON_HOVER):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=5)
        pygame.draw.rect(surface, WHITE, self.rect, 2, border_radius=5)

        text_surf = self.font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        return self.is_hovered

    def is_clicked(self, pos, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(pos)
        return False


class SnakeGame:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Premium Snake Game")
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
        self.game_mode = NORMAL  # NORMAL/DEAD_OF_NIGHT/WINTER
        self.flashlight_radius = 5  # For DEAD_OF_NIGHT mode
        self.slip_chance = 0.3  # For WINTER mode

        # Game Over buttons
        button_width = 200
        button_height = 50
        self.restart_button = Button(
            WINDOW_WIDTH // 2 - button_width - 20,
            WINDOW_HEIGHT // 2 + 100,
            button_width, button_height,
            "Restart", self.font_medium
        )
        self.menu_button = Button(
            WINDOW_WIDTH // 2 + 20,
            WINDOW_HEIGHT // 2 + 100,
            button_width, button_height,
            "Main Menu", self.font_medium
        )

        # Initialize sound system with dummy sounds
        self.sounds = {
            'eat': self.create_beep_sound(440, 0.2),
            'crash': self.create_beep_sound(220, 0.5),
            'click': self.create_beep_sound(660, 0.1),
            'slip': self.create_beep_sound(330, 0.3)
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
        self.snake = [(GRID_WIDTH // 2, GRID_HEIGHT // 2)]
        self.direction = RIGHT
        self.next_direction = RIGHT
        self.obstacles = self.create_obstacles()
        self.food = self.create_food()
        self.score = 0
        self.game_over = False
        self.paused = False
        self.speed = self.get_speed()
        self.last_move = time.time()
        self.particles = []
        self.ice_blocks = []  # For WINTER mode
        self.slipping = False  # For WINTER mode

        # Initialize ice blocks for WINTER mode
        if self.game_mode == WINTER:
            self.ice_blocks = self.create_ice_blocks(10)

        # Difficulty settings
        if self.difficulty == "EASY":
            self.obstacles = []
            self.speed = 8
        elif self.difficulty == "HARD":
            self.speed = 15
            self.obstacles = self.create_obstacles(10)

    def create_ice_blocks(self, count=5):
        ice_blocks = []
        for _ in range(count):
            while True:
                ice = (random.randint(1, GRID_WIDTH - 2),
                       random.randint(1, GRID_HEIGHT - 2))
                if (ice not in self.snake and
                        ice not in self.obstacles and
                        ice != self.food):
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
                    (self.game_mode != WINTER or food not in self.ice_blocks)):
                return food

    def create_obstacles(self, count=5):
        obstacles = []
        for _ in range(count):
            while True:
                obstacle = (random.randint(1, GRID_WIDTH - 2),
                            random.randint(1, GRID_HEIGHT - 2))
                if obstacle not in self.snake:
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
            "direction": self.direction,
            "food": self.food,
            "obstacles": self.obstacles,
            "score": self.score,
            "difficulty": self.difficulty,
            "speed": self.speed,
            "game_mode": self.game_mode
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
            self.direction = tuple(data["direction"])
            self.next_direction = tuple(data["direction"])
            self.food = tuple(data["food"])
            self.obstacles = [tuple(obs) for obs in data["obstacles"]]
            self.score = data["score"]
            self.difficulty = data["difficulty"]
            self.speed = data["speed"]
            self.game_mode = data.get("game_mode", NORMAL)
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
                    if event.key == pygame.K_UP or event.key == pygame.K_w:
                        if self.direction != DOWN:
                            self.next_direction = UP
                    elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                        if self.direction != UP:
                            self.next_direction = DOWN
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        if self.direction != RIGHT:
                            self.next_direction = LEFT
                    elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        if self.direction != LEFT:
                            self.next_direction = RIGHT
                    elif event.key == pygame.K_SPACE:
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
                        self.sounds['click'].play()
                    elif event.key == pygame.K_5:
                        self.game_mode = DEAD_OF_NIGHT
                        self.sounds['click'].play()
                    elif event.key == pygame.K_6:
                        self.game_mode = WINTER
                        self.sounds['click'].play()

            elif event.type == pygame.MOUSEMOTION and self.state == GAME_OVER:
                self.restart_button.check_hover(mouse_pos)
                self.menu_button.check_hover(mouse_pos)

            elif event.type == pygame.MOUSEBUTTONDOWN and self.state == GAME_OVER:
                if self.restart_button.is_clicked(mouse_pos, event):
                    self.state = PLAYING
                    self.reset_game()
                    self.sounds['click'].play()
                elif self.menu_button.is_clicked(mouse_pos, event):
                    self.state = MENU
                    self.sounds['click'].play()

    def update(self):
        if self.state != PLAYING or self.paused or self.game_over:
            return

        current_time = time.time()
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

        # Move snake
        head_x, head_y = self.snake[0]
        dir_x, dir_y = self.direction
        new_head = ((head_x + dir_x) % GRID_WIDTH,
                    (head_y + dir_y) % GRID_HEIGHT)

        # Check collisions
        if (new_head in self.snake[1:] or
                new_head in self.obstacles or
                new_head[0] == 0 or new_head[0] == GRID_WIDTH - 1 or
                new_head[1] == 0 or new_head[1] == GRID_HEIGHT - 1):
            self.game_over = True
            self.state = GAME_OVER
            if self.score > self.high_score:
                self.high_score = self.score
                self.save_high_score()
            self.sounds['crash'].play()
            self.add_particles(new_head, RED, 15)
            return

        self.snake.insert(0, new_head)

        # Check if food eaten
        if new_head == self.food:
            self.score += 10
            self.sounds['eat'].play()
            self.add_particles(new_head, GOLD, 8)
            self.food = self.create_food()

            # Increase speed every 3 foods
            if self.score % 30 == 0 and self.speed < 20:
                self.speed += 1
        else:
            self.snake.pop()

        self.update_particles()

    def draw_menu(self):
        self.screen.fill(BLACK)

        # Title
        title = self.font_large.render("PREMIUM SNAKE GAME", True, GREEN)
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

        back = self.font_medium.render("ESC. Back to Menu", True, WHITE)

        self.screen.blit(green, (WINDOW_WIDTH // 2 - green.get_width() // 2, 200))
        self.screen.blit(gold, (WINDOW_WIDTH // 2 - gold.get_width() // 2, 250))
        self.screen.blit(purple, (WINDOW_WIDTH // 2 - purple.get_width() // 2, 300))
        self.screen.blit(normal_mode, (WINDOW_WIDTH // 2 - normal_mode.get_width() // 2, 350))
        self.screen.blit(night_mode, (WINDOW_WIDTH // 2 - night_mode.get_width() // 2, 400))
        self.screen.blit(winter_mode, (WINDOW_WIDTH // 2 - winter_mode.get_width() // 2, 450))
        self.screen.blit(back, (WINDOW_WIDTH // 2 - back.get_width() // 2, 550))

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

        # Draw snake with flashlight effect for DEAD_OF_NIGHT mode
        if self.game_mode == DEAD_OF_NIGHT:
            # Create a surface for the darkness
            darkness = pygame.Surface((GAME_WIDTH, GAME_HEIGHT), pygame.SRCALPHA)
            darkness.fill((0, 0, 0, 220))  # Semi-transparent black

            # Draw the flashlight around the snake's head
            head = self.snake[0]
            center = (head[0] * GRID_SIZE + GRID_SIZE // 2,
                      head[1] * GRID_SIZE + GRID_SIZE // 2)

            # Draw gradient circle for flashlight
            for radius in range(self.flashlight_radius * GRID_SIZE, 0, -10):
                alpha = min(255, radius * 2)
                pygame.draw.circle(darkness, (0, 0, 0, alpha), center, radius)

            self.screen.blit(darkness, (self.game_x, self.game_y))

        # Draw snake
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

        # Draw particles
        for p in self.particles:
            pygame.draw.circle(self.screen, p['color'],
                               (int(p['pos'][0]), int(p['pos'][1])),
                               p['size'])

        # Draw UI
        score_text = self.font_medium.render(f"Score: {self.score}", True, WHITE)
        self.screen.blit(score_text, (20, 20))

        hs_text = self.font_small.render(f"High Score: {self.high_score}", True, GOLD)
        self.screen.blit(hs_text, (20, 60))

        diff_text = self.font_small.render(f"Difficulty: {self.difficulty}", True, WHITE)
        self.screen.blit(diff_text, (WINDOW_WIDTH - diff_text.get_width() - 20, 20))

        # Show current mode
        if self.game_mode == DEAD_OF_NIGHT:
            mode_text = self.font_small.render("Mode: Dead of Night", True, (100, 100, 255))
        elif self.game_mode == WINTER:
            mode_text = self.font_small.render("Mode: Winter", True, ICE_COLOR)
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
        controls = self.font_small.render("WASD/Arrows: Move | SPACE: Pause | P: Save | L: Load", True, WHITE)
        self.screen.blit(controls, (WINDOW_WIDTH // 2 - controls.get_width() // 2, WINDOW_HEIGHT - 30))

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

    def draw(self):
        if self.state == MENU:
            self.draw_menu()
        elif self.state == SETTINGS:
            self.draw_settings()
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