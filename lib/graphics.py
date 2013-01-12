#!/usr/bin/env python
#-*- coding: utf-8 -*-

import numpy as np
import matplotlib.pyplot as plt

def get_style_plot(num):
    if num == 1:
        return "bs-"
    elif num == 2:
        return "g>-"
    elif num == 3:
        return "r*-"
    elif num == 4:
        return "k.-"
    elif num == 5:
        return "y--"
    elif num == 6:
        return "cp-"
    elif num == 7:
        return "m1-"
        
    return "k-"
    
    