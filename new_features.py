import math
import os
import sys
import time

import pygame

WIDTH = 800
HEIGHT = 650
FPS = 30
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


def rot_center(image, angle, x, y):
    rotated_image = pygame.transform.rotate(image, angle)
    new_rect = rotated_image.get_rect(center=image.get_rect(center=(x, y)).center)

    return rotated_image, new_rect


class Player(pygame.sprite.Sprite):
    def __init__(self):
        pygame.sprite.Sprite.__init__(self)
        self.original_image = load_image("car.png").convert()
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.angle = 0

    def update(self):
        self.image = pygame.transform.rotate(self.original_image, self.angle)
        self.angle += 1  # Value will reapeat after 359. This prevents angle to overflow.
        self.angle %= 360
        x, y = self.rect.center  # Save its current center.
        self.rect = self.image.get_rect()  # Replace old rect with new rect.
        self.rect.center = (x, y)


all_sprites = pygame.sprite.Group()
player = Player()
all_sprites.add(player)
pos_x = 0
pos_y = 0

running = True
while running:
    clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    pressed = pygame.key.get_pressed()
    # img, rec = rot_center(player.image, 10, player.rect.centerx, player.rect.centery)
    # player.image = img
    # player.rect = rec
    # time.sleep(1)
    # # if pressed[pygame.K_LEFT]:
    # #     player.rotation -= (1 + player.velocity / 3) * math.sqrt(pos_x ** 2 + pos_y ** 2)
    # #     player.image = pygame.transform.rotate(player.image, -(1 + player.velocity / 3) * math.sqrt(
    # #         pos_x ** 2 + pos_y ** 2))
    # # if pressed[pygame.K_RIGHT]:
    # #     player.rotation += (1 + player.velocity / 3) * math.sqrt(
    # #         pos_x ** 2 + pos_y ** 2)
    # #     player.image = pygame.transform.rotate(player.image, +(1 + player.velocity / 3) * math.sqrt(
    # #         pos_x ** 2 + pos_y ** 2))
    all_sprites.update()
    screen.fill(BLACK)
    all_sprites.draw(screen)
    pygame.display.flip()
pygame.quit()
