#!/usr/bin/env python

__author__ = "Daniel Burk <burkdani@msu.edu>"
__version__ = "20160414"
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

import MDTcaldefs


def main():
    calcon = {'s_chname':'SHZ',\
          's_chsen':0.945,\
          'l_chname':'LASER',\
          'l_chsen':0.945,\
          'l_sen':1.00,\
          'l_calconst':0.579,\
          'target_dir':'c:\\seismo\\freeperiod\\',\
          'damping_ratio':0.707, \
          'damping_ratio_source':"C:\\seismo\\damping\\20160414_115959_LM_MSU_SHN.mseed", \
          'free_period':0.880,\
          'free_period_source':"C:\\seismo\\freeperiod\\2014_7_30_14_15_20_491_LM_NE8K_LASER.sac", \
          'file_type':"sac" }    

#    Frequency = MDTcaldefs.freeperiod(calcon)
#    print "Final calculated frequency = {}".format(Frequency)
     damping = MDTcaldefs.dampingratio(calcon)

#
# Check and run the main function here:
#
if __name__ == '__main__':
  main()
