from random import choices, randrange
from threading import Thread
import win_precise_time as wpt
from sprite_object import *
from npc import *


class ObjectHandler:
    def __init__(self, game):
        self.game = game
        self.sprite_binder_list = []
        self.sprite_list = {}
        self.npc_list = {}
        self.npc_sprite_path = "resources/sprites/npc/"
        self.static_sprite_path = "resources/sprites/static_sprites/"
        self.anim_sprite_path = "resources/sprites/animated_sprites/"
        self.npc_positions = {}
        self.sprite_init_from_server = False
        self.npc_init_from_server = False

        self.last_send = 0
        self.last_thread_time = 0
        self.thread_working_npc = False
        self.thread_working_sprite = False

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

            

            # sprite binder map (dont forget to add the sprite with add_sprite after binding it)
            add_sprite_binder = self.add_sprite_binder
            binder = StateSpriteBinder(self.game)
            add_sprite(binder.bind_sprite(StateSprite(game, path="resources/sprites/state_sprite/torch/0.png", pos=(11, 7.9)), 1))
            add_sprite(binder.bind_sprite(StateSprite(game, path="resources/sprites/state_sprite/torch/0.png", pos=(12, 7.9)), 1))
            binder.add_blocks_to_destroy(((11, 8)))
            add_sprite_binder(binder)

            self.add_npc(SoldierNPC(game, pos=(5.5, 14.5)))

            #spawn npc
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
        self.npc_positions = { npc.map_pos for key, npc in self.npc_list.items() if npc.health >= 1 }
        [sprite.update() for key, sprite in self.sprite_list.items()]
        [npc.update() for key, npc in self.npc_list.items()]
        [binder.update() for binder in self.sprite_binder_list]
        self.check_win()

        #Load npcs state every 30ms
        now = wpt.time()*1000
        if (not self.game.is_server and now - self.last_send) >= (100):
            thread_npc = Thread(target=self.load_npcs)
            thread_npc.start()

            thread_sprites = Thread(target=self.load_sprites)
            thread_sprites.start()

            self.last_send = now

    def add_sprite(self, sprite):
        self.sprite_list[sprite.uuid] = sprite

    def add_sprite_binder(self, binder):
        self.sprite_binder_list.append(binder)

    def toggle_sprites(self):
        #toggle the closest sprite
        best_dist = 99999999
        best_uuid = ''
        for key, sprite in self.sprite_list.items():
            if sprite.__class__.__name__ == StateSprite.__name__ and sprite.dist < sprite.activation_dist and sprite.is_displayed:
                if sprite.dist < best_dist:
                    best_uuid = sprite.uuid
            
        if best_uuid != '':
            new_state = self.sprite_list[best_uuid].toggle(appy_state = True if self.game.is_server else False)
            if not self.game.is_server:
                thread = Thread(target=self.send_toggle, args=(best_uuid, new_state))
                thread.start()

    def send_toggle(self, uuid, state):
        self.game.net_client.ToggleSprite(uuid, state)

    def get_sprite(self, uuid):
        return self.sprite_list[uuid]

    def add_npc(self, npc):
        self.npc_list[npc.uuid] = npc
    
    def check_win(self):
        if not len(self.npc_positions) and self.sprite_init_from_server and self.npc_init_from_server:
            self.game.object_renderer.win()
            self.game.is_over = True
            pg.display.flip()

    def load_sprites(self):
        #If another thread is working, ignore
        if self.thread_working_sprite:
            return
        self.thread_working_sprite = True

        try:
            sprite_list_tmp = []
            result = self.game.net_client.GetSprites()
            for sprite in result:
                if sprite.type == SpriteObject.__name__:
                    sprite_list_tmp.append(SpriteObject(self.game, sprite.path, (sprite.pos_x, sprite.pos_y), sprite.scale, sprite.shift, sprite.uuid))
                elif sprite.type == AnimatedSprite.__name__:
                    sprite_list_tmp.append(AnimatedSprite(self.game, sprite.path, (sprite.pos_x, sprite.pos_y), sprite.scale, sprite.shift, sprite.animation_time, sprite.uuid))
                elif sprite.type == StateSprite.__name__:
                    sprite_list_tmp.append(StateSprite(self.game, sprite.path, (sprite.pos_x, sprite.pos_y), sprite.scale, sprite.shift, sprite.uuid, sprite.state))

            dict_final = {}
            for sprite in sprite_list_tmp:
                dict_final[sprite.uuid] = sprite

            self.sprite_list = dict_final
            self.sprite_init_from_server = True
        
        except:
            self.game.exit()

        self.thread_working_sprite = False

    def load_npcs(self):
        #If another thread is working, ignore
        if self.thread_working_npc:
            return
        self.thread_working_npc = True

        try:
            npcs_list_tmp = []
            result = self.game.net_client.GetNpcs()
            for npc in result:
                if npc.type == SoldierNPC.__name__:
                    npc_tmp = SoldierNPC(self.game, npc.path, (npc.pos_x, npc.pos_y), npc.scale, npc.shift, npc.animation_time, npc.uuid, npc.health)
                elif npc.type == CacoDemonNPC.__name__:
                    npc_tmp = CacoDemonNPC(self.game, npc.path, (npc.pos_x, npc.pos_y), npc.scale, npc.shift, npc.animation_time, npc.uuid, npc.health)
                elif npc.type == CyberDemonNPC.__name__:
                    npc_tmp = CyberDemonNPC(self.game, npc.path, (npc.pos_x, npc.pos_y), npc.scale, npc.shift, npc.animation_time, npc.uuid, npc.health)

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
                    shouldTrigger = False
                    if npc.health < 1 and tmp_npc.health >= 1:
                        shouldTrigger = True
                    tmp_npc.health = npc.health
                    if shouldTrigger:
                        tmp_npc.check_health()
                    

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

        self.thread_working_npc = False


class StateSpriteBinder:
    def __init__(self, game):
        self.game = game
        self.sprites = []
        self.blocks_to_destroy = []
        self.triggered = False

    def bind_sprite(self, sprite, state):
        self.sprites.append((sprite.uuid, state))
        return sprite

    def add_blocks_to_destroy(self, pos):
        self.blocks_to_destroy.append(pos)

    def update(self):
        sprite_in_incorrect_state = False
        for sprite in self.sprites:
            ref = self.game.object_handler.get_sprite(sprite[0])
            if ref.state != sprite[1]:
                sprite_in_incorrect_state = True
                break
        
        if not sprite_in_incorrect_state:
            for block_pos in self.blocks_to_destroy:
                self.game.map.destroy_block(block_pos)
            self.triggered = True