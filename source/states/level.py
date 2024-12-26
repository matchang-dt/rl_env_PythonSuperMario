__author__ = 'marble_xu'

import json
import os
import sys

import numpy as np
import pygame as pg

cwd = os.path.dirname(__file__)
sys.path.append(os.path.join(cwd,".."))

import setup, tools
import constants as c
from components import info, stuff, player, brick, box, enemy, powerup, coin


class Level(tools.State):
    def __init__(self):
        tools.State.__init__(self)
        self.player = None

    def startup(self, current_time, persist, level_name='level_1'):
        self.game_info = persist
        self.persist = self.game_info
        self.game_info[c.CURRENT_TIME] = current_time
        self.death_timer = 0
        self.castle_timer = 0
        
        self.moving_score_list = []
        self.overhead_info = info.Info(self.game_info, c.LEVEL)
        self.load_map(level_name)
        self.setup_background()
        self.setup_maps()
        self.setup_ground()
        self.setup_step()
        self.setup_pipe()
        self.setup_slider()
        self.setup_static_coin()
        self.setup_brick_and_box()
        self.setup_player()
        self.setup_hidden_enemies()
        self.setup_checkpoints()
        self.setup_flagpole()
        self.setup_sprite_groups()
        self.clear = False
        self.screen_left = 0 # Left edge of screen advanced so far

    def load_map(self, level_name='level_1'):
        map_file = level_name + '.json'
        file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'maps', map_file)
        f = open(file_path)
        self.map_data = json.load(f)
        f.close()
        
    def setup_background(self):
        img_name = self.map_data[c.MAP_IMAGE]
        self.background = setup.GFX[img_name]
        self.bg_rect = self.background.get_rect()
        self.background.fill(c.SKY_BLUE)
        stage_length = 0
        for data in self.map_data[c.MAP_MAPS]:
            stage_length = max(stage_length, data['end_x'])
        self.background = pg.transform.scale(self.background, (int(stage_length), c.GAME_HEIGHT))
        self.bg_rect = self.background.get_rect()

        self.level = pg.Surface((self.bg_rect.w, self.bg_rect.h)).convert()
        self.viewport = pg.Rect(0, 0, c.GAME_WIDTH, c.GAME_HEIGHT)
        self.viewport_real_x = 0.0 # float, convert to integer before display

    def setup_maps(self):
        self.map_list = []
        if c.MAP_MAPS in self.map_data:
            for data in self.map_data[c.MAP_MAPS]:
                self.map_list.append((data['start_x'], data['end_x'], data['player_x'], data['player_y']))
            self.start_x, self.end_x, self.player_x, self.player_y = self.map_list[0]
            self.player_y += 1
        else:
            self.start_x = 0
            self.end_x = self.bg_rect.w
            self.player_x = 48
            self.player_y = 193
        
    def change_map(self, index, type):
        self.start_x, self.end_x, self.player_x, self.player_y = self.map_list[index]
        self.viewport.x = self.start_x
        if type == c.CHECKPOINT_TYPE_MAP:
            self.player.rect.x = self.viewport.x + self.player_x
            self.player.rect.bottom = self.player_y
            self.player.state = c.STAND
        elif type == c.CHECKPOINT_TYPE_PIPE_UP:
            self.player.rect.x = self.viewport.x + self.player_x
            self.player.rect.bottom = c.GROUND_HEIGHT
            self.player.state = c.UP_OUT_PIPE
            self.player.up_pipe_y = self.player_y
            
    def setup_collide(self, name):
        group = pg.sprite.Group()
        if name in self.map_data:
            for data in self.map_data[name]:
                group.add(stuff.Collider(data['x'], data['y'], 
                        data['width'], data['height'], name))
        return group

    def setup_ground(self):
        self.ground_group = pg.sprite.Group()
        if c.MAP_GROUND in self.map_data:
            for data in self.map_data[c.MAP_GROUND]:
                self.ground_group.add(stuff.Ground(data['x'], data['y'],
                                      data['width'], data['height']))

    def setup_step(self):
        self.step_group = pg.sprite.Group()
        if c.MAP_STEP in self.map_data:
            for data in self.map_data[c.MAP_STEP]:
                self.step_group.add(stuff.Step(data['x'], data['y'],
                                    data['step_num'], data['direction']))

    def setup_pipe(self):
        self.pipe_group = pg.sprite.Group()
        if c.MAP_PIPE in self.map_data:
            for data in self.map_data[c.MAP_PIPE]:
                self.pipe_group.add(stuff.Pipe(data['x'], data['y'],
                    data['width'], data['height'], data['type']))

    def setup_slider(self):
        self.slider_group = pg.sprite.Group()
        if c.MAP_SLIDER in self.map_data:
            for data in self.map_data[c.MAP_SLIDER]:
                if c.VELOCITY in data:
                    vel = data[c.VELOCITY]
                else:
                    vel = 1
                self.slider_group.add(stuff.Slider(data['x'], data['y'], data['num'],
                    data['direction'], data['range_start'], data['range_end'], vel))

    def setup_static_coin(self):
        self.static_coin_group = pg.sprite.Group()
        if c.MAP_COIN in self.map_data:
            for data in self.map_data[c.MAP_COIN]:
                self.static_coin_group.add(coin.StaticCoin(data['x'], data['y']))

    def setup_brick_and_box(self):
        self.coin_group = pg.sprite.Group()
        self.powerup_group = pg.sprite.Group()
        self.brick_group = pg.sprite.Group()
        self.brickpiece_group = pg.sprite.Group()
        self.closedbox_group = pg.sprite.Group()

        if c.MAP_BRICK in self.map_data:
            for data in self.map_data[c.MAP_BRICK]:
                brick.create_brick(self.brick_group, data, self)
        
        self.box_group = pg.sprite.Group()
        if c.MAP_BOX in self.map_data:
            for data in self.map_data[c.MAP_BOX]:
                if data['type'] == c.TYPE_COIN:
                    self.box_group.add(box.Box(data['x'], data['y'], data['type'], self.coin_group))
                else:
                    self.box_group.add(box.Box(data['x'], data['y'], data['type'], self.powerup_group))        
        if c.MAP_CLOSED_BLOCK in self.map_data:
            for data in self.map_data[c.MAP_CLOSED_BLOCK]:
                self.closedbox_group.add(stuff.Closedbox(data['x'], data['y']))

    def setup_player(self):
        if self.player is None:
            self.player = player.Player(self.game_info[c.PLAYER_NAME])
        else:
            self.player.restart()
        self.player.rect.x = self.viewport.x + self.player_x
        self.player_realx = self.player.rect.x # float of accurate position. convert to integer before display
        self.player.collision_range.rect.x = self.player.rect.x + 2
        self.player.rect.bottom = self.player_y
        self.player.collision_range.rect.y = self.player.rect.y + 1
        if c.DEBUG:
            self.player.rect.x = self.viewport.x + c.DEBUG_START_X
            self.player.rect.bottom = c.DEBUG_START_y
        self.viewport.x = max(self.player.rect.x - 110, 0)
        self.viewport_real_x = self.viewport.x

    def setup_enemies(self):
        self.enemy_group_list = []
        index = 0
        for data in self.map_data[c.MAP_ENEMY]:
            group = pg.sprite.Group()
            for item in data[str(index)]:
                group.add(enemy.create_enemy(item, self))
            self.enemy_group_list.append(group)
            index += 1
            
    def setup_hidden_enemies(self):
        self.hidden_enemy_group = pg.sprite.Group()
        for data in self.map_data[c.MAP_ENEMY]:
            self.hidden_enemy_group.add(enemy.create_enemy(data, self))
            
    def setup_checkpoints(self):
        self.checkpoint_group = pg.sprite.Group()
        for data in self.map_data[c.MAP_CHECKPOINT]:
            if c.ENEMY_GROUPID in data:
                enemy_groupid = data[c.ENEMY_GROUPID]
            else:
                enemy_groupid = 0
            if c.MAP_INDEX in data:
                map_index = data[c.MAP_INDEX]
            else:
                map_index = 0
            self.checkpoint_group.add(stuff.Checkpoint(data['x'], data['y'], data['width'], 
                data['height'], data['type'], enemy_groupid, map_index))
    
    def setup_flagpole(self):
        self.flagpole_group = pg.sprite.Group()
        if c.MAP_FLAGPOLE in self.map_data:
            for data in self.map_data[c.MAP_FLAGPOLE]:
                if data['type'] == c.FLAGPOLE_TYPE_FLAG:
                    sprite = stuff.Flag(data['x'], data['y'])
                    self.flag = sprite
                elif data['type'] == c.FLAGPOLE_TYPE_POLE:
                    sprite = stuff.Pole(data['x'], data['y'])
                else:
                    sprite = stuff.PoleTop(data['x'], data['y'])
                self.flagpole_group.add(sprite)
        
        
    def setup_sprite_groups(self):
        self.dying_group = pg.sprite.Group()
        self.enemy_group = pg.sprite.Group()
        self.shell_group = pg.sprite.Group()
        
        self.ground_step_pipe_group = pg.sprite.Group(self.ground_group,
                        self.pipe_group, self.step_group, self.slider_group)
        self.player_group = pg.sprite.Group(self.player)
        
    def update(self, surface, keys, current_time):
        self.game_info[c.CURRENT_TIME] = self.current_time = current_time
        self.handle_states(keys)
        self.draw(surface)
    
    def handle_states(self, keys):
        self.update_all_sprites(keys)
    
    def update_all_sprites(self, keys):
        if self.player.dead:
            self.player.update(keys, self.game_info, self.powerup_group)
            if self.current_time - self.death_timer > 3000:
                self.update_game_info()
                self.done = True
        elif self.player.state == c.IN_CASTLE:
            self.player.update(keys, self.game_info, None)
            self.flagpole_group.update()
            if self.current_time - self.castle_timer > 2000:
                self.update_game_info()
                self.done = True
        elif self.in_frozen_state():
            self.player.update(keys, self.game_info, None)
            self.check_checkpoints()
            self.update_viewport()
            self.overhead_info.update(self.game_info, self.player)
            for score in self.moving_score_list:
                score.update(self.moving_score_list)
        else:
            self.player.update(keys, self.game_info, self.powerup_group)
            self.flagpole_group.update()
            self.check_checkpoints()
            self.check_enemies()
            self.slider_group.update()
            self.static_coin_group.update(self.game_info)
            self.enemy_group.update(self.game_info, self)
            self.shell_group.update(self.game_info, self)
            self.brick_group.update()
            self.box_group.update(self.game_info, self.player)
            self.powerup_group.update(self.game_info, self)
            self.coin_group.update(self.game_info)
            self.brickpiece_group.update()
            self.dying_group.update(self.game_info, self)
            self.update_player_position()
            self.check_for_player_death()
            self.update_viewport()
            self.overhead_info.update(self.game_info, self.player)
            for score in self.moving_score_list:
                score.update(self.moving_score_list)

    def check_enemies(self):
        view = pg.sprite.Sprite()
        view.rect = pg.Rect(self.viewport.x, self.viewport.y, self.viewport.w + 32, self.viewport.h)
        # ↓'Group' object has no attribute 'rect'
        enemies = pg.sprite.spritecollide(view, self.hidden_enemy_group, True)
        if enemies:
            for item in enemies:
                self.enemy_group.add(item)

    def check_checkpoints(self):
        checkpoint = pg.sprite.spritecollideany(self.player, self.checkpoint_group)
        
        if checkpoint:
            if checkpoint.type == c.CHECKPOINT_TYPE_ENEMY:
                pass
            elif checkpoint.type == c.CHECKPOINT_TYPE_FLAG:
                self.done = True
                self.clear = True
                self.update_game_info()
            elif checkpoint.type == c.CHECKPOINT_TYPE_CASTLE:
                self.player.state = c.IN_CASTLE
                self.player.x_vel = 0
                self.castle_timer = self.current_time
                self.flagpole_group.add(stuff.CastleFlag(8745, 322))
            elif (checkpoint.type == c.CHECKPOINT_TYPE_MUSHROOM and
                    self.player.y_vel < 0):
                mushroom_box = box.Box(checkpoint.rect.x, checkpoint.rect.bottom - 40,
                                c.TYPE_LIFEMUSHROOM, self.powerup_group)
                mushroom_box.start_bump(self.moving_score_list)
                self.box_group.add(mushroom_box)
                self.player.y_vel = 7
                self.player.rect.y = mushroom_box.rect.bottom
                self.player.state = c.FALL
            elif checkpoint.type == c.CHECKPOINT_TYPE_PIPE:
                self.player.state = c.WALK_AUTO
            elif checkpoint.type == c.CHECKPOINT_TYPE_PIPE_UP:
                self.change_map(checkpoint.map_index, checkpoint.type)
            elif checkpoint.type == c.CHECKPOINT_TYPE_MAP:
                self.change_map(checkpoint.map_index, checkpoint.type)
            elif checkpoint.type == c.CHECKPOINT_TYPE_BOSS:
                self.player.state = c.WALK_AUTO
            checkpoint.kill()

    def update_flag_score(self):
        base_y = c.GROUND_HEIGHT - 80
        
        y_score_list = [(base_y, 100), (base_y-120, 400),
                    (base_y-200, 800), (base_y-320, 2000),
                    (0, 5000)]
        for y, score in y_score_list:
            if self.player.rect.y > y:
                self.update_score(score, self.flag)
                break
    
    # correct mario's position by this method not player class
    def update_player_position(self):
        if self.player.state == c.UP_OUT_PIPE:
            return

        self.player_realx += self.player.x_vel
        self.player.rect.x = round(self.player_realx)
        self.player.collision_range.rect.x = self.player.rect.x + 2
        if self.player.rect.x < self.start_x:
            self.player.rect.x = self.start_x
            self.player_realx = self.player.rect.x
        elif self.player.rect.right > self.end_x:
            self.player.rect.right = self.end_x
            self.player_realx = self.player.rect.x
        if self.player.rect.x < self.screen_left:
            self.player.rect.x = self.screen_left
            self.player_realx = self.player.rect.x
        self.check_player_x_collisions()
        
        if not self.player.dead:
            self.player.rect.y += round(self.player.y_vel)
            self.player.collision_range.rect.y = self.player.rect.y + 1
            self.check_player_y_collisions()
    
    def check_player_x_collisions(self):
        player = self.player.collision_range
        ground_step_pipe = pg.sprite.spritecollideany(player, self.ground_step_pipe_group)
        brick = pg.sprite.spritecollideany(player, self.brick_group)
        box = pg.sprite.spritecollideany(player, self.box_group)
        enemy = pg.sprite.spritecollideany(player, self.enemy_group)
        shell = pg.sprite.spritecollideany(player, self.shell_group)
        powerup = pg.sprite.spritecollideany(player, self.powerup_group)
        coin = pg.sprite.spritecollideany(player, self.static_coin_group)

        if box:
            self.adjust_player_for_x_collisions(box)
        elif brick:
            self.adjust_player_for_x_collisions(brick)
        elif ground_step_pipe:
            if (ground_step_pipe.name == c.MAP_PIPE and
                ground_step_pipe.type == c.PIPE_TYPE_HORIZONTAL):
                return
            self.adjust_player_for_x_collisions(ground_step_pipe)
        elif powerup:
            if powerup.type == c.TYPE_MUSHROOM:
                self.update_score(1000, powerup, 0)
                if not self.player.big:
                    self.player.y_vel = -1
                    self.player.transition_state = c.SMALL_TO_BIG
            elif powerup.type == c.TYPE_FIREFLOWER:
                self.update_score(1000, powerup, 0)
                if not self.player.big:
                    self.player.transition_state = c.SMALL_TO_BIG
                elif self.player.big and not self.player.fire:
                    self.player.transition_state = c.BIG_TO_FIRE
            elif powerup.type == c.TYPE_STAR:
                self.update_score(1000, powerup, 0)
                self.player.invincible = True
            elif powerup.type == c.TYPE_LIFEMUSHROOM:
                self.update_score(500, powerup, 0)
                self.game_info[c.LIVES] += 1
            if powerup.type != c.TYPE_FIREBALL:
                powerup.kill()
        elif enemy:
            if self.player.invincible:
                self.update_score(100, enemy, 0)
                self.move_to_dying_group(self.enemy_group, enemy)
                direction = c.RIGHT if self.player.facing_right else c.LEFT
                enemy.start_death_jump(direction)
            elif self.player.hurt_invincible:
                pass
            elif self.player.big:
                self.player.y_vel = -1
                self.player.transition_state = c.BIG_TO_SMALL
            else:
                self.player.start_death_jump(self.game_info)
                self.death_timer = self.current_time
        elif shell:
            if shell.state == c.SHELL_SLIDE:
                if self.player.invincible:
                    self.update_score(200, shell, 0)
                    self.move_to_dying_group(self.shell_group, shell)
                    direction = c.RIGHT if self.player.facing_right else c.LEFT
                    shell.start_death_jump(direction)
                elif self.player.hurt_invincible:
                    pass
                elif self.player.big:
                    self.player.y_vel = -1
                    self.player.transition_state = c.BIG_TO_SMALL
                else:
                    self.player.start_death_jump(self.game_info)
                    self.death_timer = self.current_time
            else:
                self.update_score(400, shell, 0)
                if self.player.rect.x < shell.rect.x:
                    self.player.rect.left = shell.rect.x 
                    shell.direction = c.RIGHT
                    shell.x_vel = 4
                else:
                    self.player.rect.x = shell.rect.left
                    shell.direction = c.LEFT
                    shell.x_vel = -4
                shell.rect.x += shell.x_vel * 4
                shell.real_x = shell.rect.x
                shell.state = c.SHELL_SLIDE
        elif coin:
            self.update_score(100, coin, 1)
            coin.kill()

    def adjust_player_for_x_collisions(self, collider):
        player = self.player.collision_range
        last_player_x = self.player.rect.x
        if collider.name == c.MAP_SLIDER:
            return

        if player.rect.x < collider.rect.x:
            player.rect.right = collider.rect.left
            self.player.rect.right = player.rect.right + 2
        else:
            player.rect.left = collider.rect.right
            self.player.rect.left = player.rect.left - 2
        difference = self.player.rect.x - last_player_x
        if difference < 0:
            self.viewport.x += difference
            self.viewport_real_x = self.viewport.x
        self.player_realx = self.player.rect.x
        self.player.x_vel = 0

    def check_player_y_collisions(self):
        player = self.player.collision_range
        ground_step_pipe = pg.sprite.spritecollideany(player, self.ground_step_pipe_group)
        enemy = pg.sprite.spritecollideany(player, self.enemy_group)
        shell = pg.sprite.spritecollideany(player, self.shell_group)

        # decrease runtime delay: when player is on the ground, don't check brick and box
        if self.player.rect.bottom < c.GROUND_HEIGHT:
            brick = pg.sprite.spritecollideany(player, self.brick_group)
            box = pg.sprite.spritecollideany(player, self.box_group)
            brick, box = self.prevent_collision_conflict(brick, box)
        else:
            brick, box = False, False

        if box:
            self.adjust_player_for_y_collisions(box)
        elif brick:
            self.adjust_player_for_y_collisions(brick)
        elif ground_step_pipe:
            self.adjust_player_for_y_collisions(ground_step_pipe)
        elif enemy:
            if self.player.invincible:
                self.update_score(100, enemy, 0)
                self.move_to_dying_group(self.enemy_group, enemy)
                direction = c.RIGHT if self.player.facing_right else c.LEFT
                enemy.start_death_jump(direction)
            elif (enemy.name == c.PIRANHA or
                enemy.name == c.FIRESTICK or
                enemy.name == c.FIRE_KOOPA or
                enemy.name == c.FIRE):
                pass
            elif self.player.y_vel > 0:
                self.update_score(100, enemy, 0)
                enemy.state = c.JUMPED_ON
                if enemy.name == c.GOOMBA:
                    self.move_to_dying_group(self.enemy_group, enemy)
                elif enemy.name == c.KOOPA or enemy.name == c.FLY_KOOPA:
                    self.enemy_group.remove(enemy)
                    self.shell_group.add(enemy)

                player.rect.bottom = enemy.rect.top
                self.player.rect.bottom = player.rect.bottom + 1
                self.player.state = c.JUMP
                self.player.y_vel = -2
        elif shell:
            if self.player.y_vel > 0:
                if shell.state != c.SHELL_SLIDE:
                    shell.state = c.SHELL_SLIDE
                    self.player.state = c.JUMP
                    self.player.y_vel = - 2
                    if self.player.rect.centerx < shell.rect.centerx:
                        shell.direction = c.RIGHT
                        shell.rect.left = self.player.rect.right + 5
                        shell.real_x = shell.rect.left
                    else:
                        shell.direction = c.LEFT
                        shell.rect.right = self.player.rect.left - 5
                        shell.real_x = shell.rect.left
        self.check_is_falling(self.player)
        self.check_if_player_on_IN_pipe()
    
    def prevent_collision_conflict(self, sprite1, sprite2):
        if sprite1 and sprite2:
            distance1 = abs(self.player.rect.centerx - sprite1.rect.centerx)
            distance2 = abs(self.player.rect.centerx - sprite2.rect.centerx)
            if distance1 < distance2:
                sprite2 = False
            else:
                sprite1 = False
        return sprite1, sprite2
        
    def adjust_player_for_y_collisions(self, sprite):
        player = self.player.collision_range
        if player.rect.top > sprite.rect.top:
            if sprite.name == c.MAP_BRICK:
                self.check_if_enemy_on_brick_box(sprite)
                if sprite.state == c.RESTING:
                    if self.player.big and sprite.type == c.TYPE_NONE:
                        sprite.change_to_piece(self.dying_group)
                    else:
                        if sprite.type == c.TYPE_COIN:
                            self.update_score(200, sprite, 1)
                        sprite.start_bump(self.moving_score_list)
            elif sprite.name == c.MAP_BOX:
                if sprite.state != c.OPENED:
                    self.check_if_enemy_on_brick_box(sprite)
                if sprite.state == c.RESTING:
                    if sprite.type == c.TYPE_COIN:
                        self.update_score(200, sprite, 1)
                    sprite.start_bump(self.moving_score_list)
            elif (sprite.name == c.MAP_PIPE and
                sprite.type == c.PIPE_TYPE_HORIZONTAL):
                return
            
            self.player.y_vel = 3
            player.rect.top = sprite.rect.bottom
            self.player.rect.top = player.rect.top - 1
            self.player.state = c.FALL
        else:
            self.player.y_vel = 0
            player.rect.bottom = sprite.rect.top
            self.player.rect.bottom = player.rect.bottom + 1
            if self.player.state == c.FLAGPOLE:
                self.player.state = c.WALK_AUTO
            elif self.player.state == c.END_OF_LEVEL_FALL:
                self.player.state = c.WALK_AUTO
            else:
                if self.player.x_vel != 0:
                    self.player.state = c.WALK
                else:
                    self.player.state = c.STAND
    
    def check_if_enemy_on_brick_box(self, brick):
        brick.rect.y -= 5
        enemy = pg.sprite.spritecollideany(brick, self.enemy_group)
        if enemy:
            self.update_score(100, enemy, 0)
            self.move_to_dying_group(self.enemy_group, enemy)
            if self.player.rect.centerx > brick.rect.centerx:
                direction = c.RIGHT
            else:
                direction = c.LEFT
            enemy.start_death_jump(direction)
        brick.rect.y += 5

    def in_frozen_state(self):
        if (self.player.transition_state == c.SMALL_TO_BIG or
            self.player.transition_state == c.BIG_TO_SMALL or
            self.player.transition_state == c.BIG_TO_FIRE or
            self.player.state == c.DEATH_JUMP or
            self.player.state == c.DOWN_TO_PIPE or
            self.player.state == c.UP_OUT_PIPE):
            return True
        else:
            return False

    def check_is_falling(self, target):
        if target.__class__ == player.Player:
            sprite = target.collision_range
        else:
            sprite = target
        sprite.rect.y += 1
        check_group = pg.sprite.Group(self.ground_step_pipe_group,
                            self.brick_group, self.box_group)
        
        if pg.sprite.spritecollideany(sprite, check_group) is None:
            if (target.state == c.WALK_AUTO or
                target.state == c.END_OF_LEVEL_FALL):
                target.state = c.END_OF_LEVEL_FALL
            elif (target.state != c.JUMP and 
                target.state != c.FLAGPOLE and
                not self.in_frozen_state()):
                target.state = c.FALL
        sprite.rect.y -= 1
    
    def check_for_player_death(self):
        if (self.player.rect.y > c.GAME_HEIGHT or
            self.overhead_info.time <= 0):
            self.player.start_death_jump(self.game_info)
            self.death_timer = self.current_time

    def check_if_player_on_IN_pipe(self):
        '''check if player is on the pipe which can go down in to it '''
        self.player.rect.y += 1
        pipe = pg.sprite.spritecollideany(self.player, self.pipe_group)
        if pipe and pipe.type == c.PIPE_TYPE_IN:
            if (self.player.crouching and
                self.player.rect.x < pipe.rect.centerx and
                self.player.rect.right > pipe.rect.centerx):
                self.player.state = c.DOWN_TO_PIPE
        self.player.rect.y -= 1
        
    def update_game_info(self):
        if self.player.dead:
            self.persist[c.LIVES] -= 1

        if self.persist[c.LIVES] == 0:
            self.next = c.GAME_OVER
        elif self.overhead_info.time == 0:
            self.next = c.TIME_OUT
        elif self.player.dead:
            self.next = c.LOAD_SCREEN
        else:
            # self.game_info[c.LEVEL_NUM] += 1
            self.next = c.LOAD_SCREEN

    def update_viewport(self):
        player_x = self.player.rect.x
        viewport_vel = max(self.player.x_vel, 0)
        if  player_x - 112 <= self.viewport.x <= player_x - 80:
            if viewport_vel > 1.2:
                viewport_vel = 1.2
            if self.in_frozen_state():
                viewport_vel = 0
            self.viewport_real_x += viewport_vel
            self.viewport.x = round(self.viewport_real_x)
        elif self.viewport.x < player_x - 112:
            self.viewport.x = player_x - 112
            self.viewport_real_x = self.viewport.x
            viewport_vel = 0
        else:
            self.viewport.x = player_x - 80
            self.viewport_real_x = self.viewport.x
            viewport_vel = 0

        self.viewport.x = max(0, self.viewport.x, self.screen_left)
        self.viewport.right = min(self.end_x, self.viewport.right)
        self.screen_left = self.viewport.x        
    
    def move_to_dying_group(self, group, sprite):
        group.remove(sprite)
        self.dying_group.add(sprite)
        
    def update_score(self, score, sprite, coin_num=0):
        self.game_info[c.SCORE] += score
        self.game_info[c.COIN_TOTAL] += coin_num
        x = sprite.rect.x
        y = sprite.rect.y - 10
        self.moving_score_list.append(stuff.Score(x, y, score))

    def step(action):
        pass

    def draw(self, surface):
        self.level.blit(self.background, self.viewport, self.viewport)
        self.ground_group.draw(self.level)
        self.step_group.draw(self.level)
        self.powerup_group.draw(self.level)
        self.brick_group.draw(self.level)
        self.box_group.draw(self.level)
        self.closedbox_group.draw(self.level)
        self.coin_group.draw(self.level)
        self.dying_group.draw(self.level)
        self.brickpiece_group.draw(self.level)
        self.flagpole_group.draw(self.level)
        self.shell_group.draw(self.level)
        self.enemy_group.draw(self.level)
        self.static_coin_group.draw(self.level)
        self.slider_group.draw(self.level)
        self.pipe_group.draw(self.level)
        self.player_group.draw(self.level)
        for score in self.moving_score_list:
            score.draw(self.level)
        if c.DEBUG:
            self.ground_step_pipe_group.draw(self.level)
            self.checkpoint_group.draw(self.level)

        self.screen = pg.Surface((c.GAME_WIDTH, c.GAME_HEIGHT))
        self.screen.blit(self.level, (0,0), self.viewport)

    def output_array(self):
        one_object_length = 16 * c.SIZE_MULTIPLIER
        ret = np.zeros((int(c.SCREEN_HEIGHT / one_object_length), int(c.SCREEN_WIDTH / one_object_length)),np.int)
        h = ret.shape[0]
        w = ret.shape[1]
        # print((h,w))
        view = pg.sprite.Sprite()
        view.rect = self.viewport
        powerup = pg.sprite.spritecollide(view, self.powerup_group, dokill=False)
        for item in powerup:
            i = item.rect.top // one_object_length
            j = (item.rect.left - self.viewport.left) // one_object_length
            if 0 <= i < h and 0 <= j < w:
                ret[int(i), int(j)] = 1
        brick = pg.sprite.spritecollide(view, self.brick_group, dokill=False)
        for item in brick:
            i = item.rect.top // one_object_length
            j = (item.rect.left - self.viewport.left) // one_object_length
            if 0 <= i < h and 0 <= j < w:
                ret[int(i), int(j)] = 2
        box = pg.sprite.spritecollide(view, self.box_group, dokill=False)
        for item in box:
            i = item.rect.top // one_object_length
            j = (item.rect.left - self.viewport.left) // one_object_length
            if 0 <= i < h and 0 <= j < w:
                ret[int(i), int(j)] = 3
        static_coin = pg.sprite.spritecollide(view, self.static_coin_group, dokill=False)
        for item in static_coin:
            i = item.rect.top // one_object_length
            j = (item.rect.left - self.viewport.left) // one_object_length
            if 0 <= i < h and 0 <= j < w:
                ret[int(i), int(j)] = 4
        flagpole = pg.sprite.spritecollide(view, self.flagpole_group, dokill=False)
        for item in flagpole:
            i = item.rect.top // one_object_length
            j = (item.rect.left - self.viewport.left) // one_object_length
            if 0 <= i < h and 0 <= j < w:
                ret[int(i), int(j)] = 5
        shell = pg.sprite.spritecollide(view, self.shell_group, dokill=False)
        for item in shell:
            i = item.rect.top // one_object_length
            j = (item.rect.left - self.viewport.left) // one_object_length
            if 0 <= i < h and 0 <= j < w:
                ret[int(i), int(j)] = 6
        enemy = pg.sprite.spritecollide(view, self.enemy_group, dokill=False)
        for item in enemy:
            i = item.rect.top // one_object_length
            j = (item.rect.left - self.viewport.left) // one_object_length
            if 0 <= i < h and 0 <= j < w:
                ret[int(i), int(j)] = 7
        pipe = pg.sprite.spritecollide(view, self.pipe_group, dokill=False)
        for item in enemy:
            i = item.rect.top // one_object_length
            j = (item.rect.left - self.viewport.left) // one_object_length
            if 0 <= i < h and 0 <= j < w:
                ret[int(i), int(j)] = 8
        item = self.player
        i = item.rect.top // one_object_length
        j = (item.rect.left - self.viewport.left) // one_object_length
        if 0 <= i < h and 0 <= j < w:
            ret[int(i), int(j)] = 9
        return ret
    