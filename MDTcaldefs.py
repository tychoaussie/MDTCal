#!/usr/bin/env python

__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20160428"
__license__ = "MIT"

"""
Sigcal core functions for: Freeperiod, Dampingratio, Mass Displacement tracking processing
Core functions for Waveform display.

"""
# Now, the most important part -- The legalese:
# COPYRIGHT  BOARD OF TRUSTEES OF MICHIGAN STATE UNIVERSITY
# ALL RIGHTS RESERVED

# PERMISSION IS GRANTED TO USE, COPY, COMBINE AND/OR MERGE, CREATE DERIVATIVE
# WORKS AND REDISTRIBUTE THIS SOFTWARE AND SUCH DERIVATIVE WORKS FOR ANY PURPOSE,
# SO LONG AS THE NAME OF MICHIGAN STATE UNIVERSITY IS NOT USED IN ANY ADVERTISING
# OR PUBLICITY PERTAINING TO THE USE OR DISTRIBUTION OF THIS SOFTWARE WITHOUT 
# SPECIFIC, WRITTEN PRIOR AUTHORIZATION.  IF THE ABOVE COPYRIGHT NOTICE OR ANY
# OTHER IDENTIFICATION OF MICHIGAN STATE UNIVERSITY IS INCLUDED IN ANY COPY OF 
# ANY PORTION OF THIS SOFTWARE, THEN THE DISCLAIMER BELOW MUST ALSO BE INCLUDED.

# THIS SOFTWARE IS PROVIDED AS IS, WITHOUT REPRESENTATION FROM MICHIGAN STATE
# UNIVERSITY AS TO ITS FITNESS FOR ANY PURPOSE, AND WITHOUT WARRANTY BY MICHIGAN
# STATE UNIVERSITY OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT
# LIMITATION THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
# PARTICULAR PURPOSE.

# THE MICHIGAN STATE UNIVERSITY BOARD OF TRUSTEES SHALL NOT BE LIABLE FOR ANY
# DAMAGES, INCLUDING SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES,
# WITH RESPECT TO ANY CLAIM ARISING OUT OF OR IN CONNECTION WITH THE USE OF
# THE SOFTWARE, EVEN IF IT HAS BEEN OR IS HEREAFTER ADVISED OF THE POSSIBILITY
# OF SUCH DAMAGES.

import os, sys, csv
from obspy.core import read
from scipy import signal
from scipy.integrate import simps
import obspy.signal.invsim as sim
from time import gmtime,strftime
#import pylab as plt
import matplotlib.pyplot as plt
import numpy as np
import scipy as sp
import string,subprocess
import difflib as diff
import string

from Tkinter import *
import tkSimpleDialog
#                                               calcon dictionary example:
#calcon = {'s_chname':'SHZ',\
#          's_chsen':0.945,\
#          'l_chname':'LASER',\
#          'l_chsen':0.945,\
#          'l_sen':1.00,\
#          'l_calconst':0.579,\
#          'target_dir':'c:\\MDTcal\\calibrations\\',\
#          'damping_ratio':0.707, \
#          'damping_ratio_source':"C:\\MDTcal\\calibrations\\20160414_115959_LM_MSU_SHN.mseed", \
#          'free_period':0.880 ,\
#          'free_period_source':"C:\\MDTcal\\calibrations\\20160414_120101_LM_MSU_SHN.mseed", \
#          'file_type':"mseed", \
#          'station':"NE8K", \
#          'network':"LM" }

# oops! We also need the Station name, and the network name.

# calcon dictionary:
# calcon.s_chname = sensor channel name
# calcon.s_chsen = sensor sensitivity in uv/count
# calcon.l_chname = laser position sensor channel name
# calcon.l_chsen - laser position sensor channel sensitivity in uv/count
# calcon.l_sen = laser position sensor sensitivity in V/mm
# calcon.l_calconst = geometry correction ratio between center of mass & laser target
# calcon['target_dir'] = target directory for storage of output files
# calcon.damping_ratio = calculated damping ratio
# calcon.damping_ratio_source = source file for damping ratio calculation
# calcon.free_period = calculated free period in Hz
# calcon['free_period_source'] = source file for free period calculation
# calcon['file_type'] = type of files used in the calibration.
# calcon['station'] = Station designator
# calcon['network'] = Network designator

#                  Options are:
#                              sac
#                              mseed
#                              css

#                   Note that css format uses a master file containing the 'directory' of
#                   datafiles. Thus it requires some special handling. This file is
#                   called a '.wfd' file and it points to the actual datafiles.
#                   These datafiles will be loaded as a multi-stream array, and we must
#                   then pick our data from one of those streams.
#                   Thus, two bits of info must be included: The css '.wfd' file
#                   directory and the channel name file

#
#     function dataload
#     input: file name for the target data
#            sometimes the file name contains wildcards and more than one stream gets
#            loaded at a time. Hence, we specify the target channel to find the
#            appropriate stream. This should accomodate both css, sac, and miniseed
#            irregardless if it's just one stream
#     input: The target channel with the target data
#     input: The file type: i.e. css, sac, or mseed
#     output: data list, and the delta. (sample period)
#     status: Boolean operator, True = data was successfully loaded
#
def file_preview(infile):
    st=read(infile)
    st.plot(color = 'blue',size=(500,200),ti_rotation=90)
    return()

def dataload(infile,target_channel,ftype):
#    print "Attempting to load data file {}".format(infile)
#    print "Target channel is {}.".format(target_channel)
#    print "File type is set to {}".format(ftype)
    fileformat = string.lower(ftype)
#    print "{} \n".format(fileformat)
    status = False
    delta = 999    # seconds per sample
    target_channel = target_channel[:3]


    if string.lower(ftype) !='css':
        st = read(infile) # opens the non-css stream
        for i in range(len(st)):
#            print "'{0}' = '{1}' ? ".format(string.lower(target_channel)[0:3],string.lower(st[i].stats.channel)[0:3])
            if string.lower(target_channel)[0:3] == string.lower(st[i].stats.channel)[0:3]:
                output = st[i].data
                delta = st[i].stats.delta
                status = True
 #               print " output set to {}".format(st[i].stats.channel)
    else:                     # oops, its a css file
        st = read(infile, format = "css") # unlike the sac & mseed, this points to a .wfd file full of pointers.
        for i in range(len(st)):   
            if string.lower(target_channel) == string.lower(st[i].stats.channel):
                output = st[i].data
                delta = st[i].stats.delta
                status = True 

        # it gets fuzzy from here, as we might have multiple streams for the same channel.
        # So how do we select the right one? Right now, css just drops out with a False status
#

    return(output,delta,status)



#                                                    Function csvLoad:
#                                 General purpose loading function that brings in the first line as
#                                 a header list, and the remaining dataset as a secondary list
#                                     (used in the grid search algorithm)
#
def csvload(infile):                                    
    with open(infile,'r') as fin:
        list = csv.reader(fin)
        rowcnt=0
        stack = []
        header = []
        for row in list:           # Bring in the data and create a list of lists, each of which                                  
            if rowcnt == 0:        # corresponds with a given sample.
                header.append(row)
            else:
                stack.append(row)
            rowcnt = 1
    return (header,stack)


def freeperiod(root_window,calcon):
#     source file for the free period is taken from the dictionary
#     free period value is returned.
# 
#     Assume that the code calling this def has provided us with the file 
#     containing the stream
#
#                       Dan Burk prefers to use the Laser channel for this measurement.
    Frequency = 1.0
    try:
        infile = calcon['free_period_source'] # file name
        if calcon['l_chname'] in calcon['free_period_source']:
 
            target_channel = calcon['l_chname']    # laser channel name
        else:
            target_channel = calcon['s_chname']    # If user picked sensor, use that. 

        filetype = calcon['file_type']
        laser,delta,status = dataload(infile,target_channel,filetype)

