# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 10:03:56 2024

@author: eleph
"""

import asyncio
#import nest_asyncio

import pygame, sys
from pygame.locals import *
import numpy as np

from bell_physics import init_bell, init_physics
      
if False:
    nest_asyncio.apply()

pygame.init()

phy = init_physics()
bell = init_bell(phy, np.pi+0.05)

bell.img_init = pygame.image.load('bell.png')

bell.sound = pygame.mixer.Sound('bellsound_deep.wav')
bell.img = pygame.transform.scale(bell.img_init, (2*bell.radius*phy.xscale, 2*bell.radius*phy.yscale))

#Import images and transform scales
wheelimg = pygame.image.load('wheel.png')
wheelimg = pygame.transform.scale(wheelimg, (2*bell.radius*phy.xscale, 2*bell.radius*phy.yscale))

clapperimg = pygame.image.load('clapper.png')
clapperimg = pygame.transform.scale(clapperimg, (2*bell.radius*phy.xscale, 2*bell.radius*phy.yscale))

justbellimg = pygame.image.load('justbell.png')
justbellimg = pygame.transform.scale(justbellimg, (2*bell.radius*phy.xscale, 2*bell.radius*phy.yscale))

# set up the window
DISPLAYSURF = pygame.display.set_mode((phy.pixels_x, phy.pixels_y), 0, 32)
pygame.display.set_caption('Animation')

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BLACK = (0,0,0)

async def main():
    
    fpsClock = pygame.time.Clock()

    wheel_force = 7.5

    while True: # the main game loop
        DISPLAYSURF.fill(WHITE)
        
        bell.timestep(phy)
        phy.count = phy.count + 1
    
        #DISPLAY THINGS
        
        #Display 'handstroke' or 'backstroke'
        fontObj = pygame.font.Font('freesansbold.ttf', 32)
        if bell.effect_force < 0.0:
            textSurfaceObj = fontObj.render('Handstroke', True, BLACK, WHITE)
        elif bell.rlength > bell.max_length - bell.backstroke_pull:
            textSurfaceObj = fontObj.render('Backstroke', True, BLACK, WHITE)
        else:
            textSurfaceObj = fontObj.render('', True, BLACK, WHITE)
        textRectObj = textSurfaceObj.get_rect()
        textRectObj.center = (800,500)
        
    
        #Rotate clapper relative to the bell and paste
        
        wheel_rot, (x_box, y_box) = phy.rotate(wheelimg, bell.bell_angle)
        DISPLAYSURF.blit(wheel_rot, (phy.pix(x_box,y_box)))

        clapper_rot, (x_box, y_box) = phy.rotate(clapperimg, bell.clapper_angle + bell.bell_angle)
        DISPLAYSURF.blit(clapper_rot, (phy.pix(x_box,y_box)))
        
        clapper_rot, (x_box, y_box) = phy.rotate(justbellimg, bell.bell_angle)
        DISPLAYSURF.blit(clapper_rot, (phy.pix(x_box,y_box)))
        
        #Display helpful blobs
        
        DISPLAYSURF.blit(textSurfaceObj, textRectObj)
    
        #phy.draw_point(DISPLAYSURF, bell.c_x, bell.c_y,GREEN)
    
        #phy.draw_point(DISPLAYSURF, bell.cl_x, bell.cl_y,BLUE)

        #phy.draw_point(DISPLAYSURF, bell.p_x, bell.p_y,BLUE)

        #phy.draw_point(DISPLAYSURF, 0,0,RED)
        #Check for sound
        if bell.ding == True:
        #if abs(bell.bell_angle) > bell.sound_angle and abs(bell.prev_angle) <= bell.sound_angle:
            bell.sound.play()
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