import pygame as pg
import sys
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

render_2d = False


class Game:
    def __init__(self, startServer):
        pg.init()
        if use_mouse:
            pg.mouse.set_visible(False)
        self.screen = pg.display.set_mode(RES)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0
        pg.time.set_timer(self.global_event, 40)
        if use_mouse:
            pg.event.set_grab(True)  # force mouse to stay focus in game windows
        self.is_server = startServer
        self.running = True
        self.game_uuid = ''

        self.last_send = 0
        self.thread_working = False

        if self.is_server:
            self.net_server = gRPC_Server_Interface(self)
            self.is_over = False
        else:
            self.net_client = gRPC_Client_Interface(self)
            self.is_over = True
            
        self.new_game()

    def new_game(self, game_uuid = ''):
        if game_uuid == '':
            self.game_uuid = str(uuid.uuid4())
        else:
            self.game_uuid = game_uuid
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
        distant_players_cpy = copy.copy(self.distant_players)
        for key, distant_players in distant_players_cpy.items():
                distant_players.update()
        self.weapon.update()
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)
        pg.display.set_caption(f"fps: {self.clock.get_fps() :.1f}, pos: {self.player.pos[0] :.1f}, {self.player.pos[1] :.1f}, server: {self.is_server}")

        #Check new game every 100ms
        if self.is_over:
            now = time.time()*1000
            if (not self.is_server and now - self.last_send) >= (100):
                thread = Thread(target=self.check_new_game)
                thread.start()
                self.last_send = now

    def draw(self):
        if render_2d:
            self.screen.fill('black')
            self.map.draw()
        else:
            self.object_renderer.draw()
            self.weapon.draw()

    def check_events(self):
        self.global_trigger = False
        for event in pg.event.get():
            if event.type == pg.QUIT or (
                event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE
            ):
                self.exit()
            elif event.type == self.global_event:
                self.global_trigger = True
            elif event.type == pg.KEYDOWN and event.key == pg.K_F1 and self.is_over and self.is_server:
                pg.display.flip()
                self.new_game()
            self.player.single_fire_event(event)

    def run(self):
        while self.running:
            self.check_events()
            self.update()
            self.draw()

    def check_new_game(self):
        #If another thread is working, ignore
        if self.thread_working:
            return
        self.thread_working = True

        result = self.net_client.CheckNewGame()

        if result.game_uuid != self.game_uuid:
            self.is_over = False
            self.new_game(result.game_uuid)

        self.thread_working = False

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
