#!/usr/bin/python

# Version 20160421 - Ken Abrams & Daniel Burk
#
# 20160421 - Set the default directory as the initial target when opening sigcal process dialog


from Tkinter import *
import MDTcaldefs
import tkMessageBox, tkFileDialog
import string
import subprocess

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
 
def BrowseDefaultDir(root_window,calcon_in,DirNameVar,):
    DirName=tkFileDialog.askopenfilename(parent=root_window,initialdir=calcon_in['target_dir'], \
        title = 'Select Default Directory')
    endloc=string.rfind(DirName,'/')+1
    DirName = string.replace(DirName[:endloc], "/", "\\")
    DirNameVar.set(DirName)
    calcon_in['target_dir'] = DirName

	
def BrowsePeriodFile(root_window,FileNameVar,defaultdir):
    myFormats = [
    ('SAC File','*.sac'),
    ('CSS File','*.css'),
    ('Mini SEED File','*.mseed'),
    ('All Files','*')
    ]
    FileName=tkFileDialog.askopenfilename(parent=root_window,filetypes=myFormats,initialdir=defaultdir, \
        title = 'Select Free Period File')
    FileNameVar.set(string.replace(FileName, "/", "\\"))
#    entry_field.configure(text=FileName) 
    return(FileName)

def CalcFreePeriod (calcon_in,free_file_in,free_period_in):
    calcon_in['free_file']=free_file_in.get()
    freeval = MDTcaldefs.freeperiod(root,calcon_in)
    calcon_in['Free_period']= freeval
    free_period_in.set(freeval)

def BrowseDampingFile(root_window,FileNameVar,defaultdir):
    myFormats = [
    ('SAC File','*.sac'),
    ('CSS File','*.css'),
    ('Mini SEED File','*.mseed'),
    ('All Files','*')
    ]
    FileName=tkFileDialog.askopenfilename(parent=root_window,filetypes=myFormats,initialdir=defaultdir, \
        title = 'Select Damping File')
    FileNameVar.set(string.replace(FileName, "/", "\\"))
#    entry_field.configure(text=FileName) 
    return(FileName)
    
def CalcDampingRatio (calcon_in,damping_file_in,damping_ratio_in):
    calcon_in['damping_file']=damping_file_in.get()
    damping = MDTcaldefs.dampingratio(root,calcon_in)
    calcon_in['damping_ratio']= damping
    damping_ratio_in.set(damping)
    
    
# function to call sac file preview if not empty
def ViewPeriod(FileName):
    if len(FileName)==0:
        tkMessageBox.showwarning("ERROR","No file selected")
    else:
        MDTcaldefs.file_preview(FileName)
        
# function to call sac file preview if not emty
def ViewDamping(FileName):
#    if empty(DampingFile.get()):
#        tkMessageBox.showwarning("ERROR","No file selected")
    if len(FileName)==0:
        tkMessageBox.showwarning("ERROR","No file selected")
    else:
        MDTcaldefs.file_preview(FileName)        
        
def CallSigCal(root_window,calcon_in):


    filez = tkFileDialog.askopenfilenames(parent=root_window,title='Choose a file',initialdir=calcon_in['target_dir'])


# convert from unicode to str file list
    files = []
    for file in filez:
        files.append(string.replace(str(file), "/", "\\"))

# map input fields to calcon
    calcon_in['station']=StationName.get()
    calcon_in['network']=StationNetwork.get()
    calcon_in['s_chname']=SensorName.get()
    calcon_in['s_chsen']=float(SensorSen.get())
    calcon_in['l_chname']=LaserName.get()
    calcon_in['l_chsen']=float(LaserSen.get())
    calcon_in['l_sen']=float(LaserReso.get())
    calcon_in['l_calconst']=float(LaserCal.get())
    calcon_in['target_dir']=DefaultDir.get()
    calcon_in['damping_ratio']=float(DampingValue.get())
    calcon_in['damping_ratio_source']=DampingFile.get()
    calcon_in['free_period']=float(FreeValue.get())
    calcon_in['free_period_source']=FreeFile.get()
    calcon_in['file_type']=DataFormat.get()
    
    print calcon_in
    
# call sigcal with list    
    MDTcaldefs.sigcal(calcon_in,files)
            

