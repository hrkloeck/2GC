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
#    08/23: changed the input parameters of the imaging
#    08/23: changed the way the information is extracted 
#           out of the pybdsf log file 
#
#
import os
import sys
import shutil
import glob
import json
import copy
#
import casatasks
import numpy as np
import CAL2GC_lib as C2GC

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
# paramter pre-definition
#
selfcal_add_wsclean_command      = {} #OrderedDict()
finalimaging_add_wsclean_command = {} #OrderedDict()
# =========================================

# =========================================
#
# File information
#

if len(sys.argv) == 3:
    homedir = sys.argv[1]
    MSFILE  = sys.argv[2]

else:

    MSFILE = 'J0252-7104_band1_cald.ms'
    #MSFILE = 'J0413-8000_band1_cald.ms'
    homedir = '/data/'                  # this is the singularity binding 


print('\n Use home dir: ',homedir)
print('\n Use MS file: ',MSFILE)

#
#
# ===========================

# ===========================
#
# Input for the Self-calibration run 
#
#
# General image parameter
#
weighting            = -0.5
imsize               = 8192 
bin_size             = 0.7

# Selfcalib setting
#
refant               = 'm000' # Based on werkzeugkasten
# refant               = 'm061' # use by Sarrvesh
selfcal_modes        = ['p','p','p','ap']
selfcal_solint       = ['120s','60s','10s','180s']
selfcal_interp       = ['linear','linear','linear','linear']
selfcal_niter        = [30000,30000,30000,30000]
selfcal_mgain        = [0.8,0.8,0.8,0.8]
selfcal_data         = ['DATA','CORRECTED_DATA','CORRECTED_DATA','CORRECTED_DATA']
selfcal_usemaskfile  = ['','','','']  # use the mask file determined by hand from previous runs 
selfcal_addcommand   = ['','','','']  # add additional wsclean commands 
selfcal_chan_out     = 16
selfcal_spwds        = '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15'
selfcal_threshold    = 0.000003
#
# selfcal_add_wsclean_command['-fit-spectral-pol'] = '4'
# ===========================



sc_uvrange = '>100m'


# ===========================
#
# General imaging paramter for the final imaging
#
outname             = 'FINAL_SC_IMAGE'
fim_weighting       = -0.5
fim_imsize          = 8192
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
# finalimaging_add_wsclean_command['']
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
        C2GC.apply_calibration(handmsfile,handoutputf,homedir,handfieldid,handgaintable,handinterp)

        # store casa log file to current directory 
        #
        current_casa_log = C2GC.find_CASA_logfile(checkdir='HOME',homedir='')
        if len(current_casa_log) > 0:
            shutil.move(current_casa_log,homedir)    

        # 
        print(handgaintable,' have been applied.')
        sys.exit(-1)
#
# ============================================================================================================
# ============================================================================================================
# ============================================================================================================



