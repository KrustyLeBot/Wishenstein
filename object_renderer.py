import pygame as pg
from settings import *


class ObjectRenderer:
    def __init__(self, game):
        self.game = game
        self.screen = game.screen
        self.wall_textures = self.load_wall_textures()
        self.sky_image = self.get_texture(
            "resources/textures/sky.png", (WIDTH, HALF_HEIGHT)
        )
        self.sky_offset = 0
        self.blood_screen = self.get_texture("resources/textures/blood_screen.png", RES)
        self.digit_size = 90
        self.digit_images = [self.get_texture(f'resources/textures/digits/{i}.png', [self.digit_size] * 2) for i in range(12)]
        self.digits = dict(zip(map(str, range(12)), self.digit_images))
        self.game_over_image = self.get_texture('resources/textures/game_over.png', RES)
        self.wait_revive_image = self.get_texture('resources/textures/wait_revive.png', RES)
        self.win_image = self.get_texture('resources/textures/win.png', RES)

    def draw(self):
        self.draw_background()
        self.render_game_objects()
        self.draw_player_health()
        self.draw_ennemies_left()

    def win(self):
        self.screen.blit(self.win_image, (0, 0))

    def game_over(self):
        self.screen.blit(self.game_over_image, (0, 0))

    def wait_revive(self):
        self.screen.blit(self.wait_revive_image, (0, 0))

    def draw_player_health(self):
        health = str(self.game.player.health)
        if self.game.player.health >= 0:
            for i, char in enumerate(health):
                self.screen.blit(self.digits[char], (i * self.digit_size, 0))
            self.screen.blit(self.digits['10'], ((i + 1) * self.digit_size, 0))

    def draw_ennemies_left(self):
        health = str(self.game.player.health)
        if not self.game.is_over:
            npc_count_str = str(len(self.game.object_handler.npc_list))
            npc_alive_str = str(sum(npc.health >= 1 for key, npc in self.game.object_handler.npc_list.items()))
            tot = len(npc_alive_str) + len(npc_count_str) + 1
            right = len(npc_count_str)
            
            for i, char in enumerate(npc_alive_str):
                self.screen.blit(self.digits[char], (WIDTH - (tot * self.digit_size) + (i * self.digit_size), 0))
            
            self.screen.blit(self.digits['11'], (WIDTH - (tot * self.digit_size) + ((i + 1) * self.digit_size), 0))
            
            for i, char in enumerate(npc_count_str):
                self.screen.blit(self.digits[char], (WIDTH - (right * self.digit_size) + (i * self.digit_size), 0))

    def player_damage(self):
        self.screen.blit(self.blood_screen, (0, 0))

    def draw_background(self):
        # sky
        self.sky_offset = (self.sky_offset + 4.5 * self.game.player.rel) % WIDTH
        self.screen.blit(self.sky_image, (-self.sky_offset, 0))
        self.screen.blit(self.sky_image, (-self.sky_offset + WIDTH, 0))

        # floor
        pg.draw.rect(self.screen, FLOOR_COLOR, (0, HALF_HEIGHT, WIDTH, HEIGHT))

    def render_game_objects(self):
        list_objects = sorted(self.game.raycasting.objects_to_render, key=lambda t: t[0], reverse=True)
        for depth, image, pos in list_objects:
            self.screen.blit(image, pos)

    @staticmethod
    def get_texture(path, res=(TEXTURE_SIZE, TEXTURE_SIZE)):
        texture = pg.image.load(path).convert_alpha()
        return pg.transform.scale(texture, res)

    def load_wall_textures(self):
        return {
            0: self.get_texture("resources/textures/0.png"),
            1: self.get_texture("resources/textures/1.png"),
            2: self.get_texture("resources/textures/2.png"),
            3: self.get_texture("resources/textures/3.png"),
            4: self.get_texture("resources/textures/4.png"),
            5: self.get_texture("resources/textures/5.png"),
            6: self.get_texture("resources/textures/6.png"),
        }
