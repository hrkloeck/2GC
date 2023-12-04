#
# Hans-Rainer Kloeckner
#
# MPIfR 2023
# hrk@mpifr-bonn.mpg.de
#
# ======================
#
#
#
import os
import sys
import shutil
import glob
import json

import casatasks
import numpy as np

from collections import OrderedDict

#
# singularity exec --bind ${PWD}:/data CONTAINER.simg python3 /data/APPLY_CALIB_SPLIT.py
#

# Pupose is to splitt out a file

def apply_calibration(MSFILE,homedir,gaintable=[],interp=[]):
    """
    Apply the calibration and split the data
    """

    # https://casadocs.readthedocs.io/en/v6.2.0/api/tt/casatasks.calibration.applycal.html

    msfile    = MSFILE

    if len(gaintable) > 0:
        # apply all the calibration
        casatasks.applycal(vis=msfile,gaintable=gaintable,interp=interp,parang=False, calwt=False, flagbackup=False)


def split_data(MSFILE,MSOUTPUT,homedir,fieldid,spw):
    """
    split the data
    """

    msfile    = MSFILE
    outmsfile = homedir + MSOUTPUT

    # generates a new dataset with corrected DATA column 
    casatasks.split(vis=msfile,outputvis=outmsfile,keepmms=True,field=fieldid,spw=spw,scan="",antenna="",correlation="",timerange="",intent="",array="",uvrange="",observation="",feed="",datacolumn="corrected",keepflags=True,width=1,timebin="0s",combine="")

    return homedir, MSOUTPUT


def find_CASA_logfile(checkdir='HOME',homedir=''):
    """
    """

    import datetime

    user_home_dir  = os.environ[checkdir]
    casa_log_files = sorted(glob.glob(user_home_dir+'/casa*log'), key=os.path.getmtime)
    latest_logfile = casa_log_files[-1]

    return latest_logfile




def main():

    from optparse import OptionParser

    # argument parsing
    #
    usage = "usage: %prog [options]\
            This programme can be used to apply calibration tables, split the data into a new MS file"

    parser = OptionParser(usage=usage)



    parser.add_option('--MS_FILE', dest='msfile', type=str,
                      help='MS - file name e.g. 1491291289.1ghz.1.1ghz.4hrs.ms')

    parser.add_option('--CAL_TAB', dest='caltab', default='[]', type=str,
                      help='select baselines (e.g. [tab1,tab2])')

    parser.add_option('--CAL_INTERPOL', dest='calinterp', default='[]', type=str,
                      help='select baselines (e.g. [linear])')

    parser.add_option('--DATA_TYPE', dest='datacolumn', default='corrected',type=str,
                          help='which data column to use for split e.g. DATA [default CORRECTED_DATA]')

    parser.add_option('--DOAPPLY', dest='doapply', action='store_true',default=False,
                      help='Apply calibration tabes [default False].')

    parser.add_option('--DOSPLIT', dest='dosplit', action='store_true',default=False,
                      help='Splitt the data into a new file [default False].')

    parser.add_option('--NOFGINFO', dest='fginfo', action='store_false',default=True,
                      help='Provide no CASA FG information [default runs casa, see casa log file].')

    parser.add_option('--SPWD', dest='spwd', default='', type=str,
                      help='Choose which spectral windows to split [default use all].')

    parser.add_option('--FIELDID', dest='fieldid', default=0, type=int,
                      help='Field ID [default 0].')

    parser.add_option('--WORK_DIR', dest='cwd', default='',type=str,
                      help='Points to the working directory if output is produced (e.g. usefull for containers)')

    # ----

    (opts, args)         = parser.parse_args()

     
    if opts.msfile == None:        
        parser.print_help()
        sys.exit()


    # set the parmaters
    #
    MSFILE              = opts.msfile
    data_type           = opts.datacolumn
    caltab              = opts.caltab
    calinterp           = opts.calinterp
    doapply             = opts.doapply
    dosplit             = opts.dosplit
    fieldid             = opts.fieldid
    fginfo              = opts.fginfo
    spwd                = opts.spwd
    cwd                 = opts.cwd        # used to write out information us only for container
    MSOUTPUT            = MSFILE.replace('.ms','_split.ms')


    if doapply:
        print('\n=== Apply calibration ===\n')
        if caltab != '[]' and calinterp != '[]': 
                gaintable  = eval(caltab)
                interp     = eval(calinterp)
                if len(gaintable) != len(interp):
                    print('Caution --CAL_TAB and --CAL_INTERPOL have different size. ',caltab,calinterp)
                    sys.exit(-1)

                print('CASA gaintable input: ',gaintable)
                print('CASA interp input   : ',interp)
                #
                apply_calibration(MSFILE,cwd,gaintable,interp)
        else:
            print('Caution --CAL_TAB and --CAL_INTERPOL not defined. ',caltab,calinterp)


    if dosplit:
        print('\n=== Split Data ===\n')
        if len(spwd) > 0:
            print('\n- SPWD: ',spwd)

        split_homedir, split_MSOUTPUT = split_data(MSFILE,MSOUTPUT,'',fieldid,spwd)
        MSFILE = split_MSOUTPUT
        

    if fginfo:
        print('\n=== Determine FG Information ===\n')

        # provide info about the total flagging of the dataset
        #
        cwdMSFILE = MSFILE
        casatasks.flagdata(vis=cwdMSFILE, mode='summary')
        print('\n- see CASA log file')

    # store casa log file to current directory 
    #
    current_casa_log = find_CASA_logfile(checkdir='HOME',homedir='')
    if len(cwd) > 0:
        shutil.move(current_casa_log,cwd)   
    else:
        cwd  = os.environ['PWD']
        shutil.move(current_casa_log,cwd)           
    #
    # ====================================


if __name__ == "__main__":
    main()