#
#                                    Plot the free period impulse for the user
#

        x = []
        for i in range (0,len(laser)):
            x.append(i)
        plt.plot(x,laser)
        plt.xlabel("Find beginning sample number. Place cursor on the 1st few cycles of the impulse.")
        plt.ylabel("Counts from the digitizer.")
        plt.ion()         # Start a separate thread for interaction
        plt.show()
#
#                                     Get 1st sample number from the user
#
#       start =int(raw_input('Enter the estimated sample number of the beginning of the impulse  '))
#       global root
        start = tkSimpleDialog.askinteger('Free period measurement', 'Enter beginning sample # (x value',parent=root_window) 
        plt.close()
        
        end = start + 2048            # (Nyquist/1024 breakpoints: (130sps/2)/(2048/2) = .063 Hz resolution
        if end > (len(laser)-1):
            end = (len(laser)-1)        # Truncate ending sample number to the end of file to avoid overflow 

                                      #            
                                      # Find the period of the observed signal
                                      #

        sense = signal.detrend(laser[start:end])
                                      
        N = len(sense)
        W    = np.fft.fft(sense)
        freq = np.fft.fftfreq(len(sense),delta) 

                                      # First value represents the number of samples and delta is the sample rate
                                      #
                                      # Take the sample with the largest amplitude as our center frequency. 
                                      # This only works if the signal is heavily sinusoidal and stationary 
                                      # in nature, like our calibration data.
                                      #

        idx = np.where(abs(W)==max(np.abs(W)))[0][-1]
        Frequency = abs(freq[idx])    #              Free period Frequency in Hz
                                      #
                                      # Check the target directory to see if it exists.
                                      #
        if not os.path.isdir(calcon['target_dir']):
            subprocess.call(["mkdir",calcon['target_dir']],shell=True)
                                      #
                                      # Plot Free period waveform with calculated free period.
                                      #
        caltime = strftime("%Y_%m_%dT%H_%M_%S",gmtime())
        ET = [] # elapsed time
        for i in range(0,len(sense)):
            ET.append(i*delta)
        plt.plot(ET,sense)
        plt.xlabel("Time (in seconds)    Free period frequency = {:.3f} Hz".format(Frequency))
        plt.ylabel("Counts")
        figure_name = calcon['target_dir']+caltime+"_freeperiod_"+target_channel+".png"
#        figure_name = calcon['target_dir']+caltime+"_dampingratio_"+calcon['s_chname']+".png"
        plt.savefig(figure_name)
#        plt.show()
        plt.close()

    except:
        print "Exception: Error in processing channel {0} in fileset {1}.".format(target_channel,infile)
        print "for one of the following reasons:\n\n"
        print " - Selected sample number isn't within the resonance waveform.\n"
        print " - Selected sample number is too close (within 2048 samples) of the end of file.\n"
        print " - The designated channel was not found within the designated file."
        print " - The designated file was not found.\n\n"
        print " Free period has been set to a default of 1.0 Hz. Recheck your file & try again." 

    return(Frequency)



                      # Create a low pass filter to be applied to the signal and laser
                      # in order reduce interference from 50 or 60 hz hum and stuff like that
                      #

def firfilt(interval, freq, sampling_rate):  # Interval is the array upon which you wish to apply the low pass filter
    nfreq = freq/(0.5*sampling_rate)
    taps =  sampling_rate + 1
    a = 1
    b = sp.signal.firwin(taps, cutoff=nfreq)
    firstpass = sp.signal.lfilter(b, a, interval)
    secondpass = sp.signal.lfilter(b, a, firstpass[::-1])[::-1]
    return secondpass                                  


#
#                          Damping Ratio
#                          
#                         Input: calcon   output: damping ratio number, and a saved graph.
#

def dampingratio(root_window,calcon):
#    print calcon['s_chname']                # = sensor channel name
#    print calcon['s_chsen']                 #= sensor #sensitivity in uv/count
#    print calcon['l_chname']                # = laser position sensor channel name
#    print calcon['l_chsen']                 #- laser position sensor channel sensitivity in uv/count
#    print calcon['l_sen']                   #= laser position sensor sensitivity in V/mm
    print calcon['l_calconst']              #= geometry correction ratio between center of mass & laser target
    print calcon['target_dir']              #= target directory for storage of output files
    print calcon['damping_ratio']           #= calculated damping ratio
    print calcon['damping_ratio_source']    #= source file for damping ratio calculation
    print calcon['free_period']             #= calculated free period in Hz
    print calcon['free_period_source']      #= source file for free period calculation
    print calcon['file_type']               #= type of files used in the calibration.
    print calcon['station']                 #= Station designator
    print calcon['network']

    damping_ratio = 0.707
    try:
        infile = calcon['damping_ratio_source'] # file name
        if calcon['s_chname'] in calcon['damping_ratio_source']:

            target_channel = calcon['s_chname']     # sensor channel name
        else:
            target_channel = calcon['l_chname']

        filetype = calcon['file_type']          # data file type
        sensor,delta,status = dataload(infile,target_channel,filetype)

        print 'This will assist you in the measurement of the damping ratio.\n'
        print ' Your selected file should represent several damping ratio impulses.' 
        print ' The following screens will plot the waveform within'
        print ' the file. \n'
        print ' For each impulse, measure the sample number representing:\n'
        print ' - Sample number for the downslope of the first impulse'
        print ' - Sample number representing the end of the level part'
        print ' of the wave where signal settled to zero.\n'
        print ' The sample number is found as "x" in the lower left corner of screen.\n\n'
        print ' The program will enable you to enter these sample numbers '
        print ' for as many impulses as you have within the file.\n\n'
        print ' The program will calculate the damping ratios as the '
        print ' average of Z1 to Z2, and Z2 to Z3, then make an average' 
        print ' damping ratio from the impulses. \n\n'

        sensor = firfilt(sensor,10,1/delta) # apply a 10Hz filter to the data
               #
               #     Plot the initial file for recording the impulses.
               #     Then, get the sample numbers from the user.
        x = []
        for i in range (0,len(sensor)):
            x.append(i)
        plt.plot(x,sensor)
        plt.xlabel("Use ZOOM to find starting & ending sample # for each impulse.")
        plt.ylabel("Counts from the digitizer.")
        plt.ion()          #   Put focus onto the dialog box for user input
        plt.show()
        
#        keyboard = raw_input('\n\n How many impulses have you measured? ')
#        if keyboard =="":
#            print "Nothing entered. Setting the default to one pulse."
#            keyboard = "1"
#        impnum = int(keyboard)
        impnum = tkSimpleDialog.askinteger('Damping Ratio Measurements', 'How many impulses are measured?',maxvalue=6,parent=root_window)
        if impnum == 0:
            impnum = 1


        last = []
        first = []
        for i in range (1,impnum+1):
            
#            keyboard = raw_input('\n Enter the estimated sample number of the beginning of the impulse {}  '.format(i))
#            if keyboard == "":
#                print "Nothing entered. Setting default to sample # 1"
#                keyboard = 1
#            first.append(int(keyboard))
             
            kbdint = tkSimpleDialog.askinteger('Damping Ratio Measurements', 'Impulse #{} beginning sample number:'.format(i),parent=root_window)
            if kbdint == 0:
                kbdint = 1                    
            first.append(kbdint)
            
