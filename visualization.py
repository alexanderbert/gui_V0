import tkinter as tk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import glob
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from matplotlib.backends._backend_tk import NavigationToolbar2Tk

from settings import *
import paramiko
import matplotlib
import time
from dotenv import load_dotenv
import os
import sys
import subprocess
import nmap
from pathlib import Path
from PIL import Image, ImageTk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class MainFrameV(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "Gray")
        self.columnconfigure(0, weight=6)
        #self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.grid_propagate(False)

        self.visualization_frame = VisualizeFrame(self)
        self.visualization_frame.grid(column=0, row=0, sticky="nsew")
        # self.control_frame = ControlFrame(self)
        # self.control_frame.grid(column=1, row =0, sticky="nsew")


class VisualizeFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, background = "white")
        self.columnconfigure(0, weight=10)
        self.columnconfigure(1, weight=10)
        self.columnconfigure(2, weight=1)
        #try no rows
        self.rowconfigure(0, weight=1)
        # self.rowconfigure(1, weight=1)

        self.grid_propagate(False)
        # self.image_label = tk.Label(self, text = "Image")
        # self.image_label.grid(column=0, row=0, sticky="nsew")


        self.button_frame = tk.Frame(self)
        self.button_frame.grid(column=2, row=0, sticky="nsew")
        self.button_frame.configure(bg="white")
        # self.button_frame.rowconfigure(0, weight=1)
        # self.button_frame.rowconfigure(1, weight=1)

        self.create_plot_button = tk.Button(self.button_frame, text="Plot", command= lambda: self.create_plot())
        self.create_plot_button.grid(column=2, sticky="new")
        self.create_images_button = tk.Button(self.button_frame, text="Create Images", command= lambda: self.create_images())
        self.create_images_button.grid(column=2, sticky="new")
    #
    # def open_image(self):
    #     file_path = filedialog.askopenfilename(title="Open Image files", filetypes = (("PNG File","*.png"),))
    #     if file_path:
    #         self.display_image(file_path)
    #
    # def display_image(self, file_path):
    #     image = Image.open(file_path)
    #     image_resized = image.resize((250,600))
    #     photo = ImageTk.PhotoImage(image_resized)
    #     self.image_label.config(image = photo)
    #     self.image_label.photo = photo

    def create_images(self):
        def convertRawFile(folder, filename):
            # todo find correct location on target computer
            bashCommand = "/home/sq/sq/stormquant-beta/build_old/common/raytestingutils/convertRawToCleartext "
            bashCommand = bashCommand + "-d " + folder + " -f " + filename
            process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
            output, error = process.communicate()

        folders = ["./scripts"]

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

                        # HIS NAME
                        # fig.suptitle(folderName + csvFile + " az: " + str(az) + " el: " + str(el))
                        # MY NAME FOR FILE?
                        now = datetime.now()
                        formatted_time = now.strftime("%m-%d %H:%M:%S")
                        fig.suptitle(formatted_time + " az: " + str(az) + " el: " + str(el))
                        fig.set_size_inches([15, 15])
                        if csvI == 0:
                            extension = 'x'
                        else:
                            extension = 'y'

                        ## CUT FOR SAVING FILE
                        outputFilename = formatted_time + f'%03d' % index + extension + '.png'
                        # print(outputFilename)
                        fig.savefig(outputFilename)


                        plt.close(fig)
                        os.system('rm ' + csvFile)
        print("HELLO WORLD")
        os.system('rm *.csv')

    def create_plot(self):
       # script_path = Path("./scripts/testingviz.py")
       # script_dir = script_path.parent
       # subprocess.run([sys.executable, script_path.name],
       #                cwd=script_dir,
       #                capture_output=True,
       #                text=True
       #                )

       def convertRawFile(folder, filename):
           #todo find correct location on target computer
           bashCommand = "/home/sq/sq/stormquant-beta/build_old/common/raytestingutils/convertRawToCleartext "
           # bashCommand = "/home/sq/Desktop/pythonAppImprovements/testingFiles/binFiles "
           bashCommand = bashCommand + "-d " + folder + " -f " + filename
           process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
           output, error = process.communicate()

       folders = ["./scripts"]

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

                       #HIS NAME
                       #fig.suptitle(folderName + csvFile + " az: " + str(az) + " el: " + str(el))
                       #MY NAME FOR FILE?
                       now = datetime.now()
                       formatted_time = now.strftime("%m-%d %H:%M:%S")
                       fig.suptitle(formatted_time + " az: " + str(az) + " el: " + str(el))
                       fig.set_size_inches([15, 15])
                       if csvI == 0:
                           extension = 'x'
                       else:
                           extension = 'y'


                       ## CUT FOR SAVING FILE
                       # outputFilename = folder + f'%03d' % index + extension + '.png'
                       # print(outputFilename)
                       # fig.savefig(outputFilename)

                       ##MY CODE FOR TKINTER
                       fig.set_size_inches(3.5,6)
                       plot_frame = tk.Frame(self)
                       plot_frame.grid(row=0, column=csvI, sticky="nsew")

                       canvas = FigureCanvasTkAgg(fig, plot_frame)
                       canvas.draw()
                       canvas.get_tk_widget().pack(side="top", fill="both", expand=True)

                       toolbar = NavigationToolbar2Tk(canvas, plot_frame)
                       toolbar.update()
                       toolbar.pack(side="left")

                       #PREVENTS RESIZING
                       plot_frame.pack_propagate(False)


                       # canvas = FigureCanvasTkAgg(fig, master=self)
                       # canvas.draw()
                       # canvas.get_tk_widget().grid(row=0, column=csvI, sticky="nsew")
                       #
                       # toolbar_frame = tk.Frame(self)
                       # toolbar_frame.grid(row =1, column=csvI)
                       # toolbar = NavigationToolbar2Tk(canvas, toolbar_frame)
                       # toolbar.update()
                       # #toolbar.grid(row=1, column=csvI)
                       # toolbar_frame.grid_propagate(False)

                       plt.close(fig)
                       os.system('rm ' + csvFile)
       print("HELLO WORLD")
       os.system('rm *.csv')



