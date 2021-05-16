import table_process
import rpgtools
import time
import random


class GM:
    def __init__(self, profile):
        self.name = 'GM'
        self.mood = 0
        self.dungeon_data = {'floor': 1, 'room': 1}
        with open(profile) as fl:
            gm_options = fl.readlines()[:3]
        # Readin optional GM parameters
        for option in gm_options:
            stripped = option.lstrip('/ ').rstrip('\n')
            if stripped.startswith('GM Name: '):
                self.name = stripped.replace('GM Name: ', '', 1)
            elif stripped.startswith('Starting Mood: '):
                self.mood = stripped.replace('Starting Mood: ', '', 1)
        self.data = table_process.Table(profile)

    def run_session(self, player):
        self.gm_print(self.data.table_fetch('Intro'))
        while player.is_alive:
            self.gm_print(self.data.table_fetch('RoomText'))
            choice = rpgtools.generate_menu(['Go Deeper', 'Use Item', 'Rest', 'Exit Dungeon'])
            if choice == 0:
                self.gm_print('Awesome.')
                self.dungeon_data['room'] += 1
            elif choice == 1:
                if player.inventory:
                    self.gm_print('Ok, look through your inventory and tell me what you want to use.')
                    player.use_inventory_item()
                else:
                    self.gm_print('Hey, you don\'t have any items!')
            elif choice == 2:
                self.gm_print('You take a break.')
            elif choice == 3:
                self.gm_print('Well, that was fun!')
                break
            self.encounter(player)

    def encounter(self, current_player):  # Overloaded Encounter Dice simulation
        v = self.data.table_fetch('Encounters')
        if v == 'Encounter':
            self.gm_print('An encounter!')
            self.generate_encounter(current_player)
        elif v == 'Nearby':
            self.gm_print('Something stirs in the darkness...')
            r = rpgtools.generate_menu(['Run', 'Hide', 'Face it'])
            if r == 0:
                if current_player.check('DEX'):
                    self.gm_print('You run away successfully.')
                else:
                    self.generate_encounter(current_player)
            elif r == 1:
                if current_player.check('INT'):
                    self.gm_print('You hide successfully.')
                else:
                    self.generate_encounter(current_player)
            elif r == 2:
                self.generate_encounter(current_player)
        elif v == 'Food':
            self.gm_print('You start to feel hungry...')
            if current_player.data['hunger'] <= 0:
                self.gm_print('You\'re starving!')
                current_player.data['HP'] -= 1
            else:
                current_player.data['hunger'] -= 1

        elif v == 'Trap':
            self.gm_print('A trap!')
            self.generate_encounter(current_player, enctype='trap')
        elif v == 'Light':
            self.gm_print('The lights flicker...')
            if current_player.data['light'] <= 0:
                self.gm_print('You\'re in the dark!')
            else:
                current_player.data['light'] -= 1

        elif not v:
            self.gm_print('Nothing happens. You\'re safe... for now.')

    def generate_encounter(self, current_player, enctype="creature"):
        if enctype == 'creature':
            self.gm_print('Give me a second to get this entry...')
            creature = Monster(self.data.table_fetch(f'Floor{self.dungeon_data["floor"]}'))
            self.gm_print(f'You encounter a {creature.name}!')
            # TODO: Add more options (charm, barter, negotiate, intimidate)
            self.run_combat(current_player, creature)
        elif enctype == 'trap':
            self.gm_print('You encounter a trap!')

    def run_combat(self, player, enemy):
        order = [enemy, player]
        self.gm_print('Roll initiative...')
        if player.check('DEX'):
            order = [player, enemy]
        to_escape = False
        while True:
            for actor in order:
                if actor == player:
                    self.gm_print('Your turn.')
                    choice = rpgtools.generate_menu(['Use Item', 'Flee'])
                    if choice == 0:
                        player.use_inventory_item([enemy])
                    elif choice == 1:
                        self.gm_print('Give me an escape check.')
                        if player.check('DEX'):
                            self.gm_print('You successfully disengage!')
                            break
                        else:
                            self.gm_print('You will flee at the end of the combat turn!')
                            to_escape = True
                else:
                    self.gm_print(f'It\'s the {actor.name}\'s turn.')
                    for attacks in range(actor.data['#AT']):
                        if rpgtools.roll('1d20') > player.data['AC']:
                            damage = rpgtools.roll(actor.data['Dmg'])
                            player.data['HP'] -= damage
                            self.gm_print(f'The {actor.name} hits you for {damage} damage!')
                        else:
                            self.gm_print(f'The {actor.name} misses!')
            if to_escape:
                self.gm_print('You flee!')
                break
            if player.data['HP'] <= 0:
                self.gm_print('You died!')
                exit()
            elif enemy.data['HP'] <= 0:
                self.gm_print(f'The {enemy.name} died!')
                break



    def gm_print(self, *args):
        print(f'({self.name})', ' '.join(args))
        time.sleep(1)


