from random import randint, random, choice
import copy
from threading import Thread
from sprite_object import *

render_2d_npc = False

class NPC(AnimatedSprite):
    def __init__(self, game, path='resources/sprites/npc/soldier/0.png', pos=(10.5, 5.5), scale=0.6, shift=0.38, animation_time=180, uuid_ = ''):
        super().__init__(game, path, pos, scale, shift, animation_time, uuid_)
        self.attack_images = self.get_images(self.path + '/attack')
        self.death_images = self.get_images(self.path + '/death')
        self.idle_images = self.get_images(self.path + '/idle')
        self.pain_images = self.get_images(self.path + '/pain')
        self.walk_images = self.get_images(self.path + '/walk')

        self.attack_dist = 4
        self.speed = 0.03
        self.size = 10
        self.health = 100
        self.attack_damage = 10
        self.accuracy = 1
        self.pain = False
        self.ray_cast_uuid = ''
        self.last_ray_cast_uuid = ''
        self.local_ray_cast = False
        self.player_search_trigger = False
        self.frame_counter = 0
        self.ray_cast_dist = -1

    def update(self):
        self.check_animation_time()
        self.get_sprite()
        self.run_logic()

        if render_2d_npc:
            self.draw_ray_cast()

    def check_wall(self, x, y):
        return (x, y) not in self.game.map.world_map

    def check_wall_collision(self, dx, dy):
        if self.check_wall(int(self.x + dx * self.size), int(self.y)):
            self.x += dx
        if self.check_wall(int(self.x), int(self.y + dy * self.size)):
            self.y += dy

    def movement(self):
        shouldReset = False
        if self.ray_cast_uuid == self.game.player.uuid or self.last_ray_cast_uuid == self.game.player.uuid:
            next_pos = self.game.pathfinding.get_path(self.map_pos, self.game.player.map_pos)
        elif self.ray_cast_uuid != '':
            if self.ray_cast_uuid in self.game.distant_players:
                next_pos = self.game.pathfinding.get_path(self.map_pos, self.game.distant_players[self.ray_cast_uuid].map_pos)
            else:
                shouldReset = True
        elif self.last_ray_cast_uuid != '':
            if self.last_ray_cast_uuid in self.game.distant_players:
                next_pos = self.game.pathfinding.get_path(self.map_pos, self.game.distant_players[self.last_ray_cast_uuid].map_pos)
            else:
                shouldReset = True
        else:
            shouldReset = True
        
        if shouldReset:
            #targeted player must have left
            self.ray_cast_uuid = ''
            self.last_ray_cast_uuid = ''
            return
        
        next_x, next_y = next_pos
        if next_pos not in self.game.object_handler.npc_positions:
            angle = math.atan2(next_y + 0.5 - self.y, next_x + 0.5 - self.x)
            dx = math.cos(angle) * self.speed
            dy = math.sin(angle) * self.speed
            self.check_wall_collision(dx, dy)

    def attack(self):
        if self.animation_trigger:
            self.game.sound.npc_shot.play()

            # only apply damages is local player is target
            if self.ray_cast_uuid == self.game.player.uuid and random() < self.accuracy:
                self.game.player.get_damage(self.attack_damage)

    def animate_death(self):
        if self.health < 1:
            if self.game.global_trigger and self.frame_counter < len(self.death_images) - 1:
                self.death_images.rotate(-1)
                self.image = self.death_images[0]
                self.frame_counter += 1

    def animate_pain(self):
        self.animate(self.pain_images)
        if self.animation_trigger:
            self.pain = False

    def check_hit_in_npc(self):
        if self.local_ray_cast and self.game.player.shot:
            if HALF_WIDTH - self.sprite_half_width < self.screen_x < HALF_WIDTH + self.sprite_half_width:
                self.game.sound.npc_pain.play()
                self.game.player.shot = False
                self.pain = True
                self.health -= self.game.weapon.damage
                self.check_health()

                if not self.game.is_server:
                    thread = Thread(target=self.send_damage, args=(self.uuid, self.game.weapon.damage))
                    thread.start()

    def send_damage(self, uuid, damage):
        self.game.net_client.ShootNpc(uuid, damage)

    def check_health(self):
        if self.health < 1:
            self.game.sound.npc_death.play()

    def run_logic(self):
        if self.health >= 1:
            if self.game.is_server:
                self.ray_cast_players_npc()
                self.calc_ray_cast_dist()
            
            self.check_hit_in_npc()
            
            if self.pain:
                self.animate_pain()
            elif self.ray_cast_uuid != '':
                if self.game.is_server:
                    if self.local_ray_cast and self.player.health < 1:
                        self.player_search_trigger = False
                    elif self.ray_cast_uuid in self.game.distant_players and self.game.distant_players[self.ray_cast_uuid].health < 1:
                        self.player_search_trigger = False
                    else:
                        self.player_search_trigger = True

                if self.ray_cast_uuid != '' and 0 <= self.ray_cast_dist < self.attack_dist:
                    #todo display attack from different angle depending on the target
                    self.animate(self.attack_images)
                    self.attack()
                else:
                    self.animate(self.walk_images)
                    self.movement()

            elif self.player_search_trigger:
                self.animate(self.walk_images)
                self.movement()
            else:
                self.animate(self.idle_images)
        else:
            self.animate_death()

    def draw_ray_cast(self):
        pg.draw.circle(self.game.screen, 'red', (100 * self.x, 100 * self.y), 15)
        if self.ray_cast_uuid != '':
            if self.ray_cast_uuid == self.game.player.uuid:
                pg.draw.line(self.game.screen, 'orange', (100 * self.game.player.x, 100 * self.game.player.y), (100 * self.x, 100 * self.y), 2)
            else:
                player = self.game.distant_players[self.ray_cast_uuid]
                pg.draw.line(self.game.screen, 'orange', (100 * player.x, 100 * player.y), (100 * self.x, 100 * self.y), 2)

    @property
    def map_pos(self):
        return int(self.x), int(self.y)
    
    def ray_cast_players_npc(self):
        # In order to have consistent result across all clients, we must do the raycast in a static order, by uuid
        tmp_player_dict = {}
        tmp_player_dict[self.game.player.uuid] = (self.game.player.health, self.game.player.map_pos, self.game.player.pos)

        distant_players_cpy = copy.copy(self.game.distant_players)
        for key, distant_players in distant_players_cpy.items():
            tmp_player_dict[key] = (distant_players.health, distant_players.map_pos, distant_players.pos)

        tmp_player_dict = dict(sorted(tmp_player_dict.items()))

        for key, player in tmp_player_dict.items():
            if player[0] > 1 and self.ray_cast_player_npc(player[1], player[2]):
                self.ray_cast_uuid = key
                self.last_ray_cast_uuid = self.ray_cast_uuid

                self.local_ray_cast = (key == self.game.player.uuid)
                return
        
        self.ray_cast_uuid = ''
    
    def ray_cast_player_npc(self, player_map_pos, player_pos):
        if player_map_pos == self.map_pos:
            return True
        
        wall_dist_v, wall_dist_h = 0, 0
        player_dist_v, player_dist_h = 0, 0

        self.ray_casting_result = []
        ox, oy = player_pos
        x_map, y_map = player_map_pos

        dx = self.x - ox
        dy = self.y - oy
        ray_angle = math.atan2(dy, dx)
        
        sin_a = math.sin(ray_angle)
        cos_a = math.cos(ray_angle)

        # horizontals
        y_hor, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 1e-6, -1)
        depth_hor = (y_hor - oy) / sin_a
        x_hor = ox + depth_hor * cos_a

        delta_depth = dy / sin_a
        dx = delta_depth * cos_a

        for i in range(MAX_DEPTH):
            tile_hor = int(x_hor), int(y_hor)
            if tile_hor == self.map_pos:
                player_dist_h = depth_hor
                break
            if tile_hor in self.game.map.world_map:
                wall_dist_h = depth_hor
                break
            x_hor += dx
            y_hor += dy
            depth_hor += delta_depth
        # end(horizontals)

        # verticals
        x_vert, dx = (x_map + 1, 1) if cos_a > 0 else (x_map - 1e-6, -1)
        depth_vert = (x_vert - ox) / cos_a
        y_vert = oy + depth_vert * sin_a

        delta_depth = dx / cos_a
        dy = delta_depth * sin_a

        for i in range(MAX_DEPTH):
            tile_vert = int(x_vert), int(y_vert)
            if tile_vert == self.map_pos:
                player_dist_v = depth_vert
                break
            if tile_vert in self.game.map.world_map:
                wall_dist_v = depth_vert
                break
            x_vert += dx
            y_vert += dy
            depth_vert += delta_depth
        # end(verticals)
            
        player_dist = max(player_dist_v, player_dist_h)
        wall_dist = max(wall_dist_v, wall_dist_h)

        if 0 < player_dist < wall_dist or not wall_dist:
            return True
        return False
    
    def calc_ray_cast_dist(self):
        if self.ray_cast_uuid == '':
            self.ray_cast_dist = -1
            return

        ox, oy, oangle = 0, 0, 0

        if self.local_ray_cast:
            ox = self.game.player.x
            oy = self.game.player.y
            oangle = self.game.player.y
        else:
            if not self.ray_cast_uuid in self.game.distant_players:
                self.ray_cast_dist = -1
                return
            else:
                player = self.game.distant_players[self.ray_cast_uuid]
                ox = player.x
                oy = player.y
                oangle = player.angle

        dx = self.x - ox
        dy = self.y - oy
        self.dx, self.dy = dx, dy
        self.theta = math.atan2(dy, dx)

        self.ray_cast_dist = math.hypot(dx, dy)


