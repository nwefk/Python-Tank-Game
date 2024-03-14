""" This file contains function and classes for the Artificial Intelligence used in the game.
"""

import math
from collections import defaultdict, deque
import copy
import pymunk
from pymunk import Vec2d
import gameobjects

# NOTE: use only 'map0' during development!

MIN_ANGLE_DIF = math.radians(6)   # 3 degrees, a bit more than we can turn each tick


def angle_between_vectors(vec1, vec2):
    """ Since Vec2d operates in a cartesian coordinate space we have to
        convert the resulting vector to get the correct angle for our space.
    """
    vec = vec1 - vec2
    vec = vec.perpendicular()
    return vec.angle


def periodic_difference_of_angles(angle1, angle2):
    """ Compute the difference between two angles.
    """
    return (angle1 % (2 * math.pi)) - (angle2 % (2 * math.pi))


class Ai:
    """ A simple ai that finds the shortest path to the target using
    a breadth first search. Also capable of shooting other tanks and or wooden
    boxes. """

    def __init__(self, tank, game_objects_list, tanks_list, space, currentmap):
        """ Initializes pathfinding variables, tanks and space"""
        self.tank = tank
        self.game_objects_list = game_objects_list
        self.tanks_list = tanks_list
        self.space = space
        self.currentmap = currentmap
        self.flag = None
        self.max_x = currentmap.width - 1
        self.max_y = currentmap.height - 1
        self.path = deque()
        self.move_cycle = self.move_cycle_gen()
        self.update_grid_pos()
        self.permit_metal = False

    def update_grid_pos(self):
        """ This should only be called in the beginning, or at the end of a move_cycle. """
        self.grid_pos = self.get_tile_of_position(self.tank.body.position)

    def decide(self):
        """ Main decision function that gets called on every tick of the game.
        """
        # -- Try to shoot if possible
        if not self.tank.SHOT:
            self.maybe_shoot()
        # -- Take a step in move_cycle
        next(self.move_cycle)

    def maybe_shoot(self):
        """ Makes a raycast query in front of the tank. If another tank
            or a wooden box is found, then we shoot.
        """
        x_coord = self.tank.body.position[0]
        y_coord = self.tank.body.position[1]

        start = (x_coord + 0.35 * math.cos(self.tank.body.angle + math.pi / 2),
                 y_coord + 0.35 * math.sin(self.tank.body.angle + math.pi / 2))
        end = (x_coord + self.currentmap.width * math.cos(self.tank.body.angle + math.pi / 2),
               y_coord + self.currentmap.width * math.sin(self.tank.body.angle + math.pi / 2))

        shape_filter = pymunk.ShapeFilter()
        res = self.space.segment_query_first(start, end, 0, shape_filter)
        if hasattr(res, "shape") and not isinstance(res.shape, pymunk.Segment):
            if isinstance(res.shape.parent, gameobjects.Tank) or (isinstance(res.shape.parent, gameobjects.Box) and res.shape.parent.destructable):
                self.game_objects_list.append(self.tank.shoot(self.space))
                self.tank.SHOT = True
        pass  # To be implemented

    def move_cycle_gen(self):
        """ A generator that iteratively goes through all the required steps
            to move to our goal.
        """
        while True:
            # Try to find path
            path = self.find_shortest_path()

            # If there is no path, try again
            if not path:
                self.permit_metal = True
                path = self.find_shortest_path()
                self.permit_metal = False
                if not path:
                    yield
                    continue

            # Defines the "next_coord_middle" variable
            # The destination for every cycle
            next_coord = path.popleft()
            next_x = next_coord[0] + 0.5
            next_y = next_coord[1] + 0.5
            next_coord_middle = Vec2d(next_x, next_y)

            yield

            # Define vector_angle
            vector_angle = angle_between_vectors(self.tank.body.position, next_coord_middle)

            # While current angle does not match target angle, adjust
            while abs((periodic_difference_of_angles(self.tank.body.angle, vector_angle))) > MIN_ANGLE_DIF:

                # Converts negative angles to positive angles
                if vector_angle < 0:
                    vector_angle = (2 * math.pi) + vector_angle

                # Define the absolute difference between the current angle and the target angle
                angle_difference = abs(periodic_difference_of_angles(self.tank.body.angle, vector_angle))

                if self.tank.body.angle % (2 * math.pi) < vector_angle:
                    if angle_difference > math.pi:
                        self.tank.turn_left()
                    else:
                        self.tank.turn_right()
                else:
                    if angle_difference > math.pi:
                        self.tank.turn_right()
                    else:
                        self.tank.turn_left()

                yield

            # After angle is correct, stop turning and accelerate
            self.tank.stop_turning()
            self.tank.accelerate()

            # Define driving variables
            drive = True
            every_other = True

            # While driving, check if the current distance is shorter than previous distance
            # When target tile is reached, repeat cycle.
            while drive:
                new_distance = self.tank.body.position.get_distance(next_coord_middle)
                if every_other:
                    old_distance = copy.copy(new_distance)
                    every_other = False
                else:
                    every_other = True
                if old_distance < new_distance:
                    drive = False
                self.update_grid_pos()
                yield
            self.tank.stop_moving()

    def find_shortest_path(self):
        """ A simple Breadth First Search using integer coordinates as our nodes.
            Edges are calculated as we go, using an external function.
        """
        # -- Algorithm Variables
        queue = deque()
        start_node = self.grid_pos
        queue.append(start_node)
        visited = set()
        visited.add(start_node)
        target_tile = self.get_target_tile()
        node_parents = {}

        # -- While there are tiles in the queue, go through them
        while queue:
            # -- Initialize relevant variables for cycle
            current_node = queue[0]
            queue.popleft()
            current_neighbors = self.get_tile_neighbors(current_node)

            # -- If the current node is the target node, create path
            if current_node == target_tile:
                current_child = copy.deepcopy(current_node)
                shortest_path = []
                # -- Create list by appending parent of every node.
                while current_child in node_parents:
                    shortest_path.append(node_parents[current_child])
                    current_child = node_parents[current_child]
                # -- Reverses list so it ends with target
                shortest_path.reverse()
                # -- Adds target, it wasn'ẗ a parent so it wasn't added
                shortest_path.append(target_tile.int_tuple)
                # -- Removes first part of path, so in the move_cycle the ai doesn't try to move to its current tile
                shortest_path = shortest_path[1:]
                return deque(shortest_path)

            else:
                # -- If node hasn't already been visited, "visit" it
                for i in range(len(current_neighbors)):
                    if not current_neighbors[i] in visited:
                        # -- Give nodes parents
                        node_parents[current_neighbors[i]] = current_node
                        # -- Add nodes to queue
                        queue.append(current_neighbors[i])
                        # -- Mark nodes as visited
                        visited.add(current_neighbors[i])

    def get_target_tile(self):
        """ Returns position of the flag if we don't have it. If we do have the flag,
            return the position of our home base.
        """
        if self.tank.flag is not None:
            x, y = self.tank.start_position
        else:
            self.get_flag()  # Ensure that we have initialized it.
            x, y = self.flag.x, self.flag.y
        return Vec2d(int(x), int(y))

    def get_flag(self):
        """ This has to be called to get the flag, since we don't know
            where it is when the Ai object is initialized.
        """
        if self.flag is None:
            # Find the flag in the game objects list
            for obj in self.game_objects_list:
                if isinstance(obj, gameobjects.Flag):
                    self.flag = obj
                    return self.flag

    def get_tile_of_position(self, position_vector):
        """ Converts and returns the float position of our tank to an integer position. """
        x, y = position_vector
        return Vec2d(int(x), int(y))

    def get_tile_neighbors(self, coord_vec):
        """ Returns all bordering grid squares of the input coordinate.
            A bordering square is only considered accessible if it is grass
            or a wooden box.
        """
        # -- Create tuple of input vector
        (x, y) = coord_vec
        # -- Create tuples of all neighbors
        left = (x - 1, y)
        right = (x + 1, y)
        up = (x, y - 1)
        down = (x, y + 1)
        # -- Create list of neighbors
        neighbors = [left, right, up, down]  # Find the coordinates of the tiles' four neighbors
        # -- Return filtered list
        return list(filter(self.filter_tile_neighbors, neighbors))

    def filter_tile_neighbors(self, coord):
        """ Used to filter the tile to check if it is a neighbor of the tank.
        """
        (x, y) = coord

        if 0 <= x <= self.max_x and 0 <= y <= self.max_y and (self.currentmap.boxAt(x, y) == 0 or self.currentmap.boxAt(x, y) == 2):
            return True
        elif self.permit_metal and 0 <= x <= self.max_x and 0 <= y <= self.max_y and self.currentmap.boxAt(x, y) == 3:

            return True
        else:
            return False
