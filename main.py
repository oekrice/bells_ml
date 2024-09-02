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
bell = init_bell(phy, 0.0)

# set up the window
DISPLAYSURF = pygame.display.set_mode((phy.pixels_x, phy.pixels_y), 0, 32)
pygame.display.set_caption('Animation')

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0,0,0)

async def main():
    
    fpsClock = pygame.time.Clock()

    force = 6.0 

    rlengths = []; rforces = []
    count = 0

    while True: # the main game loop
        DISPLAYSURF.fill(WHITE)
        
        bell.timestep(phy)
        phy.count = phy.count + 1
    
        #DISPLAY THINGS
        
        #Display 'handstroke' or 'backstroke'
        fontObj = pygame.font.Font('freesansbold.ttf', 32)
        if bell.rforce < 0.0:
            textSurfaceObj = fontObj.render('Handstroke', True, BLACK, WHITE)
        elif bell.rlength > bell.max_length - bell.backstroke_pull:
            textSurfaceObj = fontObj.render('Backstroke', True, BLACK, WHITE)
        else:
            textSurfaceObj = fontObj.render('', True, BLACK, WHITE)
        textRectObj = textSurfaceObj.get_rect()
        textRectObj.center = (800,500)

        bell.c_x, bell.c_y = -bell.com*np.sin(bell.angle), bell.com*np.cos(bell.angle)
        img_plot, (x_box, y_box) = phy.rotate(bell.img, bell.angle)
        
        DISPLAYSURF.blit(img_plot, (phy.pix(x_box,y_box)))
        DISPLAYSURF.blit(textSurfaceObj, textRectObj)
    
        phy.draw_point(DISPLAYSURF, bell.c_x, bell.c_y,GREEN)
    
        phy.draw_point(DISPLAYSURF, 0,0,RED)
    
        #Check for force on wheel - this takes effect at the next timestep
        press_keys = pygame.key.get_pressed()
        press_mouse = pygame.mouse.get_pressed()
            
        if press_keys[pygame.K_SPACE] or press_mouse[0]:
            if bell.rforce < 0.0:   #Can pull the entire handstroke
                bell.force = bell.rforce*force
            else:           #Can only pull some of the backstroke
                if bell.rlength > bell.max_length - bell.backstroke_pull:
                    bell.force = bell.rforce*force
                else:
                    bell.force = 0.0
        else:
            bell.force = 0.0
            
        #Check for quit
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return
            
        pygame.display.update()
        fpsClock.tick(phy.FPS)
        
        await asyncio.sleep(0)

asyncio.run(main())