def main():
#   setup main data structure
    calcon = {'s_chname':'SM3',\
          's_chsen':0.945,\
          'l_chname':'LASER',\
          'l_chsen':0.945,\
          'l_sen':1.00,\
          'l_calconst':0.579,\
          'target_dir':'c:\\seismo\\saccal\\',\
          'damping_ratio':0.707, \
          'damping_ratio_source':"C:\\seismo\\saccal\\damping\\2015_9_9_16_3_59_641_MSU_LNSM_SM3.sac", \
          'free_period':0.880,\
          'free_period_source':"C:\\seismo\\saccal\\freeperiod\\00000000_LASER.sac", \
          'file_type':"sac",\
          'station':'NE8K',\
          'network':'LM' }
    
# Setup GUI window
    global root
    root = Tk()
    root.title(string='MDT Seismic Sensor Calibration - v1.0')
#root.geometry('200x210+350+70')


# Setup default data path selection prompt
    Label(root, text="DATA SET SELECTION").grid(row=1, column=0,padx=5,pady=5,sticky=W)
    Label(root, text="Default Directory:").grid(row=2,column=0,sticky=E)

    global DefaultDir
    DefaultDir = StringVar()
    DefaultDir.set(calcon['target_dir'])
    
    SetDefaultDirectory = Entry(root, bg='white',textvariable=DefaultDir).grid(row=2,column=1,columnspan=6,sticky=W+E)
    SetDirectoryBrowse = Button(root, text='  BROWSE  ',command=lambda: BrowseDefaultDir(root,calcon,DefaultDir)).grid(row=2,column=7,padx=5,sticky=W+E)

# Setup sensor info block labels
    Label(root, text="SENSOR INFORMATION").grid(row=4,column=0,padx=5,pady=5,sticky=W)

# Prompt for Station Location name and network
#    StationName = StringVar()
    global StationName
    StationName= StringVar()
    StationName.set(calcon['station'])
    
    Label(root, text="Station Location Name:").grid(row=5,column=0,sticky=E)
    StationEntry = Entry(root,bg='white',textvariable=StationName).grid(row=5,column=1,padx=3,sticky=W)
    
    global StationNetwork
    StationNetwork = StringVar()
    StationNetwork.set(calcon['network'])    
    Label(root, text="Network:").grid(row=5,column=2,padx=3,sticky=E)
    StationEntry = Entry(root,bg='white',textvariable=StationNetwork).grid(row=5,column=3,sticky=W)    
    
# Setup sensor info block labels
    Label(root, text="Sensor Channel Name:").grid(row=6,column=0,pady=2,sticky=E)
    Label(root, text="Sensitivity:").grid(row=6,column=2,sticky=E)
    Label(root, text="uV/cnt", fg='blue').grid(row=6,column=4,sticky=W)

    global SensorName
    SensorName = StringVar()
    SensorName.set(calcon['s_chname'])
    SensorChannelName   = Entry(root, bg='white',textvariable=SensorName).grid(row=6,column=1)
    global SensorSen
    SensorSen = StringVar()
    SensorSen.set(calcon['s_chsen'])
    SensorSensitivity   = Entry(root, bg='white',textvariable=SensorSen).grid(row=6,column=3)
    
    Label(root, text="Laser Channel Name:").grid(row=7,column=0,sticky=E)
    Label(root, text="Sensitivity:").grid(row=7,column=2,sticky=E)
    Label(root, text="uV/cnt", fg='blue').grid(row=7,column=4,sticky=W)

    global LaserName
    LaserName = StringVar()
    LaserName.set(calcon['l_chname'])
    LaserChannelName   = Entry(root, bg='white',textvariable=LaserName).grid(row=7,column=1)
    global LaserSen
    LaserSen = StringVar()
    LaserSen.set(calcon['l_chsen'])
    LaserSensitivity   = Entry(root, bg='white',textvariable=LaserSen).grid(row=7,column=3)

# Setup Laser settings block
    Label(root, text="  LASER POSITION SESNSOR").grid(row=8,column=0,pady=5,sticky=W)
    Label(root, text="Resolution:").grid(row=9,column=0,sticky=E)
    Label(root, text="Cal Constant:").grid(row=10,column=0,sticky=E)
    Label(root, text="V/mm", fg='blue').grid(row=9,column=2,sticky=W)
    Label(root, text="Pendulum Ratio", fg='blue').grid(row=10,column=2,sticky=W)

    global LaserReso
    LaserReso = StringVar()
    LaserReso.set(calcon['l_sen'])
    LaserResolution = Entry(root, bg='white',textvariable=LaserReso).grid(row=9,column=1)
    global LaserCal
    LaserCal = StringVar()
    LaserCal.set(calcon['l_calconst'])
    LaserCalConstant = Entry(root, bg='white',textvariable=LaserCal).grid(row=10,column=1)
    
