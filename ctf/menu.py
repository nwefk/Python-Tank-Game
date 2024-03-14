import pygame
from ctf import *
import client
import socket
import os
import json
selected_map = "map_wood.json"


def menu(page):
    """ Creates usable menu with different pages to play the game, switch map and quit"""
    pygame.init()
    framerate = 50
    display_width = 800
    display_height = 600

    display = pygame.display.set_mode((display_width, display_height), pygame.RESIZABLE)
    pygame.display.set_caption("Capture The Flag")
    import images

    clock = pygame.time.Clock()

    def text_obj(text, font):
        text_surface = font.render(text, True, (255, 255, 255))
        return text_surface, text_surface.get_rect()

    def display_text(text, x, y, size, font_file):
        """Displays given text on screen"""
        font = pygame.font.Font(font_file, size)
        text_surf, text_rect = text_obj(text, font)
        text_rect.center = (x, y)
        display.blit(text_surf, text_rect)

    def button(msg, font_size, x, y, w, h, color, action, click):
        """ Creates a clickable button with a specified action and color"""
        mouse = pygame.mouse.get_pos()

        font = pygame.font.Font("04b_25__.ttf", font_size)

        if x + w > mouse[0] > x and y + h > mouse[1] > y:
            pygame.draw.rect(display, color, (x, y, w, h))
            if click and action is not None:
                if action == "quit":
                    pygame.quit()

                elif action == "homepage":
                    menu(action)

                elif action == "multiplayer_host":
                    menu(action)

                elif action == "multiplayer_client":
                    menu(action)

                elif action == "map_select":
                    menu(action)

                elif action.startswith("select_map_"):
                    global selected_map
                    selected_map = action[11:]
                    print(selected_map)
                    action = "homepage"
                else:
                    print("Hello", selected_map)
                    ctf_game(selected_map, action)

                pygame.display.set_mode((display_width, display_height), pygame.RESIZABLE)

        text_surf, text_rect = text_obj(msg, font)
        text_rect.center = ((x + (w / 2)), (y + (h / 2)))
        display.blit(text_surf, text_rect)

    def display_map(width, height, box_list, size):
        """Creates a small visual representation of the specified map"""
        for y in range(0, width):
            for x in range(0, height):
                if box_list[x][y] == 0:
                    display.blit(pygame.transform.scale(images.grass,
                                                        (size, size)), (y * size + 580, x * size + i * 60 + 80))
                elif box_list[x][y] == 1:
                    display.blit(pygame.transform.scale(images.rockbox,
                                                        (size, size)), (y * size + 580, x * size + i * 60 + 80))
                elif box_list[x][y] == 2:
                    display.blit(pygame.transform.scale(images.woodbox,
                                                        (size, size)), (y * size + 580, x * size + i * 60 + 80))
                elif box_list[x][y] == 3:
                    display.blit(pygame.transform.scale(images.metalbox,
                                                        (size, size)), (y * size + 580, x * size + i * 60 + 80))

    def get_ip():
        """Gets the ip of user"""
        try:
            # Create a socket to get the local IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("1.1.1.1", 80))  # Connect to Cloudflare's DNS server
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except socket.error:
            return None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                click = True
            else:
                click = False
        display.fill((0, 0, 0))
        if page == "homepage":
            display_text("CAPTURE THE FLAG!", 400, 50, 60, "AerologicaRegular-K7day.ttf")
            button("Singleplayer", 35, 230, 120, 340, 45, (255, 0, 0), "singleplayer", click)
            button("Multiplayer Host", 35, 230, 180, 340, 45, (0, 255, 0), "multiplayer_host", click)
            button("Multiplayer Client", 35, 230, 240, 340, 45, (0, 0, 255), "multiplayer_client", click)
            button("Map Select", 35, 230, 300, 340, 45, (169, 169, 169), "map_select", click)
            button("Quit", 35, 230, 360, 340, 45, (169, 169, 169), "quit", click)

        elif page == "multiplayer_host":
            display_text("MULTIPLAYER HOST", 400, 50, 60, "AerologicaRegular-K7day.ttf")
            display_text(f"IP adress: {get_ip()}", 400, 120, 20, "PokemonGb-RAeo.ttf")
            button("Start", 35, 230, 140, 340, 45, (255, 0, 0), "multiplayer", click)
            button("Back", 35, 230, 200, 340, 45, (0, 255, 0), "homepage", click)

        elif page == "multiplayer_client":
            display_text("MULTIPLAYER CLIENT", 400, 50, 60, "AerologicaRegular-K7day.ttf")
            button("Back", 35, 230, 360, 340, 45, (0, 255, 0), "homepage", click)

        elif page == "map_select":
            display_text("LEVEL SELECT", 400, 50, 60, "AerologicaRegular-K7day.ttf")
            i = 0
            # försök med enumerate istället
            for file in os.listdir("maps/"):
                map_file = open('maps/' + file)
                map_loaded = json.load(map_file)
                i += 1
                button(str(file), 35, 230, 80 + i * 60, 340, 45,
                       (255, 0, 0), ("select_map_" + str(file)), click)
                display_map(map_loaded['width'], map_loaded['height'], map_loaded['blocks'], 6)
            i += 1
            button("Back", 35, 230, 80 + i * 60, 340, 45, (0, 255, 0), "homepage", click)

        pygame.display.flip()
        clock.tick(framerate)

    pygame.quit()


if __name__ == '__main__':
    menu("homepage")
