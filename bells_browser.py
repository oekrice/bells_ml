# -*- coding: utf-8 -*-
"""
Created on Thu Aug 29 10:03:56 2024

@author: eleph
"""

import pygame, sys
from pygame.locals import *
import numpy as np
import matplotlib.pyplot as plt

pygame.init()

FPS = 60 # frames per second setting
fpsClock = pygame.time.Clock()

pixels_x = 1000
pixels_y = 600


def draw_point(pt_x, pt_y,colour):
    # Places a point on the screen at the coordinates x and y
    pygame.draw.circle(DISPLAYSURF, colour, pix(pt_x,-pt_y), 5, 0)
    
def pix(x,y):
    #Converts x and y coordinates in physics space to pixel space. 
    #Centre of the image is 0,0
    return pixels_x/2 + x*phy.xscale, pixels_y/2 + y*phy.yscale
    
class init_physics:
    #define some physical parameters, like gravity etc.
    #use m/s as units I think. Need to convert that to pixel space, naturally
    def __init__(self):
        self.g = -9.8 #Gravitational acceleration
        self.x1 = 2 #width of domain in metres
        self.y1 = self.x1 * pixels_y/pixels_x
        self.dt = 1.0/FPS
        self.xscale = pixels_x/self.x1
        self.yscale = pixels_y/self.y1


class init_bell:
    #class for attributes of the bell itself, eg. speed and location

    def __init__(self,init_x, init_y, init_angle):
        
        self.vx = 0.0
        self.vy = 0.0
        self.mass = 10.0   #mass of bell (in kg)
        self.radius = 0.5    #radius of wheel (in m)
        self.com = -0.4*self.radius #position of centre of mass (positive). Will update with better physics maybe
        self.counter = 0.8 #counterweight as proportion of weight on right side. Affects natural frequency of the swing
        self.stay_limit = 10.0  #currently doesn't do anything
        self.garter_hole = np.pi/4  #position of the garter hole relative to the stay

        self.angle = init_angle
        self.img_init = pygame.image.load('bell.png')
        self.img = pygame.transform.scale(self.img_init, (2*self.radius*phy.xscale, 2*self.radius*phy.yscale))
        self.c_x, self.c_y = 0.0, self.com
        self.accel = 0.0   #angular acceleration in radians/s^2
        self.velocity = 0.0   #angular velocity in radians/s

        self.force = 0.0  #force on the bell wheel (as in, rope pull)
        self.stay_angle = 0.15 #how far over the top can the bell go (elastic collision)
        self.friction = 0.05 #friction parameter in arbitrary units
        self.backstroke_pull = 1.0   #length of backstroke pull in metres
        
        self.sound_angle = np.pi/4   #bell angle at which it dings
        
def ropelength(bell):
    #Outputs the length of the rope above the garter hole, relative to the minimum.
    #Also outputs the maximum force available with direction.
    hole_angle = bell.angle - np.pi + bell.garter_hole
    
    if hole_angle > 0.0:
        #Fully Handstroke
        length = bell.radius*hole_angle + bell.radius
        rforce = -1.0
    elif hole_angle <= -np.pi/2:
        #Fully backstroke
        length = bell.radius*(-np.pi/2 - hole_angle) + bell.radius
        rforce = 1.0
    else:
        #Somewhere in between 
        xpos = bell.radius + bell.radius*np.sin(hole_angle)
        ypos = bell.radius - bell.radius*np.cos(hole_angle)
        vec1 = np.array([xpos, ypos])
        vec2 = np.array([np.cos(hole_angle), np.sin(hole_angle)])
        vec1  = vec1/np.linalg.norm(vec1); vec2  = vec2/np.linalg.norm(vec2);
        length = np.sqrt(xpos**2 + ypos**2)
        rforce = -np.dot(vec1,vec2)
                
    return length, rforce
    
    
    
def rotate(image, angle):
    #Rotates bell image
    init_w, _ = image.get_size()
    size_correction = init_w*np.sqrt(2)*np.cos(angle%(np.pi/2) - np.pi/4)
    rot_image = pygame.transform.rotate(image, 180*angle/np.pi)
    x_box = -(size_correction/2)/phy.xscale; y_box = -(size_correction/2)/phy.yscale
    
    return rot_image, (x_box, y_box)
        
