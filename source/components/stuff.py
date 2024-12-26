__author__ = 'marble_xu'

import sys
import os

import pygame as pg

cwd = os.path.dirname(__file__)
sys.path.append(os.path.join(cwd,".."))

import setup, tools
import constants as c

class Collider(pg.sprite.Sprite):
    def __init__(self, x, y, width, height, name):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.Surface((width, height)).convert()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.name = name
        if c.DEBUG:
            self.image.fill(c.RED)

class Ground(pg.sprite.Sprite):
    def __init__(self, x, y, width, height):
        pg.sprite.Sprite.__init__(self)
        self.rect = pg.Rect(x , y , width, height)
        self.image = pg.Surface((width, height)).convert()
        self.name = 'ground'
        tile_rect = (0, 0, 16, 16)
        one_tile = tools.get_image(setup.GFX['tile_set'], *tile_rect, c.BLACK, 1)
        row = height // 16
        column = width // 16
        for i in range(row):
            for j in range(column):
                self.image.blit(one_tile, (j * 16, i * 16))

class Step(pg.sprite.Sprite):
    def __init__(self, x, y, num, direction):
        pg.sprite.Sprite.__init__(self)
        if direction:
            self.rect = pg.Rect(x, y, 16, 16*num)
            self.image = pg.Surface((16, 16*num)).convert()
        else:
            self.rect = pg.Rect(x, y, 16*num, 16)
            self.image = pg.Surface((16*num, 16)).convert()
        self.rect.x = x
        self.rect.y = y
        self.name = 'step'
        step_rect = (0, 16, 16, 16)
        one_tile = tools.get_image(setup.GFX['tile_set'], *step_rect, c.BLACK, 1)
        for i in range(num):
            if direction:
                self.image.blit(one_tile, (0, i*16))
            else:
                self.image.blit(one_tile, (i*16, 0))

class Closedbox(pg.sprite.Sprite):
    def __init__(self, x, y):
        pg.sprite.Sprite.__init__(self)
        self.name = 'closedbox'
        closedbox_rect = (432, 0, 16, 16)
        self.image = tools.get_image(setup.GFX['tile_set'], *closedbox_rect, c.BLACK, 1)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

class Checkpoint(pg.sprite.Sprite):
    def __init__(self, x, y, width, height, type, enemy_groupid=0, map_index=0, name=c.MAP_CHECKPOINT):
        pg.sprite.Sprite.__init__(self)
        self.image = pg.Surface((width, height))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.type = type
        self.enemy_groupid = enemy_groupid
        self.map_index = map_index
        self.name = name

class Stuff(pg.sprite.Sprite):
    def __init__(self, x, y, sheet, image_rect_list, scale):
        pg.sprite.Sprite.__init__(self)
        
        self.frames = []
        self.frame_index = 0
        for image_rect in image_rect_list:
            self.frames.append(tools.get_image(sheet, 
                    *image_rect, c.BLACK, scale))
        self.image = self.frames[self.frame_index]
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def update(self, *args):
        pass

class Pole(Stuff):
    def __init__(self, x, y):
        Stuff.__init__(self, x, y, setup.GFX['tile_set'],
                [(263, 144, 2, 16)], c.BRICK_SIZE_MULTIPLIER)

class PoleTop(Stuff):
    def __init__(self, x, y):
        Stuff.__init__(self, x, y, setup.GFX['tile_set'],
                [(228, 120, 8, 8)], c.BRICK_SIZE_MULTIPLIER)

class Flag(Stuff):
    def __init__(self, x, y):
        Stuff.__init__(self, x, y, setup.GFX[c.ITEM_SHEET],
                [(128, 32, 16, 16)], c.SIZE_MULTIPLIER)
        self.state = c.TOP_OF_POLE
        self.y_vel = 5

    def update(self):
        if self.state == c.SLIDE_DOWN:
            self.rect.y += self.y_vel
            if self.rect.bottom >= 485:
                self.state = c.BOTTOM_OF_POLE

class CastleFlag(Stuff):
    def __init__(self, x, y):
        Stuff.__init__(self, x, y, setup.GFX[c.ITEM_SHEET],
                [(129, 2, 14, 14)], c.SIZE_MULTIPLIER)
        self.y_vel = -2
        self.target_height = y
    
    def update(self):
        if self.rect.bottom > self.target_height:
            self.rect.y += self.y_vel

class Digit(pg.sprite.Sprite):
    def __init__(self, image):
        pg.sprite.Sprite.__init__(self)
        self.image = image
        self.rect = self.image.get_rect()