def main:

    # ============================================================================================================
    #  DO NOT EDIT BOYOND UNLESS YOU KNOW WHAT YOU ARE DOING
    # ============================================================================================================

    selfcal_information  = {}

    # Get the source_name
    source_name          = list(C2GC.get_some_info(MSFILE,homedir))[0]


    # ============================================================================================================
    # =========  S E L F - C A L I B R A T I O N process starts here 
    # ============================================================================================================
    #
    #
    if do_selfcal: 
        #
        # Check the Self-calib input
        #
        C2GC.make_self_calinput_check(selfcal_modes,selfcal_solint,selfcal_interp,selfcal_niter,selfcal_mgain,selfcal_data,selfcal_usemaskfile,selfcal_addcommand)

        # being conservative delete the model in the MS dataset
        #
        C2GC.delmodel(MSFILE,homedir)

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

            # set imaging parameter for the masking
            #
            additional_wsclean_para_ma = {} #OrderedDict()
            additional_wsclean_para_ma['-data-column']              = selfcal_data[sc]
            additional_wsclean_para_ma['-size ']                    = str(imsize)+' '+str(imsize)
            additional_wsclean_para_ma['-scale']                    = str(bin_size)+'asec'
            additional_wsclean_para_ma['-pol']                      = 'I'
            additional_wsclean_para_ma['-weight briggs']            = str(weighting)
            additional_wsclean_para_ma['-niter']                    = str(selfcal_niter[sc])
            additional_wsclean_para_ma['-mgain']                    = str(selfcal_mgain[sc])
            additional_wsclean_para_ma['-channels-out']             = str(selfcal_chan_out) 
            additional_wsclean_para_ma['-spws']                     = str(selfcal_spwds) 
            additional_wsclean_para_ma['-threshold']                = str(selfcal_threshold)
            additional_wsclean_para_ma['-no-update-model-required'] = ''

            if selfcal_chan_out > 1:
                additional_wsclean_para_ma['-join-channels']        = ''
                additional_wsclean_para_ma['-no-mf-weighting']      = ''



            # get the full set of imaging parameter
            #
            default_imaging_para        = C2GC.get_wsclean_para()
            full_set_of_wsclean_para_ma = C2GC.concat_dic(default_imaging_para,additional_wsclean_para_ma)


            # Generates a mask file
            #
            outname     = 'MKMASK'+str(sc_marker)
            mask_file,tot_flux_model,std_resi  = C2GC.masking(MSFILE,outname,homedir,full_set_of_wsclean_para_ma,sc_marker,dodelmaskimages)


            # here we collect information on the model, the noise etc.
            #
            selfcal_information['SC'+str(sc)]['pybdsf_info'] = [tot_flux_model,std_resi]

            # If needed add a mask to be used instead
            #
            if len(selfcal_usemaskfile[sc]) > 0:
                mask_file = selfcal_usemaskfile[sc]

            selfcal_information['SC'+str(sc)]['MASK'] = mask_file


            # set imaging parameter for model generation
            #
            additional_wsclean_para_sc = {} #OrderedDict()
            additional_wsclean_para_sc['-data-column']              = selfcal_data[sc]
            additional_wsclean_para_sc['-size ']                    = str(imsize)+' '+str(imsize)
            additional_wsclean_para_sc['-scale']                    = str(bin_size)+'asec'
            additional_wsclean_para_sc['-pol']                      = 'I'
            additional_wsclean_para_sc['-weight briggs']            = str(weighting)
            additional_wsclean_para_sc['-niter']                    = str(selfcal_niter[sc])
            additional_wsclean_para_sc['-mgain']                    = str(selfcal_mgain[sc])
            additional_wsclean_para_sc['-channels-out']             = str(selfcal_chan_out) 
            additional_wsclean_para_sc['-spws']                     = str(selfcal_spwds) 
            additional_wsclean_para_sc['-threshold']                = str(selfcal_threshold)
            if selfcal_chan_out > 1:
                additional_wsclean_para_sc['-join-channels']        = ''
                additional_wsclean_para_sc['-no-mf-weighting']      = ''


            additional_wsclean_para_sc['-fits-mask']                = homedir+mask_file

            if len(selfcal_add_wsclean_command.keys()) > 0:
                additional_wsclean_para_sc = C2GC.concat_dic(additional_wsclean_para_sc,selfcal_add_wsclean_command)

            # get the full set of imaging parameter
            #
            default_imaging_para        = C2GC.get_wsclean_para()
            full_set_of_wsclean_para_sc = C2GC.concat_dic(default_imaging_para,additional_wsclean_para_sc)

            # Add model into the MS file
            #
            outname        = 'MODIM'+str(sc_marker)
            images         = C2GC.make_image(MSFILE,outname,homedir,full_set_of_wsclean_para_sc)

            # determine the stats of the model subtracted image
            #
            if selfcal_chan_out > 1:
                stats_image    = outname+'-MFS-residual.fits'
            else:
                stats_image    = outname+'-residual.fits'

            selfcal_information['SC'+str(sc)]['Stats'] = C2GC.get_imagestats(stats_image,homedir)

            # provide the entire flux density of the model
            #
            if selfcal_chan_out > 1:
                stats_image    = outname+'-MFS-model.fits'
            else:
                stats_image    = outname+'-model.fits'

            selfcal_information['SC'+str(sc)]['Model'] = [C2GC.sum_imageflux(stats_image,homedir,threshold=0)]

            # need to clean up the images
            #
            scdir = 'SC_'+str(sc_marker)+'_MODEL'+'/'
            os.mkdir(homedir+scdir)
            get_files = sorted(glob.glob(homedir+outname+'*'),key=os.path.getmtime)
            for im in get_files:
                shutil.move(im,homedir+scdir)


            # Generates a calibration table
            #
            print('Start calibration SC-step ',sc,' mode ',selfcal_modes[sc])

            CALTAB  = 'SC'+str(sc_marker)+'_CALTAB_'+selfcal_modes[sc]

            addgaintable, addinterp = C2GC.calib_data(MSFILE,CALTAB,homedir,selfcal_solint[sc],selfcal_modes[sc],refant,sc_uvrange,selfcal_interp[sc],addgaintable,addinterp)

            # store calibrations to account for
            # the individual calibration steps 
            # to be applied 
            #
            selfcal_information['SC'+str(sc)]['calip_setting'] = [selfcal_niter[sc],selfcal_data[sc],selfcal_mgain[sc],selfcal_solint[sc],selfcal_modes[sc]]
            selfcal_information['SC'+str(sc)]['calip_inter']   = [copy.copy(addgaintable),copy.copy(addinterp)]


            # produce bsl shadems images
            #    
            if selfcal_modes[sc] == 'p':
                figurename = 'SC'+str(sc_marker)+'_CALCHECK_'+selfcal_modes[sc]
                plotype = 'phase'
                pltfiles = C2GC.plot_check_cal(MSFILE,homedir,plotype,figurename)
                #
                # move the images
                for im in pltfiles:
                    shutil.move(im,homedir+scdir)

            if selfcal_modes[sc] == 'ap':
                figurename = 'SC'+str(sc_marker)+'_CALCHECK_'+selfcal_modes[sc]
                plotype = 'phase'
                pltfiles = C2GC.plot_check_cal(MSFILE,homedir,plotype,figurename)
                #
                figurename = 'SC'+str(sc_marker)+'_CALCHECK_'+selfcal_modes[sc]
                plotype = 'amp'
                pltfiles = C2GC.plot_check_cal(MSFILE,homedir,plotype,figurename)
                # move the images
                for im in pltfiles:
                    shutil.move(im,homedir+scdir)


            # being conservative delete the model in the MS dataset
            #
            C2GC.delmodel(MSFILE,homedir)

        # store casa log file to current directory 
        #
        current_casa_log = C2GC.find_CASA_logfile(checkdir='HOME',homedir='')
        if len(current_casa_log) > 0:
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


        # Set the imaging parameters
        #
        additional_wsclean_para = {} #OrderedDict()
        #
        additional_wsclean_para['-data-column']              = fim_data
        additional_wsclean_para['-size ']                    = str(fim_imsize)+' '+str(fim_imsize)
        additional_wsclean_para['-scale']                    = str(fim_bin_size)+'asec'
        additional_wsclean_para['-pol']                      = 'I'
        additional_wsclean_para['-weight briggs']            = str(fim_weighting)
        additional_wsclean_para['-niter']                    = str(fim_niter)
        additional_wsclean_para['-mgain']                    = str(fim_mgain)
        additional_wsclean_para['-channels-out']             = str(fim_chan_out) 
        additional_wsclean_para['-spws']                     = fim_spwds 
        additional_wsclean_para['-threshold']                = str(fim_threshold)
        if fim_chan_out > 1:
            additional_wsclean_para['-join-channels']        = ''
            additional_wsclean_para['-no-mf-weighting']      = ''

        additional_wsclean_para['-no-update-model-required'] = ''
        #

        if len(finalimaging_add_wsclean_command.keys()) > 0:
                additional_wsclean_para = C2GC.concat_dic(additional_wsclean_para,finalimaging_add_wsclean_command)

        # get the full set of imaging parameter
        #
        default_imaging_para        = C2GC.get_wsclean_para()
        full_set_of_wsclean_para    = C2GC.concat_dic(default_imaging_para,additional_wsclean_para)

        # produce the final image
        #
        images = C2GC.make_image(MSFILE,outname,homedir,full_set_of_wsclean_para)

        # get stats 
        #
        get_residual_files = sorted(glob.glob(homedir+outname+'*'+'residual.fits'),key=os.path.getmtime)
        selfcal_information['FINALIMAGES'] = {}
        #
        for rsidat in get_residual_files:
            resi_file_name = rsidat.replace(homedir,'')
            file_key       = 'Stats_'+rsidat.replace(homedir,'').replace(outname,'').replace('residual.fits','').replace('-','')
            selfcal_information['FINALIMAGES'][file_key] = C2GC.get_imagestats(resi_file_name,homedir)

        # run cataloger and source finding
        #
        if fim_chan_out > 1:
            final_image    = outname+'-MFS-image.fits'
        homedir,pybdsf_dir,pybdsf_log = C2GC.cataloging_fits(final_image,homedir)
        pybdsf_info = C2GC.get_info_from_pybdsflog(pybdsf_log,pybdsf_dir+'/',homedir+'/')

        # collect information on the model, the noise etc.
        #
        selfcal_information['FINALIMAGES']['pybdsf_info'] = pybdsf_info

        # need to clean up the images
        #
        scdir = 'FINAL_SC'+str(len(selfcal_modes))+'_IMAGES'+fim_imagedir_ext+'/'
        os.mkdir(homedir+scdir)
        get_files = sorted(glob.glob(homedir+outname+'*'),key=os.path.getmtime)
        for im in get_files:
            shutil.move(im,homedir+scdir)


    # ============================================================================================================
    # =========  S A V E  I N F O R M A T I O N 
    # ============================================================================================================
    #
    self_cal_info = 'FINAL_SC_IMAGE_'+source_name+'_SELFCALINFO'+fim_imagedir_ext+'.json'
    if len(self_cal_info) > 0:
        C2GC.save_to_json(selfcal_information,self_cal_info,homedir)

    print('finish !')
