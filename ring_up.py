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
nnodes = 1     #nuber of nodes in the first layer. As a list in case more are added
ninputs = 2    #initially just the angle and velocity of the bell. Will add more if necessary

nweights = [ninputs*nnodes]
nbiases = [ninputs*nnodes]
for layer in range(nlayers-1):
    nweights.append(nnodes[layer]*nnodes)
    nbiases.append(nnodes[layer]*nnodes)
nweights.append(nnodes)
nbiases.append(nnodes)
    
dof = sum(nweights)
print('Total degrees of freedom in network:', sum(nweights) + sum(nbiases))

def sigmoid(x):
    #Basic sigmoid function
    return 1.0/(1.0 + np.exp(-x))
    
def cost_fn(phy, bell, angles, velocities):
    #Calculates the cost function for th an individual run.
    ncounts = int(5.0*phy.FPS)   #range to consider
    ccount = 0
    cf = 0
    for i in range(0, len(angles) - ncounts):
        cf += (np.pi - abs(angles[i]))**2
        ccount += 1
    return cf/ccount

def init_network(max_weight = 2.0):
    #Max weights as 1/(root(nodes)) was recommended at some point. That seems reasonable.
    #Initial biases at zero is probably fine
    weights = []
    biases = []
    weights = np.zeros(dof)
    biases = np.zeros(dof)
    
    # Map to the hidden layer
    for n in range(ninputs):
        for i in range(nnodes):
            #weights[i + n*nnodes] = 2*max_weight*(random.random() - 0.5)
            #biases[i + n*nnodes] = 2*max_weight*(random.random() - 0.5)
            weights[i + n*nnodes] = 0.0
            biases[i + n*nnodes] = 0.0
    weights[nnodes] = 1.0
    biases[nnodes] = 0.0

    # Map to the end
    for i in range(nnodes):
        #weights[i + ninputs*nnodes] = 2*max_weight*(random.random() - 0.5)
        #biases[i + ninputs*nnodes] = 2*max_weight*(random.random() - 0.5)
        weights[i + ninputs*nnodes] = 0.0
        biases[i + ninputs*nnodes] = 0.0

    weights[ninputs*nnodes] = 1.0
    biases[ninputs*nnodes] = 0.5 

    print('Network initialised')
    return weights, biases

def find_force(phy, bell, weights, biases):
    #Given the current state of the network, find the force to pull with. The essence of the forward problem.
    data = [bell.angle, bell.velocity]
    nodes = np.zeros(nnodes)
    #Find neuron values
    for i in range(nnodes):
        nodesum = 0
        for n in range(ninputs):
            nodesum += data[n]*weights[i + n*nnodes] + biases[i + n*nnodes]
        nodes[i] = sigmoid(nodesum)
      
    for i in range(nnodes):
        outsum = 0
        outsum += weights[i + ninputs*nnodes]*nodes[i] + biases[i + ninputs*nnodes]
        
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
    for run_count in range(1):  #only one run per gradient to start with? Obviously can't do that
        phy = init_physics()
        bell = init_bell(phy, 0.0)
        angles, velocities = run(phy, bell, find_force, weights, biases)
    #U this data calculate a gradient function.
    cf = cost_fn(phy, bell, angles, velocities)
    #plt.plot(angles)
    #plt.show()
    print('Initial cost function', cf)
    delta = 0.01
    eta = 0.5
    
    grad_w = np.zeros(dof)
    grad_b = np.zeros(dof)
    
    for k in range(len(weights)):
        weights[k] = weights[k] + delta
        bell = init_bell(phy, 0.0)
        angles, velocities = run(phy, bell, find_force, weights, biases)
        cf1 = cost_fn(phy, bell, angles, velocities)
            
        weights[k] = weights[k] - 2*delta
        bell = init_bell(phy, 0.0)
        angles, velocities = run(phy, bell, find_force, weights, biases)
        cf2 = cost_fn(phy, bell, angles, velocities)

        weights[k] = weights[k] + delta   #return to its original value
        
        grad_w[k] = (cf1 - cf2)
            
    for k in range(len(biases)):
        biases[k] = biases[k] + delta
        bell = init_bell(phy, 0.0)
        angles, velocities = run(phy, bell, find_force, weights, biases)
        cf1 = cost_fn(phy, bell, angles, velocities)
            
        biases[k] = biases[k] - 2*delta
        bell = init_bell(phy, 0.0)
        angles, velocities = run(phy, bell, find_force, weights, biases)
        cf2 = cost_fn(phy, bell, angles, velocities)

        biases[k] = biases[k] + delta   #return to its original value
        
        grad_b[k] = (cf1 - cf2)

    weights = weights - eta*grad_w
    #biases = biases - eta*grad_b
    
    plt.ylim(-2,2)
    plt.plot(weights)
    plt.plot(biases)
    plt.show()
     
weights, biases = init_network()

#gradient(weights, biases, cost_fn)

while True:
    gradient(weights, biases, cost_fn)

































