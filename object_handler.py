from random import choices, randrange
from threading import Thread
import time
from sprite_object import *
from npc import *


class ObjectHandler:
    def __init__(self, game):
        self.game = game
        self.sprite_list = []
        self.npc_list = {}
        self.npc_sprite_path = "resources/sprites/npc/"
        self.static_sprite_path = "resources/sprites/static_sprites/"
        self.anim_sprite_path = "resources/sprites/animated_sprites/"
        self.npc_positions = {}
        self.sprite_init_from_server = False
        self.npc_init_from_server = False

        self.last_send = 0
        self.last_thread_time = 0
        self.thread_working = False

        if self.game.is_server:
            self.sprite_init_from_server = True
            self.npc_init_from_server = True

            # sprite map
            add_sprite = self.add_sprite
            add_sprite(AnimatedSprite(game))
            add_sprite(AnimatedSprite(game, pos=(1.5, 1.5)))
            add_sprite(AnimatedSprite(game, pos=(1.5, 7.5)))
            add_sprite(AnimatedSprite(game, pos=(5.5, 3.25)))
            add_sprite(AnimatedSprite(game, pos=(5.5, 4.75)))
            add_sprite(AnimatedSprite(game, pos=(7.5, 2.5)))
            add_sprite(AnimatedSprite(game, pos=(7.5, 5.5)))
            add_sprite(AnimatedSprite(game, pos=(14.5, 1.5)))
            add_sprite(AnimatedSprite(game, pos=(14.5, 4.5)))
            add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + "red_light/0.png", pos=(14.5, 5.5)))
            add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + "red_light/0.png", pos=(14.5, 7.5)))
            add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + "red_light/0.png", pos=(12.5, 7.5)))
            add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + "red_light/0.png", pos=(9.5, 7.5)))
            add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + "red_light/0.png", pos=(14.5, 12.5)))
            add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + "red_light/0.png", pos=(9.5, 20.5)))
            add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + "red_light/0.png", pos=(10.5, 20.5)))
            add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + "red_light/0.png", pos=(3.5, 14.5)))
            add_sprite(AnimatedSprite(game, path=self.anim_sprite_path + "red_light/0.png", pos=(3.5, 18.5)))
            add_sprite(AnimatedSprite(game, pos=(14.5, 24.5)))
            add_sprite(AnimatedSprite(game, pos=(14.5, 30.5)))
            add_sprite(AnimatedSprite(game, pos=(1.5, 30.5)))
            add_sprite(AnimatedSprite(game, pos=(1.5, 24.5)))

            self.add_npc(SoldierNPC(game))

            # spawn npc
            # self.enemies = 20
            # self.npc_types = [SoldierNPC, CacoDemonNPC, CyberDemonNPC]
            # self.weights = [70, 20, 10]
            # self.restricted_area = {(i, j) for i in range(10) for j in range(10)} #no npc in the first 10x10 blocks
            # self.spawn_npc()
        else:
            thread_sprites = Thread(target=self.load_sprites)
            thread_sprites.start()

            thread_npc = Thread(target=self.load_npcs)
            thread_npc.start()

    def spawn_npc(self):
        for i in range(self.enemies):
                npc = choices(self.npc_types, self.weights)[0]
                pos = x, y = randrange(self.game.map.cols), randrange(self.game.map.rows)
                #while npc pos is colliding with walls or in the restricted area, generate new pos
                while (pos in self.game.map.world_map) or (pos in self.restricted_area):
                    pos = x, y = randrange(self.game.map.cols), randrange(self.game.map.rows)
                self.add_npc(npc(self.game, pos=(x + 0.5, y + 0.5)))

    def update(self):
        self.npc_positions = { npc.map_pos for key, npc in self.npc_list.items() if npc.alive }
        [sprite.update() for sprite in self.sprite_list]
        [npc.update() for key, npc in self.npc_list.items()]
        self.check_win()

        #Load npcs state every 30ms
        now = time.time()*1000
        if (not self.game.is_server and now - self.last_send) >= (30):
            thread = Thread(target=self.load_npcs)
            thread.start()
            self.last_send = now

    def add_sprite(self, sprite):
        self.sprite_list.append(sprite)

    def add_npc(self, npc):
        self.npc_list[npc.uuid] = npc
    
    def check_win(self):
        if not len(self.npc_positions) and self.sprite_init_from_server and self.npc_init_from_server:
            self.game.object_renderer.win()
            self.game.is_over = True
            pg.display.flip()

    def load_sprites(self):
        try:
            sprite_list_tmp = []
            result = self.game.net_client.GetSprites()
            for sprite in result:
                if sprite.type == SpriteObject.__name__:
                    sprite_list_tmp.append(SpriteObject(self.game, sprite.path, (sprite.pos_x, sprite.pos_y), sprite.scale, sprite.shift, sprite.uuid))
                elif sprite.type == AnimatedSprite.__name__:
                    sprite_list_tmp.append(AnimatedSprite(self.game, sprite.path, (sprite.pos_x, sprite.pos_y), sprite.scale, sprite.shift, sprite.animation_time, sprite.uuid))

            self.sprite_list = sprite_list_tmp
            self.sprite_init_from_server = True
        
        except:
            self.game.exit()

    def load_npcs(self):
        #If another thread is working, ignore
        if self.thread_working:
            return
        self.thread_working = True

        try:
            npcs_list_tmp = []
            result = self.game.net_client.GetNpcs()
            for npc in result:
                if npc.type == SoldierNPC.__name__:
                    npc_tmp = SoldierNPC(self.game, npc.path, (npc.pos_x, npc.pos_y), npc.scale, npc.shift, npc.animation_time, npc.uuid)
                elif npc.type == CacoDemonNPC.__name__:
                    npc_tmp = CacoDemonNPC(self.game, npc.path, (npc.pos_x, npc.pos_y), npc.scale, npc.shift, npc.animation_time, npc.uuid)
                elif npc.type == CyberDemonNPC.__name__:
                    npc_tmp = CyberDemonNPC(self.game, npc.path, (npc.pos_x, npc.pos_y), npc.scale, npc.shift, npc.animation_time, npc.uuid)

                npc_tmp.ray_cast_uuid = npc.ray_cast_uuid
                npc_tmp.last_ray_cast_uuid = npc.last_ray_cast_uuid
                npc_tmp.local_ray_cast = (npc.ray_cast_uuid == self.game.player.uuid)
                npc_tmp.ray_cast_dist = npc.ray_cast_dist
                npcs_list_tmp.append(npc_tmp)

            # Smart merge npcs, and only overrides pos/health/raycast info if npc already exist
            # This avoid re-setting npc animation time and triggers
            npcs_dict_final = {}  
            for npc in npcs_list_tmp:
                if npc.uuid in self.npc_list:
                    tmp_npc = self.npc_list[npc.uuid]

                    tmp_npc.x = npc.x
                    tmp_npc.y = npc.y
                    tmp_npc.health = npc.health

                    tmp_npc.ray_cast_uuid = npc.ray_cast_uuid
                    tmp_npc.last_ray_cast_uuid = npc.last_ray_cast_uuid
                    tmp_npc.local_ray_cast = npc.local_ray_cast
                    tmp_npc.ray_cast_dist = npc.ray_cast_dist

                    npcs_dict_final[npc.uuid] = tmp_npc
                else:
                    npcs_dict_final[npc.uuid] = npc
            
            self.npc_list = npcs_dict_final
            self.npc_init_from_server = True
        
        except:
            self.game.exit()

        self.thread_working = False