#            keyboard = raw_input('Enter the estimated sample number of the ending of the impulse train {} '.format(i))
#            if keyboard =="":
#                print "Nothing entered. Setting default to sample 1024"
#                keyboard = "1024"
#            last.append(int(keyboard))
            
            kbdint = tkSimpleDialog.askinteger('Damping Ratio Measurements', 'Impulse #{} ending sample number:'.format(i),parent=root_window)
            if kbdint == 0:
                kbdint = 1                    
            last.append(kbdint)
        
                 #
                 # Start looking for the zero crossings
                 #
        print first
        print last
        nn = 0
        hn = []
        freep = []
        for i in range(0,impnum):

            sense = sensor[first[i]:last[i]]
            sgrad = np.gradient(sense,80)
                                  # sgrad is the derivative of the sensor: Scan for zero crossings
            sgfilt = sp.signal.symiirorder1(sgrad,4,.8)
            dt = []
            Z = []                            # Z is the list of sensor values corresponding to where the derivative flips sign,
            ZZ = []                           # and should represent where the local max/min occurred in the waveform.
            offset = np.mean(sense[(len(sense)-131):len(sense)])   # Use the tail to determine the zero point of the impulse          
            polarity = 0
           
            zero_crossings = np.where(np.diff(np.sign(sgfilt)))[0]
  
            for n in range(0,len(zero_crossings)):
               Z.append(sense[zero_crossings[n]]-offset)

               if (n<>0) and (n<4):
                   dt.append(2*(zero_crossings[n]-zero_crossings[n-1])*delta)
                   # time between the peaks in seconds
                   # Z represents the actual peak sample where the derivative went to zero 
                   # and is offset corrected

            for n in range(0,len(Z)-1):
                zz = np.abs(Z[n])       # zz is the absolute value of the signal datapoint
                ZZ.append(zz)           # ZZ is the list of absolute values from Z
                                        # Adjust Z for middle tail-end to fix bias problems
                                        # Calculate the list of "good" points based on the fact that each value should 
                                        # be smaller than the next 
            nn = 0
            flag = True
  
            for n in range(1,len(ZZ)):
                    if np.int(ZZ[n])>np.int(ZZ[n-1]): # look at peak to see if is indeed smaller than prev impulse
                        flag = False
                    else:
                        if flag == True:
                            nn +=1
                            # print "ZZ[{0}] reports as {1}".format(n,ZZ[n])
            if nn>3:
                nn = 3 # stop counting at 4   
            #
            #   # calculate a list of damping ratios starting with the second local max
            #
            hh = []
            fp = []
            for n in range(1,nn):
                result = np.log(np.abs(float(Z[n-1])/Z[n])) / np.sqrt(np.square(np.pi)+np.log(np.abs(float(Z[n-1])/Z[n])))
                if result == result:   # look out for NaN's from bad impulses
                    hh.append(result)
            hn.append(np.mean(hh))

            print '\n Damping ratios for impulse {0} that create a mean of {1:0.3f} are as follows: '.format(i,np.mean(hh))
            print hh
 
        hm = np.median(hn) # hn is the list of the median damping ratios from the impulses.
        ha = np.mean(hn) # hz is the list of mean damping ratios from the impulses

        print '\n\n The median damping ratio for your {0} impulses = {1:0.3f} . '.format(impnum,hm)
        print '\n The mean damping ratio for your {0} impulses = {1:0.3f} . '.format(impnum,ha)
                                      #
                                      # Check the target directory to see if it exists.
                                      #
        if not os.path.isdir(calcon['target_dir']):
            subprocess.call(["mkdir",calcon['target_dir']],shell=True)
                                      #
                                      # Plot Free period waveform with calculated free period.
                                      #
        caltime = strftime("%Y_%m_%d %H_%M_%S",gmtime())
        ET = [] # elapsed time
        for i in range(0,len(sensor)):
            ET.append(i*delta)
        plt.plot(ET,sensor)
        title = "Damping Ratio calculation on "+caltime+" using channel :"+target_channel
        plt.title(title) 
        plt.xlabel("Time (in seconds)    Mean damping ratio = {:.3f} ".format(ha))
        plt.ylabel("Counts")
        figure_name = calcon['target_dir']+caltime+"_dampingratio_"+target_channel+".png"
        plt.savefig(figure_name)
        plt.show()
        plt.close()
    except:
        print "Exception: Error in processing channel {0} in fileset {1}.".format(target_channel,infile)
        print "Something didnt work."
        print "mean damping ratio set to default of 0.707! Calibration will not be accurate."
        ha = 0.707

    mean_damping_ratio=ha           # Just for the sake of clarity
    return(mean_damping_ratio)

#
#
#                                   Sigcal
#
#
# Sigcal used to use a 'header' and 'stack' for loading generic data from a csv file.
# def 'load' deprecated
# def 'getoptions' deprecated- might need this in Kens code
# def 'sacparse' for parsing through working directories - useful in Kens stuff?
# def sacload used to match up the laser to the sensor data
#
# def wfdaudit : useful for auditing the wfd



#                                   # Function sacparse
                                    # Input the file list, the sensor channel, the laser channel name
                                    # and return a sorted list of sac files for these two channel pairs
def sacparse(filelist,senchan,lsrchan):
    sensorfiles = []
    laserfiles = []
    print "senchan set to: {0} and lsrchan set to: {1} \n File list contains {2} items.".format(senchan,lsrchan,len(filelist))
    for i in range(0,len(filelist)):

        if senchan in filelist[i]:
            sensorfiles.append(filelist[i])

        if lsrchan in filelist[i]:
            laserfiles.append(filelist[i])
    sensorfiles.sort(key=str.lower)
    laserfiles.sort(key=str.lower)
    print "A total of {} sensor/laser channel sets found.".format(len(laserfiles))
    if len(sensorfiles)!=len(laserfiles):
        print "Warning!! Sensor length {0} vs laser length {1} \n channel set mismatch! Calibration may be invalid." \
              .format(len(sensorfiles),len(laserfiles))
        print " Ensure that when you designate input files, that there is a laser position sensor channel file for"
        print " every channel sensor file. They must match!"
#        sys.exit()
    return(sensorfiles,laserfiles)



                                   # Function sacload
                                   # Bring in two file names, compare, load the stream and
                                   # output the stream data and sample period (in seconds)
                                   #
#def sacload(sensorfile,laserfile,senchan,lsrchan):
                                   # input parameters: infile[],senchan,lsrchan
#    result = diff.ndiff(sensorfile,laserfile)    # Result gives us the common letters from the file name
#    txt = ''.join(result)
#    common = ""
#    for i in range(0,int(len(txt))/3):
#        if (txt[i*3] == " "):
#            common = common+txt[i*3+2]
#        if (txt[i*3] == "-") or (txt[i*3] == "+"):  # Add a wild card for any letters that are different
#            common = common+"*"
#    st=read(common)                                 # Read all conforming channels that match the channel names
#    delta = st[0].stats.delta
#    for i in range(0,len(st)):
#        if (string.lower(senchan) == string.lower(st[i].stats.channel)):   # If the stream matches sensor or laser channel name
#            sensor = st[i].data
#        elif (string.lower(lsrchan) == string.lower(st[i].stats.channel)): # Append it.
#            laser = st[i].data
#    return(sensor,laser,delta)



                               # support for css data format #
								
