# -*- coding: utf-8 -*-
"""
Created on Mon Sep  2 18:23:39 2024

@author: eleph
"""

import numpy as np
import random
import matplotlib.pyplot as plt

from run_bell import run
from bell_physics import init_bell, init_physics

#File for creating and training the neural network, if that is at all possible...
#Requires the definition of a cost function, creation of arrays and the algorithm for gradient descent
#This is the hard bit...

#### ML PARAMETERS HERE
 
nlayers = 1     #number of hidden layers
nnodes = [10]     #nuber of nodes in the first layer. As a list in case more are added
ninputs = 2    #initially just the angle and velocity of the bell. Will add more if necessary

nweights = [ninputs*nnodes[0]]
nbiases = [ninputs*nnodes[0]]
for layer in range(nlayers-1):
    nweights.append(nnodes[layer]*nnodes[layer+1])
    nbiases.append(nnodes[layer]*nnodes[layer+1])
nweights.append(nnodes[-1])
nbiases.append(nnodes[-1])
    
print('Total degrees of freedom in network:', sum(nweights) + sum(nbiases))

def sigmoid(x):
    #Basic sigmoid function
    return 1.0/(1.0 + np.exp(-x))
    
def cost_fn(phy, bell, angles, velocities):
    #Calculates the cost function for th an individual run.
    ncounts = int(5.0*phy.FPS)   #range to consider
    cfs = []
    for i in range(0, len(angles) - ncounts):
        cfs.append((np.pi + bell.stay_angle - np.max(angles[i:i+ncounts]))**2)
    return np.sum(cfs)/len(cfs)

def init_network(max_weight = 1.0):
    #Max weights as 1/(root(nodes)) was recommended at some point. That seems reasonable.
    #Initial biases at zero is probably fine
    weights = []
    biases = []
    for layer in range(nlayers + 1):
        weights.append([])
        biases.append([])
        for i in range(nweights[layer]):
            weights[-1].append(0.0)
            biases[-1].append(0.0)
           
    for group in range(len(nweights)):
        max_weight = 1/np.sqrt(nweights[group])
        for i in range(nweights[group]):
            weights[group][i] = 2*max_weight*(random.random() - 0.5)
            biases[group][i] = 0.0
        
    print('Network initialised with random values')
    return weights, biases

def find_force(phy, bell, weights, biases):
    #Given the current state of the network, find the force to pull with. The essence of the forward problem.
    data = [bell.angle, bell.velocity]
    nodes = np.zeros(nnodes[0])
    for i in range(nnodes[0]):
        nodesum = 0
        for j in range(ninputs):
            nodesum += weights[0][i + j*nnodes[0]]*data[j] + biases[0][i + j*nnodes[0]]
        nodes[i] = sigmoid(nodesum)
        
    for i in range(nnodes[0]):
        outsum = 0
        outsum += weights[1][i]*nodes[i] + biases[1][i]
        
    out = sigmoid(outsum)
    
    #Out is the probability of pulling    
    if random.random() < out:
        return 1.0
    else:
        return 0.0
    
    
def gradient(weights, biases, fn):
    #Calculates the gradient of the cost function at the current state of the weights and biases/
    #Acheives this by performing several runs
    print('Calculating gradient...')
    for run_count in range(1):  #only one run per gradient to start with? Obviously can'to do that
        phy = init_physics()
        bell = init_bell(phy, 0.0)
        angles, velocities = run(phy, bell, find_force, weights, biases)
    #U this data calculate a gradient function.
    cf = cost_fn(phy, bell, angles, velocities)
    plt.plot(angles)
    plt.show()
    print('Initial cost function', cf)
    delta = 0.01
    eta = 0.0005
    for i in range(len(weights)):
        for j in range(len(weights[i])):
            weights[i][j] = weights[i][j] + delta
            bell = init_bell(phy, 0.0)
            angles, velocities = run(phy, bell, find_force, weights, biases)
            cf1 = cost_fn(phy, bell, angles, velocities)
            
            weights[i][j] = weights[i][j] - 2*delta
            bell = init_bell(phy, 0.0)
            angles, velocities = run(phy, bell, find_force, weights, biases)
            cf2 = cost_fn(phy, bell, angles, velocities)

            weights[i][j] = weights[i][j] + delta   #return to its original value
            
            weights[i][j] = weights[i][j] - eta*(cf1 - cf2)/(2*delta)
            
    for i in range(len(biases)):
        for j in range(len(biases[i])):
            biases[i][j] = biases[i][j] + delta
            bell = init_bell(phy, 0.0)
            angles, velocities = run(phy, bell, find_force, weights, biases)
            cf1 = cost_fn(phy, bell, angles, velocities)
            
            biases[i][j] = biases[i][j] - 2*delta
            bell = init_bell(phy, 0.0)
            angles, velocities = run(phy, bell, find_force, weights, biases)
            cf2 = cost_fn(phy, bell, angles, velocities)

            biases[i][j] = biases[i][j] + delta   #return to its original value
            biases[i][j] = biases[i][j] - eta*(cf1 - cf2)/(2*delta)
     

    plt.plot(weights[0])
    plt.plot(biases[0])
    plt.show()
     
weights, biases = init_network()

while True:
    gradient(weights, biases, cost_fn)

































