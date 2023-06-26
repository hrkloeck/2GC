#
# Hans-Rainer Kloeckner
#
# MPIfR 2023
# hrk@mpifr-bonn.mpg.de
#
# 
# 
# - imaging is done with wsclean any information can be found via
#
#     https://wsclean.readthedocs.io/en/latest/usage.html
#
# - calibration is done with CASA task gaincal and applycal any information via
#    
#    https://casa.nrao.edu/docs/taskref/gaincal-task.html
# 
# -  good source for plots and explanation of CASA handling 
#   
#    https://www.jb.man.ac.uk/DARA/ERIS22/3C277_full.html
#
#
# History:
#
#
#
#
import os
import sys
import shutil
import glob
import json
#
import casatasks
import numpy as np
from CAL2GC_lib import *

# ============================================
# ============================================
# ============================================
#
# How to run the self-calibration 
#
# 1. Prepare the working directory
#
#    git clone https://github.com/JonahDW/Image-processing.git
#    git clone https://github.com/hrkloeck/DASKMSWERKZEUGKASTEN.git
#    git clone https://github.com/hrkloeck/2GC.git
# 
# 2. copy the script  cp 2GC/*py .
#
# 3. copy your MS file into the directory
#
# 4. Edit the Self_calibration_2GC.py file      # THIS WILL CHANGE IN THE FUTURE
#
# Start the singularity (important with bind)
#
# singularity exec --bind ${PWD}:/data CONTAINER.simg python /data/Self_calibration_2GC.py
#
# =========================================


# File information
#
#MSFILE  = 'J0408-6545_cal.ms'
MSFILE = 'J0252-7104_cal.ms'
#MSFILE = 'Deep2pcal.ms'
#
homedir = '/data/'                  # this is the singularity binding 
#
# ===========================

#
# Input for the Self-calibration run 
#

# Generate image parameter
#
weighting            = -0.5
imsize               = 1024
bin_size             = 0.7
# refant               = 'm061' # use by Sarrvesh
refant               = 'm029' # Based on werkzeugkasten

# Selfcalib setting
#
selfcal_modes        = ['p','p','p','ap']
selfcal_solint       = ['120s','60s','10s','180s']
selfcal_interp       = ['linear','linear','linear','linear']
selfcal_niter        = [30000,30000,30000,30000]
selfcal_mgain        = [0.8,0.8,0.8,0.8]
selfcal_data         = ['DATA','CORRECTED_DATA','CORRECTED_DATA','CORRECTED_DATA']
selfcal_usemaskfile  = ['','','','']  # use the mask file determined by hand from previous runs 
selfcal_addcommand   = ['','','','']  # add additional wsclean commands 
#
# ===========================

#
# Input for the final imaging
#
outname             = 'FINAL_SC_IMAGE'
fim_weighting       = -0.5
fim_imsize          = 1024
fim_bin_size        = 0.7
#
fim_niter           = 300000
fim_data            = 'CORRECTED_DATA'
fim_mgain           = 0.8
fim_chan_out        = 16
fim_spwds           = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15'
fim_threshold       = 0.000003
fim_imagedir_ext    = ''             # additional extension of the final directory 
#
# ===========================

# ===========================
#
# do the steering
#

# swith the self-calibration
#
do_selfcal      = True

# swith the final imaging
#
dofinal_image   = True

# cleaning up 
#
dodelmaskimages = True   # If True, deletes the images from which the mask has been produced
#
# ===========================

# ============================================================================================================
# ============================================================================================================
# ============================================================================================================


