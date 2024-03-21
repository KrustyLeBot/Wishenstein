import pygame as pg
import pygame_textinput
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


profile_code = True
use_static_port = True
STATIC_PORT = 5000

if profile_code:
    from pyinstrument import Profiler


class Game:
    def __init__(self):
        pg.init()

        self.render_2d = False
        self.use_mouse = False

        if self.use_mouse:
            pg.mouse.set_visible(False)
        self.screen = pg.display.set_mode(RES)
        self.clock = pg.time.Clock()
        self.delta_time = 1
        self.global_trigger = False
        self.global_event = pg.USEREVENT + 0
        pg.time.set_timer(self.global_event, 40)
        if self.use_mouse:
            pg.event.set_grab(True)  # force mouse to stay focus in game windows
        self.is_server = False
        self.init = False
        self.running = True
        self.is_over = True
        self.net_init = False
        self.game_uuid = ''

        self.last_send = 0
        self.thread_working = False

        pg.font.init()
        font = pg.font.SysFont('Consolas', 24)
        self.textinput = pygame_textinput.TextInputVisualizer(font_object = font)
        self.text_surfaces = []

        self.text_surfaces.append(font.render('Press F1 to create a server.', False, (0, 0, 0)))
        self.text_surfaces.append(font.render('To connect to server, type ip:port and hit Enter (only port for localhost).', False, (0, 0, 0)))

        self.text_surfaces.append(font.render('Press G to interact with world elements.', False, (0, 0, 0)))
            

    def new_game(self, game_uuid = '', ip = ''):
        if not self.net_init:
            if self.is_server:
                self.net_server = gRPC_Server_Interface(self, STATIC_PORT if use_static_port else -1)
            else:
                self.net_client = gRPC_Client_Interface(self, ip if ':' in ip else f'localhost:{STATIC_PORT if use_static_port else ip}')
            self.net_init = True

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

        if game_uuid == '':
            self.game_uuid = str(uuid.uuid4())
        else:
            self.game_uuid = game_uuid
        
        self.init = True
        

    def update(self):
        if self.is_server:
            self.net_server.update()
            pg.display.set_caption(f"fps: {self.clock.get_fps() :.1f}, server: {self.is_server}, Listened port: {self.net_server.port}")
        elif not self.init:
            pg.display.set_caption(f"fps: {self.clock.get_fps() :.1f}")
        else:
            pg.display.set_caption(f"fps: {self.clock.get_fps() :.1f}, server: {self.is_server}")


        if self.init:
            self.player.update()
            self.raycasting.update()
            self.object_handler.update()
            distant_players_cpy = copy.copy(self.distant_players)
            for key, distant_players in distant_players_cpy.items():
                    distant_players.update()
            self.weapon.update()
        pg.display.flip()
        self.delta_time = self.clock.tick(FPS)

        #Check new game every 100ms
        if self.init and self.is_over:
            now = wpt.time()*1000
            if (not self.is_server and now - self.last_send) >= (100):
                thread = Thread(target=self.check_new_game)
                thread.start()
                self.last_send = now

    def draw(self):
        if self.init:
            if self.render_2d:
                self.screen.fill('black')
                self.map.draw()
            else:
                self.object_renderer.draw()
                self.weapon.draw()
        else:
            self.screen.fill((225, 225, 225))
            y = 0
            line_space = 30
            for text_surface in self.text_surfaces:
                self.screen.blit(text_surface, (10, y))
                y += line_space
            y += line_space
            self.screen.blit(self.textinput.surface, (10, y))
            pass

    def check_events(self):
        self.global_trigger = False
        events = pg.event.get()
        self.textinput.update(events)
        for event in events:
            if event.type == pg.QUIT or (event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE):
                self.exit()
            elif not self.init:
                if event.type == pg.KEYDOWN and event.key == pg.K_F1:
                    pg.display.flip()
                    self.is_server = True
                    self.new_game()
                elif event.type == pg.KEYDOWN and event.key == pg.K_RETURN:
                    pg.display.flip()
                    self.is_server = False
                    self.new_game(ip = self.textinput.value)
            elif event.type == self.global_event:
                self.global_trigger = True
            elif event.type == pg.KEYDOWN and event.key == pg.K_F1 and self.is_over and self.is_server:
                pg.display.flip()
                self.new_game()
            elif event.type == pg.KEYDOWN and event.key == pg.K_g:
                self.object_handler.toggle_sprites()
            
            if self.init:
                self.player.single_fire_event(event)

    def run(self):
        while self.running:
            self.check_events()
            self.update()
            self.draw()

    def check_new_game(self):
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



if __name__ == "__main__":
    if profile_code:
        profiler = Profiler(interval = 0.0001)
        profiler.start()

    game = Game()
    game.run()

    if profile_code:
        profiler.stop()
        profiler.print()
    exit()
