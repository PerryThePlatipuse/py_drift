import math
import os
import sys
import pygame
import random
from itertools import cycle

WIDTH = 1300
HEIGHT = 700
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (75, 93, 3)
BLUE = (0, 0, 255)
LIGHT_GREY = (178, 178, 178)
DARK_GREY = (78, 78, 78)

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My Game")
clock = pygame.time.Clock()


def load_image(name, colorkey=None):
    fullname = os.path.join('images', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


class Camera:
    def __init__(self, dx, dy):
        self.dx = dx
        self.dy = dy

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - WIDTH // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - HEIGHT // 2)


class Minimap(pygame.sprite.Sprite):
    image = load_image("minimap-road.png").convert_alpha()

    def __init__(self):
        super().__init__()
        self.image = Minimap.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = 260 * 4
        self.rect.y = 0


class MinimapPlayer(pygame.sprite.Sprite):
    image = load_image('minimap-player.png').convert_alpha()

    def __init__(self):
        super().__init__()
        self.image = MinimapPlayer.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = 1040 + car_red_red.rect.x / 10
        self.rect.y = car_red_red.rect.y / 10

    def update(self):
        self.rect.x = 1040 + car_red_red.real_x / 10
        self.rect.y = car_red_red.real_y / 10


class Grass(pygame.sprite.Sprite):
    image = load_image("grass2.png").convert_alpha()

    def __init__(self, deceleration=0.5, velocity_limit=0.2):
        super().__init__()
        self.deceleration = deceleration
        self.velocity_limit = velocity_limit
        self.image = Grass.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)


class Road(pygame.sprite.Sprite):
    image = load_image("road2.png").convert_alpha()

    def __init__(self):
        super().__init__()
        self.image = Road.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)


class Border(pygame.sprite.Sprite):
    image = load_image("borders2.png").convert_alpha()

    def __init__(self):
        super().__init__()
        self.image = Border.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)


screen_rect = (0, 0, WIDTH, HEIGHT)


class Particle(pygame.sprite.Sprite):
    fire = [load_image("smoke.png").convert_alpha()]
    for scale in (20, 35, 50, 65, 80):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__()
        self.fire[0] = self.fire[1]
        self.image = random.choice(self.fire)
        self.rect = self.image.get_rect()
        self.image_alpha = 255
        self.fade = random.randint(5, 10)
        self.velocity = [dx, dy]
        self.rect.x, self.rect.y = pos

        self.gravity = 5

    def update(self):
        self.image_alpha -= self.fade
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
        if self.image_alpha <= 0:
            self.kill()
        else:
            self.image.set_alpha(self.image_alpha)


def create_particles(position, car):
    particle_count = 1
    numbers = range(-1, 1)
    if not car.on_grass:
        for _ in range(particle_count):
            Particle(position, random.choice(numbers), random.choice(numbers))


