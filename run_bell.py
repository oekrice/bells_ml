# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 18:06:27 2024

@author: eleph
"""

#Runs the game automatically, rather than running the game as in main.py
#For use with the machine learning things, which will be kept elsewhere
#Logs and (optionally) plots the progress of the bell, unlike the game version


import numpy as np
import matplotlib.pyplot as plt
import random

from bell_physics import init_bell, init_physics
    
phy = init_physics()
bell = init_bell(phy, 0.0)


def run(phy, bell, force_fn, weights, biases):
    angles = []; velocities = []
    phy.count = 0
    max_force = 6.0   #maximum force
    
    maxcount = int(60.0*phy.FPS)
    
    while True: # the main game loop
        
        bell.timestep(phy)
        phy.count = phy.count + 1
        
        if phy.count > maxcount:
            break
        
        angles.append(bell.angle)
        velocities.append(bell.velocity)
                    
        bell.force = force_fn(phy, bell, weights, biases)*max_force*bell.effect_force

    return angles, velocities