def wfdaudit(cwd,wfdin):  # Audit the css wfd file and repair it if there are missing streams.
                          # Input: Record of current working directory, and the name of the wfd file

    wfdout = cwd+wfdin[:-4]+"_audit.wfd"
    wfdin = cwd+wfdin
    cssbufffile = open(wfdin)
    print "this is wfdin: '{}'".format(wfdin)
    cssbuffout = open(wfdout, mode = "w")
    
    #     Okay, we need to fix the wfd by editing it and removing reference to any non-existent files.
    #     Audit the wfd and create a modified version.
    #     Auditing and removing non-existent file references ensures we can open the CSS.
    
    cssbuff = []
    try:
        for i in range(0,1000):
            buff =cssbufffile.readline()
            if buff != "":
                cssbuff.append(buff)        
    except:
        print "There was a Problem when opening wfd file"

    buffout = []    
    for i in range(0,len(cssbuff)):
        buffile = cwd+cssbuff[i][150:225].lstrip() # parse out the file names found inside wfd
 #       print "buffile = '{}'".format(buffile)
        if os.path.isfile(buffile):
#           print '"{}" exists.'.format(buffile)
            cssbuffout.write(cssbuff[i])
    return(wfdout)  # Return the name of the audited wfd file

	
	
def cssload(sensorstream,laserstream): #   Two separate streams from the wfd.
    delta=sensorstream.stats.delta
    sensor =sensorstream.data
    laser = laserstream.data

    return(sensor,laser,delta)

#
#
# def for getcal is deprecated
#
#
#
# def process:
# variables in cconstant must be matched to the new dictionary
# 
# calcon dictionary:
# calcon['s_chname'] = sensor channel name
# calcon['s_chsen'] = sensor sensitivity in uv/count
# calcon['l_chname'] = laser position sensor channel name
# calcon['l_chsen'] - laser position sensor channel sensitivity in uv/count
# calcon['l_sen'] = laser position sensor sensitivity in V/mm
# calcon['l_calconst'] = geometry correction ratio between center of mass & laser target
# calcon['target_dir'] = target directory for storage of output files
# calcon['damping_ratio'] = calculated damping ratio
# calcon['damping_ratio_source'] = source file for damping ratio calculation
# calcon['free_period'] = calculated free period in Hz
# calcon['free_period_source'] = source file for free period calculation
# calcon['file_type'] = type of files used in the calibration.
# calcon['station'] = Station designator
# calcon['network'] = Network designator 
 
def process(sensor,laser,delta,calcon):         # cconstant is a list of the calibration values. 

    Station = calcon['station']        # Name of Station under test
    Network = calcon['network']
    Sensorchanname = calcon['s_chname']# cconstant[cconstant[13]*2+1] 
    sensor_adccal = calcon['s_chsen']  # float(cconstant[cconstant[13]*2+2])# ADC channel sensitivity for sensor channel
    laserchanname = calcon['l_chname'] # cconstant[cconstant[14]*2+1]
    laser_adccal = calcon['l_chsen']  # cconstant[cconstant[14]*2+2] )       # ADC channel sensitivity for the laser channel uV/count
    laserres = calcon['l_sen']        # CALIBRATED value from laser position sensor in mV/micron
    lcalconst = calcon['l_calconst']  # Typ. 0.957, for the SM3, based on the geometry of the laser target 
                                      # and center of mass relative to radius of moment arm
    h = calcon['damping_ratio']      # typically about 0.7 but MUST be accurately measured beforehand!
    resfreq = calcon['free_period']   # Typically between 0.7 and 1.3 Hz. Expressed in Hz, not seconds.
    Rn = (np.pi * 2.0 * resfreq)      # Free period as expressed in radians / second                      
    lasercal = laserres/1000          # microns / count from the CALIBRATED laser and CALIBRATED ADC.
                                      # Parse out the sensor and laser data

#    return(Frequency,sensor_rms,laser_rms,fcal,Rn,h,gmcorrect)
# Frequency of the analysis point
# Sensor rms value in v^2/Hz 
# laser rms value in m/sec^2/Hz 
# sensitivity in V/m/sec
# resonance frequency (free period) of sensor
# Damping ratio of the sensor
# ground motion correction factor

    calibration = {'frequency':0.0,             \
                    'sensor_rms':0.0,           \
                   'laser_rms':0.0,             \
                   'sensitivity':0.0,           \
                   'freeperiod':resfreq,        \
                   'h':calcon['damping_ratio'], \
                   'gmcorrect':lcalconst}


                                      #            
                                      # Find the period of the observed signal
                                      #

    # Create a head and tail for the file of 4096 sample apiece.
    # We will create two ratios, from the head and tail of the file
    # and use the one with the lowest standard deviation for determining
    # the one for use with the FFT
    
    sensor = signal.detrend(sensor)
    laser = signal.detrend(laser)
    sensor1 = []
    sensor2 = []
    laser1 = []
    laser2 = []
   # print "The length of the sensor chunk for this file is {} samples.".format(len(sensor)/2)
    for i in range(0,len(sensor)/2):
        sensor1.append(sensor[i]) # take the first 4096 samples
        sensor2.append(sensor[(len(sensor)-(len(sensor)/2)+i)]) # Take the last 4096 samples
        laser1.append(laser[i]) # take the first 4096 samples
        laser2.append(laser[(len(laser)-(len(sensor)/2)+i)]) # take the last 4096 samples
    
    ratio1 = np.std(sensor1)*np.std(laser1)
    ratio2 = np.std(sensor2)*np.std(laser2)
    if ratio1<ratio2:                      # The chunk with the smallest standard deviation wins.
        sensor3 = sensor1
        laser3 = laser1
    else:
        sensor3 = sensor2
        laser3 = laser2
                         # Apply the ADC constants to the sensor channel data to convert to units of volts
    sensor3 = sensor_adccal*np.array(sensor3)
                         # Apply an FFT to the sensor data
                         # Generate a frequency table
                         # Find the index point where rms energy is highest
                         # Return the frequency in Hz.
    senfft   = np.fft.fft(sensor3)
    freq = np.fft.fftfreq(len(sensor3),delta) # Length of the sample set and delta is the samplerate
    idx = np.where(abs(senfft)==max(np.abs(senfft)))[0][-1]
    Frequency = abs(freq[idx])
    calibration['frequency']=Frequency # redundant, I know, but this code is retrofitted in a hurry
   
                                      #
                                      # Take the sample with the largest amplitude as our center frequency. 
                                      # This only works if the signal is heavily sinusoidal and stationary 
                                      # in nature, like our calibration data.
                                      #
    period = 1/(Frequency*delta) # represents the number of samples for one cycle of the test signal.
    gmcorrect = (2*np.pi*Frequency)**2/np.sqrt((Rn**2-(2*np.pi*Frequency)**2)**2+(4*h**2*(2*np.pi*Frequency)**2*Rn**2))

                                      #
                                      # create an axis representing time.
                                      #

    dt = [] # Create an x axis that represents elapsed time in seconds. delta = seconds per sample, i represents sample count
    for i in range(0,len(sensor)):
        dt.append(i*delta)

                                      # gmcorrect is the correction factor for observed pendulum motion 
                                      # vs true ground motion.
                                      # Now compensate the laser signal.
                                      # laser_adccal is the ADC in uV/count
                                      # lasercal = unit-corrected resolution of laser

    gmotion = laser_adccal*lasercal*lcalconst/gmcorrect*np.array(laser3)

                                      # Calculate the FFT for the ground motion signal
    lasfft   = np.fft.fft(gmotion)    # 
    freqlaser = np.fft.fftfreq(len(laser3),delta) # number of samples and delta is the sample rate
                                      #
                                      # Take the rms value of each signal at the main frequency only
                                      #

    calibration['sensor_rms'] = np.abs(np.sqrt(senfft[idx]**2)/(len(freq)/2)) # This is a relative value.
    calibration['laser_rms'] = np.abs(np.sqrt(lasfft[idx]**2)/(len(freq)/2))  # This is a relative value

                                      # Since the FFT at a single frequency breakpoint is by definition 
                                      # the energy contributed by a sine at that frequency,
                                      # the derivative and integral are related by a factor of 2pi*f
                                      #
                                      # Calculate the equivilant rms value of the derivative and integral 
                                      # of each signal.
                                      # Integral of sensor = sensor / 2pi*f
                                      # Derivative of laser = laser * 2pi*f
                                      # in either case, the ratio works out to sensor_rms/(2pi*f*laser_rms)
  
    cal = calibration['sensor_rms']/(2*np.pi*Frequency*calibration['laser_rms']) # This is the calibration sensitivity in V/m/sec.
    if not np.isnan(cal):
        calibration['sensitivity'] = cal
    
                                      #
                                      #     Reset the ground motion back to laser displacement
                                      #     for output 
                                      #


                                      #
                                      #     Calculate the phase difference between input signal and the response
                                      #     not yet implemented
    phase = 0.0

                                      #
                                      #     Return the results of this single frequency breakpoint
                                      #
   
    return(calibration)






