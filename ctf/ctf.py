""" Main file for the game.
"""
from curses import KEY_DOWN, KEY_UP
import pygame
from pygame.locals import *
from pygame.color import *
import pymunk
from menu import *
import sys
import getopt


# ----- Initialisation ----- #
def ctf_game(map, gamemode):
    """ The entire Capture The Flag game, called in menu.py"""
    import json
    # -- Initialise the display
    pygame.mixer.pre_init(44100, -16, 1, 2)
    pygame.init()
    pygame.mixer.init()
    pygame.display.set_mode()

    # -- Initialise the clock
    clock = pygame.time.Clock()
    # -- Can disable AI for debugging
    ai_toggle = True

    is_map_loaded = False

    # -- Initialise the physics engine
    space = pymunk.Space()
    space.gravity = (0.0, 0.0)
    space.damping = 0.1  # Adds friction to the ground for all objects

    # -- Command line arguments
    # Remove 1st argument from the
    # list of command line arguments
    argumentList = sys.argv[1:]

    # Options
    options = "m:"

    # Long options
    long_options = ["map"]

    # Sounds
    scream_sound = pygame.mixer.Sound("scream.ogg")
    explosion_sound = pygame.mixer.Sound("explosion.ogg")

    def explosion_visual(x, y, game_objects_list):
        explosion = gameobjects.Explosion(x, y, game_objects_list)
        explosion_sound.play()
        game_objects_list.append(explosion)

    try:

        # Parsing argument
        arguments, values = getopt.getopt(argumentList, options, long_options)

        # checking each argument
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-m", "--map"):
                map_file = open(('maps/% s') % (currentValue))
                map_loaded = json.load(map_file)
                is_map_loaded = True
                print("YES")

    except getopt.error as err:
        # output error, and return with an error code
        print(str(err))

    if not is_map_loaded and isinstance(map, str) and map.endswith('.json'):
        map_file = open('maps/' + map)
        map_loaded = json.load(map_file)

    collision_types = {
        "bullet": 1,
        "tank": 2,
        "box": 3
    }

    def collision_bullet_tank(arb, space, data):
        bullet_coords = arb.shapes[0].body.position
        scream_sound.play()
        explosion_visual(bullet_coords[0], bullet_coords[1], game_objects_list)
        space.remove(arb.shapes[0], arb.shapes[0].body)
        game_objects_list.remove(arb.shapes[0].parent)
        arb.shapes[1].parent.body.position = arb.shapes[1].parent.start_position
        arb.shapes[1].parent.body.angle = arb.shapes[1].parent.start_angle
        if arb.shapes[1].parent.flag:
            arb.shapes[1].parent.flag = None
            flag.is_on_tank = False
        arb.shapes[1].parent.body.position = arb.shapes[1].parent.start_position

        return False

    def collision_bullet_box(arb, space, data):
        bullet_coords = arb.shapes[0].body.position
        box_coords = arb.shapes[1].body.position
        explosion_visual(bullet_coords[0], bullet_coords[1], game_objects_list)
        if arb.shapes[1].parent.destructable:
            space.remove(arb.shapes[1], arb.shapes[1].body)
            game_objects_list.remove(arb.shapes[1].parent)

        space.remove(arb.shapes[0], arb.shapes[0].body)
        game_objects_list.remove(arb.shapes[0].parent)
        return True

    tank_handler = space.add_collision_handler(collision_types["bullet"], collision_types["tank"])
    tank_handler.pre_solve = collision_bullet_tank

    box_handler = space.add_collision_handler(collision_types["bullet"], collision_types["box"])
    box_handler.pre_solve = collision_bullet_box
    # -- Import from the ctf framework
    # The framework needs to be imported after initialisation of pygame
    import ai
    import images
    import gameobjects
    import maps
    import socket
    import threading
    import json

    # -- Constants
    FRAMERATE = 50

    # -- Variables

    #   Define the current level
    try:
        map_loaded
    except NameError:
        print('No map supplied, loading default map')
        current_map = maps.map0
    else:
        current_map = maps.Map(map_loaded["width"],
                               map_loaded["height"],
                               map_loaded["blocks"],
                               map_loaded["tanks"],
                               map_loaded["flag"])

    #   List of all game objects
    game_objects_list = []
    tanks_list = []
    bases_list = []

    # -- Resize the screen to the size of the current level
    screen = pygame.display.set_mode(current_map.rect().size)

    # Generate the background
    background = pygame.Surface(screen.get_size())

    #   Copy the grass tile all over the level area
    for x in range(0, current_map.width):
        for y in range(0, current_map.height):
            # The call to the function "blit" will copy the image
            # contained in "images.grass" into the "background"
            # image at the coordinates given as the second argument
            background.blit(images.grass, (x * images.TILE_SIZE, y * images.TILE_SIZE))

    # Create the boxes
    for x in range(0, current_map.width):
        for y in range(0, current_map.height):
            # Get the type of boxes
            box_type = current_map.boxAt(x, y)
            # If the box type is not 0 (aka grass tile), create a box
            if (box_type != 0):
                # Create a "Box" using the box_type, aswell as the x, y coordinates,
                # and the pymunk space
                box = gameobjects.get_box_with_type(x, y, box_type, space)
                game_objects_list.append(box)

    # Create the flag
    flag = gameobjects.Flag(current_map.flag_position[0], current_map.flag_position[1])
    game_objects_list.append(flag)

    ai_list = []
    # Create the tanks
    # Loop over the starting poistion
    for i in range(0, len(current_map.start_positions)):
        # Get the starting position of the tank "i"
        pos = current_map.start_positions[i]
        # Create their bases
        base = gameobjects.GameVisibleObject(pos[0], pos[1], images.bases[i])
        bases_list.append(base)
        game_objects_list.append(base)

        # Create the tank, images.tanks contains the image representing the tank
        tank = gameobjects.Tank(pos[0], pos[1], pos[2], images.tanks[i], space)
        # Add the tank to the list of tanks
        tanks_list.append(tank)
        game_objects_list.append(tank)

    for i in range(len(tanks_list)):
        if i > 0:
            ai_instance = ai.Ai(tanks_list[i], game_objects_list, tanks_list, space, current_map)
            ai_list.append(ai_instance)

    # Create a Fog object at the position of the first tank in the list.
    fog = gameobjects.Fog(tanks_list, screen)
    max_connections = len(tanks_list)

    # Create Boundaries
    boundary_body = space.static_body
    map_boundaries = (current_map.rect().size[0] / images.TILE_SIZE, current_map.rect().size[1] / images.TILE_SIZE)
    walls = [pymunk.Segment(boundary_body, (0, 0), (0, map_boundaries[1]), 0.0),
             pymunk.Segment(boundary_body, (map_boundaries[0], 0), (map_boundaries[0], map_boundaries[1]), 0.0),
             pymunk.Segment(boundary_body, (0, 0), (map_boundaries[0], 0), 0.0),
             pymunk.Segment(boundary_body, (0, map_boundaries[1]), (map_boundaries[0], map_boundaries[1]), 0.0)]
    space.add(*walls)

    # ----- Main Loop -----#

    # -- Control whether the game run
    running = True
    skip_update = 0

    def player1(event):
        if event.type == KEYDOWN and event.key == K_UP:
            tanks_list[0].accelerate()

        if event.type == KEYDOWN and event.key == K_DOWN:
            tanks_list[0].decelerate()

        if event.type == KEYUP and (event.key == K_DOWN or event.key == K_UP):
            tanks_list[0].stop_moving()

        if event.type == KEYUP and (event.key == K_LEFT or event.key == K_RIGHT):
            tanks_list[0].stop_turning()

        if event.type == KEYDOWN and event.key == K_LEFT:
            tanks_list[0].turn_left()

        if event.type == KEYDOWN and event.key == K_RIGHT:
            tanks_list[0].turn_right()

        if event.type == KEYDOWN and event.key == K_k:
            ai_list[0].decide()

        if event.type == KEYDOWN and event.key == K_RETURN and not tanks_list[0].SHOT:
            game_objects_list.append(tanks_list[0].shoot(space))
            tanks_list[0].SHOT = True

        if event.type == KEYDOWN and event.key == K_r:
            print(tanks_list[0].body.angle)

    def player_online(event):
        if event["type"] == KEYDOWN and event["key"] == K_UP:
            tanks_list[event["player"]].accelerate()

        if event["type"] == KEYDOWN and event["key"] == K_DOWN:
            tanks_list[event["player"]].decelerate()

        if event["type"] == KEYUP and (event["key"] == K_DOWN or event["key"] == K_UP):
            tanks_list[event["player"]].stop_moving()

        if event["type"] == KEYUP and (event["key"] == K_LEFT or event["key"] == K_RIGHT):
            tanks_list[event["player"]].stop_turning()

        if event["type"] == KEYDOWN and event["key"] == K_LEFT:
            tanks_list[event["player"]].turn_left()

        if event["type"] == KEYDOWN and event["key"] == K_RIGHT:
            tanks_list[event["player"]].turn_right()

        if event["type"] == KEYDOWN and event["key"] == K_RETURN and not tanks_list[0].SHOT:
            game_objects_list.append(tanks_list[event["player"]].shoot(space))
            tanks_list[event["player"]].SHOT = True

    def serialize_game_objects(game_objects):
        serialized_objects = []
        for obj in game_objects:
            serialized_objects.append(obj.to_json())

        return json.dumps(serialized_objects)

    def send_screen(client_socket, player_number):
        player_data = json.dumps(player_number).encode()
        client_socket.sendall(player_data)
        while True:
            try:
                data = client_socket.recv(1024)
                if data:
                    json_data = data.decode()
                    try:
                        event = json.loads(json_data)
                        player_online(event)
                    except Exception as e:
                        print(e)
            except socket.timeout:
                # Handle the timeout (no data available)
                pass
            except Exception as e:
                print(e)

            serialized_data = serialize_game_objects(game_objects_list)
            client_socket.sendall(serialized_data.encode())

    def get_ip():
        try:
            # Create a socket to get the IP address
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("1.1.1.1", 5005))  # Connect to Cloudflare's DNS server
            local_ip = s.getsockname()[0]
            s.close
            return local_ip
        except socket.error:
            return None

    def server_thread():
        # Set up server
        server_ip = get_ip()
        server_port = 5005
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((server_ip, server_port))
        server_socket.listen(max_connections)
        order_number = 0

        print(f"Server listening on {server_ip}:{server_port}")

        # Wait for a clients to connect
        try:
            while True:

                client_socket, client_address = server_socket.accept()
                print(f"Connection from {client_address}")
                client_handler = threading.Thread(target=send_screen, args=(client_socket, order_number))  # Creates a new thread to handle each player
                client_handler.start()
                if order_number > 0 and ai_toggle:
                    ai_list.pop(0)  # Removes AI control over the connected player's tank
                order_number += 1

        except Exception as e:
            print(e)

    if gamemode == "multiplayer":
        server_thread = threading.Thread(target=server_thread)
        server_thread.start()

    while running:
        # -- Handle the events
        for event in pygame.event.get():
            # Check if we receive a QUIT event (for instance, if the user press the
            # close button of the wiendow) or if the user press the escape key.
            if event.type == QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                running = False

            if gamemode == "singleplayer":
                player1(event)

        if ai_toggle:
            for i in range(len(ai_list)):
                ai_list[i].update_grid_pos()
                ai_list[i].decide()

        # -- Update flag condition
        for tank in tanks_list:
            tank.try_grab_flag(flag)
            if tank.has_won():
                running = False

        # -- Update physics

        if skip_update == 0:
            # Loop over all the game objects and update their speed in function of their
            # acceleration.
            for obj in game_objects_list:
                obj.update()
            skip_update = 2
        else:
            skip_update -= 1

        #   Check collisions and update the objects position
        space.step(1 / FRAMERATE)

        #   Update object that depends on an other object position (for instance a flag)
        for obj in game_objects_list:
            obj.post_update()

        # -- Update Display

        # Display the background on the screen
        screen.blit(background, (0, 0))

        # Update the display of the game objects on the screen
        for obj in game_objects_list:
            obj.update_screen(screen)

        # Update fog position based on the first tank's position and refresh it on the screen.
        if gamemode == "singleplayer":
            fog.update_()
            fog.draw(screen)

        # Redisplay the entire screen (see double buffer technique)
        # pixel_data = pygame.image.tostring(screen, 'RGB')

        # Send the pixel data to the client

        pygame.display.flip()
        # client_socket.sendall(pixel_data)
        #   Control the game framerate
        clock.tick(FRAMERATE)


if __name__ == '__main__':
    ctf_game(map, "singleplayer")
