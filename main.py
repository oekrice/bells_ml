# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 10:03:56 2024

@author: eleph
"""

import asyncio
import nest_asyncio

import pygame, sys
from pygame.locals import *
import numpy as np

from bell_physics import init_bell, init_physics
from display import display_tools

if True:
    nest_asyncio.apply()

pygame.init()

phy = init_physics()
bell = init_bell(phy, 0.0)
dp = display_tools(phy, bell)

bell.sound = pygame.mixer.Sound('bellsound_deep.wav')

#Set up colours
dp.define_colours()
#Import images and transform scales
dp.import_images(phy, bell)
# set up the window
pygame.display.set_caption('Animation')

async def main():
    
    fpsClock = pygame.time.Clock()

    wheel_force = 600   #force on the rope (in Newtons)

    while True: # the main game loop
    
        dp.surface.fill(dp.WHITE)
        
        bell.timestep(phy)
        phy.count = phy.count + 1
        
        dp.draw_rope(phy, bell)

        dp.display_stroke(phy, bell)   #Displays the text 'handstroke' or 'backstroke'
        dp.draw_bell(phy, bell)        
    
        #Check for sound
        if bell.ding == True:
        #if abs(bell.bell_angle) > bell.sound_angle and abs(bell.prev_angle) <= bell.sound_angle:
            bell.sound.play()
            #continue
        #Check for force on wheel - this takes effect at the next timestep
        press_keys = pygame.key.get_pressed()
        press_mouse = pygame.mouse.get_pressed()
            
        if press_keys[pygame.K_SPACE] or press_mouse[0]:
            if bell.effect_force < 0.0:   #Can pull the entire handstroke
                bell.wheel_force = bell.effect_force*wheel_force
            else:           #Can only pull some of the backstroke
                if bell.rlength > bell.max_length - bell.backstroke_pull:
                    bell.wheel_force = bell.effect_force*wheel_force
                else:
                    bell.wheel_force = 0.0
        else:
            bell.wheel_force = 0.0
            
        #Check for quit
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return
            
        pygame.display.update()
        fpsClock.tick(phy.FPS)
        
        await asyncio.sleep(0)

asyncio.run(main())