#
#
#
#                                                    Sigcal
#
                                     #           MAIN PROGRAM BODY
                                     
def sigcal(calcon,files):


#    cconstant,fileopts = getoptions()           # Use the getoptions def to parse the command line options.
    wdir     = calcon['target_dir']            # working directory
#   filelist = files            # the file list that complies to the file type or station name


    filetype = string.lower(calcon['file_type'])            # The type of files to be processed.


#    print " calibration file: '{}'".format(calfile)
#    print " output file : '{}'".format(outfile)
#    print " The selected file type is: {} ".format(filetype)
#    print " The target directory is: {}".format(wdir)    
#    print " Cal control file: {}\n\n".format(calfile)
#    print " The length of the file list is {} files.".format(len(filelist))
    for i in range(0,len(files)):
        print " File # {0}: '{1}' ".format(i,files[i])

                                                           #    constant = getconstants(calfile)
#    cconstant = getcal(calfile)                        # Generate a list of the calibration constants
                                                           # 
                                                           # Create the header for the calibration output file.
                                                           # Header contains the station name, ADC cal constants,
                                                           # Laser cal constant, the geometric correction factor,
                                                           # the damping ratio, and the free period frequency.


                                                           #
                                                           # Now loop through the directory of csv files to build the
                                                           # calibration curve


    if filetype == "sac" or filetype =="mseed":
        frequency = []  
        sensor = []
        laser = []
        calnum = []
        infile_sensor = []
        infile_laser = []
        rn = []
        h = []
        gm_correct = []


        (sensorfiles,laserfiles) = sacparse(files,calcon['s_chname'],calcon['l_chname'])# returns a two item list of matched file names for the channel pair
                                 # create a list of matched channel files for each frequency

        for n in range(0,len(sensorfiles)):
            print "{0}, {1}, {2} \n ".format(sensorfiles[n],calcon['s_chname'],calcon['file_type'])
            print "{0}, {1}, {2} \n ".format(laserfiles[n],calcon['l_chname'],calcon['file_type'])
            sensordata,delta,status = dataload(sensorfiles[n],calcon['s_chname'],calcon['file_type'])
            laserdata, delta,status = dataload(laserfiles[n], calcon['l_chname'],calcon['file_type'])

            
 
                   # This should return two lists:
                   # sensor data, laser data, and the delta.
                   # We discard status at this point...maybe use it in the future for better error handling.
            
            
            calibration = process(sensordata,laserdata,delta,calcon)
                   #
                   # Process the file and output to outfile based on parameters
                   #
                #    calibration = {'frequency':             \ # defined in the process definition
                #                   'sensor_rms':            \
                #                   'laser_rms':             \
                #                   'sensitivity': 0.0              \
                #                   'resfreq':resfreq        \
                #                   'h':h                    \
                #                   'gmcorrect':lcalconst    \
                #                   }
            frequency.append(calibration['frequency'])
            sensor.append(calibration['sensor_rms'])
            laser.append(calibration['laser_rms'])
            calnum.append(calibration['sensitivity'])
            rn.append(calibration['freeperiod'])
            h.append(calibration['h'])
            gm_correct.append(calibration['gmcorrect'])
            infile_sensor.append(sensorfiles[n])
            infile_laser.append(laserfiles[n])
            

    if filetype == "css":                    # Start working on bringing in the css file format
        frequency = []  
        sensor = []
        laser = []
        calnum = []
        filenames = []
        rn = []
        h = []
        gm_correct = []
        senchan = cconstant[1]  #  cal_constants[((cal_constants[13]*2)+1)] # This points at the name of the sensor channel
        lsrchan = cconstant[3]  #  cal_constants[((cal_constants[14]*2)+1)] 
	# Remember that the file name references the wfd containing the file names and they all get loaded at once.
	# So, we need to open the wfd here. Then, we need to parse through the paired streams and feed them into the loader.
	# This IS NOT like the SAC file or miniseed at all. The user must ensure that there is only one wfd in the cal directory.
	# Create a css parse definition that will:
		# - Make a list of paired channelsets
	
	#cssparse should return:
		# The streams (css_stream)
		# The list of paired channel streams (element list): streamlist[0] - sensor, streamlist[1] laser
		# 
        for i in range(0,len(filelist)): # each file is a list of files. 
		    # For each file, first audit the file.
			# - Audit the wfd wfdaudit(cwd,wfdin) return--> wfdout which is the filename of the cleaned wfd
            wfd =read(wfdaudit(wdir,filelist[i]),format = "css")

			# Then, load the streams from that file
            streamlist0 = []
            streamlist1 = []
            print senchan, lsrchan
            for j in range(0,len(wfd)): #           j is the list number and streamlist is a listing of those numbers
                if senchan == wfd[j].stats.channel: # that correspond to streams containing that senchan data
                    streamlist0.append(j)
                if lsrchan == wfd[j].stats.channel:
                    streamlist1.append(j)
            streamlist = [streamlist0,streamlist1] # Streamlist is a list of streams matching sensor and laser
				
		
            for n in range(0,len(streamlist[0])): # n represents the number of paired channel streams are located in the directory
		    # cssload needs to bring in the streams, parse the time-history into two lists, and output the delta.
               data = cssload(wfd[streamlist[0][n]],wfd[streamlist[1][n]]) # The data is derived from the matched streams.
            #     data[0] is the sensor data 
			
            #     data[1] is the laser data 
            #     data[2] is the delta (sample period in seconds) 
               (freq,senrms,lasrms,cal,resonance,damprat,gm_c) = process(data[0],data[1],data[2],cconstant) # cal_constants) # Process the file and output to outfile based on parameters

            # Process input arguments are sensor data, laser data, delta and cal_constants

               frequency.append(freq)
               sensor.append(senrms)
               laser.append(lasrms)
               calnum.append(cal)
               rn.append(resonance)
               h.append(damprat)
               gm_correct.append(gm_c)
               filenames.append(filelist[i])

