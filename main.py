import signal
import pygame as pg
import sys
import time
from settings import *
from map import *
from player import *
from raycasting import *
from object_renderer import *
from object_handler import *
from weapon import *
from sound import *
from pathfinding import *
from gRPC_interfaces import *


class Game:
    def __init__(self, startServer):
        pg.init()
        pg.mouse.set_visible(False)
        self.screen = pg.display.set_mode(RES)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0
        pg.time.set_timer(self.global_event, 40)
        #pg.event.set_grab(True)  # force mouse to stay focus in game windows
        self.is_over = True
        self.is_server = startServer
        self.running = True

        if self.is_server:
            self.net_server = gRPC_Server_Interface(self)
        else:
            self.net_client = gRPC_Client_Interface(self)

        self.new_game()

    def new_game(self):
        pg.event.clear()           

        self.map = Map(self)
        self.player = Player(self)
        self.distant_players = {}
        self.object_renderer = ObjectRenderer(self)
        self.raycasting = RayCasting(self)
        self.object_handler = ObjectHandler(self)
        self.weapon = Weapon(self)
        self.sound = Sound(self)
        self.pathfinding = PathFinding(self)
        

    def update(self):
        if self.is_server:
            self.net_server.update()
        self.player.update()
        self.raycasting.update()
        self.object_handler.update()
        self.weapon.update()
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(
            f"fps: {self.clock.get_fps() :.1f}, pos: {self.player.pos[0] :.1f}, {self.player.pos[1] :.1f}, server: {self.is_server}"
        )

    def draw(self):
        # self.object_renderer.draw()
        # self.weapon.draw()
        self.screen.fill('black')
        self.map.draw()
        self.player.draw()
        for key, distant_players in self.distant_players.items():
            distant_players.draw()

    def check_events(self):
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT or (
                event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE
            ):
                self.exit()
            elif event.type == self.global_event:
                self.global_trigger = True
            elif event.type == pg.KEYDOWN and event.key == pg.K_F1 and self.is_over:
                pg.display.flip()
                self.new_game()
            self.player.single_fire_event(event)

    def run(self):
        while self.running:
            self.check_events()
            self.update()
            self.draw()

    def exit_gracefully(self):
        pass

    def exit(self):
        self.running = False
        if self.is_server:
            self.net_server.server.stop(0)
        exit()


if __name__ == "__main__":
    startServer = False
    if len(sys.argv) == 2:
        startServer = sys.argv[1] == 'True'
    
    game = Game(startServer)
    game.run()
