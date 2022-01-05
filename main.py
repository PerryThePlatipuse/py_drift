import math
import os
import sys

import pygame


WIDTH = 1366
HEIGHT = 768
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


class Car(pygame.sprite.Sprite):
    def __init__(self, forward_acceleration=1.0, backward_acceleration=1.0, drift_acceleration=1.0, max_velocity=1.0,
                 spawn_x=400, spawn_y=300):
        # drift_acceleration from 0.1 to 2, max_velocity should be less than 1.5
        pygame.sprite.Sprite.__init__(self)
        self.froward_acceleration = forward_acceleration
        self.backward_acceleration = backward_acceleration
        self.max_velocity = max_velocity
        self.drift_acceleration = drift_acceleration
        self.original_image = load_image("car.png").convert()
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.rect.x = spawn_x
        self.rect.y = spawn_y
        self.angle = 0
        self.velocity = 0

    def update(self):
        self.angle = int(self.angle)
        self.angle %= 360


all_sprites = pygame.sprite.Group()
car = Car(forward_acceleration=1, backward_acceleration=3, drift_acceleration=0.3, max_velocity=0.5)
all_sprites.add(car)
pos_x = 0
pos_y = 0

running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    pressed = pygame.key.get_pressed()
    if pressed[pygame.K_UP]:
        car.velocity += 1 / (car.velocity + car.froward_acceleration)
    if pressed[pygame.K_DOWN]:
        car.velocity -= 1 / (car.velocity + car.backward_acceleration)
    car.velocity = min(car.max_velocity, car.velocity)
    pos_x += math.sin(math.radians(car.angle)) * car.velocity
    pos_y += math.cos(math.radians(car.angle)) * car.velocity
    car.rect.x += int(pos_x)
    car.rect.y += int(pos_y)
    if pressed[pygame.K_LEFT]:
        angle = int(+(car.drift_acceleration + car.velocity / 3) * math.sqrt(pos_x ** 2 + pos_y ** 2))
        car.angle += angle
        car.image = pygame.transform.rotate(car.original_image, car.angle)
        x, y = car.rect.center  # Save its current center.
        car.rect = car.image.get_rect()  # Replace old rect with new rect.
        car.rect.center = (x, y)
    if pressed[pygame.K_RIGHT]:
        angle = int(-(car.drift_acceleration + car.velocity / 3) * math.sqrt(pos_x ** 2 + pos_y ** 2))
        car.angle += angle
        car.image = pygame.transform.rotate(car.original_image, car.angle)
        x, y = car.rect.center  # Save its current center.
        car.rect = car.image.get_rect()  # Replace old rect with new rect.
        car.rect.center = (x, y)
    pos_x /= 1.08
    pos_y /= 1.08
    car.velocity /= 5
    if abs(car.velocity) < 0.01: car.velocity = 0
    all_sprites.update()
    screen.fill(BLACK)
    all_sprites.draw(screen)
    pygame.display.flip()
pygame.quit()