#
#                                              Write the calibrations to cal output file
#

    if len(frequency)<>0:
        caltime = strftime("%Y_%m_%d %H_%M_%S",gmtime())

        outfile  = calcon['target_dir']+caltime+'_caldata_'+calcon['network']+'_'+calcon['station']+ \
                          '_'+calcon['s_chname']+'.cal'

        outlog = calcon['target_dir']+caltime+'_caldata_'+calcon['network']+'_'+calcon['station']+ \
                          '_'+calcon['s_chname']+".log"

        # Write out the cal controls used for generation of the calibration curve data
        
        calcontrol = []
        calcontrol.append(calcon['station'])              # 0= Station designator
        calcontrol.append(calcon['s_chname'])             #1 sensor channel name
        calcontrol.append(calcon['s_chsen'])              #2= sensor sensitivity in uv/count
        calcontrol.append(calcon['l_chname'])             #3= laser position sensor channel name
        calcontrol.append(calcon['l_chsen'])              #4- laser position sensor channel sensitivity in uv/count
        calcontrol.append(calcon['l_sen'])                #5= laser position sensor sensitivity in V/mm
        calcontrol.append(calcon['l_calconst'])           #6= geometry correction ratio between center of mass & laser target
        calcontrol.append(calcon['damping_ratio'])        #7= calculated damping ratio
        calcontrol.append(calcon['free_period'])          #8= calculated free period in Hz
        calcontrol.append(calcon['network'])              #9= Network designator
        calcontrol.append(calcon['target_dir'])           #10= target directory for storage of output files
        calcontrol.append(calcon['file_type'])            #11= type of files used in the calibration.
        calcontrol.append(calcon['damping_ratio_source']) #12= source file for damping ratio calculation
        calcontrol.append(calcon['free_period_source'])   #13= source file for free period calculation

        with open(outfile,'wb') as csvfile:   # use 'wb' in place of 'a' if you want to overwrite the file.
            outrow = csv.writer(csvfile, delimiter = ",",
                                quotechar='|', quoting=csv.QUOTE_MINIMAL)
            outrow.writerow(calcontrol) # cal_constants)

                                          # Write out the calibration matrix to the csv calibration output file
                                          
        with open(outfile,'a') as csvfile:    # use 'wb' in place of 'a' if you want to overwrite the file.
            for n in range(len(frequency)):
                print("Sensitivity calculates to: {0:.3f} V/m/sec at {1:.2f} Hz".format(calnum[n],frequency[n]))

                if calnum[n]<>0.00:
                    outrow = csv.writer(csvfile, delimiter = ",",
                                        quotechar='|', quoting=csv.QUOTE_MINIMAL)
                    outrow.writerow([frequency[n],calnum[n],infile_sensor[n],infile_laser[n]])
                else:
                    print "    entry {} Hz ignored due to bad amplitude or frequency calculation.".format(frequency[n])
         
            print "\n output sent to {} \n\n".format(outfile)


#
#                                Grid Search control parameters
#
        nsearch = 1 # Default grid search type - Optimize amplitude only.
        lmult = 1.70 # Default Lower frequency of grid search average amplitude calculation
        hmult = 5.0 # Default upper frequency of grid search average amplitude calculation
#
#                                Call the grid search to plot the response and calculate the sac poles&zeros
#   
    
        grid_search(outfile,nsearch,lmult,hmult,calcon['target_dir'])
    else:
        print "No data files of the appropriate format were found within this directory."












######################## Start of grid_search algorithm by Hans Hartse ###################

                                 ###### LA-CC-14-079 #######
# Author: Hans Hartse, LANL : August, 2014
# Modified by D Burk, Michigan State University
# Version: 20140831
#
# Modification 20140828 : Adjust amplitude calculation to start at 2x freeperiod to 5x freeperiod
# Also correct the path of the plot file output
# Modification 20140831 : minor bug fixes to file output path, and of lmult,hmult
#
# holds the following functions:
# write_sacpz - write a SAC-style pole-zero file where input is an ObsPy "dictionary"
# find_pole_zero - grid search about MSU measured/estimated response, free-period, and damping factor
# plot_response_curves - plots amplitude and phase curves using best-fit information from grid search
# plot_misfit_results - plot an RMS misfit vs iteration number from grid search

# write a function that will take obsby resp "dictionary" info
# and create a sac pole-zero file
# add one extra zero for sac pz to declare velocity, rather than displacement



def write_sacpz(fname, resp):

# resp is the obspy data structure holding poles, zeros, and scale factor
    print "SAC poles & zeros result:\n"
    with open(fname,'w') as f:
        f.write("ZEROS {}\n".format(len(resp['zeros']) + 1 ))
        print "ZEROS: {}".format(len(resp['zeros']) + 1 )
        f.write("POLES {}\n".format(len(resp['poles'])))
        print "POLES {}\n".format(len(resp['poles']))
        for pole in resp['poles']:
            f.write("{:e} {:e}\n".format(pole.real, pole.imag))
            print "real:{:e} Imaginary:{:e}".format(pole.real, pole.imag)
        f.write("CONSTANT {:e}".format(resp['gain']))
        print "\nsensor gain constant {:2.3f} Volts/(m/sec)".format(resp['gain'])

    spz = "SAC pole-zero file is named %s" % ( fname )
    print ( "\n" )
    print spz



#################################################################################


# start of function that does a grid search to find a response that best fits the MSU measured response
# function "find_pole_zero"
                              # Input parameters:
                              # freq_msu: List of frequencies of n terms
                              # amp_msu: List of ampltudes at those frequencies (n terms)
                              # station: station description
                              # msu_freep: Measured Free-period frequency from calibration
                              # msu_damp: Measured damping ratio from calibration
                              # nsearch: Constraint options (0 = fully constrainted,1,2,3 = full grid search)
                              # coarse_search: The step size for grid searching parameters (Typ 0.1)
                              # fine_search: Step size for fine grid searching (typ 0.005)
                              # nloops: Number of iterations to try for best fit (Typ. 4)
                              # ngrids: Total number of grid points within the search to use (typ. 20)
 
def find_pole_zero(freq_msu,amp_msu,station,msu_freep,msu_damp,nsearch,coarse_search,fine_search,nloops,ngrids,lmult,hmult):

# ngrids is the number of grid points to be searched for each parameter, per each "percentage" loop
                        # At nsearch = 3, grid search on amplitude, damping ratio, and free period.
    nfreqs = ngrids
    if ( nsearch < 3 ): # Set flags. Free period is constrained at nsearch = 2
        nfreqs = 1
    ndamps = ngrids
    if ( nsearch < 2 ): # Set flags. Free period & Damping ratio is constrained at nsearch = 1
        ndamps = 1
    nscales = ngrids
    if ( nsearch < 1 ): # set flags. Free period, Damping Ratio, and amplitude are all constrained.
        nscales = 1

# search the grids nloops times, first between coarse_search percent smaller than starting params 
#   and coarse_search percent larger than starting params, then, eventually search only within fine_search percent
#   of the best params found on each previous loop search

    search_range = np.linspace(coarse_search, fine_search, nloops)

# freq_msu is array holding frequency values where MSU made amp measurements
# amp_msu is array holding amplitude values measured by MSU
# note that msu_freep is the MSU estimated freee period in seconds

# now find average amplitude from MSU measurements where freq > 1 Hz
#
# edit: Change the average amplitude calculation to use frequencies greater than 
# 3x the free period frequency but less than 8x the free-period frequency.
# This program calculates only two poles & zeros: Response should be flat within
# this passband and avoids any weird issues at higher frequencies and keeps 
# calculation off the knee of the response curve in cases of high or low damping
# ratios
# - drb 08/28/2014

    count = 0
    amp_average = 0.
