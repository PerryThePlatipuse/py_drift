import math
import os
import sys
import pygame
import random
from itertools import cycle
from network import Network
from PIL import Image
import time

YELLOW = (255, 255, 0)
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
size_for_gif=(644, 604)
FORMAT = "RGBA"


def pil_to_game(img):
    data = img.tobytes("raw", FORMAT)
    return pygame.image.fromstring(data, img.size, FORMAT)


def get_gif_frame(img, frame):
    img.seek(frame)
    return  img.convert(FORMAT)


def init():
    return pygame.display.set_mode(size_for_gif)


def exit():
    pygame.quit()


pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("My Game")
clock = pygame.time.Clock()


class Camera:
    def __init__(self):
        self.dx = 400
        self.dy = 300

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - WIDTH // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - HEIGHT // 2)


def load_image(name, colorkey=None):
    fullname = os.path.join('images', name)
    # если файл не существует, то выходим
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    return image


class Minimap(pygame.sprite.Sprite):
    image = load_image("minimap-road.png").convert_alpha()

    def __init__(self):
        super().__init__(all_sprites)
        self.image = Minimap.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = 260 * 4
        self.rect.y = 0


class MinimapPlayerRed(pygame.sprite.Sprite):
    image = load_image('minimap-player_red.png').convert_alpha()

    def __init__(self):
        super().__init__(all_sprites)
        self.image = MinimapPlayerRed.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = 1040 + car_red.rect.x / 10
        self.rect.y = car_red.rect.y / 10

    def update(self):
        self.rect.x = 1040 + car_red.real_x / 10
        self.rect.y = car_red.real_y / 10


class MinimapPlayerBlue(pygame.sprite.Sprite):
    image = load_image('minimap-player.png').convert_alpha()

    def __init__(self):
        super().__init__(all_sprites)
        self.image = MinimapPlayerBlue.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = 1040 + car_blue.rect.x / 10
        self.rect.y = car_blue.rect.y / 10

    def update(self):
        self.rect.x = 1040 + car_blue.real_x / 10
        self.rect.y = car_blue.real_y / 10


screen_rect = (0, 0, WIDTH, HEIGHT)
global_dx = 400
global_dy = 300


class Grass(pygame.sprite.Sprite):
    image = load_image("grass2.png").convert_alpha()

    def __init__(self, deceleration=0.5, velocity_limit=0.2):
        super().__init__(all_sprites)
        self.deceleration = deceleration
        self.velocity_limit = velocity_limit
        self.image = Grass.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)


class Road(pygame.sprite.Sprite):
    image = load_image("road2.png").convert_alpha()

    def __init__(self):
        super().__init__(all_sprites)
        self.image = Road.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)


class Border(pygame.sprite.Sprite):
    image = load_image("borders2.png").convert_alpha()

    def __init__(self):
        super().__init__(all_sprites)
        self.image = Border.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)


