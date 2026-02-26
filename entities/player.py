import pygame
from assets import load_image


class Player(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()

        # Load image
        self.image = load_image("images/test_sprite.png")

        # Create rectangle
        self.rect = self.image.get_rect(center=pos)

        # Movement speed (pixels per second)
        self.speed = 250

    def update(self, dt):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed * dt
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed * dt
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed * dt
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed * dt