__author__ = 'marble_xu'

import os
import json
import sys
import os

import pygame as pg

cwd = os.path.dirname(__file__)
sys.path.append(os.path.join(cwd,".."))

import setup, tools
import constants as c
from components import powerup

class Player(pg.sprite.Sprite):
    def __init__(self, player_name):
        pg.sprite.Sprite.__init__(self)
        self.player_name = player_name
        self.load_data()
        self.setup_timer()
        self.setup_state()
        self.setup_speed()
        self.load_images()
        
        if c.DEBUG:
            self.right_frames = self.big_fire_frames[0]
            self.left_frames = self.big_fire_frames[1]
            self.big = True
            self.fire = True
            
        self.frame_index = 0
        self.state = c.WALK
        self.transition_state = c.NEUTRAL
        self.image = self.right_frames[self.frame_index]
        self.rect = self.image.get_rect()
        self.fireball_count = 0
        self.jump_limit = 9
        self.collision_range = pg.sprite.Sprite()
        self.collision_range.rect = pg.Rect(self.rect.x + 2, self.rect.y + 1, self.rect.w - 4, self.rect.h - 2)
        self.collision_range.state = None

    def restart(self):
        '''restart after player is dead or go to next level'''
        if self.dead:
            self.dead = False
            self.big = False
            self.fire = False
            self.set_player_image(self.small_normal_frames, 0)
            self.right_frames = self.small_normal_frames[0]
            self.left_frames = self.small_normal_frames[1]
        self.state = c.STAND
        self.fireball_count = 0

    def load_data(self):
        player_file = str(self.player_name) + '.json'
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'player', player_file)
        f = open(file_path)
        self.player_data = json.load(f)

    def setup_timer(self):
        self.walking_timer = 0
        self.walking_first = True
        self.death_timer = 0
        self.flagpole_timer = 0
        self.transition_timer = 0
        self.transition_first = True
        self.hurt_invincible_timer = 0
        self.hurt_first = True
        self.invincible_timer = 0
        self.invincible_first = True
        self.last_fireball_time = 0

    def setup_state(self):
        self.facing_right = True
        self.allow_jump = True
        self.allow_fireball = True
        self.dead = False
        self.big = False
        self.fire = False
        self.hurt_invincible = False
        self.invincible = False
        self.crouching = False

    def setup_speed(self):
        speed = self.player_data[c.PLAYER_SPEED]
        self.x_vel = 0
        self.y_vel = 0
        
        self.max_walk_vel = speed[c.MAX_WALK_SPEED]
        self.max_run_vel = speed[c.MAX_RUN_SPEED]
        self.max_y_vel = speed[c.MAX_Y_VEL]
        self.walk_accel = speed[c.WALK_ACCEL]
        self.run_accel = speed[c.RUN_ACCEL]
        self.initial_speed = speed[c.INITIAL_SPEED]
        self.jump_vel = speed[c.JUMP_VEL]
        self.jump_threshold = self.max_run_vel * 0.9
        
        self.gravity = c.GRAVITY
        self.max_x_vel = self.max_walk_vel
        self.x_accel = self.walk_accel
        self.break_accel = speed['break_accel']

    def load_images(self):
        sheet = setup.GFX['mario_bros']
        frames_list = self.player_data[c.PLAYER_FRAMES]

        self.right_frames = []
        self.left_frames = []

        self.right_small_normal_frames = []
        self.left_small_normal_frames = []
        self.right_big_normal_frames = []
        self.left_big_normal_frames = []
        self.right_big_fire_frames = []
        self.left_big_fire_frames = []
        
        for name, frames in frames_list.items():
            for frame in frames:
                image = tools.get_image(sheet, frame['x'], frame['y'], 
                                    frame['width'], frame['height'],
                                    c.BLACK, c.SIZE_MULTIPLIER)
                left_image = pg.transform.flip(image, True, False)

                if name == c.RIGHT_SMALL_NORMAL:
                    self.right_small_normal_frames.append(image)
                    self.left_small_normal_frames.append(left_image)
                elif name == c.RIGHT_BIG_NORMAL:
                    self.right_big_normal_frames.append(image)
                    self.left_big_normal_frames.append(left_image)
                elif name == c.RIGHT_BIG_FIRE:
                    self.right_big_fire_frames.append(image)
                    self.left_big_fire_frames.append(left_image)
        
        self.small_normal_frames = [self.right_small_normal_frames,
                                    self.left_small_normal_frames]
        self.big_normal_frames = [self.right_big_normal_frames,
                                    self.left_big_normal_frames]
        self.big_fire_frames = [self.right_big_fire_frames,
                                    self.left_big_fire_frames]
                                    
        self.all_images = [self.right_small_normal_frames,
                           self.left_small_normal_frames,
                           self.right_big_normal_frames,
                           self.left_big_normal_frames,
                           self.right_big_fire_frames,
                           self.left_big_fire_frames]
        
        self.right_frames = self.small_normal_frames[0]
        self.left_frames = self.small_normal_frames[1]

    def update(self, keys, game_info, fire_group):
        self.current_time = game_info[c.CURRENT_TIME]
        self.handle_state(keys, fire_group)
        self.check_if_hurt_invincible()
        self.check_if_invincible()
        self.animation()

    def handle_state(self, keys, fire_group):
        if self.transition_state == c.SMALL_TO_BIG:
            self.changing_to_big()
        elif self.transition_state == c.BIG_TO_SMALL:
            self.changing_to_small()
        elif self.transition_state == c.BIG_TO_FIRE:
            self.changing_to_fire()
        elif self.state == c.STAND:
            self.standing(keys, fire_group)
        elif self.state == c.WALK:
            self.walking(keys, fire_group)
        elif self.state == c.JUMP:
            self.jumping(keys, fire_group)
        elif self.state == c.FALL:
            self.falling(keys, fire_group)
        elif self.state == c.DEATH_JUMP:
            self.jumping_to_death()
        elif self.state == c.FLAGPOLE:
            self.flag_pole_sliding()
        elif self.state == c.WALK_AUTO:
            self.walking_auto()
        elif self.state == c.END_OF_LEVEL_FALL:
            self.y_vel += self.gravity
        elif self.state == c.IN_CASTLE:
            self.frame_index = 0
        elif self.state == c.SMALL_TO_BIG:
            self.changing_to_big()
        elif self.state == c.BIG_TO_SMALL:
            self.changing_to_small()
        elif self.state == c.BIG_TO_FIRE:
            self.changing_to_fire()
        elif self.state == c.DOWN_TO_PIPE:
            self.y_vel = 1
            self.rect.y += self.y_vel
        elif self.state == c.UP_OUT_PIPE:
            self.y_vel = -1
            self.rect.y += self.y_vel
            if self.rect.bottom < self.up_pipe_y:
                self.state = c.STAND

    def check_to_allow_jump(self, keys):
        if not keys[4]:
            self.allow_jump = True
    
    def check_to_allow_fireball(self, keys):
        if not keys[3]:
            self.allow_fireball = True

    def standing(self, keys, fire_group):
        self.check_to_allow_jump(keys)
        self.check_to_allow_fireball(keys)
        
        self.frame_index = 0
        self.x_vel = 0
        self.y_vel = 0
        
        if keys[3]:
            if self.fire and self.allow_fireball and not not keys[1]:
                self.shoot_fireball(fire_group)

        if keys[1]:
            self.update_crouch_or_not(True)

        if keys[0]:
            self.facing_right = False
            self.update_crouch_or_not()
            self.state = c.WALK
        elif keys[2]:
            self.facing_right = True
            self.update_crouch_or_not()
            self.state = c.WALK
        elif keys[4]:
            if self.allow_jump:
                if not keys[1] or not self.big:
                    self.update_crouch_or_not()
                else:
                    self.update_crouch_or_not(True)
                self.state = c.JUMP
                self.y_vel = self.jump_vel
                self.jump_step = self.jump_limit
                self.jump_start = self.current_time

        if not keys[1]:
            self.update_crouch_or_not()

    def update_crouch_or_not(self, isDown=False):
        if not self.big:
            self.crouching = True if isDown else False
            return
        if not isDown and not self.crouching:
            return
        
        self.crouching = True if isDown else False
        frame_index = 7 if isDown else 0 
        bottom = self.rect.bottom
        left = self.rect.x
        if self.facing_right:
            self.image = self.right_frames[frame_index]
        else:
            self.image = self.left_frames[frame_index]
        self.rect = self.image.get_rect()
        self.rect.bottom = bottom
        self.rect.x = left
        self.frame_index = frame_index
        self.collision_range.rect = pg.Rect(self.rect.x + 2, self.rect.y + 1, self.rect.w - 4, self.rect.h - 2)

    def walking(self, keys, fire_group):
        self.check_to_allow_jump(keys)
        self.check_to_allow_fireball(keys)

        if self.frame_index == 0:
            self.frame_index += 1
            self.walking_timer = self.current_time
            self.walking_step = 0
        elif self.walking_step > self.calculate_animation_speed():
            if self.frame_index < 3:
                self.frame_index += 1
            else:
                self.frame_index = 1
            self.walking_step = 0
        self.walking_step += 1
        
        if keys[3]:
            self.max_x_vel = self.max_run_vel
            self.x_accel = self.run_accel
            if self.fire and self.allow_fireball and not keys[1]:
                self.shoot_fireball(fire_group)
        else:
            self.max_x_vel = self.max_walk_vel
            self.x_accel = self.walk_accel
        
        if keys[4]:
            if self.allow_jump:
                self.state = c.JUMP
                self.jump_start = self.current_time
                if abs(self.x_vel) > self.jump_threshold:
                    self.jump_step = self.jump_limit + 4
                    self.y_vel = self.jump_vel
                else:
                    self.jump_step = self.jump_limit
                    self.y_vel = self.jump_vel
                

        if keys[0]:
            self.facing_right = False
            self.update_crouch_or_not()
            if self.x_vel > 0:
                self.frame_index = 5
                self.x_accel = c.SMALL_TURNAROUND
            
            self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel, True)
        elif keys[2]:
            self.facing_right = True
            self.update_crouch_or_not()
            if self.x_vel < 0:
                self.frame_index = 5
                self.x_accel = c.SMALL_TURNAROUND
            
            self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel)
        else:
            if keys[1]:
                self.update_crouch_or_not(True)
            else:
                self.update_crouch_or_not()
            if self.facing_right:
                if self.x_vel > 0:
                    self.x_vel -= self.break_accel
                else:
                    self.x_vel = 0
                    self.state = c.STAND
            else:
                if self.x_vel < 0:
                    self.x_vel += self.break_accel
                else:
                    self.x_vel = 0
                    self.state = c.STAND

    def jumping(self, keys, fire_group):
        """ y_vel value: positive is down, negative is up """
        self.check_to_allow_fireball(keys)
        self.allow_jump = False
        self.jump_step -= 1

        if not self.crouching:
            self.frame_index = 4
        self.gravity = c.JUMP_GRAVITY

        if keys[2]:
            self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel)
        elif keys[0]:
            self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel, True)
        if not keys[4] or self.jump_step < 1:
            self.gravity = c.GRAVITY
            self.state = c.FALL

        if keys[3]:
            if self.fire and self.allow_fireball and not self.crouching:
                self.shoot_fireball(fire_group)

    def crouching_jumping(self, keys, fire_group):
        """ y_vel value: positive is down, negative is up """
        self.check_to_allow_fireball(keys)
        
        self.allow_jump = False
        self.gravity = c.JUMP_GRAVITY
        self.jump_step -= 1

        if keys[2]:
            self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel)
        elif keys[0]:
            self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel, True)
        
        if not keys[4] or self.jump_step < 1:
            self.gravity = c.GRAVITY
            self.state = c.FALL

    def falling(self, keys, fire_group):
        self.check_to_allow_fireball(keys)
        self.y_vel = self.cal_vel(self.y_vel, self.max_y_vel, self.gravity)
        
        if keys[2]:
            self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel)
        elif keys[0]:
            self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel, True)
        
        if keys[3]:
            if self.fire and self.allow_fireball and not self.crouching:
                self.shoot_fireball(fire_group)
    
    def jumping_to_death(self):
        if self.death_timer == 0:
            self.death_timer = self.current_time
        elif (self.current_time - self.death_timer) > 500:
            self.rect.y += self.y_vel
            self.y_vel += self.gravity

    def cal_vel(self, vel, max_vel, accel, isNegative=False):
        """ max_vel and accel must > 0 """
        if isNegative:
            new_vel = vel * -1
        else:
            new_vel = vel
        tmp_vel = new_vel + accel 
        if tmp_vel < max_vel:
            new_vel += accel
        elif tmp_vel < self.max_run_vel:
            new_vel -= self.break_accel
        if new_vel > self.max_run_vel:
            new_vel = self.max_run_vel
        if isNegative:
            return new_vel * -1
        else:
            return new_vel

    def calculate_animation_speed(self):
        if self.x_vel == 0:
            animation_speed = 13
        elif self.x_vel > 0:
            animation_speed = 13 - self.x_vel * 3
        else:
            animation_speed = 13 + self.x_vel * 3
        return animation_speed

    def shoot_fireball(self, powerup_group):
        if self.fireball_count < 2:
            self.allow_fireball = False
            powerup_group.add(powerup.FireBall(self.rect.right, 
                            self.rect.y, self.facing_right))
            self.frame_index = 6
            self.fireball_count += 1

    def flag_pole_sliding(self):
        self.state = c.FLAGPOLE
        self.x_vel = 0
        self.y_vel = 5

        if self.flagpole_timer == 0:
            self.flagpole_timer = self.current_time
        elif self.rect.bottom < 493:
            if (self.current_time - self.flagpole_timer) < 65:
                self.frame_index = 9
            elif (self.current_time - self.flagpole_timer) < 130:
                self.frame_index = 10
            else:
                self.flagpole_timer = self.current_time
        elif self.rect.bottom >= 493:
            self.frame_index = 10

    def walking_auto(self):
        self.max_x_vel = 5
        self.x_accel = self.walk_accel
        
        self.x_vel = self.cal_vel(self.x_vel, self.max_x_vel, self.x_accel)
        
        if (self.walking_timer == 0 or (self.current_time - self.walking_timer) > 200):
            self.walking_timer = self.current_time
        elif (self.current_time - self.walking_timer >
                    self.calculate_animation_speed()):
            if self.frame_index < 3:
                self.frame_index += 1
            else:
                self.frame_index = 1
            self.walking_timer = self.current_time

    def changing_to_big(self):
        step_list = [8, 12, 22, 26, 30, 34, 38, 42, 46, 50, 56]
        # size value 0:small, 1:middle, 2:big
        size_list = [1, 0, 1, 0, 1, 2, 0, 1, 2, 0, 2]
        frames = [(self.small_normal_frames, 0), (self.small_normal_frames, 7),
                    (self.big_normal_frames, 0)]
        if self.transition_first:
            self.big = True
            self.change_index = 0
            self.transition_first = False
            self.transition_step = 0
        elif self.transition_step >= step_list[self.change_index]:
            if (self.change_index + 1) >= len(step_list):
                # player becomes big
                self.transition_first = True
                self.set_player_image(self.big_normal_frames, 0)
                self.transition_state = c.NEUTRAL
                self.right_frames = self.right_big_normal_frames
                self.left_frames = self.left_big_normal_frames
            else:
                frame, frame_index = frames[size_list[self.change_index]]
                self.set_player_image(frame, frame_index)
            self.change_index += 1
        self.transition_step += 1

    def changing_to_small(self):
        step_list = [16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56]
        # size value 0:big, 1:middle, 2:small
        size_list = [0, 1, 2, 1, 2, 1, 2, 1, 2, 1, 2]
        frames = [(self.big_normal_frames, 4), (self.big_normal_frames, 8),
                    (self.small_normal_frames, 8)]

        if self.transition_first:
            self.change_index = 0
            self.transition_first = False
            self.transition_step = 0
        elif self.transition_step >= step_list[self.change_index]:
            if (self.change_index + 1) >= len(step_list):
                # player becomes small
                self.transition_first = True
                self.set_player_image(self.small_normal_frames, 0)
                self.transition_state = c.NEUTRAL
                self.big = False
                self.fire = False
                self.hurt_invincible = True
                self.right_frames = self.right_small_normal_frames
                self.left_frames = self.left_small_normal_frames
            else:
                frame, frame_index = frames[size_list[self.change_index]]
                self.set_player_image(frame, frame_index)
            self.change_index += 1
        self.transition_step += 1

    def changing_to_fire(self):
        step_list = [4, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60]
        # size value 0:fire, 1:big green, 2:big red, 3:big black
        size_list = [0, 1, 2, 3, 0, 1, 2, 3, 0, 1, 2, 3, 0, 1]
        frames = [(self.big_fire_frames, 3), (self.big_normal_frames, 3),
                    (self.big_fire_frames, 3), (self.big_normal_frames, 3)]
                    
        if self.transition_first:
            self.change_index = 0
            self.transition_first = False
            self.transition_step = 0
        elif self.transition_step >= step_list[self.change_index]:
            if (self.change_index + 1) >= len(step_list):
                # player becomes fire
                self.transition_first = True
                self.set_player_image(self.big_fire_frames, 3)
                self.fire = True
                self.transition_state = c.NEUTRAL
                self.right_frames = self.right_big_fire_frames
                self.left_frames = self.left_big_fire_frames
            else:
                frame, frame_index = frames[size_list[self.change_index]]
                self.set_player_image(frame, frame_index)
            self.change_index += 1
        self.transition_step += 1

    def set_player_image(self, frames, frame_index):
        self.frame_index = frame_index
        if self.facing_right:
            self.right_frames = frames[0]
            self.image = frames[0][frame_index]
        else:
            self.left_frames = frames[1]
            self.image = frames[1][frame_index]
        bottom = self.rect.bottom
        centerx = self.rect.centerx
        self.rect = self.image.get_rect()
        self.rect.bottom = bottom
        self.rect.centerx = centerx
        self.collision_range.rect = pg.Rect(self.rect.x + 2, self.rect.y + 1, self.rect.w - 4, self.rect.h - 2)

    def check_if_hurt_invincible(self):
        if self.hurt_invincible:
            if self.hurt_first:
                self.hurt_step = 0
                self.flash_step = 0
                self.hurt_first = False
            elif self.hurt_step < 121:
                if self.flash_step < 3:
                    self.image.set_alpha(0)
                elif self.flash_step < 4:
                    self.image.set_alpha(255)
                else:
                    self.flash_step = 0
                self.hurt_step += 1
                self.flash_step += 1
            else:
                self.hurt_invincible = False
                self.hurt_first = True
                for frames in self.all_images:
                    for image in frames:
                        image.set_alpha(255)

    def check_if_invincible(self):
        if self.invincible:
            if self.invincible_first:
                self.invincible_step = 0
                self.flash_step = 0
                self.invincible_first = False
            elif self.invincible_step < 361:
                if self.flash_step < 3:
                    self.image.set_alpha(0)
                elif self.flash_step < 4:
                    self.image.set_alpha(255)
                else:
                    self.flash_step = 0
            elif self.invincible_step < 481:
                if self.flash_step < 7:
                    self.image.set_alpha(0)
                elif self.flash_step < 12:
                    self.image.set_alpha(255)
                else:
                    self.flash_step = 0
            else:
                self.invincible = False
                self.invincible_first = True
                for frames in self.all_images:
                    for image in frames:
                        image.set_alpha(255)
            self.invincible_step += 1
            self.flash_step += 1

    def animation(self):
        if self.facing_right:
            self.image = self.right_frames[self.frame_index]
        else:
            self.image = self.left_frames[self.frame_index]

    def start_death_jump(self, game_info):
        self.dead = True
        self.y_vel = -11
        self.gravity = .5
        self.frame_index = 6
        self.state = c.DEATH_JUMP