class Particle(pygame.sprite.Sprite):
    fire = [load_image("smoke.png").convert_alpha()]
    for scale in (20, 35, 50, 65, 80):
        fire.append(pygame.transform.scale(fire[0], (scale, scale)))

    def __init__(self, pos, dx, dy):
        super().__init__(all_sprites)
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
        self.angle = 270
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
        self.dct_checkpoints = {1: False, 2: False, 3: False, 4: False, 5: False, 6: False, 7: False, 8: False, 9: False}
        self.count = 0
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        center_x, center_y = self.rect.center  # Save its current center.
        self.rect = self.image.get_rect()  # Replace old rect with new rect.
        self.rect.center = (center_x, center_y)

    def update1(self, pressed):
        if self.unplayable:
            return
        if pressed[self.key_f]:
            self.velocity += 1 / (self.velocity + self.forward_acceleration)
        if pressed[self.key_b]:
            self.velocity -= 1 / (self.velocity + self.backward_acceleration)
        if pressed[self.key_f] and pressed[self.key_b]:
            create_particles((self.rect.x, self.rect.y), self)  # burnout )))
        if pygame.sprite.collide_mask(self, border):
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
        if pygame.sprite.collide_mask(self, grass):
            if self.on_grass is False:
                self.max_velocity -= grass.velocity_limit
                self.forward_acceleration -= grass.deceleration
                self.backward_acceleration -= grass.deceleration
                self.on_grass = True
        if not pygame.sprite.collide_mask(self, grass):
            if self.on_grass is True:
                self.max_velocity = self.max_velocity_const
                self.forward_acceleration = self.froward_acceleration_const
                self.backward_acceleration = self.backward_acceleration_const
                self.on_grass = False

        # Checkpoints...

        if pygame.sprite.collide_mask(self, checkpoint1):
            self.dct_checkpoints[1] = True
        elif pygame.sprite.collide_mask(self, checkpoint2) and self.dct_checkpoints[1] is True:
            self.dct_checkpoints[2] = True
        elif pygame.sprite.collide_mask(self, checkpoint3) and self.dct_checkpoints[2] is True:
            self.dct_checkpoints[3] = True
        elif pygame.sprite.collide_mask(self, checkpoint4) and self.dct_checkpoints[3] is True:
            self.dct_checkpoints[4] = True
        elif pygame.sprite.collide_mask(self, checkpoint5) and self.dct_checkpoints[4] is True:
            self.dct_checkpoints[5] = True
        elif pygame.sprite.collide_mask(self, checkpoint6) and self.dct_checkpoints[5] is True:
            self.dct_checkpoints[6] = True
        elif pygame.sprite.collide_mask(self, checkpoint7) and self.dct_checkpoints[6] is True:
            self.dct_checkpoints[7] = True
        elif pygame.sprite.collide_mask(self, checkpoint8) and self.dct_checkpoints[7] is True:
            self.dct_checkpoints[8] = True
        elif pygame.sprite.collide_mask(self, checkpoint9) and self.dct_checkpoints[8] is True:
            self.dct_checkpoints[9] = True
        elif pygame.sprite.collide_mask(self, finish):
            # if self.on_finish is False:
            #     self.on_finish = True
            #     print("finish")
            if self.dct_checkpoints[9] is True:
                self.dct_checkpoints = {1: False, 2: False, 3: False, 4: False, 5: False, 6: False, 7: False,
                                        8: False, 9: False}
                self.count += 1
            # elif not pygame.sprite.collide_mask(self, finish):
            #     if self.on_finish is True:
            #         self.on_finish = False
        # print(self.dct_checkpoints)
        # print(self.count)

    def turn_left(self, x, y):
        if self.unplayable:
            return
        angle = int(+(self.drift_acceleration + self.velocity / 3) * math.sqrt(x ** 2 + y ** 2))
        self.angle += angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        center_x, center_y = self.rect.center  # Save its current center.
        self.rect = self.image.get_rect()  # Replace old rect with new rect.
        self.rect.center = (center_x, center_y)

    def turn_right(self, x, y):
        if self.unplayable:
            return
        angle = int(-(self.drift_acceleration + self.velocity / 3) * math.sqrt(x ** 2 + y ** 2))
        self.angle += angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        center_x, center_y = self.rect.center  # Save its current center.
        self.rect = self.image.get_rect()  # Replace old rect with new rect.
        self.rect.center = (center_x, center_y)


class FinishLine(pygame.sprite.Sprite):
    image = load_image("finish-2.png").convert_alpha()

    def __init__(self):
        super().__init__(all_sprites)
        self.image = FinishLine.image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rect.x = 1300
        self.rect.y = 600
        self.count = -1


class Checkpoint(pygame.sprite.Sprite):
    def __init__(self, x=1300, y=700, angle=0):
        super().__init__(all_sprites)
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


running = True
coords_dict = {}


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
        # print(string_rendered.get_width() // 2)
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
    # print(coords_dict)

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
            # print(f'Start: {mouse_x, mouse_y}')
        elif coords_dict['Quit'][0] <= mouse_x <= 590 + coords_dict['Quit'][2] and \
                coords_dict['Quit'][1] <= mouse_y <= 310 + coords_dict['Quit'][3]:
            pygame.draw.rect(screen, DARK_GREY, tuple(coords_dict['Quit']))
            string_rendered = font.render('Quit', True, WHITE)
            screen.blit(string_rendered, rendered_strings['Quit'])
            on_start = False
            on_quit = True
            # print(f'Quit: {mouse_x, mouse_y}')
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


