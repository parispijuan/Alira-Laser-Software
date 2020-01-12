"""
Jake Bryon, Dec 16 2019
Class for displaying data taken from laser expirement


issues to address:
figure out how to plot up to 4 plots and add data to each individual
subplot and plot them independently

"""
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button
import os
from datetime import date
import csv
from analysis import *


class Display:
    """
    Creating class which will handle all plotting and interactions
    with manipulating data via buttons and text boxes

    data: 1xNumPlots array containing data sets of Analysis class
    NumPlots: int; Number of plots to be displayed 
    Num: int; spcifies which plot will be manipulated when methods are acted
    """

    def __init__(self, data):
        """
        initialize by creating plot and pulling out data from main data 
        """
        self.data = data
        self.NumPlots = data.size
        self.Num = 0

        #### creating subplots given number requested
        #### for 1-3 plots, just lay out in a row
        if self.NumPlots == 1:
            self.fig, self.subplots = ( 
                plt.subplots(1,1, figsize = [14.0, 7.0]) )
            ### need subplots to be in a list
            self.subplots = [self.subplots]

        elif self.NumPlots == 2:
            self.fig, self.subplots = ( 
                plt.subplots(1,2, figsize = [14.0, 7.0]) )

        elif self.NumPlots == 3:
            self.fig, self.subplots = ( 
                plt.subplots(1,3, figsize = [14.0, 7.0]) )
        #### when plotting 4, use 2x2 grid
        elif self.NumPlots == 4:
            self.fig, self.subplots_temp = ( 
                plt.subplots(2,2, figsize = [14.0, 7.0]) )
            # turn format of subplots array to look like others
            self.subplots = np.array([
                self.subplots_temp[0,0],
                self.subplots_temp[0,1],
                self.subplots_temp[1,0],
                self.subplots_temp[1,1]
                ])
        else:
            #### given error if number of data sets is too large
            print('This number of plots is not supported')
       
        ######### plot all lines
        self.lines = np.array([0,0,0,0], dtype=object)
        for i in range(0,self.NumPlots):
            self.subplot_data(i)

    def place_buttons(self):
        """
        method to layout all buttons for interacting with plot
        """
        ########## adjust all subplots to make room for buttons
        self.fig.subplots_adjust(left = 0.15, bottom = 0.2, wspace = 0.1)

        ### placing reset button
        axbutton_reset = plt.axes([0.01, 0.90, 0.08, 0.05])
        self.button_reset = Button(axbutton_reset, 'Reset')
        self.button_reset.on_clicked(self.reset)

        ### placing differentiation button
        axbutton_dif = plt.axes([0.01, 0.60, 0.08, 0.05])
        self.button_dif = Button(axbutton_dif, 'Differentiate')
        self.button_dif.on_clicked(self.differentiate)

        ### placing integration button
        axbutton_int = plt.axes([0.01, 0.50, 0.08, 0.05])
        self.button_int = Button(axbutton_int, 'Integrate')
        self.button_int.on_clicked(self.integrate)

        ### placing normalization button
        axbutton_nor = plt.axes([0.01, 0.40, 0.08, 0.05])
        self.button_nor = Button(axbutton_nor, 'Normalize')
        self.button_nor.on_clicked(self.normalize)

        ### placing down text box to choose plot for manipulation
        axtext_subnum = plt.axes([0.03, 0.80, 0.06, 0.05])
        self.text_subnum = TextBox(axtext_subnum, 'Plot:', 
            initial = '0')
        self.text_subnum.on_submit(self.Num_change)

        ### text box for trimming data
        axtext_trim = plt.axes([0.03, 0.70, 0.06, 0.05])
        self.text_trim = TextBox(axtext_trim, 'Trim:',
            initial = '0,end')
        self.text_trim.on_submit(self.trim)

        ### text box for saving data
        axtext_save = plt.axes([0.15, 0.10, 0.15, 0.05])
        self.text_save = TextBox(axtext_save, 'Save Adjusted Data (.csv):',
            initial = 'DataAdjusted')
        self.text_save.on_submit(self.saveData)
 

    def subplot_data(self, plot_num, line_style = '-'):
        """
        function to append data to specified subplot

        lines: array containing the 2D lines for each plot
        plot_num: int; specifices which subplot to plot
        line_style: sets how to plot the data, default is just a normal line
        """
        
        if plot_num == 0:
            self.lines[0] = self.subplots[0].plot(
                self.data[0].data_adjusted, line_style)
        elif plot_num == 1:
             self.lines[1] = self.subplots[1].plot(
                 self.data[1].data_adjusted, line_style)
        elif plot_num == 2:
            self.lines[2] = self.subplots[2].plot(
                 self.data[2].data_adjusted, line_style)
        elif plot_num == 3:
             self.lines[3] = self.subplots[3].plot(
                self.data[3].data_adjusted, line_style)
        else:
             print('Data not found for plot')

    ### functions used for buttons
    def reset(self, event):
        """
        function to restore adjusted data back to the raw original
        """

        self.data[self.Num].reset()

        ### clear data from figure
        self.subplots[self.Num].cla()
        ### append subplot with new data 
        self.subplot_data(plot_num = self.Num)


    def differentiate(self, event):
        """
        fucntion to differentiate specified data set
        """

        ### computer derivitive
        self.data[self.num].differentiate()

        self.subplots[self.Num].cla()
        self.subplot_data(plot_num = self.Num)


    def integrate(self, event):
        """
        fucntion to integrate specified data set
        """

        ### computer derivitive
        self.data[self.Num].integrate()

        self.subplots[self.Num].cla()
        self.subplot_data(plot_num = self.Num)


    def normalize(self, event):
        """
        fucntion to normalize specified data set
        """

        ### computer derivitive
        self.data[self.Num].normalize()

        self.subplots[self.Num].cla()
        self.subplot_data(plot_num = self.Num)


    ### functions used for text box entries
    def Num_change(self, text):
        """
        method to change Num which tells the plot to be manipulated
        """
        plot_number = text
        self.Num = int(plot_number)
        print(self.Num)


    def trim(self, text):
        """
        method to specify a range of data to work with, trim off other parts
        """
        x_span = text.split(',')
        
        ### make sure input correct length
        if len(x_span) != 2: print('please enter "start,stop"')

        ## pull out starting value
        x_start = int(x_span[0])

        ### pull out stop value
        if x_span[1] == 'end':
            x_stop = -1
        else:
            x_stop = int(x_span[1])

        ### trim the data
        self.data[self.Num].trim(x_start, x_stop)
        ### clear data from figure
        self.subplots[self.Num].cla()
        ### append subplot with new data 
        self.subplot_data(plot_num = self.Num)

    def saveData(self, text):
        """
        method to create a folder with the days date. This folder will be used
        to save specified data into
        """
        ### finding the date and making a directory with the date
        today = date.today()
        Today_Date = today.strftime("%b_%d_%Y")
        
        Date_Directory = os.path.join(Today_Date)
        ### check if the directory exists, if not create it
        if os.path.exists(Date_Directory):
            print(Date_Directory + ' : exists')
            if os.path.isdir(Date_Directory):
                print(Date_Directory + ' : is a directory')
        else:
            print('no such directory')
            print('making directory')
            os.mkdir(Date_Directory)

        SaveName = text
        save_loc = Date_Directory + '/' + SaveName + '.csv'
        np.savetxt(
            save_loc, 
            self.data[self.Num].data_adjusted, 
            delimiter = ','
            )

    ### simple plotting method
    def show(self):
        """
        function to display all plots
        """
        plt.show()
