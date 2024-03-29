import pygame as pg
import math
import uuid
import win_precise_time as wpt
import copy
from threading import Thread
from settings import *
from map import *
from sprite_object import *

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
        self.thread_working = False
        self.endTriggered = False
        self.last_move = 0

    def recover_health(self):
        if self.check_health_recovery_delay() and self.health < PLAYER_MAX_HEALTH:
            self.health += 1

    def check_health_recovery_delay(self):
        time_now = pg.time.get_ticks()
        if time_now - self.time_prev > self.health_recovery_delay:
            self.time_prev = time_now
            return True

    def check_game_over(self):
        if self.endTriggered:
            return

        anyPlayerAlive = False
        distant_players_cpy = copy.copy(self.game.distant_players)
        for key, distant_players in distant_players_cpy.items():
            if distant_players.health >= 1:
                anyPlayerAlive = True

        if self.health < 1:
            if not anyPlayerAlive:
                self.endTriggered = True
                self.game.object_renderer.game_over()
                pg.display.flip()
                pg.time.delay(1500)
                self.game.new_game()
            else:
                self.game.object_renderer.wait_revive()

    def get_damage(self, damage):
        self.health -= damage
        self.time_prev = pg.time.get_ticks() #reset health gen when getting hit
        self.game.object_renderer.player_damage()
        self.game.sound.player_pain.play()
        self.check_game_over()

    def single_fire_event(self, event):
        if self.health >= 1 and ((event.type == pg.MOUSEBUTTONDOWN and event.button == 1) or (event.type == pg.KEYDOWN and event.key == pg.K_SPACE)):
            if not self.shot and not self.game.weapon.reloading:
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

        if dx != 0 or dy != 0:
            self.check_wall_collision(dx, dy)

        if not self.game.use_mouse:
            #keys simplify multi client movement for debug
            if keys[pg.K_LEFT]:
                self.angle -= PLAYER_ROT_SPEED * self.game.delta_time
            if keys[pg.K_RIGHT]:
                self.angle += PLAYER_ROT_SPEED * self.game.delta_time

        self.angle %= math.tau

    def check_wall(self, x, y):
        return (x, y) not in self.game.map.world_map

    def check_wall_collision(self, dx, dy):
        scale = PLAYER_SIZE_SCALE / self.game.delta_time
        if self.check_wall(int(self.x + dx * scale), int(self.y)):
            self.x += dx
        if self.check_wall(int(self.x), int(self.y + dy * scale)):
            self.y += dy
        self.last_move = wpt.time() * 1000

    def draw(self):
        pg.draw.line(self.game.screen, "yellow", (self.x * 100, self.y * 100), (self.x * 100 * WIDTH * math.cos(self.angle), self.y * 100 * WIDTH * math.sin(self.angle)),2)
        pg.draw.circle(self.game.screen, "green", (self.x * 100, self.y * 100), 15)

    def mouse_control(self):
        if self.game.use_mouse:
            mx, my = pg.mouse.get_pos()
            if mx < MOUSE_BORDER_LEFT or mx > MOUSE_BORDER_RIGHT:
                pg.mouse.set_pos([HALF_WIDTH, HALF_HEIGHT])
            self.rel = pg.mouse.get_rel()[0]
            self.rel = max(-MOUSE_MAX_REL, min(MOUSE_MAX_REL, self.rel))
            self.angle += self.rel * MOUSE_SENSITIVITY * self.game.delta_time

    def revive(self):
        self.health = PLAYER_MAX_HEALTH // 2
    
    def update(self):
        self.check_game_over()
        if self.health >= 1:
            self.movement()
            self.mouse_control()
            if not self.game.is_over:
                self.recover_health()
        else:
            self.game.object_renderer.player_damage()

        #Send pos every 30ms in a separate thread
        now = wpt.time()*1000
        if (not self.game.is_server and now - self.last_send) >= (30) and not self.thread_working:
            thread = Thread(target=self.send_position)
            thread.start()
            self.last_send = now

        if self.game.render_2d:
            self.draw()

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
            position_dict_tmp = []
            result = self.game.net_client.SendPosition(uuid = self.uuid, pos_x = self.x, pos_y = self.y, pos_angle = self.angle, health = self.health, last_move = self.last_move)
            for position in result:
                if position.uuid == self.game.player.uuid:
                    # update local health if we were dead
                    if self.game.player.health < 1:
                        self.game.player.health = position.health
                else:
                    position_dict_tmp.append(DistantPlayer(self.game, position.uuid, position.pos_x, position.pos_y, position.pos_angle, position.health, position.last_move))
            
            # Smart merge players, and only overrides pos/health info if player already exist
            # This avoid re-setting player animation time and triggers
            distant_players_copy = copy.copy(self.game.distant_players)
            players_dict_final = {}  
            for player in position_dict_tmp:
                if player.uuid in distant_players_copy:
                    tmp_player = distant_players_copy[player.uuid]

                    tmp_player.x = player.x
                    tmp_player.y = player.y
                    tmp_player.angle = player.angle
                    tmp_player.health = player.health
                    tmp_player.last_move = player.last_move

                    players_dict_final[player.uuid] = tmp_player
                else:
                    players_dict_final[player.uuid] = player

            self.game.distant_players = players_dict_final
        
        except:
            self.game.exit()
    
        self.thread_working = False