class Player:
    def __init__(self, name):
        self.name = name
        self.is_alive = True
        self.inventory = [Item('Rusty Sword', 'attack', ['HP', '-1d6']), Item('Ration', 'stat', ['hunger', 3])]
        self.xp = 0
        self.data = {
            'STR': rpgtools.roll('3d6'),
            'DEX': rpgtools.roll('3d6'),
            'CON': rpgtools.roll('3d6'),
            'INT': rpgtools.roll('3d6'),
            'WIS': rpgtools.roll('3d6'),
            'CHA': rpgtools.roll('3d6'),
            'AC': 10,
            'HP': 10,
            'light': 3,
            'hunger': 3
        }

    def check(self, stat):
        self.player_print(f'Gonna make a {stat} check...')
        res = rpgtools.roll('1d20') < self.data[stat]
        if res:
            self.player_print('Pass.')
        else:
            self.player_print('Miss.')

    def use_inventory_item(self, extra_targets=None):
        target = self
        if self.inventory:
            choice = self.inventory[rpgtools.generate_menu(self.inventory, use_attr='name')]
            self.player_print(f"I'm gonna use {choice.name}.")
            if extra_targets:
                possible_targets = [self]+extra_targets
                self.player_print("Gotta pick a target.")
                target = possible_targets[rpgtools.generate_menu(possible_targets, use_attr='name')]
            if choice.use_case == 'attack':
                self.player_print("Making an attack roll...")
                res = rpgtools.roll('1d20')+self.data['STR']
                if res > target.data['AC']:
                    self.player_print('Hit.')
                    choice.use(target)
                else:
                    self.player_print('Miss.')
            else:
                choice.use(target)

    def player_print(self, *args):
        print(f'({self.name})', ' '.join(args))
        time.sleep(1)


class Item:
    def __init__(self, name, use, data):
        self.name = name
        self.use_case = use
        self.data = data

    def use(self, target):
        if self.use_case == 'stat' or self.use_case == 'attack':
            target.data[self.data[0]] += rpgtools.roll(self.data[1])


class Monster:
    def __init__(self, statline):
        statline = statline.split(':')
        self.name = statline[0].strip()
        statline = [_.strip().split() for _ in statline[1].split(';') if _.strip() != '']
        self.data = {}
        for line in statline:
            if line[0] == 'AC':
                self.data['AC'] = int(line[1])
            elif line[0] == 'HD':
                self.data['HP'] = rpgtools.roll(f'{int(line[1])}d6')
            elif line[0] == '#AT':
                self.data['#AT'] = int(line[1])
                self.data['AttackName'] = line[2]
            elif line[0] == 'Dmg':
                self.data['Dmg'] = line[1]
                self.data['DamageName'] = line[2]
        print(self.name, self.data)


def reduce(player, stat, amt):
    player.data[stat] += amt


if __name__ == '__main__':
    myGM = GM('text/john.txt')
    myPlayer = Player(input('Enter your name: '))
    myGM.run_session(myPlayer)
