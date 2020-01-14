## 
# display contains the Display class which takes in an Analysis class as input
# and handles all plotting and interaction with plots. Also contains methods
# to save data to csv file

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button
import os
from datetime import date
import csv
from analysis import *


## Display class handles all plotting and interactions
# with manipulating data via buttons and text boxes
class Display:

    ## initialize object by pulling out individual analysis structures from
    # data array, create main figure and all subplots with data
    # @param self the object pointer
    # @param data numpy array containing Analysis classes of data
    #
    def __init__(self, data):
        #### data: numpy array of Analysis class objects containing data
        self.data = data

        ## NumPlots: int, number of data sets and plots shown
        self._NumPlots = data.size

        ## Num: int, activate plot/data set that is being manipulated
        # plots are zero indexed and move from left to right in order
        # of numbering. Ex: if wanting to manipulate the first data
        # set entered or the left most plot, use Num = 0
        self.Num = 0

        # creating subplots given number requested
        # for 1-3 plots, just lay out in a row
        if self._NumPlots == 1:
            self.fig, self.subplots = ( 
                plt.subplots(1,1, figsize = [14.0, 7.0]) )
            ## subplots: list containing all subplots of the figure
            self.subplots = [self.subplots]

        elif self._NumPlots == 2:
            self.fig, self.subplots = ( 
                plt.subplots(1,2, figsize = [14.0, 7.0]) )

        elif self._NumPlots == 3:
            self.fig, self.subplots = ( 
                plt.subplots(1,3, figsize = [14.0, 7.0]) )
        # when plotting 4, use 2x2 grid
        elif self._NumPlots == 4:
            self.fig, self._subplots_temp = ( 
                plt.subplots(2,2, figsize = [14.0, 7.0]) )
            # turn format of subplots array to look like others
            self.subplots = np.array([
                self._subplots_temp[0,0],
                self._subplots_temp[0,1],
                self._subplots_temp[1,0],
                self._subplots_temp[1,1]
                ])
        else:
            # given error if number of data sets is too large
            print('This number of plots is not supported')
       
        ## lines: array that holds the lines which are displayed on the 
        # subplots. 
        self.lines = np.array([0,0,0,0], dtype=object)
        for i in range(0,self._NumPlots):
            self.subplot_data(i)


    ## method to layout all buttons and text boxes for interacting with plots
    #
    def place_buttons(self):

        # adjust all subplots to make room for buttons
        self.fig.subplots_adjust(left = 0.18, bottom = 0.2, wspace = 0.2)
        self.fig.suptitle('Alira Laser Data Plotting')

        # placing reset button
        axbutton_reset = plt.axes([0.03, 0.90, 0.08, 0.05])
        self._button_reset = Button(axbutton_reset, 'Reset')
        self._button_reset.on_clicked(self.reset)

        # placing differentiation button
        axbutton_dif = plt.axes([0.03, 0.60, 0.08, 0.05])
        self._button_dif = Button(axbutton_dif, 'Differentiate')
        self._button_dif.on_clicked(self.differentiate)

        # placing integration button
        axbutton_int = plt.axes([0.03, 0.50, 0.08, 0.05])
        self._button_int = Button(axbutton_int, 'Integrate')
        self._button_int.on_clicked(self.integrate)

        # placing normalization button
        axbutton_nor = plt.axes([0.03, 0.40, 0.08, 0.05])
        self._button_nor = Button(axbutton_nor, 'Normalize')
        self._button_nor.on_clicked(self.normalize)

        # placing down text box to choose plot for manipulation
        axtext_subnum = plt.axes([0.05, 0.80, 0.06, 0.05])
        self._text_subnum = TextBox(axtext_subnum, 'Plot:', 
            initial = '0')
        self._text_subnum.on_submit(self.Num_change)

        # text box for trimming data
        axtext_trim = plt.axes([0.05, 0.70, 0.06, 0.05])
        self._text_trim = TextBox(axtext_trim, 'Trim:',
            initial = '0,end')
        self._text_trim.on_submit(self.trim)

        # text box for dividing and finding ratio of data
        axtext_rato = plt.axes([0.05, 0.30, 0.06, 0.05])
        self._text_rato = TextBox(axtext_rato, 'Ratio:',
            initial = '1')
        self._text_rato.on_submit(self.ratio)

        # text box for saving data
        axtext_save = plt.axes([0.15, 0.08, 0.15, 0.05])
        self._text_save = TextBox(axtext_save, 'Save Adjusted Data (.csv):',
            initial = 'DataAdjusted')
        self._text_save.on_submit(self.saveData)
 

    ## method to append data to specified subplot
    # This method is used when methods that change the specifed data set
    # are called in order to replot and update that subplot
    # 
    # @param self the object pointer
    # @param plot_num int; specifices which subplot to plot
    # @param line_style sets line style, default is just a normal line
    #
    def subplot_data(self, plot_num, line_style = '-'):
       
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


    ## method to restore adjusted data back to the raw original
    # Calls analysis.reset() on specified data set
    #
    # @param self the object pointer
    # @param event click action on button, activates method
    #
    def reset(self, event):

        self.data[self.Num].reset()

        ### clear data from figure
        self.subplots[self.Num].cla()
        ### append subplot with new data 
        self.subplot_data(plot_num = self.Num)


    ## method to differentiate specified data set
    # Calls Analysis.differentiate() on specified data set
    #
    # @param self the object pointer
    # @param event click action on button, activates method
    #
    def differentiate(self, event):
        
        self.data[self.Num].differentiate()

        self.subplots[self.Num].cla()
        self.subplot_data(plot_num = self.Num)


    ## method to integrate specified data set
    # calls Analysis.integrate() on specifed data set
    #
    # @param self the object pointer
    # @param event click action on button, activates method
    #
    def integrate(self, event):
        self.data[self.Num].integrate()

        self.subplots[self.Num].cla()
        self.subplot_data(plot_num = self.Num)

    ## method to normalize specified data set
    # calls Analysis.normalize() on specifed data set
    #
    # @param self the object pointer
    # @param event click action on button, activates method
    #
    def normalize(self, event):
        self.data[self.Num].normalize()

        self.subplots[self.Num].cla()
        self.subplot_data(plot_num = self.Num)


    ## method to change which data set is being altered, ie change Num
    #
    # @param self the object pointer
    # @param text text input from textbox, must be int;
    #   specifies which plot will be affected by buttons and methods called,
    #   changes the Num variable
    #
    def Num_change(self, text):
        plot_number = text
        self.Num = int(plot_number)
        print(self.Num)

    ## method to specify a range within the data to cut out, so 
    # anything outside of the range will be taken out of the data_adjusted
    # Calls Analysis.trim()
    #
    # @param self the object pointer
    # @param text text input from textbox, must be of form 'int1,int2'
    #   where int1 is the first integer that marks the start of the trim
    #   int2 marks end, when trim happens only elements found within 
    #   range of int1 and int2 in the array elements will be left
    #
    def trim(self, text):
        x_span = text.split(',')
        
        # make sure input correct length
        if len(x_span) != 2: print('please enter "start,stop"')

        # pull out starting value
        x_start = int(x_span[0])

        # pull out stop value
        if x_span[1] == 'end':
            x_stop = -1
        else:
            x_stop = int(x_span[1])

        # trim the data
        self.data[self.Num].trim(x_start, x_stop)
        # clear data from figure
        self.subplots[self.Num].cla()
        # append subplot with new data 
        self.subplot_data(plot_num = self.Num)


    ## method to take the ratio of current specified data set with another
    # data set. 
    # Calls method Analysis.ratio()
    #
    # @param self the object pointer
    # @param text text entered from text box, must be integer; 
    #   specified the plot the plot that will be element wise divided by the
    #   current plot, designated by Num. 
    #   ie: if I am currently working on data in plot 0, if I want to find
    #   ratio of plot 0 over plot 2, I would enter '2'
    #
    def ratio(self, text):
        ratio_number = int(text)

        self.data[self.Num].ratio(self.data[ratio_number].data_adjusted)

        self.subplots[self.Num].cla()
        self.subplot_data(plot_num = self.Num)


    ## method to save the specifed data set in a csv format
    # creates a folder with the name of the current date in format:
    #   Month_Day_Year
    #
    # @param self the object pointer
    # @param text text entered from text box, the text will be the name 
    #   that the csv will be saved as. ie: if I enter 'filename' it will
    #   save the specified data set to 'DATE/filename.csv'
    #
    def saveData(self, text):
        # finding the date and making a directory with the date
        today = date.today()
        Today_Date = today.strftime("%b_%d_%Y")
        
        Date_Directory = os.path.join(Today_Date)
        # check if the directory exists, if not create it
        if os.path.exists(Date_Directory):
            if os.path.isdir(Date_Directory):
                print(Date_Directory + ' : is a directory')
        else:
            os.mkdir(Date_Directory)

        SaveName = text
        save_loc = Date_Directory + '/' + SaveName + '.csv'
        np.savetxt(
            save_loc, 
            self.data[self.Num].data_adjusted, 
            delimiter = ','
            )

    ## method to show plots
    #
    # @param self the object pointer
    #
    def show(self):
        plt.show()

