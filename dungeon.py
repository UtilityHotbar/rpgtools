import coretools
import random
import time


class Dungeon:
    def __init__(self, name, layers, height=20, width=20, display=False, limit='4d6'):
        self.name = name
        self.max_layers = layers
        self.directory = [[] for _ in range(self.max_layers)]
        self.width = width
        self.height = height
        self.limit = limit
        self.map = [[['.']*self.width for _ in range(self.height)] for i in range(self.max_layers)]
        curr_layer = 0
        for _ in range(self.max_layers):
            self.generate_layer(curr_layer, display)
            curr_layer += 1

    def generate_layer(self, curr_layer, display):
        layer = self.map[curr_layer]
        layer[10][10] = '<'
        curr_dir = self.directory[curr_layer]
        room_num = 0
        curr_dir.append(Room('EXIT', None, '<', [10, 10]))
        foundexit = False
        while room_num < coretools.roll(self.limit):
            candidates = []
            targetroom = None
            # Scan for rooms that you can expand from
            for x in range(self.width):
                for y in range(self.height):
                    if layer[y][x] in ['<', '#']:
                        candidates.append([x, y])
            # Pick random room to expand
            expand = random.choice(candidates)
            for room in curr_dir:
                if [room.x, room.y] == expand:
                    targetroom = room
            directions = {'n': [0, -1], 's': [0, 1], 'e': [1, 0], 'w': [-1, 0]}
            directions_available = ['n', 's', 'e', 'w']
            for direction in directions:
                tx = expand[0] + directions[direction][0]
                ty = expand[1] + directions[direction][1]
                if tx < 0 or tx > self.width-1:
                    directions_available.remove(direction)
                    continue
                if ty < 0 or ty > self.height-1:
                    directions_available.remove(direction)
                    continue
                ty = expand[1] + directions[direction][1]
                if layer[ty][tx] != '.':
                    directions_available.remove(direction)
            if directions_available != []:
                chosen = random.choice(directions_available)
                tx = expand[0] + directions[chosen][0]
                ty = expand[1] + directions[chosen][1]
                if coretools.roll('1d20') == 1 and not foundexit:
                    char = '>'
                    foundexit = True
                else:
                    char = '#'
                layer[ty][tx] = char
                newroom = Room(targetroom, chosen, char, [tx, ty])
                curr_dir.append(newroom)
                targetroom.exits[chosen] = newroom
                room_num += 1
            if display:
                self.display_progress(layer)
                time.sleep(0.1)
        if not foundexit:
            curr_dir[-1].kind = '>'
            layer[curr_dir[-1].y][curr_dir[-1].x] = '>'
            if display:
                self.display_progress(layer)
                time.sleep(0.1)

    def display_progress(self, layer):
        print('\n'.join([''.join(_) for _ in layer]))
        print(' ')

    def display_map(self, curr_layer, cx, cy, display=True):
        rooms = self.directory[curr_layer]
        canvas = [['?' for _ in range(15)] for _ in range(15)]
        centre_x = 2
        centre_y = 2
        for room in rooms:
            if room.visited and room.x in range(cx-1, cx+2) and room.y in range(cy-1, cy+2):
                centre_x = 2+5*(room.x-cx+1)
                centre_y = 2+5*(room.y-cy+1)
                for x in range(centre_x-2, centre_x+3):
                    for y in range(centre_y-2, centre_y+3):
                        if x in [centre_x-2, centre_x+2] or y in [centre_y-2, centre_y+2]:
                            canvas[y][x] = '#'
                        else:
                            canvas[y][x] = '.'
                for exit in room.exits:
                    if exit == 'n':
                        canvas[centre_y-2][centre_x] = '+'
                    elif exit == 's':
                        canvas[centre_y+2][centre_x] = '+'
                    elif exit == 'e':
                        canvas[centre_y][centre_x+2] = '+'
                    elif exit == 'w':
                        canvas[centre_y][centre_x-2] = '+'
                if room.x == cx and room.y == cy:
                    canvas[centre_y][centre_x] = '@'
        fincanvas = '\n'.join([''.join(_) for _ in canvas])
        if display:
            print(fincanvas)
        return fincanvas


class Room:
    def __init__(self, parent, entry_direction, kind, coords):
        inverse = {'n': 's', 's': 'n', 'e': 'w', 'w': 'e'}
        self.entrance = parent
        self.kind = kind
        if entry_direction:
            self.exits = {inverse[entry_direction]: parent}
        else:
            self.exits = {}
        self.x = coords[0]
        self.y = coords[1]
        self.visited = False
        self.data = {}  # Use to store extra data about rooms in case you make them more complicated


def explore(dungeon):
    curr_layer = 0
    layer = dungeon.directory[curr_layer]
    curr_room = layer[0]
    while True:
        curr_room.visited = True
        dungeon.display_map(curr_layer, curr_room.x, curr_room.y)
        print(f'You are in a room of type {curr_room.kind}')
        ways_out = list(curr_room.exits.keys())
        c = coretools.generate_menu(ways_out+['Back'])
        if c == len(ways_out+['Back'])-1:
            curr_room = curr_room.entrance
            if curr_room == 'EXIT':
                print('You left the dungeon')
                break
        else:
            curr_room = curr_room.exits[ways_out[c]]


if __name__ == '__main__':
    myDungeon = Dungeon('test', 3, display=False)
    explore(myDungeon)