class DistantPlayer(AnimatedSprite):
    def __init__(self, game, uuid, pos_x, pos_y, pos_angle, health, last_move):
        super().__init__(game, 'resources/sprites/players/0.png', (pos_x, pos_y), 0.6, 0.38, 180, uuid)
        self.game = game
        self.x = pos_x
        self.y = pos_y
        self.angle = pos_angle
        self.uuid = uuid
        self.last_update = wpt.time()
        self.health = health
        self.revived = False

        self.last_move = last_move

        self.walk_images = self.get_images(self.path + '/walk')
        self.idle_images = self.get_images(self.path + '/idle_front')
        self.walk_back_images = self.get_images(self.path + '/walk_back')
        self.idle_back_images = self.get_images(self.path + '/idle_back')

        self.walk_left_images = self.get_images(self.path + '/walk_left')
        self.idle_left_images = self.get_images(self.path + '/idle_left')
        self.walk_left_back_images = self.get_images(self.path + '/walk_left_back')
        self.idle_left_back_images = self.get_images(self.path + '/idle_left_back')
        self.walk_left_front_images = self.get_images(self.path + '/walk_left_front')
        self.idle_left_front_images = self.get_images(self.path + '/idle_left_front')

        self.walk_right_images = self.get_images(self.path + '/walk_right')
        self.idle_right_images = self.get_images(self.path + '/idle_right')
        self.walk_right_back_images = self.get_images(self.path + '/walk_right_back')
        self.idle_right_back_images = self.get_images(self.path + '/idle_right_back')
        self.walk_right_front_images = self.get_images(self.path + '/walk_right_front')
        self.idle_right_front_images = self.get_images(self.path + '/idle_right_front')

        self.death_images = self.get_images(self.path + '/death')

        self.deathTriggered = False
        self.frame_counter = 0
        self.revive_dist = 1

    def draw_2d(self):
        pg.draw.line(self.game.screen, "yellow", (self.x * 100, self.y * 100), (self.x * 100 * WIDTH * math.cos(self.angle), self.y * 100 * WIDTH * math.sin(self.angle)), 2)
        pg.draw.circle(self.game.screen, "orange", (self.x * 100, self.y * 100), 15)

    def update(self):
        self.check_animation_time()
        self.get_sprite()

        if self.health < 1:
            keys = pg.key.get_pressed()
            if (self.deathTriggered and keys[ACTION_KEY] and self.norm_dist < self.revive_dist):
                if self.frame_counter == 0:
                    if not self.game.is_server:
                        self.game.net_client.Revive(self.uuid)
                    else:
                        self.revive()
                else:
                    self.animate_revive()
            else:
                self.animate_death()
                if not self.deathTriggered:
                    self.deathTriggered = True
                    self.game.sound.player_death.play()
        else:
            idle = False
            now = wpt.time() * 1000
            if (now - self.last_move) > 100:
                idle = True

            # todo add extra image to sprite with AI
            # Choose animation depending on angle
            if self.angle > self.player.angle:
                delta = self.angle - self.player.angle
                deg = math.degrees(delta)
                if 157.5 <= deg < 202.5:
                    self.animate(self.idle_images if idle else self.walk_images)
                elif 247.5 <= deg < 292.5:
                    self.animate(self.idle_left_images if idle else self.walk_left_images)
                elif 67.5 <= deg < 112.5:
                    self.animate(self.idle_right_images if idle else self.walk_right_images)
                elif 112.5 <= deg < 157.5:
                    self.animate(self.idle_right_front_images if idle else self.walk_right_front_images)
                elif 22.5 <= deg < 67.5:
                    self.animate(self.idle_right_back_images if idle else self.walk_right_back_images)
                elif 202.5 <= deg < 247.5:
                    self.animate(self.idle_left_front_images if idle else self.walk_left_front_images)
                elif 292.5 <= deg < 337.5:
                    self.animate(self.idle_left_back_images if idle else self.walk_left_back_images)
                else:
                    self.animate(self.idle_back_images if idle else self.walk_back_images)
            else:
                delta = self.player.angle - self.angle
                deg = math.degrees(delta)
                if 157.5 <= deg < 202.5:
                    self.animate(self.idle_images if idle else self.walk_images)
                elif 247.5 <= deg < 292.5:
                    self.animate(self.idle_right_images if idle else self.walk_right_images)
                elif 67.5 <= deg < 112.5:
                    self.animate(self.idle_left_images if idle else self.walk_left_images)
                elif 112.5 <= deg < 157.5:
                    self.animate(self.idle_left_front_images if idle else self.walk_left_front_images)
                elif 22.5 <= deg < 67.5:
                    self.animate(self.idle_left_back_images if idle else self.walk_left_back_images)
                elif 202.5 <= deg < 247.5:
                    self.animate(self.idle_right_front_images if idle else self.walk_right_front_images)
                elif 292.5 <= deg < 337.5:
                    self.animate(self.idle_right_back_images if idle else self.walk_right_back_images)
                else:
                    self.animate(self.idle_back_images if idle else self.walk_back_images)
        
        if self.game.render_2d:
            self.draw_2d()

    def animate_death(self):
        if self.health < 1:
            if self.game.global_trigger and self.frame_counter < len(self.death_images) - 1:
                self.death_images.rotate(-1)
                self.image = self.death_images[0]
                self.frame_counter += 1
                
    def animate_revive(self):
        if self.health < 1:
            if self.game.global_trigger and self.frame_counter > 0:
                self.death_images.rotate(1)
                self.image = self.death_images[0]
                self.frame_counter -= 1

    def revive(self):
        self.health = PLAYER_MAX_HEALTH // 2
        self.revived = True

    @property
    def pos(self):
        return self.x, self.y
    
    @property
    def map_pos(self):
        return int(self.x), int(self.y)