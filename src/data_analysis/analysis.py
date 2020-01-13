"""
analysis contains the Analysis class which handles 
all storage and manipulation of input data.
It stores data in two attributes: data_raw and data_adjusted, with 
data_raw being the raw input that is never changed and data_adjusted
starting at the raw input and being able to be changed with class methods.
"""
import numpy as np
import numpy.random as npr
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button
import os
from datetime import date
import csv
from scipy import integrate

class Analysis:
    """
    The Analysis class handles all storage and manipulation of input data.
    It stores data in two attributes: data_raw and data_adjusted, with 
    data_raw being the raw input that is never changed and data_adjusted
    starting at the raw input and being able to be changed with class methods.

    Class Attributes:

    data_raw: N length numpy array containing input data

    data_adjusted: N length array containing data that has undergone all
    methods that have been appiled

    Example of using code to take derivitive:
    data = np.linspace(0,10,10)
    data_analysis = Analysis(data)
    data_analysis.differentiate()

    This creates a class that stores the data, a linear spaced array, 
    and takes the derivitive. In this example, data_adjusted would
    would be the derivitive of the data array and data_raw would
    still be the same untouched array.
    """
    def __init__(self, data):
        """
        data: Nx1 numpy array

        To initialize the class object, need to give an input array
        which will then be stored data to be manipulated for analysis
        """

        ## Nx1 numpy array composed of input data, never altered
        self.data_raw = data
        ## Nx1 numpy array composed of data, changed by each method run
        self.data_adjusted = np.copy(data)

    def reset(self):
        """ resets data_adjusted back to the raw """
        self.data_adjusted = self.data_raw

    def differentiate(self):
        """ calculates derivitive of data_adjusted """
        self.data_adjusted = np.gradient(self.data_adjusted)

    def integrate(self):
        """ calculates integral of data_adjusted """
        self.data_adjusted = integrate.cumtrapz(self.data_adjusted)

    def trim(self, start, stop):
        """ 
        start: int
        stop: int

        trims data_adjusted by cutting array at start and stop elements
        of the data_adjsuted array
        """
        self.data_adjusted = self.data_adjusted[start:stop]

    def normalize(self):
        """ 
        normalizes data_adjusted by dividing by largest element in array 
        """
        self.data_adjusted = self.data_adjusted/max(self.data_adjusted)

    def ratio(self, ratio_data):
        """
        ratio_data: Nx1 numpy array, must be equal length of data_adjusted

        takes the ratio of the current data_adjusted with a new array
        """
        self.data_adjusted = np.divide(
            self.data_adjusted,
            ratio_data
            )


