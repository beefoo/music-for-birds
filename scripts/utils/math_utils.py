# -*- coding: utf-8 -*-

import math
import numpy as np

def norm(value, a, b):
    return 1.0 * (value - a) / (b - a)

def weighted_mean(values):
    count = len(values)
    if count <= 0:
        return 0
    weights = [w**2 for w in range(count, 0, -1)]
    return np.average(values, weights=weights)
