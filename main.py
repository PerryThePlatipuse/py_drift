import math
import os
import sys
import pygame
import random

WIDTH = 1300
HEIGHT = 700
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

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
    def __init__(self):
        self.dx = 400
        self.dy = 300

    def apply(self, obj):
        obj.rect.x += self.dx
        obj.rect.y += self.dy

    def update(self, target):
        self.dx = -(target.rect.x + target.rect.w // 2 - WIDTH // 2)
        self.dy = -(target.rect.y + target.rect.h // 2 - HEIGHT // 2)


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


screen_rect = (0, 0, WIDTH, HEIGHT)
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


def create_particles(position):
    particle_count = 1
    numbers = range(-1, 1)
    for _ in range(particle_count):
        Particle(position, random.choice(numbers), random.choice(numbers))


class Car(pygame.sprite.Sprite):
    def __init__(self, forward_acceleration=1.0, backward_acceleration=1.0, drift_acceleration=1.0,
                 max_velocity=1.0, friction=1.08, velocity_friction=5, spawn_x=400, spawn_y=300):
        # drift_acceleration from 0.1 to 2, max_velocity should be less than 1.5
        pygame.sprite.Sprite.__init__(self)
        self.forward_acceleration = forward_acceleration
        self.backward_acceleration = backward_acceleration
        self.froward_acceleration_const = forward_acceleration
        self.backward_acceleration_const = backward_acceleration
        self.max_velocity = max_velocity
        self.max_velocity_const = max_velocity
        self.drift_acceleration = drift_acceleration
        self.friction = friction
        self.velocity_friction = velocity_friction
        self.original_image = load_image("car.png").convert_alpha()
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.x = spawn_x
        self.rect.y = spawn_y
        self.angle = 0
        self.velocity = 0
        self.delta_x = 0
        self.delta_y = 0
        self.mask = pygame.mask.from_surface(self.image)
        self.on_grass = False

    def update1(self, pressed):
        if pressed[pygame.K_UP] or pressed[pygame.K_w]:
            self.velocity += 1 / (self.velocity + self.forward_acceleration)
        if pressed[pygame.K_DOWN] or pressed[pygame.K_s]:
            self.velocity -= 1 / (self.velocity + self.backward_acceleration)
        if (pressed[pygame.K_DOWN] or pressed[pygame.K_s]) and (pressed[pygame.K_UP] or pressed[pygame.K_w]):
            create_particles((car.rect.x, car.rect.y)) # burnout )))
        if pygame.sprite.collide_mask(self, border):
            self.delta_x = -self.delta_x // 1.4
            self.delta_y = -self.delta_y // 1.4
        self.velocity = min(self.max_velocity, self.velocity)
        self.delta_x += math.sin(math.radians(self.angle)) * self.velocity
        self.delta_y += math.cos(math.radians(self.angle)) * self.velocity
        self.rect.x += int(self.delta_x)
        self.rect.y += int(self.delta_y)
        if pressed[pygame.K_LEFT] or pressed[pygame.K_a]:
            self.turn_left(self.delta_x, self.delta_y)
            if car.velocity != 0:
                create_particles((car.rect.x, car.rect.y))
        if pressed[pygame.K_RIGHT] or pressed[pygame.K_d]:
            self.turn_right(self.delta_x, self.delta_y)
            if car.velocity != 0:
                create_particles((car.rect.x, car.rect.y))
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

    def turn_left(self, x, y):
        angle = int(+(self.drift_acceleration + self.velocity / 3) * math.sqrt(x ** 2 + y ** 2))
        car.angle += angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        center_x, center_y = self.rect.center  # Save its current center.
        self.rect = self.image.get_rect()  # Replace old rect with new rect.
        self.rect.center = (center_x, center_y)

    def turn_right(self, x, y):
        angle = int(-(self.drift_acceleration + self.velocity / 3) * math.sqrt(x ** 2 + y ** 2))
        car.angle += angle
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        center_x, center_y = self.rect.center  # Save its current center.
        self.rect = self.image.get_rect()  # Replace old rect with new rect.
        self.rect.center = (center_x, center_y)


all_sprites = pygame.sprite.LayeredUpdates()
car = Car(drift_acceleration=0.5, max_velocity=1)
grass = Grass(deceleration=0.7)
border = Border()
road = Road()
camera = Camera()
all_sprites.add(grass)
all_sprites.add(road)
all_sprites.add(car)
all_sprites.add(border)

running = True

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    pressed = pygame.key.get_pressed()
    car.update1(pressed)
    camera.update(car)
    for sprite in all_sprites:
        camera.apply(sprite)
    all_sprites.update()
    screen.fill(BLACK)
    all_sprites.draw(screen)
    pygame.display.flip()
    all_sprites.move_to_front(car)
pygame.quit()
