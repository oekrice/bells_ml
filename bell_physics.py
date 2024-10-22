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
        self.x1 = 2 #width of domain in 'metres'
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
        self.counter = 0.1 #counterweight as proportion of weight on right side. Affects natural frequency of the swing
        self.garter_hole = np.pi/4  #position of the garter hole relative to the stay
        
        self.com_1 = -0.4*self.radius   #point at which gravity acts in the correct direction
        self.com_2 = -self.com_1    #point at which gravity acts in the counterweight direction
                #This is sort of arbirtrary given you can adjust the proportions, and I'll leave it as that        
        
        self.clapper_angle = 0.0  #Angle of clapper RELATIVE to the bell
        self.clapper_mass = 0.05*self.mass   # mass of clapper (proportionally to the bell I suppose)
        self.clapper_limit = 0.5   #maximum clapper angle  (will need tweaking)
        self.clapper_pivot = 0.1*self.com_1 #distance of pivot point from the centre of the bell
        self.clapper_length = 0.575*self.radius  #clapper length
        self.clapper_velocity = 0.0  #clapper angular velocity
        self.onedge = False
        self.ding = False; self.ding_reset = True
        
        self.m1 = self.mass/(1.0 + self.counter)   #mass through right-side position
        self.m2 = self.mass - self.m1   #mass through wrong-side position

        self.bell_angle = init_angle
        self.c_x, self.c_y = 0.0, self.com_1   #centres of mass for plotting
        self.cl_x, self.cl_y = 0.0, self.clapper_pivot + self.clapper_length   #centres of mass for clapper. 
        self.p_x, self.p_y = 0.0, self.clapper_pivot 

        self.accel = 0.0   #angular acceleration in radians/s^2
        self.velocity = 0.0   #angular velocity in radians/s

        self.wheel_force = 0.0  #force on the bell wheel (as in, rope pull)
        self.stay_angle = 0.2 #how far over the top can the bell go (elastic collision)
        self.friction = 0.1 #friction parameter in arbitrary units
        self.backstroke_pull = 1.0   #length of backstroke pull in metres
        
        self.sound_angle = np.pi/4   #bell angle at which it dings
        self.prev_angle = init_angle #previous maximum angle
        self.max_length = 0.0   #max backstroke length
        
        self.rlength, self.effect_force = self.ropelength()
        self.rlengths = []; self.effect_forces = []


    def timestep(self, phy):
        #Do the timestep here, using only bell.force, which comes either from an input or the machine
        #Update the physics here
        
        #Moment due to gravity in the direction of rotation
        self.force = 0.0
        self.force = self.force - np.sin(self.bell_angle)*phy.g*self.m1*self.com_1
        self.force = self.force - np.sin(self.bell_angle)*phy.g*self.m2*self.com_2
        self.force = self.force - self.velocity*self.friction
        #if self.onedge:
        self.force = self.force + self.p_x*phy.g*self.clapper_mass
        
        #Angular cceleration due to gravity 
        if self.onedge:   #depends on whether the clapper is currently resting on the side of the bell
            self.accel = self.force/(abs(self.com_1*self.m1) + abs(self.com_2*self.m2) + abs((self.clapper_pivot+self.clapper_length)*self.clapper_mass))
        else:
            self.accel = self.force/(abs(self.com_1*self.m1) + abs(self.com_2*self.m2))

        #Acceleration on the wheel
        self.accel = self.accel + self.wheel_force*self.radius/(abs(self.com_1*self.m1) + abs(self.com_2*self.m2))
        #Velocity timestep (forward Euler)
        self.velocity = self.velocity + self.accel*phy.dt 
        #extra friction so it actually stops at some point
        if abs(self.velocity) < 0.01 and self.force == 0.0:
            self.velocity = 0.5*self.velocity
            
        self.prev_angle = self.bell_angle
        self.bell_angle = self.bell_angle + self.velocity*phy.dt
                
        #Update location of the clapper (using some physics which may well be dodgy)
        #raw_angle = np.arctan2(self.cl_x - self.p_x, self.cl_y - self.p_y)
        #Add gravity moment from clapper (mass is irrelevant as it cancels out)
        cl_force = phy.g*(self.cl_x - self.p_x)/self.clapper_length
        cl_force = cl_force - 1.0*self.clapper_velocity*self.friction
        self.clapper_velocity = self.clapper_velocity + cl_force*phy.dt - self.accel*phy.dt   #this is RELATIVE to the bell
        
        
        #check if stay has been hit, and bounce if so
        if self.bell_angle > np.pi + self.stay_angle:
            self.velocity = -0.7*self.velocity
            self.bell_angle = 2*np.pi + 2*self.stay_angle - self.bell_angle
        if self.bell_angle < -np.pi - self.stay_angle:
            self.velocity = -0.7*self.velocity
            self.bell_angle = -2*np.pi - 2*self.stay_angle - self.bell_angle

        #Update clapper angle
        self.clapper_angle = self.clapper_angle + self.clapper_velocity*phy.dt
        
        #Check if bell has struck
        if self.clapper_angle < -self.clapper_limit:
            self.clapper_velocity = 0.0
            self.clapper_angle = -self.clapper_limit
            self.onedge = True
        elif self.clapper_angle > self.clapper_limit:
            self.clapper_velocity = 0.0
            self.clapper_angle = self.clapper_limit
            self.onedge = True
        else:
            self.onedge = False
        if self.onedge and self.ding_reset:
            self.ding = True
            self.ding_reset = False
        else:
            self.ding = False
        if abs(self.clapper_angle) < self.clapper_limit - 0.1:
            self.ding_reset = True
            
        self.rlength, self.effect_force = self.ropelength()
        self.rlengths.append(self.rlength); self.effect_forces.append(self.effect_force)

        if len(self.rlengths) > 3: #Maximum height of previous backstroke. To allow for adjustment of tail end length.
            if self.effect_force > 0.0 and self.rlengths[-1] < self.rlengths[-2] and self.rlengths[-2] > self.rlengths[-3]:
                self.max_length = self.rlengths[-1]
        
        self.c_x, self.c_y = - self.com_1*np.sin(self.bell_angle),  self.com_1*np.cos(self.bell_angle)
        self.p_x, self.p_y = - self.clapper_pivot*np.sin(self.bell_angle),  self.clapper_pivot*np.cos(self.bell_angle)

        self.cl_x = self.clapper_pivot*np.sin(self.bell_angle) + self.clapper_length*np.sin(self.bell_angle + self.clapper_angle)
        self.cl_y = -self.clapper_pivot*np.cos(self.bell_angle) - self.clapper_length*np.cos(self.bell_angle + self.clapper_angle)


    def ropelength(self):
        #Outputs the length of the rope above the garter hole, relative to the minimum.
        #Also outputs the maximum force available with direction.
        hole_angle = self.bell_angle - np.pi + self.garter_hole
        
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
        