class Car(pygame.sprite.Sprite):
    def __init__(self, forward_acceleration=1.0, backward_acceleration=1.0, drift_acceleration=1.0,
                 max_velocity=1.0, friction=1.08, velocity_friction=5, spawn_x=1300, spawn_y=700, color="red",
                 key_f=pygame.K_w, key_b=pygame.K_s, key_r=pygame.K_d, key_l=pygame.K_a, unplayable=False):
        # drift_acceleration from 0.1 to 2, max_velocity should be less than 1.5
        pygame.sprite.Sprite.__init__(self)
        self.unplayable = unplayable
        self.color = color
        self.forward_acceleration = forward_acceleration
        self.backward_acceleration = backward_acceleration
        self.froward_acceleration_const = forward_acceleration
        self.backward_acceleration_const = backward_acceleration
        self.max_velocity = max_velocity
        self.max_velocity_const = max_velocity
        self.drift_acceleration = drift_acceleration
        self.friction = friction
        self.velocity_friction = velocity_friction
        self.original_image = load_image("car_2.png").convert_alpha() if color == "red" else load_image(
            "car_1.png").convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.x = spawn_x
        self.rect.y = spawn_y
        self.real_x = spawn_x
        self.real_y = spawn_y
        self.angle = 0
        self.velocity = 0
        self.delta_x = 0
        self.delta_y = 0
        self.mask = pygame.mask.from_surface(self.image)
        self.on_grass = False
        self.key_f = key_f
        self.key_r = key_r
        self.key_l = key_l
        self.key_b = key_b
        self.on_finish = False

    def update1(self, pressed):
        if pressed[self.key_f]:
            self.velocity += 1 / (self.velocity + self.forward_acceleration)
        if pressed[self.key_b]:
            self.velocity -= 1 / (self.velocity + self.backward_acceleration)
        if pressed[self.key_f] and pressed[self.key_b]:
            create_particles((self.rect.x, self.rect.y), self)  # burnout )))
        if pygame.sprite.collide_mask(self, border_red):
            self.delta_x = -self.delta_x // 1.4
            self.delta_y = -self.delta_y // 1.4
        self.velocity = min(self.max_velocity, self.velocity)
        self.delta_x += math.sin(math.radians(self.angle)) * self.velocity
        self.delta_y += math.cos(math.radians(self.angle)) * self.velocity
        self.rect.x += int(self.delta_x)
        self.rect.y += int(self.delta_y)
        self.real_x += int(self.delta_x)
        self.real_y += int(self.delta_y)
        if pressed[self.key_l]:
            self.turn_left(self.delta_x, self.delta_y)
            if self.velocity != 0:
                create_particles((self.rect.x, self.rect.y), self)
        if pressed[self.key_r]:
            self.turn_right(self.delta_x, self.delta_y)
            if self.velocity != 0:
                create_particles((self.rect.x, self.rect.y), self)
        self.delta_x /= self.friction
        self.delta_y /= self.friction
        self.velocity /= self.velocity_friction
        if abs(self.velocity) < 0.01: self.velocity = 0
        self.angle = int(self.angle)
        self.angle %= 360
        if pygame.sprite.collide_mask(self, grass_red):
            if self.on_grass is False:
                self.max_velocity -= grass_red.velocity_limit
                self.forward_acceleration -= grass_red.deceleration
                self.backward_acceleration -= grass_red.deceleration
                self.on_grass = True
        if not pygame.sprite.collide_mask(self, grass_red):
            if self.on_grass is True:
                self.max_velocity = self.max_velocity_const
                self.forward_acceleration = self.froward_acceleration_const
                self.backward_acceleration = self.backward_acceleration_const
                self.on_grass = False

    def turn_left(self, x, y):
        angle = int(+(self.drift_acceleration + self.velocity / 3) * math.sqrt(x ** 2 + y ** 2))
        self.angle += angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        center_x, center_y = self.rect.center  # Save its current center.
        self.rect = self.image.get_rect()  # Replace old rect with new rect.
        self.rect.center = (center_x, center_y)

    def turn_right(self, x, y):
        angle = int(-(self.drift_acceleration + self.velocity / 3) * math.sqrt(x ** 2 + y ** 2))
        self.angle += angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        center_x, center_y = self.rect.center  # Save its current center.
        self.rect = self.image.get_rect()  # Replace old rect with new rect.
        self.rect.center = (center_x, center_y)


class FinishLine(pygame.sprite.Sprite):
    image = load_image("finish-2.png").convert_alpha()

    def __init__(self):
        super().__init__(all_sprites_red)
        self.image = FinishLine.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = 1300
        self.rect.y = 600
        self.count = -1

    def update(self):
        if pygame.sprite.collide_mask(self, car_red_red):
            if car_red_red.on_finish is False:
                car_red_red.on_finish = True
                self.count += 1
        elif not pygame.sprite.collide_mask(self, car_red_red):
            if car_red_red.on_finish is True:
                car_red_red.on_finish = False


class Checkpoint(pygame.sprite.Sprite):
    def __init__(self, x=1300, y=700, angle=0):
        super().__init__(all_sprites_red)
        self.original_image = load_image("checkpoint.png").convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = x
        self.rect.y = y
        self.angle = angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        center_x, center_y = self.rect.center
        self.rect = self.image.get_rect()
        self.rect.center = (center_x, center_y)


