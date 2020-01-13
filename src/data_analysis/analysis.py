"""
Jake Bryon, Dec 9 2019
writing a basic script to explore making interactive plots
using a class structure
"""
import numpy as np
import numpy.random as npr
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button
import os
from datetime import date
import csv
from scipy import integrate

### defining class for preforming analysis on data
"""
Analysis class takes in raw data as input and handles all manipulation of data
it stores data into two main pieces, data raw, which is never altered, and
data_adjusted which is manipulated with the other mthods
"""
class Analysis:

    def __init__(self, data_raw):
        self.data_raw = data_raw
        self.data_adjusted = np.copy(data_raw)

    def reset(self):
        """ resets data_adjusted back to the raw """
        self.data_adjusted = self.data_raw

    def differentiate(self):
        """ calculates derivitive of the data set """
        self.data_adjusted = np.gradient(self.data_adjusted)

    def integrate(self):
        """ calculates integral of the data set """
        self.data_adjusted = integrate.cumtrapz(self.data_adjusted)

    def trim(self, start, stop):
        """ trims the data by cutting array at start and stop """
        self.data_adjusted = self.data_adjusted[start:stop]

    def normalize(self):
        """ normalizes by dividing by largest element in array """
        self.data_adjusted = self.data_adjusted/max(self.data_adjusted)