#
# class ControlFrame(tk.Frame):
#     def __init__(self, parent):
#         super().__init__(parent, background = 'blue')
#         self.grid_propagate(False)
#         self.create_plot_button = tk.Button(self, text="Plot", command= lambda: self.create_plot())
#         self.create_plot_button.grid(column=0, row=0, sticky="nsew")
#
#         self.images_button = tk.Button(self, text="IMAGES", command=lambda: parent.visualization_frame.open_image())
#         self.images_button.grid(column=0, row=1, sticky="nsew")

    # def create_plot(self):
    #    # script_path = Path("./scripts/testingviz.py")
    #    # script_dir = script_path.parent
    #    # subprocess.run([sys.executable, script_path.name],
    #    #                cwd=script_dir,
    #    #                capture_output=True,
    #    #                text=True
    #    #                )
    #
    #    def convertRawFile(folder, filename):
    #        # bashCommand = "/home/jake/Documents/stormquant-beta/cmake-build-debug/common/raytestingutils/convertRawToCleartext "
    #        bashCommand = "/home/sq/sq/stormquant-beta/build_old/common/raytestingutils/convertRawToCleartext "
    #        # bashCommand = "/home/sq/Desktop/pythonAppImprovements/testingFiles/binFiles "
    #        bashCommand = bashCommand + "-d " + folder + " -f " + filename
    #        process = subprocess.Popen(bashCommand.split(), stdout=subprocess.PIPE)
    #        output, error = process.communicate()
    #
    #    folders = ["./scripts"]
    #
    #    for mainfolder in folders:
    #        output = []
    #        for folder in np.sort(glob.glob(mainfolder)):
    #            for index, file in enumerate(np.sort(glob.glob(folder + "/*.bin"))[:]):
    #                print(folder, '/' + file.split('/')[-1])
    #                convertRawFile(folder, '/' + file.split('/')[-1])
    #
    #        legenedArr = []
    #        freq = np.fft.fftfreq(6000, d=1.0 / 25e6)
    #        for folder in np.sort(glob.glob(mainfolder)):
    #            for index, file in enumerate(np.sort(glob.glob(folder + "/*_x.csv"))):
    #                metaFile = file.split('_x')[0] + "_meta.txt"
    #                xfile = file
    #                yfile = file.split('_x')[0] + "_y.csv"
    #                with open(metaFile, 'r') as fid:
    #                    lines = fid.readlines()
    #                data = lines[0].split(',')
    #                el = float(data[0])
    #                az = float(data[1])
    #                az = 0.0
    #                el = 0.0
    #                folderName = os.getcwd().split('/')[-1]
    #                for csvI, csvFile in enumerate([xfile, yfile]):
    #                    fig, ax = plt.subplots(3, 1)
    #                    df = pd.read_csv(csvFile, header=None).transpose()
    #                    ax[0].plot(df[0])
    #                    for i in range(50):
    #                        ax[0].plot([i * 50, i * 50], [-20000, 20000], 'k--')
    #                    ax[0].set_xlim([100, 800])
    #                    ax[0].set_ylim([-5000, 5000])
    #                    ax[1].plot(df[0])
    #                    ax[1].set_ylim(-2500, 2500)
    #                    # cutOutIndex = [1790, 1830]
    #                    # cutOutDifference = cutOutIndex[1] - cutOutIndex[0]
    #                    # freq2 = np.fft.fftfreq(cutOutDifference, d=1.0 / 25e6)
    #                    # ax3 = ax[2].twinx()
    #                    ax[2].plot(freq, np.fft.fft(df[0]))
    #                    # ax3.plot(freq2, np.fft.fft(df[0][cutOutIndex[0]:cutOutIndex[1]]), 'r--')
    #                    # legenedArr.append(file)
    #                    # ax[0].legend(legenedArr)
    #                    fig.suptitle(folderName + csvFile + " az: " + str(az) + " el: " + str(el))
    #                    fig.set_size_inches([15, 15])
    #                    if csvI == 0:
    #                        extension = 'x'
    #                    else:
    #                        extension = 'y'
    #                    outputFilename = folder + f'%03d' % index + extension + '.png'
    #                    print(outputFilename)
    #                    fig.savefig(outputFilename)
    #
    #                    canvas = FigureCanvasTkAgg(fig, master=self.parent.visualization_frame)
    #                    canvas.draw()
    #                    canvas.get_tk_widget().grid(row=0, column=index, sticky="nsew")
    #
    #                    #plt.close(fig)
    #                    os.system('rm ' + csvFile)
    #    print("HELLO WORLD")
    #    os.system('rm *.csv')