class Score():
    def __init__(self, x, y, score):
        self.x = x
        self.y = y
        self.y_vel = -3
        self.create_images_dict()
        self.score = score
        self.create_score_digit()
        self.distance = 130 if self.score == 1000 else 75
        
    def create_images_dict(self):
        self.image_dict = {}
        digit_rect_list = [(1, 168, 3, 8), (5, 168, 3, 8),
                            (8, 168, 4, 8), (0, 0, 0, 0),
                            (12, 168, 4, 8), (16, 168, 5, 8),
                            (0, 0, 0, 0), (0, 0, 0, 0),
                            (20, 168, 4, 8), (0, 0, 0, 0)]
        digit_string = '0123456789'
        for digit, image_rect in zip(digit_string, digit_rect_list):
            self.image_dict[digit] = tools.get_image(setup.GFX[c.ITEM_SHEET],
                                    *image_rect, c.BLACK, c.BRICK_SIZE_MULTIPLIER)
    
    def create_score_digit(self):
        self.digit_group = pg.sprite.Group()
        self.digit_list = []
        for digit in str(self.score):
            self.digit_list.append(Digit(self.image_dict[digit]))
        
        for i, digit in enumerate(self.digit_list):
            digit.rect = digit.image.get_rect()
            digit.rect.x = self.x + (i * 10)
            digit.rect.y = self.y
    
    def update(self, score_list):
        for digit in self.digit_list:
            digit.rect.y += self.y_vel
        
        if (self.y - self.digit_list[0].rect.y) > self.distance:
            score_list.remove(self)
            
    def draw(self, screen):
        for digit in self.digit_list:
            screen.blit(digit.image, digit.rect)


class Pipe(Stuff):
    def __init__(self, x, y, width, height, type, name=c.MAP_PIPE):
        if type == c.PIPE_TYPE_HORIZONTAL:
            rect = [(32, 128, 37, 30)]
        else:
            rect = [(0, 160, 32, 30)]
        Stuff.__init__(self, x, y, setup.GFX['tile_set'],
                rect, c.BRICK_SIZE_MULTIPLIER)
        self.name = name
        self.type = type
        if type != c.PIPE_TYPE_HORIZONTAL:
            self.create_image(x, y, height)

    def create_image(self, x, y, pipe_height):
        img = self.image
        rect = self.image.get_rect()
        width = rect.w
        height = rect.h
        self.image = pg.Surface((width, pipe_height)).convert()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

        top_height = height//2 + 3
        bottom_height = height//2 - 3
        self.image.blit(img, (0,0), (0, 0, width, top_height))
        num = (pipe_height - top_height) // bottom_height + 1
        for i in range(num):
            y = top_height + i * bottom_height
            self.image.blit(img, (0,y), (0, top_height, width, bottom_height))
        self.image.set_colorkey(c.BLACK)

    def check_ignore_collision(self, level):
        if self.type == c.PIPE_TYPE_HORIZONTAL:
            return True
        elif level.player.state == c.DOWN_TO_PIPE:
            return True
        return False

class Slider(Stuff):
    def __init__(self, x, y, num, direction, range_start, range_end, vel, name=c.MAP_SLIDER):
        Stuff.__init__(self, x, y, setup.GFX[c.ITEM_SHEET],
                [(64, 128, 15, 8)], 2.8)
        self.name = name
        self.create_image(x, y, num)
        self.range_start = range_start
        self.range_end = range_end
        self.direction = direction
        if self.direction == c.VERTICAL:
            self.y_vel = vel
        else:
            self.x_vel = vel
        

    def create_image(self, x, y, num):
        '''original slider image is short, we need to multiple it '''
        if num == 1:
            return
        img = self.image
        rect = self.image.get_rect()
        width = rect.w
        height = rect.h
        self.image = pg.Surface((width * num, height)).convert()
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        for i in range(num):
            x = i * width
            self.image.blit(img, (x,0))
        self.image.set_colorkey(c.BLACK)

    def update(self):
        if self.direction ==c.VERTICAL:
            self.rect.y += self.y_vel
            if self.rect.y < -self.rect.h:
                self.rect.y = c.SCREEN_HEIGHT
                self.y_vel = -1
            elif self.rect.y > c.SCREEN_HEIGHT:
                self.rect.y = -self.rect.h
                self.y_vel = 1
            elif self.rect.y < self.range_start:
                self.rect.y = self.range_start
                self.y_vel = 1
            elif self.rect.bottom > self.range_end:
                self.rect.bottom = self.range_end
                self.y_vel = -1
        else:
            self.rect.x += self.x_vel
            if self.rect.x < self.range_start:
                self.rect.x = self.range_start
                self.x_vel = 1
            elif self.rect.left > self.range_end:
                self.rect.left = self.range_end
                self.x_vel = -1
    
