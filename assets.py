# assets.py
import pygame
import os

BASE_DIR = os.path.dirname(__file__)

def load_image(relative_path):
    """
    Loads an image from the assets folder with transparency.
    Example: load_image("images/test_sprite.png")
    """
    full_path = os.path.join(BASE_DIR, "assets", relative_path)
    image = pygame.image.load(full_path).convert_alpha()
    return image
