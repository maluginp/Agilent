#!/usr/bin/env pytho
#-*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt

def get_style_plot(num,points=True):
    if num == 1:
        return "bs-" if (points) else "b-" 
    elif num == 2:
        return "g>-" if (points) else "g-" 
    elif num == 3:
        return "r*-" if (points) else "r-" 
    elif num == 4:
        return "k.-" if (points) else "k-"
    elif num == 5:
        return "y--" if (points) else "y-"
    elif num == 6:
        return "cp-" if (points) else "c-"
    elif num == 7:
        return "m1-" if (points) else "m-"
        
    return "k-"
    
    