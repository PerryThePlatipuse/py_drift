import math
import os
import sys

import pygame


WIDTH = 1366
HEIGHT = 768
FPS = 30
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)


#-------------скорост----------------
FORWARD_VELOCITY = 1
BACKWARD_VELOCITY = 3
MAX_VELOCITY = 10#x3
#-------------скорост----------------

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
        self.rect.x = 400
        self.rect.y = 300
        # img, rec = rot_center(self.original_image, -90, self.rect.centerx, self.rect.centery)
        # self.image = img
        # self.rect = rec
        # self.angle = 270
        self.angle = 0
        self.velocity = 0

    def update(self):
        self.angle = int(self.angle)
        self.angle %= 360



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
    if pressed[pygame.K_UP]:
        player.velocity += 1 / (player.velocity + FORWARD_VELOCITY)
    if pressed[pygame.K_DOWN]:
        player.velocity -= 1 / (player.velocity + BACKWARD_VELOCITY)
    pos_x += math.sin(math.radians(player.angle)) * player.velocity
    pos_y += math.cos(math.radians(player.angle)) * player.velocity
    player.rect.x += int(pos_x)
    player.rect.y += int(pos_y)
    if pressed[pygame.K_LEFT]:
        angle = int(+(0.3 + player.velocity / 3) * math.sqrt(pos_x ** 2 + pos_y ** 2))
        player.angle += angle
        player.image = pygame.transform.rotate(player.original_image, player.angle)
        x, y = player.rect.center  # Save its current center.
        player.rect = player.image.get_rect()  # Replace old rect with new rect.
        player.rect.center = (x, y)
    if pressed[pygame.K_RIGHT]:
        angle = int(-(0.3 + player.velocity / 3) * math.sqrt(pos_x ** 2 + pos_y ** 2))
        player.angle += angle
        player.image = pygame.transform.rotate(player.original_image, player.angle)
        x, y = player.rect.center  # Save its current center.
        player.rect = player.image.get_rect()  # Replace old rect with new rect.
        player.rect.center = (x, y)
    pos_x /= 1.08
    pos_y /= 1.08
    player.velocity /= 5
    if abs(player.velocity) < 0.01: player.velocity = 0
    all_sprites.update()
    screen.fill(BLACK)
    all_sprites.draw(screen)
    pygame.display.flip()
pygame.quit()