def start_screen():
    global coords_dict
    pygame.mixer.music.load('music/StepWay - Bit Kawai.mp3')
    pygame.mixer.music.play(-1)
    sound_start = pygame.mixer.Sound('music/Start.mp3')
    sound_start.set_volume(0.3)

    intro_text = ["Start",
                  "Quit"]

    fon = pygame.transform.scale(load_image('start_screen.png'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 64)
    text_coord = 200
    rendered_strings = {}
    for line in intro_text:
        string_rendered = font.render(line, True, pygame.Color('white'))
        intro_rect = string_rendered.get_rect()
        text_coord += 40
        intro_rect.top = text_coord
        intro_rect.x = 650 - string_rendered.get_width() // 2
        print(string_rendered.get_width() // 2)
        text_coord += intro_rect.height
        text_w = string_rendered.get_width()
        text_h = string_rendered.get_height()
        coords_dict[line] = [640 - string_rendered.get_width() // 2, text_coord - 55, text_w + 20, text_h + 20]
        pygame.draw.rect(screen, LIGHT_GREY, (640 - string_rendered.get_width() // 2, text_coord - 55, text_w + 20,
                                              text_h + 20))
        rendered_strings[line] = intro_rect
        screen.blit(string_rendered, intro_rect)
    on_start = False
    on_quit = False
    print(coords_dict)

    # Strat: 51
    # Quit: 47

    while True:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if coords_dict['Start'][0] <= mouse_x <= 590 + coords_dict['Start'][2] and \
                coords_dict['Start'][1] <= mouse_y <= 230 + coords_dict['Start'][3]:
            pygame.draw.rect(screen, DARK_GREY, tuple(coords_dict['Start']))
            string_rendered = font.render('Start', True, WHITE)
            screen.blit(string_rendered, rendered_strings['Start'])
            on_start = True
            on_quit = False
        elif coords_dict['Quit'][0] <= mouse_x <= 590 + coords_dict['Quit'][2] and \
                coords_dict['Quit'][1] <= mouse_y <= 310 + coords_dict['Quit'][3]:
            pygame.draw.rect(screen, DARK_GREY, tuple(coords_dict['Quit']))
            string_rendered = font.render('Quit', True, WHITE)
            screen.blit(string_rendered, rendered_strings['Quit'])
            on_start = False
            on_quit = True
            print(f'Quit: {mouse_x, mouse_y}')
        else:
            pygame.draw.rect(screen, LIGHT_GREY, tuple(coords_dict['Start']))
            pygame.draw.rect(screen, LIGHT_GREY, tuple(coords_dict['Quit']))
            string_rendered = font.render('Start', True, pygame.Color('white'))
            screen.blit(string_rendered, rendered_strings['Start'])
            string_rendered = font.render('Quit', True, pygame.Color('white'))
            screen.blit(string_rendered, rendered_strings['Quit'])
            on_start = False
            on_quit = False
        for event in pygame.event.get():
            if event.type == pygame.MOUSEMOTION:
                pass
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN or \
                    event.type == pygame.MOUSEBUTTONDOWN:
                if on_start:
                    sound_start.play()
                    pygame.mixer.music.stop()
                    pygame.mixer.music.unload()
                    return
                elif on_quit:
                    pygame.quit()
                    sys.exit()
        pygame.display.flip()
        clock.tick(FPS)


all_sprites_red = pygame.sprite.LayeredUpdates()
not_all_sprites = pygame.sprite.Group()
car_red_red = Car(drift_acceleration=0.5, max_velocity=1)
car_blue_red = Car(drift_acceleration=0.5, max_velocity=1, spawn_x=1400, spawn_y=800, key_r=pygame.K_l, key_b=pygame.K_k,
                   key_l=pygame.K_j, key_f=pygame.K_i, color="blue")
grass_red = Grass(deceleration=0.7)
border_red = Border()
road_red = Road()
camera_red = Camera(dx=1000, dy=1000)
minimap_red = Minimap()
minimap_player_red = MinimapPlayer()
finish_red = FinishLine()
all_sprites_red.add(grass_red)
all_sprites_red.add(road_red)
all_sprites_red.add(car_red_red)
all_sprites_red.add(border_red)
all_sprites_red.add(minimap_red)
all_sprites_red.add(minimap_player_red)
all_sprites_red.add(car_blue_red)
all_sprites_red.add(finish_red)

# checkpoints...

checkpoint1_red = Checkpoint(650, 606)
checkpoint2_red = Checkpoint(265, 115, 30)
checkpoint3_red = Checkpoint(1221, 346)
checkpoint4_red = Checkpoint(2135, 457, 120)
checkpoint5_red = Checkpoint(2292, 1176, 30)
checkpoint6_red = Checkpoint(1563, 1228)
checkpoint7_red = Checkpoint(497, 1055, 90)
checkpoint8_red = Checkpoint(1197, 865)
checkpoint9_red = Checkpoint(1790, 730, 90)
all_sprites_red.add(checkpoint1_red, checkpoint2_red, checkpoint3_red, checkpoint4_red, checkpoint5_red, checkpoint6_red, checkpoint7_red,
                    checkpoint8_red,
                    checkpoint9_red)


all_sprites_blue = pygame.sprite.LayeredUpdates()
car_red_blue = Car(drift_acceleration=0.5, max_velocity=1)
car_blue_blue = Car(drift_acceleration=0.5, max_velocity=1, spawn_x=1400, spawn_y=800, key_r=pygame.K_l, key_b=pygame.K_k,
                    key_l=pygame.K_j, key_f=pygame.K_i, color="blue")
grass_blue = Grass(deceleration=0.7)
border_blue = Border()
road_blue = Road()
camera_blue = Camera(dx=525, dy=307 * 3)
minimap_blue = Minimap()
minimap_player_blue = MinimapPlayer()
finish_blue = FinishLine()
all_sprites_blue.add(grass_blue)
all_sprites_blue.add(road_blue)
all_sprites_blue.add(car_red_blue)
all_sprites_blue.add(border_blue)
all_sprites_blue.add(minimap_blue)
all_sprites_blue.add(minimap_player_blue)
all_sprites_blue.add(car_blue_blue)
all_sprites_blue.add(finish_blue)

# checkpoints...

checkpoint1_blue = Checkpoint(650, 606)
checkpoint2_blue = Checkpoint(265, 115, 30)
checkpoint3_blue = Checkpoint(1221, 346)
checkpoint4_blue = Checkpoint(2135, 457, 120)
checkpoint5_blue = Checkpoint(2292, 1176, 30)
checkpoint6_blue = Checkpoint(1563, 1228)
checkpoint7_blue = Checkpoint(497, 1055, 90)
checkpoint8_blue = Checkpoint(1197, 865)
checkpoint9_blue = Checkpoint(1790, 730, 90)
all_sprites_blue.add(checkpoint1_blue, checkpoint2_blue, checkpoint3_blue, checkpoint4_blue, checkpoint5_blue, checkpoint6_blue, checkpoint7_blue,
                     checkpoint8_blue,
                     checkpoint9_blue)


running = True
coords_dict = {}

start_screen()
playlist = cycle(['music/StepWay - Born With Attitude.mp3', 'music/StepWay - Miff.mp3',
                  'music/StepWay - Bullet Hate.mp3'])
pygame.mixer.music.load('music/StepWay - Bullet Hate.mp3')
pygame.mixer.music.set_volume(0)
pygame.mixer.music.load(next(playlist))
pygame.mixer.music.queue(next(playlist))
pygame.mixer.music.set_endevent(pygame.USEREVENT)
pygame.mixer.music.play()

pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((1630, 1050))
pygame.display.set_caption("My Game")

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.USEREVENT:
            pygame.mixer.music.queue(next(playlist))
    pressed = pygame.key.get_pressed()
    car_red_red.update1(pressed)
    car_blue_red.update1(pressed)
    car_red_blue.update1(pressed)
    car_blue_blue.update1(pressed)
    camera_red.update(car_red_red)
    camera_blue.update(car_blue_blue)
    for sprite in all_sprites_red:
        if not isinstance(sprite, Minimap) and not isinstance(sprite, MinimapPlayer): camera_red.apply(sprite)
    for sprite in all_sprites_blue:
        if not isinstance(sprite, Minimap) and not isinstance(sprite, MinimapPlayer): camera_blue.apply(sprite)
    all_sprites_red.update()
    all_sprites_blue.update()
    screen.fill(GREEN)
    all_sprites_red.draw(screen)
    all_sprites_blue.draw(screen)
    pygame.display.flip()
    all_sprites_red.move_to_front(car_red_red)
    all_sprites_blue.move_to_front(car_blue_blue)
pygame.quit()
