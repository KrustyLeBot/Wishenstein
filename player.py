import pygame as pg
import math
import uuid
import time
import grpc
import copy
from threading import Thread
from settings import *
from map import *


class Player:
    def __init__(self, game):
        self.game = game
        self.x, self.y = PLAYER_POS
        self.angle = PLAYER_ANGLE
        self.shot = False
        self.health = PLAYER_MAX_HEALTH
        self.rel = 0
        self.health_recovery_delay = 700
        self.time_prev = pg.time.get_ticks()
        self.uuid = str(uuid.uuid4())
        self.last_send = 0
        self.last_thread_time = 0
        self.thread_working = False

    def recover_health(self):
        if self.check_health_recovery_delay() and self.health < PLAYER_MAX_HEALTH:
            self.health += 1

    def check_health_recovery_delay(self):
        time_now = pg.time.get_ticks()
        if time_now - self.time_prev > self.health_recovery_delay:
            self.time_prev = time_now
            return True

    def check_game_over(self):
        if self.health < 1:
            self.game.object_renderer.game_over()
            pg.display.flip()
            pg.time.delay(1500)
            self.game.new_game()

    def get_damage(self, damage):
        self.health -= damage
        self.time_prev = pg.time.get_ticks() #reset health gen when getting hit
        self.game.object_renderer.player_damage()
        self.game.sound.player_pain.play()
        self.check_game_over()

    def single_fire_event(self, event):
        if event.type == pg.MOUSEBUTTONDOWN:
            if event.button == 1 and not self.shot and not self.game.weapon.reloading:
                self.shot = True
                self.game.sound.shotgun.play()
                self.game.weapon.reloading = True

    def movement(self):
        sin_a = math.sin(self.angle)
        cos_a = math.cos(self.angle)

        dx, dy = 0, 0
        speed = PLAYER_SPEED * self.game.delta_time
        speed_sin = speed * sin_a
        speed_cos = speed * cos_a

        keys = pg.key.get_pressed()
        if (KEY_MAPPING == WASD_MAPPING and keys[pg.K_w]) or (
            KEY_MAPPING == ZQSD_MAPPING and keys[pg.K_z]
        ):
            dx += speed_cos
            dy += speed_sin
        if keys[pg.K_s]:
            dx -= speed_cos
            dy -= speed_sin
        if (KEY_MAPPING == WASD_MAPPING and keys[pg.K_a]) or (
            KEY_MAPPING == ZQSD_MAPPING and keys[pg.K_q]
        ):
            dx += speed_sin
            dy -= speed_cos
        if keys[pg.K_d]:
            dx -= speed_sin
            dy += speed_cos

        self.check_wall_collision(dx, dy)

        self.angle %= math.tau

    def check_wall(self, x, y):
        return (x, y) not in self.game.map.world_map

    def check_wall_collision(self, dx, dy):
        scale = PLAYER_SIZE_SCALE / self.game.delta_time
        if self.check_wall(int(self.x + dx * scale), int(self.y)):
            self.x += dx
        if self.check_wall(int(self.x), int(self.y + dy * scale)):
            self.y += dy

    def draw(self):
        pg.draw.line(
            self.game.screen,
            "yellow",
            (self.x * 100, self.y * 100),
            (
                self.x * 100 * WIDTH * math.cos(self.angle),
                self.y * 100 * WIDTH * math.sin(self.angle),
            ),
            2,
        )
        pg.draw.circle(self.game.screen, "green", (self.x * 100, self.y * 100), 15)

    def mouse_control(self):
        mx, my = pg.mouse.get_pos()
        if mx < MOUSE_BORDER_LEFT or mx > MOUSE_BORDER_RIGHT:
            pg.mouse.set_pos([HALF_WIDTH, HALF_HEIGHT])
        self.rel = pg.mouse.get_rel()[0]
        self.rel = max(-MOUSE_MAX_REL, min(MOUSE_MAX_REL, self.rel))
        self.angle += self.rel * MOUSE_SENSITIVITY * self.game.delta_time

    def update(self):
        self.movement()
        self.mouse_control()
        self.recover_health()

        #Send pos every 100ms in a separate thread
        now = time.time()*1000
        if (not self.game.is_server and now - self.last_send) >= (100):
            thread = Thread(target=self.send_position)
            thread.start()
            self.last_send = now

    @property
    def pos(self):
        return self.x, self.y

    @property
    def map_pos(self):
        return int(self.x), int(self.y)
    
    def send_position(self):
        #If another thread is working, ignore
        if self.thread_working:
            return
        self.thread_working = True

        try:
            result = self.game.net_client.SendPosition(uuid = self.uuid, pos_x = self.x, pos_y = self.y, pos_angle = self.angle)
            print(f'yield receive {result}')
            for position in result:
                print(f'yield receive {result}')
                self.game.distant_players[position.uuid] = DistantPlayer(self.game, position.uuid, position.pos_x, position.pos_y, position.pos_angle)
        except grpc.RpcError as rpc_error:
            pass
    
        self.thread_working = False


class DistantPlayer:
    def __init__(self, game, uuid, pos_x, pos_y, pos_angle):
        self.game = game
        self.x = pos_x
        self.y = pos_y
        self.angle = pos_angle
        self.uuid = uuid
        self.last_update = time.time()

    def draw(self):
        pg.draw.line(
            self.game.screen,
            "yellow",
            (self.x * 100, self.y * 100),
            (
                self.x * 100 * WIDTH * math.cos(self.angle),
                self.y * 100 * WIDTH * math.sin(self.angle),
            ),
            2,
        )
        pg.draw.circle(self.game.screen, "orange", (self.x * 100, self.y * 100), 15)