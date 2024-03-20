import pygame as pg
import math
import cProfile
from settings import *


class RayCasting:
    def __init__(self, game):
        self.game = game
        self.ray_casting_result = []
        self.objects_to_render = []
        self.textures = self.game.object_renderer.wall_textures

    def get_objects_to_render(self):
        self.objects_to_render = []

        #we must take the furthest displayed element, and replace it by a black image of the width of the screen
        #this will ensure to have a black displayed texture instead of potentially transparent space
        temp = []
        for values in self.ray_casting_result:
            ray, depth, proj_height, texture, offset = values

            if proj_height < HEIGHT:
                wall_column = self.textures[texture].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), 0, SCALE, TEXTURE_SIZE
                )
                wall_column = pg.transform.scale(wall_column, (SCALE, proj_height))
                wall_pos = (ray * SCALE, HALF_HEIGHT - proj_height // 2)
            else:
                texture_height = TEXTURE_SIZE * HEIGHT / proj_height
                wall_column = self.textures[texture].subsurface(
                    offset * (TEXTURE_SIZE - SCALE), HALF_TEXTURE_SIZE - texture_height // 2,
                    SCALE, texture_height
                )
                wall_column = pg.transform.scale(wall_column, (SCALE, HEIGHT))
                wall_pos = (ray * SCALE, 0)
            
            self.objects_to_render.append((depth, wall_column, wall_pos))

    def ray_cast(self):
        self.ray_casting_result = []
        ox, oy = self.game.player.pos
        x_map, y_map = self.game.player.map_pos

        ray_angle = self.game.player.angle - HALF_FOV + 0.0001
        for ray in range(NUM_RAYS):
            texture_hor, texture_vert = 0, 0

            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            # horizontals
            y_hor, dy = (y_map + 1, 1) if sin_a > 0 else (y_map - 0.0001, -1)
            depth_hor = (y_hor - oy) / sin_a
            x_hor = ox + depth_hor * cos_a

            delta_depth = dy / sin_a
            dx = delta_depth * cos_a

            for i in range(MAX_DEPTH):
                tile_hor = x_hor//1, y_hor//1
                if tile_hor in self.game.map.world_map:
                    texture_hor = self.game.map.world_map[tile_hor]
                    break
                x_hor += dx
                y_hor += dy
                depth_hor += delta_depth
            # end(horizontals)
            
            # verticals
            x_vert, dx = (x_map + 1, 1) if cos_a > 0 else (x_map - 0.0001, -1)
            depth_vert = (x_vert - ox) / cos_a
            y_vert = oy + depth_vert * sin_a

            delta_depth = dx / cos_a
            dy = delta_depth * sin_a

            for i in range(MAX_DEPTH):
                tile_vert = int(x_vert), int(y_vert)
                if tile_vert in self.game.map.world_map:
                    texture_vert = self.game.map.world_map[tile_vert]
                    break
                x_vert += dx
                y_vert += dy
                depth_vert += delta_depth
            # end(verticals)

            if depth_vert < depth_hor:
                depth, texture = depth_vert, texture_vert
                y_vert %= 1
                offset = y_vert if cos_a > 0 else (1 - y_vert)
            else:
                depth, texture = depth_hor, texture_hor
                x_hor %= 1
                offset = (1 - x_hor) if sin_a > 0 else x_hor

            if self.game.render_2d:
                pg.draw.line(self.game.screen, 'blue', (100 * ox, 100 * oy), (100 * ox + 100 * depth * cos_a, 100 * oy + 100 * depth * sin_a), 2)

            # remove fishbowl effect
            # Depth is length of arc between player and wall. but center of wall is closer than the sides => fishbowl
            # So we consider the real depth is the smallest one, aka  old_depth * cos(alpha)
            #
            #                 ---------------------
            #                  \        |        / <- old depth
            #                   \       |       /
            #                    \      |      /
            #                     \     |     /
            #                      \    |    /
            #                       \   |   /
            #                        \  |  /
            #                         \ | /
            #                          \|/
            #                           x    (alpha is angle between arc and center)
            #
            
            depth *= math.cos(self.game.player.angle - ray_angle)

            # projection
            proj_height = SCREEN_DIST / (depth + 1e-6)

            self.ray_casting_result.append((ray, depth, proj_height, texture, offset))

            ray_angle += DELTA_ANGLE

    def update(self):
        print('ray_cast')
        cProfile.runctx('self.ray_cast()', globals(), locals())
        #self.ray_cast()
        print('get_objects_to_render')
        cProfile.runctx('self.get_objects_to_render()', globals(), locals())
        #self.get_objects_to_render()