#Setup Free Period file dialog and action buttons
    Label(root, text="  FREE PERIOD MEASUREMENT").grid(row=11, column=0,pady=5,sticky=W)
    Label(root, text="Data File:").grid(row=12,column=0,sticky=E)

    global FreeFile
    FreeFile = StringVar()
    FreeFile.set(calcon['free_period_source'])
    
    global FreeValue
    FreeValue = StringVar()
    FreeValue.set(calcon['free_period']) 

    FreePeriodFileEntry = Entry(root, bg='white',textvariable=FreeFile).grid(row=12, column=1, columnspan=6,sticky=W+E)
    FreePeriodBrowse = Button(root, text=' BROWSE ', command=lambda: BrowsePeriodFile(root,FreeFile,DefaultDir)).grid(row=12,column=7,padx=5,sticky=W+E)
    FreePeriodView   = Button(root, text='  VIEW  ', command=lambda: ViewPeriod(calcon['free_period_source'])).grid(row=13,column=7,padx=5,sticky=W+E)

    FreePeriodCalc   = Button(root, text=' CALCULATE',command=lambda: CalcFreePeriod(calcon,FreeFile,FreeValue)).grid(row=13, column=1,pady=3)

    Label(root, text='Value:').grid(row=14,column=0,sticky=E)
    FreePeriod = Entry(root, bg = 'white', fg='red',textvariable=FreeValue).grid(row=14,column=1,sticky=W)
    Label(root, text='Hz',fg='blue').grid(row=14,column=2,sticky=W)

#Setup Dampening File Selection
    Label(root, text="  DAMPING RATIO (h)").grid(row=15, column=0,pady=5,sticky=W)
    Label(root, text="Data File:").grid(row=16,column=0,sticky=E)
    global DampingFile
    DampingFile = StringVar()
    DampingFile.set(calcon['damping_ratio_source'])
    global DampingValue
    DampingValue = StringVar()
    DampingValue.set(calcon['damping_ratio'])
    
    DampingFileEntry = Entry(root, bg='white',textvariable=DampingFile).grid(row=16, column=1, columnspan=6,sticky=W+E)
    DampingBrowse = Button(root, text=' BROWSE ', command=lambda: BrowseDampingFile(root,DampingFile,DefaultDir)).grid(row=16,column=7,padx=5,sticky=W+E)
    DampingView   = Button(root, text='  VIEW  ', command=lambda: ViewPeriod(calcon['damping_ratio_source'])).grid(row=17,column=7,padx=5,sticky=W+E)
    
    DampingCalc   = Button(root, text=' CALCULATE', command=lambda: CalcDampingRatio(calcon,DampingFile,DampingValue)).grid(row=17, column=1,pady=3)

    Label(root, text="Value:").grid(row=18,column=0,sticky=E)
    DampingRatio = Entry(root, bg='white', fg='red',textvariable=DampingValue).grid(row=18,column=1,sticky=W)


#Select Data Format
    Label(root, text="  SELECT DATA FORMAT").grid(row=19, column=0,pady=5,sticky=W)
    global DataFormat
    DataFormat = StringVar()
    DataFormat.set("SAC")
    Radiobutton(root, text="CSS", variable=DataFormat, value='CSS').grid(row=20,column=1,sticky=W)
    Radiobutton(root, text="SAC", variable=DataFormat, value='SAC').grid(row=21,column=1,sticky=W)
    Radiobutton(root, text="MSEED", variable=DataFormat, value='MSEED').grid(row=22,column=1,sticky=W)
    Label(root, text="  ").grid(row=23,column=0)

#SigCal Process Button Setup
    SigCalButton = Button(root,text=' PROCESS SIGCAL',command=lambda: CallSigCal(root,calcon)).grid(row=24,column=1,pady=7)
#SigCalButton.config(state=NORMAL)


# Preload calcontrol file if exists
#SigCalButton.config(state=DISABLED)

  #  xxx = tkFileDialog.askopenfilename(parent=root,initialdir=calcon['target_dir'])

    root.mainloop()

main()