def gameover_screen():
    fon = pygame.transform.scale(load_image('gameover_screen.png'), (WIDTH, HEIGHT))
    running = True
    while running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        screen.blit(fon, (0, 0))
        font = pygame.font.Font(None, 64)
        if win_disel_red:
            win = "RED"
        if win_disel_blue:
            win = "BLUE"
        winner_s = font.render(win, 1, RED if win == "RED" else BLUE)
        time_s = font.render(f'{time_passed:.2f} seconds', 1, WHITE)
        screen.blit(winner_s, (620, 280))
        screen.blit(time_s, (580, 480))
        pygame.display.flip()




start_screen()
playlist = cycle(['music/StepWay - Born With Attitude.mp3', 'music/StepWay - Miff.mp3',
                  'music/StepWay - Bullet Hate.mp3'])
pygame.mixer.music.load('music/StepWay - Bullet Hate.mp3')
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.load(next(playlist))
pygame.mixer.music.queue(next(playlist))
pygame.mixer.music.set_endevent(pygame.USEREVENT)
pygame.mixer.music.play()


net = Network()
pos = net.getPos()


all_sprites = pygame.sprite.LayeredUpdates()
not_all_sprites = pygame.sprite.Group()

if pos[0]:
    car_red = Car(drift_acceleration=0.7, max_velocity=1, color="red", spawn_x=1300, spawn_y=700)
    car_blue = Car(drift_acceleration=0.7, max_velocity=1, spawn_x=1400, spawn_y=800, key_r=pygame.K_l,
                   key_b=pygame.K_k,
                   key_l=pygame.K_j, key_f=pygame.K_i, color="blue", unplayable=True)
else:
    car_red = Car(drift_acceleration=0.7, max_velocity=1, color="red", spawn_x=1300, spawn_y=700, key_r=pygame.K_l, key_b=pygame.K_k, key_l=pygame.K_j, key_f=pygame.K_i, unplayable=True)
    car_blue = Car(drift_acceleration=0.7, max_velocity=1, spawn_x=1400, spawn_y=800, color="blue")
send_info = [0] * 6
received_info = [0] * 6

init()
gif_img = Image.open("images/car_load.gif")
current_frame = 0
clock = pygame.time.Clock()
while not received_info[4]:
    frame = pil_to_game(get_gif_frame(gif_img, current_frame))
    screen.blit(frame, (0, 0))
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            break
    current_frame = (current_frame + 1) % gif_img.n_frames
    pygame.display.flip()
    clock.tick(10)
    received_info = net.send(send_info[:])
    send_info[0] = not received_info[0]
    send_info[1] = car_red.real_x
    send_info[2] = car_red.real_y
    send_info[3] = car_red.angle
    send_info[4] = True

screen = pygame.display.set_mode((WIDTH, HEIGHT))
grass = Grass(deceleration=0.7)
border = Border()
road = Road()
camera = Camera()
minimap = Minimap()
minimap_player_red = MinimapPlayerRed()
minimap_player_blue = MinimapPlayerBlue()
finish = FinishLine()
all_sprites.add(minimap_player_blue)
all_sprites.add(grass)
all_sprites.add(road)
all_sprites.add(car_red)
all_sprites.add(car_blue)
all_sprites.add(border)
all_sprites.add(minimap)
all_sprites.add(minimap_player_red)
all_sprites.add(finish)

# checkpoints...

checkpoint1 = Checkpoint(650, 606)
checkpoint2 = Checkpoint(265, 115, 30)
checkpoint3 = Checkpoint(1221, 346)
checkpoint4 = Checkpoint(2135, 457, 120)
checkpoint5 = Checkpoint(2292, 1176, 30)
checkpoint6 = Checkpoint(1563, 1228)
checkpoint7 = Checkpoint(497, 1055, 90)
checkpoint8 = Checkpoint(1197, 865)
checkpoint9 = Checkpoint(1790, 730, 90)
all_sprites.add(checkpoint1, checkpoint2, checkpoint3, checkpoint4, checkpoint5, checkpoint6, checkpoint7,  checkpoint8,
                checkpoint9)

