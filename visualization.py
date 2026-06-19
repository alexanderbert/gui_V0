import tkinter as tk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
from tkinter import ttk, messagebox
from settings import *
import paramiko
import matplotlib
import time
from dotenv import load_dotenv
import os
import sys
import subprocess
import nmap

class MainFrameV(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "Gray")
        self.columnconfigure(0, weight=6)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        self.visualization_frame = VisualizeFrame(self)
        self.visualization_frame.grid(column=0, row=0, sticky="nsew")
        self.control_frame = ControlFrame(self)
        self.control_frame.grid(column=1, row =0, sticky="nsew")


class VisualizeFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "red")
        self.grid_propagate(False)


class ControlFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = 'blue')
        self.grid_propagate(False)
        self.create_plot_button = tk.Button(self, text="Plot", command= lambda: self.create_plot())
        self.create_plot_button.grid(column=0, row=0, sticky="nsew")


    def create_plot(self):

        def convertRawFile(folder, filename):
            bashCommand = "/home/jake/Documents/stormquant-beta/cmake-build-debug/common/raytestingutils/convertRawToCleartext "
            bashCommand = bashCommand + "-d " + folder + " -f " + filename
            process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()

        folders = ["./"]

        for mainfolder in folders:
            output = []
            for folder in np.sort(glob.glob(mainfolder)):
                for index, file in enumerate(np.sort(glob.glob(folder + "/*.bin"))[:]):
                    print(folder, '/' + file.split('/')[-1])
                    convertRawFile(folder, '/' + file.split('/')[-1])

            legenedArr = []
            freq = np.fft.fftfreq(6000, d=1.0 / 25e6)
            for folder in np.sort(glob.glob(mainfolder)):
                for index, file in enumerate(np.sort(glob.glob(folder + "/*_x.csv"))):
                    metaFile = file.split('_x')[0] + "_meta.txt"
                    xfile = file
                    yfile = file.split('_x')[0] + "_y.csv"
                    with open(metaFile, 'r') as fid:
                        lines = fid.readlines()
                    data = lines[0].split(',')
                    el = float(data[0])
                    az = float(data[1])
                    az = 0.0
                    el = 0.0
                    folderName = os.getcwd().split('/')[-1]
                    for csvI, csvFile in enumerate([xfile, yfile]):
                        fig, ax = plt.subplots(3, 1)
                        df = pd.read_csv(csvFile, header=None).transpose()
                        ax[0].plot(df[0])
                        for i in range(50):
                            ax[0].plot([i * 50, i * 50], [-20000, 20000], 'k--')
                        ax[0].set_xlim([100, 800])
                        ax[0].set_ylim([-5000, 5000])
                        ax[1].plot(df[0])
                        ax[1].set_ylim(-2500, 2500)
                        # cutOutIndex = [1790, 1830]
                        # cutOutDifference = cutOutIndex[1] - cutOutIndex[0]
                        # freq2 = np.fft.fftfreq(cutOutDifference, d=1.0 / 25e6)
                        # ax3 = ax[2].twinx()
                        ax[2].plot(freq, np.fft.fft(df[0]))
                        # ax3.plot(freq2, np.fft.fft(df[0][cutOutIndex[0]:cutOutIndex[1]]), 'r--')
                        # legenedArr.append(file)
                        # ax[0].legend(legenedArr)
                        fig.suptitle(folderName + csvFile + " az: " + str(az) + " el: " + str(el))
                        fig.set_size_inches([15, 15])
                        if csvI == 0:
                            extension = 'x'
                        else:
                            extension = 'y'
                        outputFilename = folder + f'%03d' % index + extension + '.png'
                        print(outputFilename)
                        fig.savefig(outputFilename)
                        plt.close(fig)
                        os.system('rm ' + csvFile)
        os.system('rm *.csv')



