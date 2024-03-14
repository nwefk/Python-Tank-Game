import socket
import threading
import json
import pygame
import time
import copy

from pygame.color import *
from pygame.locals import QUIT


# Pygame initialization
def ctf_client(server_ip):
    """ Creates game client"""
    pygame.init()
    pygame.display.set_mode()
    import maps
    import images

    current_map = maps.map0
    screen = pygame.display.set_mode(current_map.rect().size)
    pygame.display.set_caption("CTF Client")
    background = pygame.Surface(screen.get_size())

    for x in range(0, current_map.width):
        for y in range(0, current_map.height):
            background.blit(images.grass, (x * images.TILE_SIZE, y * images.TILE_SIZE))

    # Connects to the server and sets number on player
    server_port = 5005
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((server_ip, server_port))
    player_number = client_socket.recv(1).decode()
    player = copy.copy(int(player_number))
    player_number = None

    # Serializes events
    def serialize_event(event):
        event_dict = {
            'type': event.type,
            'player': player
        }
        if event.type in (pygame.KEYDOWN, pygame.KEYUP):
            event_dict['key'] = event.key
        return json.dumps(event_dict)

    # Sends serialized events
    def event_handler(client_socket):
        while True:
            for event in pygame.event.get():
                serialized_event = serialize_event(event)
                client_socket.sendall(serialized_event.encode())

            event_dict = {'type': None}
            no_event = json.dumps(event_dict)
            client_socket.sendall(no_event.encode())
            time.sleep(0.04)

    event_thread = threading.Thread(target=event_handler, args=(client_socket,))
    event_thread.start()

    # Receives and draws object data
    def receive_screen():

        while True:
            data = client_socket.recv(16384)

            json_data = data.decode()
            try:
                game_objects = json.loads(json_data)

            except Exception as e:
                print(e)

            screen.blit(background, (0, 0))
            for obj in game_objects:
                sprite = pygame.image.load(obj["sprite"])
                sprite = pygame.transform.rotate(sprite, obj["orientation"])
                screen.blit(sprite, (obj["x"], obj["y"]))

            pygame.display.flip()
            data = None

    receive_screen()


if __name__ == '__main__':
    ctf_client("10.244.32.22")