# set up the window
DISPLAYSURF = pygame.display.set_mode((pixels_x, pixels_y), 0, 32)
pygame.display.set_caption('Animation')

WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0,0,0)

bellImg = pygame.image.load('bell.png')

paused = False

phy = init_physics()
bell = init_bell(0,0,0.0)
force = 6.0

rlengths = []; rforces = []
max_length = 0.0
count = 0

sound = pygame.mixer.Sound('bellsound.wav')
prev_angle = 0.0

while True: # the main game loop
    DISPLAYSURF.fill(WHITE)
    
    if not paused:
        #Update the physics here
        bell.accel = (np.sin(bell.angle)*phy.g)*(1.0-bell.counter)/-bell.com - bell.velocity*bell.friction*10.0/bell.mass
        #Add force if necessary
        bell.accel = bell.accel + bell.force*bell.radius/(-bell.com*bell.mass)
        bell.velocity = bell.velocity + bell.accel*phy.dt 
        #extra friction so it actually stops at some point
        if abs(bell.velocity) < 0.01 and bell.force == 0.0:
            bell.velocity = 0.5*bell.velocity
            
        prev_angle = bell.angle
        bell.angle = bell.angle + bell.velocity*phy.dt
                
        #check if stay has been hit, and bounce if so
        if bell.angle > np.pi + bell.stay_angle:
            bell.velocity = -0.7*bell.velocity
            bell.angle = 2*np.pi + 2*bell.stay_angle - bell.angle
        if bell.angle < -np.pi - bell.stay_angle:
            bell.velocity = -0.7*bell.velocity
            bell.angle = -2*np.pi - 2*bell.stay_angle - bell.angle

        #Check for sound
        if abs(bell.angle) > bell.sound_angle and abs(prev_angle) <= bell.sound_angle:
            sound.play()

        rlength, rforce = ropelength(bell)
        rlengths.append(rlength); rforces.append(rforce)
        
        if len(rlengths) > 3: #Maximum height of previous backstroke. To allow for adjustment of tail end length.
            if rforce > 0.0 and rlengths[-1] < rlengths[-2] and rlengths[-2] > rlengths[-3]:
                max_length = rlengths[-1]
                
    #Display 'handstroke' or 'backstroke'
    fontObj = pygame.font.Font('freesansbold.ttf', 32)

    if rforce < 0.0:
        textSurfaceObj = fontObj.render('Handstroke', True, BLACK, WHITE)
    elif rlength > max_length - bell.backstroke_pull:
        textSurfaceObj = fontObj.render('Backstroke', True, BLACK, WHITE)
    else:
        textSurfaceObj = fontObj.render('', True, BLACK, WHITE)

    textRectObj = textSurfaceObj.get_rect()

    textRectObj.center = (800,500)
    
    count = count + 1
    
    if count % 100 == 0:  #plot some data
        plt.plot(rlengths)
        #plt.plot(rforces)
        plt.plot(max_length*np.ones(len(rlengths)))
        plt.show()
        
    bell.c_x, bell.c_y = -bell.com*np.sin(bell.angle), bell.com*np.cos(bell.angle)
    
    img_plot, (x_box, y_box) = rotate(bell.img, bell.angle)
    
    
    DISPLAYSURF.blit(img_plot, (pix(x_box,y_box)))
    DISPLAYSURF.blit(textSurfaceObj, textRectObj)

    draw_point(bell.c_x, bell.c_y,GREEN)

    draw_point(0,0,RED)

    #Check for force on wheel
    press = pygame.key.get_pressed()
    
    if press[pygame.K_RIGHT]:
        bell.force = 1.0*force
    elif press[pygame.K_LEFT]:
        bell.force = -1.0*force
    elif press[pygame.K_UP]:
        if rforce < 0.0:   #Can pull the entire handstroke
            bell.force = rforce*force
        else:           #Can only pull some of the backstroke
            if rlength > max_length - bell.backstroke_pull:
                bell.force = rforce*force
            else:
                bell.force = 0.0
    else:
        bell.force = 0.0
        
                    
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            #Check for pause
            if event.key == pygame.K_SPACE:
                paused = not(paused)

        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    pygame.display.update()
    fpsClock.tick(FPS)