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
selfcal_add_wsclean_command      = {} 
finalimaging_add_wsclean_command = {} 
# =========================================

# =========================================
#
# File information
#

if len(sys.argv) == 3:
    homedir = sys.argv[1]
    MSFILE  = sys.argv[2]

else:

    #MSFILE = 'J0252-7104_band1_cald.ms'
    MSFILE = 'J0413-8000_band1_cald.ms'
    homedir = '/data/'                  # this is the singularity binding 


print('\n Use home dir: ',homedir)
print('\n Use MS file: ',MSFILE)

#
#
# ===========================


# ===========================
#
# General imaging paramter for the final imaging
#
fim_weighting       = [-2,-1,-0.5,-0.4,-0.3,-0.2,-0.1,0,0.1,0.2,0.3,0.4,0.5,1,2]
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



# ============================================================================================================
# ============================================================================================================
# ============================================================================================================


# ============================================================================================================
#  DO NOT EDIT BOYOND UNLESS YOU KNOW WHAT YOU ARE DOING
# ============================================================================================================

selfcal_information  = {} 

# Get the source_name
source_name   = list(C2GC.get_some_info(MSFILE,homedir))[0]



# ============================================================================================================
# =========  F I N A L  I M A G I N G 
# ============================================================================================================
#
#

# Get the source_name
source_name          = list(get_some_info(MSFILE,homedir))[0]

selfcal_information  = OrderedDict()

for robust in fim_weighting:

    # ============================================================================================================
    # =========   I M A G I N G 
    # ============================================================================================================

    print('Do imaging with robust ',robust)

    # that for the time being ok, but need source name here
    #
    outname       = 'FINAL_R'+str(robust)+'_IMAGE_'+source_name


    # Set the imaging parameters
    #
    additional_wsclean_para = {} #OrderedDict()
    #
    additional_wsclean_para['-weight briggs']            = str(robust)
    #
    additional_wsclean_para['-data-column']              = fim_data
    additional_wsclean_para['-size ']                    = str(fim_imsize)+' '+str(fim_imsize)
    additional_wsclean_para['-scale']                    = str(fim_bin_size)+'asec'
    additional_wsclean_para['-pol']                      = 'I'
    additional_wsclean_para['-niter']                    = str(fim_niter)
    additional_wsclean_para['-mgain']                    = str(fim_mgain)
    additional_wsclean_para['-channels-out']             = str(fim_chan_out) 
    additional_wsclean_para['-spws']                     = fim_spwds 
    additional_wsclean_para['-threshold']                = str(fim_threshold)
    if fim_chan_out > 1:
        additional_wsclean_para['-join-channels']            = ''
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
    get_residual_files = glob.glob(homedir+outname+'*'+'residual.fits')
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
    scdir = 'FINAL_'+str(robust)+'_IMAGES'+fim_imagedir_ext+'/'
    os.mkdir(homedir+scdir)
    get_files = glob.glob(homedir+outname+'*')
    for im in get_files:
        shutil.move(im,homedir+scdir)
     

# ============================================================================================================
# =========  S A V E  I N F O R M A T I O N 
# ============================================================================================================
#
self_cal_info = 'FINAL_'+str(robust)+'_IMAGE_'+source_name+'_INFO'+fim_imagedir_ext+'.json'
if len(self_cal_info) > 0:
    C2GC.save_to_json(selfcal_information,self_cal_info,homedir)

print('finish !')