#    lmult = lmult/msu_freep # make it a multiplier of freeperiod in Hz (lowest)
#    hmult = hmult/msu_freep                                         # (Highest)
    
    for i, freq in enumerate(freq_msu):
        if ( freq > lmult) and (freq < hmult):  
                                      # Set frequency discriminator to msu_freep * 2 to get off the 
                                      # knee of the curve for SP instruments - drb
           amp_average = amp_average + amp_msu[i] 
           count += 1
    amp_average = amp_average / float(count)

                                      # set preliminary "best parameters"

    best_freep = msu_freep 
    best_damp = msu_damp
    best_scale = amp_average


                                      # best_fit is the RMS misfit between MSU observed 
                                      # and model amplitudes in log10 space,
                                      #    an outrageously large value, initially

    best_fit = 1000000.
    best_corner = 1/msu_freep
    best_index = 0
                                      # an index counter to keep track of the total number of searches/misfits
    j = 0
                                      # for use with later plotting
                                      # prepare array to hold total number of interation results

    misfits = np.zeros(nscales * ndamps * nfreqs * nloops)

                                      # prepare array to store each iteration number

    misfit_count = np.zeros(nscales * ndamps * nfreqs * nloops)

                                      # start of loops 

    for range in search_range:

                                      # build a list of "corner frequencies" to test
                                      # I think these "corner frequencies" - in ObsPy Speak means 1/free period of seismometer

        freep_adjust = best_freep * range
        fp_long = best_freep + freep_adjust
        fp_short = best_freep - freep_adjust

                                      # the case where free period is held constant at the MSU-supplied value

        if ( nsearch < 3 ):
            fp_long = best_freep
            fp_short = best_freep

                                      # np.linspace will create an array from low_freq to high_freq over nfreqs of even spacing

        corners = np.linspace(1./fp_long, 1./fp_short, nfreqs)
        print ( "\nsearching free periods between %f and %f seconds" % ( fp_long, fp_short ) )

                                      # build a list of damping factors to test

        damp_adjust = best_damp * range
        low_damp = best_damp - damp_adjust 
        high_damp = best_damp + damp_adjust
        if ( high_damp >= 1.0 ):
            print ( "\nwarning - damping factor is %f - must be below 1.0 - setting damping to 0.9999" % ( high_damp ) )
            high_damp = 0.9999
        if ( nsearch < 2 ):
            low_damp = best_damp
            high_damp = best_damp

        damps = np.linspace(low_damp, high_damp, ndamps)
        print ( "searching damping factors between %f and %f" % ( low_damp, high_damp ) )

                                      # build a list of scale factors to test

        scale_adjust = best_scale * range
        low_scale = best_scale - scale_adjust 
        high_scale = best_scale + scale_adjust
        if ( nsearch < 1 ):
            low_scale = best_scale
            high_scale = best_scale
            nscales = 1
        scales = np.linspace(low_scale, high_scale, nscales)
        print ( "searching scale factors between %f and %f" % ( low_scale, high_scale ) )

                                      # here are the grid search loops, over corners, dampings, and scales

        for corner in corners:   
            for damp in damps:
                for scale in scales:

                                      # the key obspy function to find inst resp based on "corner frequency" and damping constant 
                                      # cornFreq2Paz takes an instrument's corner freq and damping factor to produce
                                      #   an Obspy-style paz file

                    resp = sim.corn_freq_2_paz(corner, damp) 
                    resp['gain'] = scale
                    amp_predicted = np.zeros_like(freq_msu)
                    for i, freq in enumerate(freq_msu):
                        amp_predicted[i] = sim.paz_2_amplitude_value_of_freq_resp(resp, freq) 
    
                    misfit = np.linalg.norm(np.log10(amp_msu) - np.log10(amp_predicted))
                    misfits[j] = misfit
                    misfit_count[j] = j + 1
       
                    if ( misfit < best_fit ):
                       best_fit = misfit
                       best_corner = corner
                       best_damp = damp
                       best_scale = scale
                       best_index = j

                    j = j + 1

                                      # find the best free period, which is 1/best_corner
                                      # this happens at the end of a particlar grid search loop

        best_freep  = 1./best_corner 

                                      # end of all loops

                                      # find poles and zeros using best corner freq, damp and scale 

    resp = sim.corn_freq_2_paz(best_corner, best_damp) 
    resp['gain'] = best_scale
    return(resp, best_freep, best_damp, best_scale, amp_average, misfits, misfit_count, best_index) 
                                      # end of function "find_pole_zero"


############################################################

#
#
                             # start of function "plot_response_curve"
                             # function plot_response_curve
#
#

def plot_response_curves(resp, freq_msu, amp_msu, best_freep, best_damp, best_scale, msu_freep,\
msu_damp, amp_average, amp_label, channel, sac_pz_file,target_dir,caltime):

                             # build an array of zeros with same length as freq_msu

    amp_predicted = np.zeros_like(freq_msu)

                             # loop over the frequencies present in the msu data file one at a time
                             # to find the amplitudes predicted for a given frequency 
                             # based on the best resp file

    for i, freq in enumerate(freq_msu):
        amp_predicted[i] = sim.paz_2_amplitude_value_of_freq_resp(resp, freq) 
                             # this code taken straight from the Obspy webpage examples 
                             # numbers for obspy to create a resp curve, based on an fft of a time series
                             # with sample rate of 0.01

    samp_rate = 0.01
    npts = 16384

                             # obtain "continuous" amp and freq values from obsby function to display continuous response curve

    poles = resp['poles']
    zeros = resp['zeros']
    h, f = sim.paz_to_freq_resp(poles, zeros, best_scale, samp_rate, npts, freq=True)

                             # plotting amp vs freq

    plt.figure()

                             # plot the continuous response curve, and the msu data, 

    plt.loglog(f, abs(h), freq_msu, amp_msu, 'go', markersize=6 )

                             # plot the predicted amplitudes at the MSU frequencies

    plt.loglog(freq_msu, amp_predicted, 'ro', markersize=4 )

                             # labels

    plt.xlabel('Frequency [Hz]')

                             # this str function is part of the standard Python, no need to "import" a special "package"

    plt.ylabel( str(amp_label) )
    plt.suptitle('Frequency vs Amplitude: Channel ' + str(channel) )

                             # plot over range from 2/3 * minimum frequency to 2.0 * maximum frequency  
                             # and over range from 2/3 * minimum amplitude to 2.0 * maximum amplitude  

    plx_min = 0.05 # freq_msu[0] * 0.66
    plx_max = 40.0 # freq_msu[len(freq_msu) - 1] * 2.00
    ply_min = 0.10 # amp_msu[0] * 0.66
    ply_max = 1000.0 # amp_msu[len(freq_msu) - 1] * 2.00
    plt.axis([plx_min, plx_max, ply_min, ply_max])

    freep_per = 100. * ( abs ( best_freep - msu_freep ) / msu_freep )
    damp_per = 100. * ( abs ( best_damp - msu_damp ) / msu_damp )
    scale_per = 100. * ( abs ( best_scale - amp_average ) / amp_average )
    rsp = ""
    cdt = "Calibration date = "+ caltime
    print "{} \n".format(cdt)
    tfp = "free period = %.3f Hz (%.2f%% MSU: %.3f)" % ( 1./best_freep, freep_per, 1./msu_freep )
    print ( "\n" )
    print tfp
    tdr = "damping = %.3f (%.2f%% MSU: %.3f)" % ( best_damp, damp_per, msu_damp )
    print tdr
    tsf = "scale = %.3f Volts/(m/sec)( Avg. amp: %.2f)" % ( best_scale, amp_average )
    print tsf
    spz = "File: %s" % ( sac_pz_file )
    #f.write("ZEROS {}\n".format(len(resp['zeros']) + 1 ))
    zzz = "ZEROS: {}".format(len(resp['zeros']) + 1 )
     #   f.write("POLES {}\n".format(len(resp['poles'])))
    ppp = "POLES {}\n".format(len(resp['poles']))
    for pole in resp['poles']:
      #      f.write("{:e} {:e}\n".format(pole.real, pole.imag))
        rsp = rsp+"real:  {:e} Imaginary:  {:e}\n".format(pole.real, pole.imag)
       # f.write("CONSTANT {:e}".format(resp['gain']))
    print "\nsensor gain constant {:2.3f} Volts/(m/sec)".format(resp['gain'])
 

                             # post results as text lines on the plot

    xtext = plx_min * 7.
    ytext = ply_min * 60
    plt.text( xtext, ytext, cdt )
    ytext = ply_min * 40
    plt.text( xtext, ytext, tfp )
    ytext = ply_min * 30
    plt.text( xtext, ytext, tdr )
    ytext = ply_min * 20
    plt.text( xtext, ytext, tsf )
    ytext = ply_min * 10
    plt.text( xtext, ytext, zzz )
    ytext = ply_min * 5
    plt.text( xtext, ytext, ppp )
    ytext = ply_min * 2
    plt.text( xtext, ytext, rsp )

                             # post some symbols and text for a legend

    amp_symbol = np.zeros(1)
    amp_symbol[0] = best_scale * 1.0
    freq_symbol = np.zeros(1)
    freq_symbol[0] = freq_msu[0]
    plt.loglog(freq_symbol, amp_symbol, 'go', markersize=6 )
    plt.text( freq_symbol[0] * 1.1, amp_symbol[0], 'Measurement', va='center' )
    amp_symbol[0] = best_scale * 0.70
    freq_symbol[0] = freq_msu[0]
    plt.loglog(freq_symbol, amp_symbol, 'ro', markersize=4 )
    plt.text( freq_symbol[0] * 1.1, amp_symbol[0], 'Model Best Fit', va='center' )
    plt.grid(True, which='major')
    plt.grid(True, which='minor')

  #  cconstant,fileopts = getoptions()           # Use the getoptions def to parse the command line options.
  #  wdir     = fileopts[0]            # working directory

    fig = target_dir+"\\"+caltime+'_'+channel + '_freq_v_amp' + '.png' # Place it in current working directory - drb
    txt = "best-fit freq. vs amplitude: \n    %s" % ( fig )
    print "\n"
    print txt
    plt.savefig( fig )

    plt.show()
