##
# analysis contains the Analysis class which handles 
# all storage and manipulation of input data.
# It stores data in two attributes: data_raw and data_adjusted, with 
# data_raw being the raw input that is never changed and data_adjusted
# starting at the raw input and being able to be changed with class methods.

import numpy as np
import numpy.random as npr
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button
import os
from datetime import date
import csv
from scipy import integrate

##
# The Analysis class handles all storage and manipulation of input data.
# It stores data in two attributes: data_raw and data_adjusted, with 
# data_raw being the raw input that is never changed and data_adjusted
# starting at the raw input and being able to be changed with class methods.
# 
# Example of using code to take derivitive:
# data = np.linspace(0,10,10)
# data_analysis = Analysis(data)
# data_analysis.differentiate()
# 
# This creates a class that stores the data, a linear spaced array, 
# and takes the derivitive. In this example, data_adjusted would
# would be the derivitive of the data array and data_raw would
# still be the same untouched array.
#

class Analysis:

    ## initialize object by creating two seperate copies of the input
    # array of data
    #
    # @param self the object pointer
    # @param data Nx1 Numpy array containing data to be analyzed
    #
    def __init__(self, data):
        ## Nx1 numpy array composed of input data, never altered
        self.data_raw = data
        ## Nx1 numpy array composed of data, changed by each method run
        self.data_adjusted = np.copy(data)

    ## method to reset data_adjusted, set it equal to data_raw the 
    # original untouched data
    #
    # @param self the object pointer
    #
    def reset(self):
        self.data_adjusted = self.data_raw

    ## method to calculate the derivitve of data_adjusted
    #
    # @param self the object pointer
    #
    def differentiate(self):
        self.data_adjusted = np.gradient(self.data_adjusted, \
            self.data_raw[1]-self.data_raw[0])
        
        self.data_adjusted = np.around(self.data_adjusted,12)

    ## method to integrate data_adjusted
    #
    # @param self the object pointer 
    #
    def integrate(self):
        self.data_adjusted = integrate.cumtrapz(self.data_adjusted)

    ## method to cut data at specifed points, picks out a range from 
    # data_adjusted and sets it to this specific range of the array
    #
    # @param self the object pointer
    # @param start int; the starting index of the array which will mark
    #   the new first element of the new data adjusted
    # @param stop int; the final index of the array
    #
    def trim(self, start, stop):
        self.data_adjusted = self.data_adjusted[start:stop]

    ## method to normalize data by the largest element in data_adjusted
    #
    # @param self the object pointer
    #
    def normalize(self):
        self.data_adjusted = self.data_adjusted/max(self.data_adjusted)

    ## method to calculated the ratio of data_adjusted with another input
    # array that must be of equal length
    #
    # @param self the object pointer
    # param ratio_data the array which data_Adjusted will the element wise
    #   divided by
    #
    def ratio(self, ratio_data):
        if np.prod(self.data_adjusted.shape) == np.prod(ratio_data.shape):
            self.data_adjusted = np.divide( 
                self.data_adjusted,
                ratio_data
                )

