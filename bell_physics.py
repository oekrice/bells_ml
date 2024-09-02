# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 17:29:08 2024

@author: eleph
"""
import numpy as np
import pygame, sys
from pygame.locals import *

class init_physics:
    #define some physical parameters, like gravity etc.
    #use m/s as units I think. Need to convert that to pixel space, naturally
    #Also various plotting tools in here, because I can't think where else to put them
    def __init__(self):
        self.pixels_x = 1000
        self.pixels_y = 600
        self.FPS = 60
        self.g = -9.8 #Gravitational acceleration
        self.x1 = 2 #width of domain in metres
        self.y1 = self.x1 * self.pixels_y/self.pixels_x
        self.dt = 1.0/self.FPS
        self.xscale = self.pixels_x/self.x1
        self.yscale = self.pixels_y/self.y1
        self.count = 0

    def rotate(self, image, angle):
        #Rotates bell image
        init_w, _ = image.get_size()
        size_correction = init_w*np.sqrt(2)*np.cos(angle%(np.pi/2) - np.pi/4)
        rot_image = pygame.transform.rotate(image, 180*angle/np.pi)
        x_box = -(size_correction/2)/self.xscale; y_box = -(size_correction/2)/self.yscale
    
        return rot_image, (x_box, y_box)

    def draw_point(self, surface, pt_x, pt_y,colour):
        # Places a point on the screen at the coordinates x and y
        pygame.draw.circle(surface, colour, self.pix(pt_x,-pt_y), 5, 0)
        
    def pix(self, x,y):
        #Converts x and y coordinates in physics space to pixel space. 
        #Centre of the image is 0,0
        return self.pixels_x/2 + x*self.xscale, self.pixels_y/2 + y*self.yscale

class init_bell:
    #class for attributes of the bell itself, eg. speed and location

    def __init__(self, phy, init_angle):
        
        self.vx = 0.0
        self.vy = 0.0
        self.mass = 10.0   #mass of bell (in kg)
        self.radius = 0.5    #radius of wheel (in m)
        self.com = -0.4*self.radius #position of centre of mass (positive). Will update with better physics maybe
        self.counter = 0.8 #counterweight as proportion of weight on right side. Affects natural frequency of the swing
        self.stay_limit = 10.0  #currently doesn't do anything
        self.garter_hole = np.pi/4  #position of the garter hole relative to the stay
        
        self.angle = init_angle
        self.c_x, self.c_y = 0.0, self.com
        self.accel = 0.0   #angular acceleration in radians/s^2
        self.velocity = 0.0   #angular velocity in radians/s

        self.force = 0.0  #force on the bell wheel (as in, rope pull)
        self.stay_angle = 0.15 #how far over the top can the bell go (elastic collision)
        self.friction = 0.05 #friction parameter in arbitrary units
        self.backstroke_pull = 1.0   #length of backstroke pull in metres
        
        self.sound_angle = np.pi/4   #bell angle at which it dings
        self.prev_angle = init_angle #previous maximum angle
        self.max_length = 0.0   #max backstroke length
        
        self.rlength, self.effect_force = self.ropelength()
        self.rlengths = []; self.effect_forces = []


    def timestep(self, phy):
        #Do the timestep here, using only bell.force, which comes either from an input or the machine
        #Update the physics here
        self.accel = (np.sin(self.angle)*phy.g)*(1.0-self.counter)/-self.com - self.velocity*self.friction*10.0/self.mass
        #Add force if necessary
        self.accel = self.accel + self.force*self.radius/(-self.com*self.mass)
        self.velocity = self.velocity + self.accel*phy.dt 
        #extra friction so it actually stops at some point
        if abs(self.velocity) < 0.01 and self.force == 0.0:
            self.velocity = 0.5*self.velocity
            
        self.prev_angle = self.angle
        self.angle = self.angle + self.velocity*phy.dt
                
        #check if stay has been hit, and bounce if so
        if self.angle > np.pi + self.stay_angle:
            self.velocity = -0.7*self.velocity
            self.angle = 2*np.pi + 2*self.stay_angle - self.angle
        if self.angle < -np.pi - self.stay_angle:
            self.velocity = -0.7*self.velocity
            self.angle = -2*np.pi - 2*self.stay_angle - self.angle

        self.rlength, self.effect_force = self.ropelength()
        self.rlengths.append(self.rlength); self.effect_forces.append(self.effect_force)

        if len(self.rlengths) > 3: #Maximum height of previous backstroke. To allow for adjustment of tail end length.
            if self.effect_force > 0.0 and self.rlengths[-1] < self.rlengths[-2] and self.rlengths[-2] > self.rlengths[-3]:
                self.max_length = self.rlengths[-1]
        
    def ropelength(self):
        #Outputs the length of the rope above the garter hole, relative to the minimum.
        #Also outputs the maximum force available with direction.
        hole_angle = self.angle - np.pi + self.garter_hole
        
        if hole_angle > 0.0:
            #Fully Handstroke
            length = self.radius*hole_angle + self.radius
            effect_force = -1.0
        elif hole_angle <= -np.pi/2:
            #Fully backstroke
            length = self.radius*(-np.pi/2 - hole_angle) + self.radius
            effect_force = 1.0
        else:
            #Somewhere in between 
            xpos = self.radius + self.radius*np.sin(hole_angle)
            ypos = self.radius - self.radius*np.cos(hole_angle)
            vec1 = np.array([xpos, ypos])
            vec2 = np.array([np.cos(hole_angle), np.sin(hole_angle)])
            vec1  = vec1/np.linalg.norm(vec1); vec2  = vec2/np.linalg.norm(vec2);
            length = np.sqrt(xpos**2 + ypos**2)
            effect_force = -np.dot(vec1,vec2)
                    
        return length, effect_force
        