#    plt.close()


                             # plotting phase vs freq, not sure how much this can be trusted

#plt.subplot(122)

    plt.figure()

                             #take negative of imaginary part

    phase = np.unwrap(np.arctan2(-h.imag, h.real))
    plt.semilogx(f, phase)
    plt.xlabel('Frequency [Hz]')

    plt.ylabel('Phase [radians]')

                             # title, centered above both subplots

    plt.suptitle('Frequency vs Phase: ' + str(channel) )
    plt.axis([0.004, 100, -3.5, 0.5])

                             # make more room in between subplots for the ylabel of right plot

#plt.subplots_adjust(wspace=0.3)
    plt.grid(True, which='major')
    plt.grid(True, which='minor')
    fig = target_dir+"\\"+caltime+'_'+channel +'_freq_v_phase.png' # save in data directory
    txt = "best-fit frequency vs phase: \n    %s" % ( fig )
    print "\n"
    print txt
    plt.savefig( fig )
#    plt.show()
    plt.close()

# end of function plot_response_curves




########################################################################


                                           
def grid_search(outfile,nsearch,lmult,hmult,target_dir):                 # Subroutine grid search
                                          # Bring in the data and plot.                
                                          #
                                          # Prepare to make the poles and zeroes from Hans Hartse gridsearch algorithm
                                          # Set up the control constants.
#    print"Grid search will iterate through several scenarios in order to find "
#    print"a best fit poles & zeros combination to describe the sensitivity curve."
#    print"\nThere are several options for this search:"
#    print"Option 0: Constrain all parameters to the calibration file (no grid search)"
#    print"Option 1: Optimize amplitude but constrain damping ratio and free period"
#    print"Option 2: Optimize amplitude, damping ratio but constrain free period"
#    print"Option 3: Optimize for amplitude, damping ratio and free period"
#    print"\n Most calibrations are best served with option 1.\n"

#    Inputstring = raw_input("\n\n Choose grid search option: 0,1,2, or 3):")
#    if (Inputstring == ""):
#	Inputstring = 2        # use the default
#    nsearch = int(Inputstring) # use measured freeperiod 
					  # 0: Full constraint on grid search to use MSU-measured amplitudes, damping ratio and free period.
                                          # 1: Optimize for amplitude w/i passband but constrain damping ratio and free period.
                                          # 2: Optimize amplitude w/i passband, optimize damping ratio, but constrain free period.
                                          # 3: Grid search for optimum amplitude, damping ratio AND free period
    coarse_search = 0.10                  # Typically 0.10
    fine_search = 0.005                   # Typically 0.005
    nloops = 6                            # Number of iterations through the grid (typically 4 or 5)
    ngrids = 21                           # Number of steps (typically 20)
    amp_units = "V*sec/m"
    amp_label = "Amplitude [" + amp_units + "]"

    fdata = csvload(outfile)

    header = fdata[0]                     # The header contains the initial constants used for creation of the datafile
                                          # and includes the damping ratio, free period frequency, and channel calibration information
                                          # in this order:

    station = fdata[0][0][0]          # fdata[0][0][0]  # Station name
    chname = fdata[0][0][1]           # fdata[0][0][1]  # Sensor name
    network = fdata[0][0][9]          # fdata[0][0][9]  = network designator
    target_dir = fdata[0][0][10]      # fdata[0][0][10] = target directory 
                                          #fdata[0][0][2]  # Channel 0 ADC sensitivity in microvolts / count
                                          # fdata[0][0][3]  # Laser name
                                          # fdata[0][0][4]   # Laser ADC sensitivity
                                          # fdata[0][0][5]  # Laser position sensor in millivolts/micron
                                          # fdata[0][0][6] # Lcalconstant geometry correction factor
    msu_damp = float(fdata[0][0][7])     # fdata[0][0][7] # h damping ratio
    msu_freep = 1/float(fdata[0][0][8])  # fdata[0][0]8] # Free period oscillation in Seconds, not Hz (as stored in cal file).

    caltime = strftime("%Y_%m_%d %H_%M_%S",gmtime())
    channel = network+"_"+station+'_'+chname
    # print "okay here is channel --> {}".format(channel)
    freq_msu = []                         # Initialize the frequency array
    amp_msu = []                          # Initialize the matching amplitude array

    for i in range(0,len(fdata[1])):      #        Build the list of frequencies and sensitivities from the file.
        freq_msu.append(float(fdata[1][i][0]))     # Field 0 is the frequency
        amp_msu.append(float(fdata[1][i][1]))      # Field 1 is the average sensitivity

                                          #    plot_curve(Station,Frequencies,Sensitivities,Freeperiod,h)
                                          #    plot_curve2(Station,Frequencies,Calint,Calderiv,Freeperiod,h)

                                          # Perform the grid search and create the curve

    (resp,best_freep,best_damp,best_scale,amp_average,misfits,misfit_count,best_index) = \
     find_pole_zero(freq_msu,amp_msu,channel,msu_freep,msu_damp,nsearch,\
     coarse_search,fine_search,nloops,ngrids,lmult,hmult)

                                          # Create the sac poles & zeros file

    sac_pz_file = target_dir +'\\'+caltime+'_'+channel+'.sacpz' # Set the file name to whatever station name is.

    write_sacpz(sac_pz_file,resp)

                                          # Plot the data for the user.

    plot_response_curves(resp,freq_msu,amp_msu,best_freep,best_damp,best_scale,\
    msu_freep,msu_damp,amp_average,amp_label,channel,sac_pz_file,target_dir,caltime)