win_disel_red = False
win_disel_blue = False
k=0
start_time = time.time()
while running:
    # print(f"x: {car_red.rect.x}, y:{car_red.rect.y}")
    print(k)
    received_info = net.send(send_info[:])
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.USEREVENT:
            pygame.mixer.music.queue(next(playlist))
    pressed = pygame.key.get_pressed()
    if not received_info[0]:
        send_info[0] = not received_info[0]
        send_info[1] = car_red.real_x
        send_info[2] = car_red.real_y
        send_info[3] = car_red.angle
        send_info[5] = car_red.count
        car_red.update1(pressed)
        car_blue.rect.x = received_info[1]
        car_blue.rect.y = received_info[2]
        car_blue.real_y = received_info[2]
        car_blue.real_x = received_info[1]
        car_blue.angle = received_info[3]
        car_blue.count = received_info[5]
        for sprite in all_sprites:
            if not (isinstance(sprite, Minimap) or isinstance(sprite, MinimapPlayerRed) or
                    isinstance(sprite, Car) and sprite.color == "blue" or
                    isinstance(sprite, MinimapPlayerBlue)):
                camera.apply(sprite)
        camera.update(car_red)
        car_blue.image = pygame.transform.rotate(car_blue.original_image, car_blue.angle)
        center_x, center_y = car_blue.rect.center  # Save its current center.
        car_blue.rect = car_blue.image.get_rect()  # Replace old rect with new rect.
        car_blue.rect.center = (center_x, center_y)
    else:
        send_info[0] = not received_info[0]
        send_info[1] = car_blue.real_x
        send_info[2] = car_blue.real_y
        send_info[3] = car_blue.angle
        send_info[5] = car_blue.count
        car_blue.update1(pressed)
        car_red.rect.x = received_info[1]
        car_red.rect.y = received_info[2]
        car_red.angle = received_info[3]
        car_red.real_x = received_info[1]
        car_red.real_y = received_info[2]
        car_red.count = received_info[5]
        for sprite in all_sprites:
            if not (isinstance(sprite, Minimap) or isinstance(sprite, MinimapPlayerRed) or
                    isinstance(sprite, Car) and sprite.color == "red" or
                    isinstance(sprite, MinimapPlayerBlue)):
                camera.apply(sprite)
        camera.update(car_blue)
        car_red.image = pygame.transform.rotate(car_red.original_image, car_red.angle)
        center_x, center_y = car_red.rect.center  # Save its current center.
        car_red.rect = car_red.image.get_rect()  # Replace old rect with new rect.
        car_red.rect.center = (center_x, center_y)
    global_dx += camera.dx
    global_dy += camera.dy
    if not received_info[0]: # play red car
        car_blue.rect.x += global_dx
        car_blue.rect.y += global_dy
    else:
        car_red.rect.x += global_dx
        car_red.rect.y += global_dy
    # fontObj = pygame.font.Font('freesansbold.ttf', 50)
    # textSurfaceObj = fontObj.render('Hello world!', True, YELLOW, BLUE)
    # textRectObj = textSurfaceObj.get_rect()
    # textRectObj.center = (500, 400)
    # screen.blit(textSurfaceObj, textRectObj)
    all_sprites.update()
    screen.fill(GREEN)
    all_sprites.draw(screen)
    all_sprites.move_to_front(car_red)
    all_sprites.move_to_front(car_blue)
    all_sprites.move_to_front(minimap)
    all_sprites.move_to_front(minimap_player_red)
    all_sprites.move_to_front(minimap_player_blue)
    time_passed = time.time() - start_time
    font = pygame.font.SysFont("Arial", 32)
    textSurf1 = font.render(f'current lap: {time_passed:.2f}', 1, WHITE)
    if car_red.unplayable:
        textSurf = font.render(f'Laps: {car_blue.count}', 1, WHITE)
        last_check = list(filter(lambda x: car_blue.dct_checkpoints[x], car_blue.dct_checkpoints.keys()))
        last_check = 0 if not last_check else max(last_check)
        checkpoints_text = font.render(f'Last checkpoint: {last_check}', 1, WHITE)
    else:
        textSurf = font.render(f'Laps: {car_red.count}', 1, WHITE)
        last_check = list(filter(lambda x: car_red.dct_checkpoints[x], car_red.dct_checkpoints.keys()))
        last_check = 0 if not last_check else max(last_check)
        checkpoints_text = font.render(f'Last checkpoint: {last_check}', 1, WHITE)
    if car_red.count == 1:
        win_disel_red = True
        k += 1
    if car_blue.count == 1:
        win_disel_blue = True
        k += 1
    if k == 10:
        running = False
    screen.blit(textSurf, (1020, 150))
    screen.blit(textSurf1, (1020, 180))
    screen.blit(checkpoints_text, (1020, 210))
    pygame.display.flip()

print(win_disel_red, win_disel_blue)
gameover_screen()
pygame.quit()
