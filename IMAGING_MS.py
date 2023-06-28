#
# Imaging tool using the TClean from Casa
#
# Just as a test to get in band spectral shape images 
#
# Hans-Rainer Kloeckner
# 
# 2023 - MPIfR 
#
#
# singularity exec --bind "$PWD":/data SINGULARITY.simg python /data/IMAGING_MS.py --HELP
#
# 

import os
import sys
import shutil
import glob
import json
from optparse import OptionParser

import casatasks
import numpy as np
from CAL2GC_lib import *


def main():


    # argument parsing
    #
    print('\n== MS Imaging == \n')

    # ----
    parser       = new_argument_parser()
    (opts, args) = parser.parse_args()

    if opts.msfile == None or opts.fits_output_filename == None or opts.help:
        parser.print_help()
        sys.exit()


    # set the parameters
    #
    MSFN           = opts.msfile
    outputfilename = opts.fits_output_filename
    outputtype     = eval(opts.outputtype)
    cleanup        = opts.cleanup
    msinfofile     = opts.msinfofile
    imsize         = opts.imsize
    niter          = opts.niter
    homedir        = opts.homedir
    datacolumn     = opts.datacolumn


    # hard coded for the time being 
    #
    gridder     = 'wproject'          # 'standard'
    deconvolver = 'mtmfs'             # 'hogbom' 
    #gridder     = 'standard'
    #deconvolver = 'hogbom'  

    scales      = [0,2,3,5]
    nterms      = 2
    wprojplanes = 128
    weighting   = 'briggs'
    robust      = -0.5
    bin_size    = '0.7arcsec'
    threshold   = 0.000003
    spw         = '1,2,3,4,5,6,7,8,9,10,11,12,13,14,15' #'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15'
    gain        =  0.8  # 0.1

    field       = '0'

    file_taylor_ext = []
    if nterms > 1:
        for i in range(nterms):
            file_taylor_ext.append('.tt'+str(i))
    else:
        file_taylor_ext = ['']

    # Get the source_name
    source_name   = list(get_some_info(MSFN,homedir))[0]

    # Generate image using the casa tclean imager
    #
    docasatclean = True
    if docasatclean:

        msfile     = homedir + MSFN
        outputfile = homedir + outputfilename

        try:
            casatasks.tclean(vis=msfile,imagename=outputfile,field=field,selectdata=True,specmode='mfs',spw=spw,nterms=nterms,\
                                 deconvolver=deconvolver,scales=scales,datacolumn=datacolumn,gridder=gridder,imsize=imsize,cell=bin_size,\
                                 wprojplanes=wprojplanes,weighting=weighting,robust=robust,niter=niter,gain=gain,threshold=threshold,interactive=False,savemodel='none')

        except RuntimeError as exc:
            print(' * Got exception: {}'.format(exc))

        for outtyp in outputtype:
            for tt in file_taylor_ext:
                casatasks.exportfits(imagename=outputfile+'.'+outtyp+tt,fitsimage=outputfile+'_'+outtyp+tt+'.fits',history=False)



    imaging_information  = {}

    # Generate a source finding
    #
    final_image    = outputfilename+'_image'+file_taylor_ext[0]+'.fits'
    cata_dir,final_tot_flux_model,final_std_resi  = cataloging_file(final_image,homedir)

    # here we collect information on the model, the noise etc.
    #
    imaging_information['FINALIMAGE'] = {}
    imaging_information['FINALIMAGE']['pybdfs_info'] = [final_tot_flux_model,final_std_resi]

    # determine the stats of the model subtracted image
    #
    stats_image    = outputfilename+'_residual'+file_taylor_ext[0]+'.fits'
    imaging_information['FINALIMAGE']['Stats_resi'] = get_imagestats(stats_image,homedir)

    # save infomation
    #
    self_cal_info = 'FINAL_IMAGE_'+source_name+'_INFO'+'.json'
    if len(self_cal_info) > 0:
        save_to_json(imaging_information,self_cal_info,homedir)


    # store casa log file to current directory 
    #
    #current_casa_log = find_CASA_logfile(checkdir='HOME',homdir='')
    #shutil.move(current_casa_log,homedir)    


    # delete all produced files except the outfile
    #
    if cleanup:
        #im_file_ext_casa = ['image','mask','model','pb','psf','residual','sumwt']
        im_file_ext_casa = ['mask','model','pb','sumwt*','alpha*','image*','residual*','psf*']
        for imfile in im_file_ext_casa:
            for tt in file_taylor_ext:
                os.system('rm -fr '+homedir+outputfilename+'.'+imfile)


def new_argument_parser():

    #
    # some input for better playing around with the example
    #
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)


    parser.add_option('--MS_FILE', dest='msfile', type=str,
                      help='MS - file name e.g. 1491291289.1ghz.1.1ghz.4hrs.ms')

    parser.add_option('--FITS_OUTPUT_FILENAME', dest='fits_output_filename', type=str,
                      default = 'IMTESTING',help='indicate a Name [default = IMTESTING]')

    parser.add_option('--OUTPUTTYPE', dest='outputtype', type=str,default='["image","residual","psf"]',
                      help='Save the individual output e.g. \'["image","psf","mask","model","pb","residual","sumwt"]\' ')

    parser.add_option('--DATA_TYPE', dest='datacolumn', default='data',type=str,
                      help='which data column to use (e.g corrected) [default data]')

    parser.add_option('--MS_INFO_FILE', dest='msinfofile', type=str,
                      help='MS - information generated by GET_MS_INFO.py ')

    parser.add_option('--IMAGE_SIZE', dest='imsize', type=int, default=512,
                      help='Image size in pixel [default = 512]')

    parser.add_option('--NITER', dest='niter', type=int, default=0,
                      help='Number of clean components [default = 0]')

    parser.add_option('--CLEANOTUP', dest='cleanup', action='store_false',
                      default=True,help='Switch to clear all mask')

    #parser.add_option('--CLEANUP', dest='cleanup', action='store_true',
    #                  default=False,help='Switch to clear all mask')

    parser.add_option('--BINDIR', dest='homedir', default='/data/',
                      help='define the singularity binding directory [default /data/]')

    parser.add_option('--HELP', dest='help', action='store_true',
                      default=False,help='Show info on input')

    return parser




    
if __name__ == "__main__":
    main()
