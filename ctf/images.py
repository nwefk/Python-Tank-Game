""" Graphics assests for the game
"""

import pygame
import os

main_dir = os.path.split(os.path.abspath(__file__))[0]
loaded_image_path = None


def load_image(file, return_path=False):
    """ Load an image from the data directory. """
    global loaded_image_path
    file = os.path.join(main_dir, 'data', file)
    try:
        surface = pygame.image.load(file)
    except pygame.error:
        raise SystemExit('Could not load image "%s" %s' % (file, pygame.get_error()))

    if return_path:
        return surface.convert_alpha()
    return surface.convert_alpha()


TILE_SIZE = 40  # Define the default size of tiles

explosion = load_image('explosion.png')  # Image of an explosion

grass = load_image('grass.png')  # Image of a grass tile

rockbox = load_image('rockbox.png')  # Image of a rock box (wall)

metalbox = load_image('metalbox.png')  # Image of a metal box

woodbox = load_image('woodbox.png')  # Image of a wood box

flag = load_image('flag.png')  # Image of flag

bullet = load_image('bullet.png')  # Image of bullet

# List of image of tanks of different colors
tanks = [load_image('tank_orange.png'), load_image('tank_blue.png'), load_image('tank_white.png'),
         load_image('tank_yellow.png'), load_image('tank_red.png'), load_image('tank_gray.png')]

# List of image of bases corresponding to the color of each tank
bases = [load_image('base_orange.png'), load_image('base_blue.png'), load_image('base_white.png'),
         load_image('base_yellow.png'), load_image('base_red.png'), load_image('base_gray.png')]


def find_matching_image(surface_to_match):
    """ Find the first matching image in the data folder. """
    data_folder = os.path.join(main_dir, 'data')
    for filename in os.listdir(data_folder):
        if filename.endswith(".png"):
            file_path = os.path.join(data_folder, filename)
            if filename == "bullet.png":
                loaded_surface = bullet

            else:
                loaded_surface = load_image(filename)

            if are_surfaces_equal(surface_to_match, loaded_surface):
                return file_path


def are_surfaces_equal(surface1, surface2):
    """ Check if the content of two surfaces is equal. """
    width, height = surface1.get_size()

    # Check dimensions
    if surface2.get_size() != (width, height):
        return False

    # Check pixel data
    for x in range(width):
        for y in range(height):
            pixel1 = surface1.get_at((x, y))
            pixel2 = surface2.get_at((x, y))

            if pixel1 != pixel2:
                return False

    return True