# ============================================================================================================
# =========  NEED TO APPLY A CALTABLE BEFORE THE SELFCAL DO BY HAND !!!
# ============================================================================================================
#
doapply_precal = False
#
if doapply_precal: 
    handmsfile    = ''
    handoutputf   = 'Deep2pcal.ms'
    handgaintable = ['/data/SC0_CALTAB_p','/data/SC1_CALTAB_p','/data/SC2_CALTAB_p','/data/SC3_CALTAB_p','/data/SC4_CALTAB_ap',]
    handinterp    = ['linear','linear','linear','linear','linear']
    handfieldid   = '0'
    if len(handgaintable) > 0 and len(handmsfile) > 0:
        apply_calibration(handmsfile,handoutputf,homedir,handfieldid,handgaintable,handinterp)

        # store casa log file to current directory 
        #
        current_casa_log = find_CASA_logfile(checkdir='HOME',homdir='')
        shutil.move(current_casa_log,homedir)    

        # 
        print(handgaintable,' have been applied.')
        sys.exit(-1)
#
# ============================================================================================================
# ============================================================================================================
# ============================================================================================================




# ============================================================================================================
#  DO NOT EDIT BOYOND UNLESS YOU KNOW WHAT YOU ARE DOING
# ============================================================================================================

selfcal_information  = {}

# Get the source_name
source_name   = list(get_some_info(MSFILE,homedir))[0]

# ============================================================================================================
# =========  S E L F - C A L I B R A T I O N process starts here 
# ============================================================================================================
#
#
if do_selfcal: 
    #
    # Check the Self-calib input
    #
    make_self_calinput_check(selfcal_modes,selfcal_solint,selfcal_interp,selfcal_niter,selfcal_mgain,selfcal_data,selfcal_usemaskfile,selfcal_addcommand)

    # being conservative delete the model in the MS dataset
    #
    delmodel(MSFILE,homedir)

    # essential for applying calibration in CASA
    #
    addgaintable, addinterp = [],[]

    for sc in range(len(selfcal_modes)):

        # bookeeping
        #
        print('Performing selfcalibration step ',sc,' ',selfcal_modes[sc])
        #
        selfcal_information['SC'+str(sc)] = {}
        sc_marker = sc

        # Generates a mask file
        #
        outname     = 'MKMASK'+str(sc_marker)
        mask_file,tot_flux_model,std_resi  = masking(MSFILE,outname,homedir,weighting,imsize,bin_size,selfcal_niter[sc],selfcal_data[sc],selfcal_mgain[sc],sc_marker,dodelmaskimages)

        # here we collect information on the model, the noise etc.
        #
        selfcal_information['SC'+str(sc)]['pybdfs_info'] = [tot_flux_model,std_resi]

        # If needed add a mask to be used instead
        #
        if len(selfcal_usemaskfile[sc]) > 0:
            mask_file = selfcal_usemaskfile[sc]

        selfcal_information['SC'+str(sc)]['MASK'] = mask_file

        # Add model into the MS file
        #
        outname        = 'MODIM'+str(sc_marker)
        images         = make_image(MSFILE,outname,homedir,weighting,imsize,bin_size,selfcal_niter[sc],selfcal_data[sc],selfcal_mgain[sc],chan_out=-1,spwds=-1,threshold=-1,maskfile=mask_file,updatemodel=True,add_command='')

        # determine the stats of the model subtracted image
        #
        stats_image    = outname+'-MFS-residual.fits'
        selfcal_information['SC'+str(sc)]['Stats'] = get_imagestats(stats_image,homedir)

        # provide the entire flux density of the model
        #
        stats_image    = outname+'-MFS-model.fits'
        selfcal_information['SC'+str(sc)]['Model'] = [sum_imageflux(stats_image,homedir,threshold=0)]

        # need to clean up the images
        #
        scdir = 'SC_'+str(sc_marker)+'_MODEL'+'/'
        os.mkdir(homedir+scdir)
        get_files = glob.glob(homedir+outname+'*')
        for im in get_files:
            shutil.move(im,homedir+scdir)


        # Generates a calibration table
        #
        print('Start calibration SC-step ',sc,' mode ',selfcal_modes[sc])

        CALTAB  = 'SC'+str(sc_marker)+'_CALTAB_'+selfcal_modes[sc]

        addgaintable, addinterp = calib_data(MSFILE,CALTAB,homedir,selfcal_solint[sc],selfcal_modes[sc],refant,selfcal_interp[sc],addgaintable,addinterp)

        # store calibrations to account for
        # the individual calibration steps 
        # to be applied 
        #

        #print(addgaintable, addinterp)

        selfcal_information['SC'+str(sc)]['calip_setting'] = [selfcal_niter[sc],selfcal_data[sc],selfcal_mgain[sc],selfcal_solint[sc],selfcal_modes[sc]]

        selfcal_information['SC'+str(sc)]['calip_inter']   = [addgaintable,addinterp]


        # produce bsl shadems images
        #    
        if selfcal_modes[sc] == 'p':
            figurename = 'SC'+str(sc_marker)+'_CALCHECK_'+selfcal_modes[sc]
            plotype = 'phase'
            pltfiles = plot_check_cal(MSFILE,homedir,plotype,figurename)
            #
            # move the images
            for im in pltfiles:
                shutil.move(im,homedir+scdir)

        if selfcal_modes[sc] == 'ap':
            figurename = 'SC'+str(sc_marker)+'_CALCHECK_'+selfcal_modes[sc]
            plotype = 'phase'
            pltfiles = plot_check_cal(MSFILE,homedir,plotype,figurename)
            #
            figurename = 'SC'+str(sc_marker)+'_CALCHECK_'+selfcal_modes[sc]
            plotype = 'amp'
            pltfiles = plot_check_cal(MSFILE,homedir,plotype,figurename)
            # move the images
            for im in pltfiles:
                shutil.move(im,homedir+scdir)


        # being conservative delete the model in the MS dataset
        #
        delmodel(MSFILE,homedir)

    # store casa log file to current directory 
    #
    current_casa_log = find_CASA_logfile(checkdir='HOME',homdir='')
    shutil.move(current_casa_log,homedir)    