class SoldierNPC(NPC):
    def __init__(self, game, path='resources/sprites/npc/soldier/0.png', pos=(10.5, 5.5), scale=0.6, shift=0.38, animation_time=180, uuid_ = '', health = -1):
        super().__init__(game, path, pos, scale, shift, animation_time, uuid_)
        self.attack_dist = 4
        if health == -1:
            self.health = 100
        else:
            self.health = health
        self.attack_damage = 10
        self.speed = 0.03
        self.accuracy = 0.15

class CacoDemonNPC(NPC):
    def __init__(self, game, path='resources/sprites/npc/caco_demon/0.png', pos=(10.5, 6.5), scale=0.7, shift=0.27, animation_time=250, uuid_ = '', health = -1):
        super().__init__(game, path, pos, scale, shift, animation_time, uuid_)
        self.attack_dist = 1.0
        if health == -1:
            self.health = 150
        else:
            self.health = health
        self.attack_damage = 25
        self.speed = 0.05
        self.accuracy = 0.35

class CyberDemonNPC(NPC):
    def __init__(self, game, path='resources/sprites/npc/cyber_demon/0.png', pos=(11.5, 6.0), scale=1.0, shift=0.04, animation_time=210, uuid_ = '', health = -1):
        super().__init__(game, path, pos, scale, shift, animation_time, uuid_)
        self.attack_dist = 6
        if health == -1:
            self.health = 350
        else:
            self.health = health
        self.attack_damage = 15
        self.speed = 0.055
        self.accuracy = 0.25