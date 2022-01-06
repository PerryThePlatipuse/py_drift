import math
import os
import sys

import pygame


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


class Track(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(all_sprites)
        self.image = load_image("bg-test.png")
        self.rect = self.image.get_rect()


class Car(pygame.sprite.Sprite):
    def __init__(self, forward_acceleration=1.0, backward_acceleration=1.0, drift_acceleration=1.0,
                 max_velocity=1.0, friction=1.08, velocity_friction=5, spawn_x=400, spawn_y=300):
        # drift_acceleration from 0.1 to 2, max_velocity should be less than 1.5
        pygame.sprite.Sprite.__init__(self)
        self.froward_acceleration = forward_acceleration
        self.backward_acceleration = backward_acceleration
        self.max_velocity = max_velocity
        self.drift_acceleration = drift_acceleration
        self.friction = friction
        self.velocity_friction = velocity_friction
        self.original_image = load_image("car.png")
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.x = spawn_x
        self.rect.y = spawn_y
        self.angle = 0
        self.velocity = 0
        self.delta_x = 0
        self.delta_y = 0

    def update(self, pressed):
        if pressed[pygame.K_UP]:
            self.velocity += 1 / (self.velocity + self.froward_acceleration)
        if pressed[pygame.K_DOWN]:
            self.velocity -= 1 / (self.velocity + self.backward_acceleration)
        self.velocity = min(self.max_velocity, self.velocity)
        self.delta_x += math.sin(math.radians(self.angle)) * self.velocity
        self.delta_y += math.cos(math.radians(self.angle)) * self.velocity
        self.rect.x += int(self.delta_x)
        self.rect.y += int(self.delta_y)
        if pressed[pygame.K_LEFT]:
            self.turn_left(self.delta_x, self.delta_y)
        if pressed[pygame.K_RIGHT]:
            self.turn_right(self.delta_x, self.delta_y)
        self.delta_x /= self.friction
        self.delta_y /= self.friction
        self.velocity /= self.velocity_friction
        if abs(self.velocity) < 0.01: self.velocity = 0
        self.angle = int(self.angle)
        self.angle %= 360

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


all_sprites = pygame.sprite.Group()
car = Car(drift_acceleration=1.5, max_velocity=0.5)
track = Track()
all_sprites.add(track)
all_sprites.add(car)


running = True

while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    pressed = pygame.key.get_pressed()
    car.update(pressed)
    # all_sprites.update()
    screen.fill(BLACK)
    all_sprites.draw(screen)
    pygame.display.flip()
pygame.quit()
