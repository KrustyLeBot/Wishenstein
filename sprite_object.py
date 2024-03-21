import pygame as pg
import math
import os
import uuid
import win_precise_time as wpt
from collections import deque
from settings import *


class SpriteObject:
    def __init__(
        self,
        game,
        path="resources/sprites/static_sprites/candlebra.png",
        pos=(10.5, 3.5),
        scale=0.7,
        shift=0.27,
        uuid_ = ''
    ):
        if uuid_ == '':
            self.uuid = str(uuid.uuid4())
        else:
            self.uuid = uuid_
        self.game = game
        self.raw_path = path
        self.animation_time = 0
        self.state = 0
        self.player = game.player
        self.x, self.y = pos
        self.image = pg.image.load(path).convert_alpha()
        self.IMAGE_WIDTH = self.image.get_width()
        self.IMAGE_HALF_WIDTH = self.IMAGE_WIDTH // 2
        self.IMAGE_RATIO = self.IMAGE_WIDTH / self.image.get_height()
        self.dx, self.dy, self.theta, self.screen_x, self.dist, self.norm_dist = (
            0,
            0,
            0,
            0,
            1,
            1,
        )
        self.sprite_half_width = 0
        self.SPRITE_SCALE = scale
        self.SPRITE_HEIGHT_SHIFT = shift
        self.is_displayed = False

    def get_sprite_projection(self):
        proj = SCREEN_DIST / self.norm_dist * self.SPRITE_SCALE
        proj_width, proj_height = proj * self.IMAGE_RATIO, proj

        image = pg.transform.scale(self.image, (proj_width, proj_height))

        self.sprite_half_width = proj_width // 2
        height_shift = proj_height * self.SPRITE_HEIGHT_SHIFT
        pos = (
            self.screen_x - self.sprite_half_width,
            HALF_HEIGHT - proj_height // 2 + height_shift,
        )

        self.game.raycasting.objects_to_render.append((self.norm_dist, image, pos))

    def get_sprite(self):
        dx = self.x - self.player.x
        dy = self.y - self.player.y
        self.dx, self.dy = dx, dy
        self.theta = math.atan2(dy, dx)

        delta = self.theta - self.player.angle

        if (dx > 0 and self.player.angle > math.pi) or (dx < 0 and dy < 0):
            delta += math.tau

        delta_rays = delta / DELTA_ANGLE
        self.screen_x = (HALF_NUM_RAYS + delta_rays) * SCALE

        self.dist = math.hypot(dx, dy)
        self.norm_dist = self.dist * math.cos(delta)
        if (-self.IMAGE_HALF_WIDTH < self.screen_x < (WIDTH + self.IMAGE_HALF_WIDTH) and self.norm_dist > 0.1):
            self.get_sprite_projection()
            self.is_displayed = True
        else:
            self.is_displayed = False

    def update(self):
        self.get_sprite()

    @property
    def map_pos(self):
        return (int(self.x), int(self.y))


class AnimatedSprite(SpriteObject):
    def __init__(
        self,
        game,
        path="resources/sprites/animated_sprites/green_light/0.png",
        pos=(11.5, 3.5),
        scale=0.8,
        shift=0.16,
        animation_time=120,
        uuid_ = ''
    ):
        super().__init__(game, path, pos, scale, shift, uuid_)
        self.animation_time = animation_time
        self.path = path.rsplit("/", 1)[0]
        self.images = self.get_images(self.path)
        self.animation_time_prev = pg.time.get_ticks()
        self.animation_trigger = False

    def update(self):
        super().update()
        self.check_animation_time()
        self.animate(self.images)

    def animate(self, images):
        if self.animation_trigger:
            images.rotate(-1)
            self.image = images[0]

    def check_animation_time(self):
        self.animation_trigger = False
        time_now = pg.time.get_ticks()
        if time_now - self.animation_time_prev > self.animation_time:
            self.animation_time_prev = time_now
            self.animation_trigger = True

    def get_images(self, path):
        images = deque()
        for file_name in sorted(os.listdir(path)):
            if os.path.isfile(os.path.join(path, file_name)):
                img = pg.image.load(path + "/" + file_name).convert_alpha()
                images.append(img)
        return images


class StateSprite(SpriteObject):
    def __init__(
        self,
        game,
        path="resources/sprites/state_sprite/torch/0.png",
        pos=(11.5, 3.5),
        scale=0.8,
        shift=0.16,
        uuid_ = '',
        state = 0,
        last_press_uuid = '',
        hold = False
    ):
        super().__init__(game, path, pos, scale, shift, uuid_)
        self.path = path.rsplit("/", 1)[0]

        self.off_state = 0
        self.on_state = 1


        self.state = state
        self.image = self.get_images()
        self.activation_dist = 1
        self.key = pg.K_f

        self.last_press_uuid = last_press_uuid
        self.hold = hold
        self.last_toggle = 0

    def get_images(self):
        return pg.image.load(self.path + "/" + f"{self.state}" + ".png").convert_alpha()
    
    def toggle(self, state = -1, appy_state = False):
        new_state = -1
        if state == -1:
            if self.state == self.off_state:
                new_state = self.on_state
            elif self.state == self.on_state:
                new_state = self.off_state
        else:
            new_state = state

        if appy_state:
            self.state = new_state
            self.image = self.get_images()

        self.last_toggle = wpt.time()
        return (new_state, self.last_press_uuid)
    
    def press(self, appy_state = False, presser_uuid = ''):
        new_state = self.on_state
        if appy_state:
            self.state = new_state
            self.image = self.get_images()
            if self.hold:
                if self.state == 0:
                    self.last_press_uuid = ''
                else:
                    self.last_press_uuid = presser_uuid

        return (new_state, presser_uuid)
    
    def release(self, appy_state = False, presser_uuid = ''):
        new_state = self.off_state
        if appy_state:
            self.state = new_state
            self.image = self.get_images()
            if self.hold:
                if self.state == 0:
                    self.last_press_uuid = ''
                else:
                    self.last_press_uuid = presser_uuid

        return (new_state, presser_uuid)