# ============================================================================================================
# =========  F I N A L  I M A G I N G 
# ============================================================================================================
#
#
if dofinal_image: 

    # that for the time being ok, but need source name here
    #
    outname       = 'FINAL_SC_IMAGE_'+source_name
    #
    # produce the final image
    #
    images        = make_image(MSFILE,outname,homedir,fim_weighting,fim_imsize,fim_bin_size,fim_niter,fim_data,fim_mgain,chan_out=fim_chan_out,spwds=fim_spwds,threshold=fim_threshold,maskfile='',updatemodel=False,add_command='')

    # get stats 
    #
    get_residual_files = glob.glob(homedir+outname+'*'+'residual.fits')
    selfcal_information['FINALIMAGES'] = {}
    #
    for rsidat in get_residual_files:
        resi_file_name = rsidat.replace(homedir,'')
        file_key       = 'Stats_'+rsidat.replace(homedir,'').replace(outname,'').replace('residual.fits','').replace('-','')
        selfcal_information['FINALIMAGES'][file_key] = get_imagestats(resi_file_name,homedir)

    # Generate a source finding
    #
    final_image    = outname+'-MFS-image.fits'
    cata_dir,final_tot_flux_model,final_std_resi  = cataloging_file(final_image,homedir)

    # here we collect information on the model, the noise etc.
    #
    selfcal_information['FINALIMAGES']['pybdfs_info'] = [final_tot_flux_model,final_std_resi]

    # need to clean up the images
    #
    scdir = 'FINAL_SC'+str(len(selfcal_modes))+'_IMAGES'+fim_imagedir_ext+'/'
    os.mkdir(homedir+scdir)
    get_files = glob.glob(homedir+outname+'*')
    for im in get_files:
        shutil.move(im,homedir+scdir)
     

# ============================================================================================================
# =========  S A V E  I N F O R M A T I O N 
# ============================================================================================================
#
self_cal_info = 'FINAL_SC_IMAGE_'+source_name+'_SELFCALINFO'+fim_imagedir_ext+'.json'
if len(self_cal_info) > 0:
    save_to_json(selfcal_information,self_cal_info,homedir)

print('finish !')
