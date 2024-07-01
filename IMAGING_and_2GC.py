#
# Hans-Rainer Kloeckner
#
# MPIfR 2024
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
# Start the singularity (important with bind)
#
# singularity exec --bind ${PWD}:/data CONTAINER.simg python /data/Self_calibration_2GC.py
#
# ============================================
# ============================================
# ============================================
#
#
# History:
#    08/23: changed the input parameters of the imaging
#    08/23: changed the way the information is extracted 
#           out of the pybdsf log file 
#    03/24: changed input structure and limitations
#           use json file for inout
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
#
from optparse import OptionParser


def main():

    # argument parsing
    #
    usage = "usage: %prog [options]"
    parser = OptionParser(usage=usage)


    parser.add_option('--MS_FILE', dest='msfile', type=str,
                      help='MS - file name e.g. 1491291289.1ghz.1.1ghz.4hrs.ms')

    parser.add_option('--WORK_DIR', dest='cwd', default='',type=str,
                      help='Points to the working directory (e.g. useful for containers)')

    parser.add_option('--IMAGING_DEFAULT_FILE', dest='iminputjson',default='IMAGING_2GC_DEFAULTS.json',type=str,
                      help='Input imaging default file name in JSON format [default: IMAGING_2GC_DEFAULTS.json].')

    parser.add_option('--IMAG_PARA_DATACOLUMN', dest='datacol', default='DATA', type=str,
                      help='Data column for imaging [default: DATA] also possible CORRECTED_DATA')

    parser.add_option('--IMAG_PARA_IMSTOKES', dest='imstokes', default='I', type=str,
                      help='Stokes output image [default I]')

    parser.add_option('--IMAG_PARA_IMSIZE', dest='imsize', default=8192, type=int,
                      help='imsize in pixel [default 8192 pixel]')

    parser.add_option('--IMAG_PARA_SCALE', dest='imscale', default=1, type=float,
                      help='scale in arcsec [default: 1]')

    parser.add_option('--IMAG_PARA_ROBUST', dest='robust', default=-0.5, type=float,
                      help='robust weighting [default -0.5]')

    parser.add_option('--IMAG_PARA_NITER', dest='imniter', default=1, type=int,
                      help='niter parameter for cleaning [default 1]')

    parser.add_option('--IMAG_PARA_GAIN', dest='imagegain', default=0.1, type=float,
                      help='clean gain parameter [default 0.1]')

    parser.add_option('--IMAG_PARA_THRESHOLD', dest='imthreshold', default=1E-6, type=float,
                      help='threshold parameter for cleaning [default 1E-6]')

    parser.add_option('--IMAG_PARA_SPWDS', dest='imspwds', default='0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15', type=str,
                      help='default \'0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15\'')

    parser.add_option('--DOSELFCAL', dest='do_selfcal', action='store_true', default=False,
                      help='switch to include 2GC self-calibration. [default no self-calibration]')

    parser.add_option('--DOIMAGING', dest='do_imaging', action='store_false', default=True,
                      help='switch to exclude final imaging. [default do final imaging]')

    parser.add_option('--DODELMAKSIMAGES', dest='dodelmaskimages', action='store_false', default=True,
                      help='delete mask images for LSM modeling. [default delete them]')

    # ----

    (opts, args)         = parser.parse_args()

    if opts.msfile == None:
        parser.print_help()
        sys.exit()


    # set the parmaters
    #
    homedir         = opts.cwd
    MSFILE          = opts.msfile
    #
    imstokes        = opts.imstokes

    imniter         = opts.imniter
    imagegain       = opts.imagegain

    imthreshold     = opts.imthreshold

    imsize          = opts.imsize
    weighting       = opts.robust
    bin_size        = opts.imscale
    spwds           = opts.imspwds
    datacol         = opts.datacol


    iminputjson     = opts.iminputjson

    do_selfcal      = opts.do_selfcal
    do_imaging      = opts.do_imaging
    dodelmaskimages = opts.dodelmaskimages    






    # =========================================
    # paramter pre-definition
    #
    selfcal_add_wsclean_command      = {} 
    finalimaging_add_wsclean_command = {} 
    #
    outname             = 'FINAL_SC_IMAGE'
    fim_imagedir_ext    = ''

    # =========================================


    print('\n Use home dir: ',homedir)
    print('\n Use MS file: ',MSFILE,'\n')
    #
    #
    # ===========================

    # ===========================
    #
    # Possible input into the IMAGING_2GC_DEFAULTS.json file
    #
    #
    # ADD_SELFCAL_WSCLEAN_COMMAND 
    #        wsclean_para
    #
    # "-fit-spectral-pol": 4
    # ===========================



    # ============================================================================================================
    # ============================================================================================================
    # ============================================================================================================



    # ============================================================================================================
    #  DO NOT EDIT BOYOND UNLESS YOU KNOW WHAT YOU ARE DOING
    # ============================================================================================================

    selfcal_information  = {}

    # Get the source_name
    source_name          = list(C2GC.get_some_info(MSFILE,homedir))[0]

    # === define the default imaging parameter
    #
    # Get the default imaging parameter 
    #
    default_imaging_para = C2GC.get_json(iminputjson,homedir+'2GC/')['IMAGING_DEFAULT']['wsclean_para']
    #
    # set some specific parameter from the input
    # 
    chan_out             = len(eval(spwds))
    #
    additional_wsclean_para = {}
    additional_wsclean_para['-size ']                 = str(imsize)+' '+str(imsize)
    additional_wsclean_para['-scale']                 = str(bin_size)+'asec'
    additional_wsclean_para['-pol']                   = imstokes
    additional_wsclean_para['-channels-out']          = str(chan_out) 
    additional_wsclean_para['-spws']                  = str(spwds)
    #
    # combine the defaults 
    #
    default_wsclean_para = C2GC.concat_dic(default_imaging_para,additional_wsclean_para)
    #

    # add additional inputs from user
    #
    additional_imaging_para = C2GC.get_json(iminputjson,homedir+'2GC/')['ADD_WSCLEAN_COMMAND']['wsclean_para']
    #
    if len(additional_imaging_para) > 0:
        full_default_wsclean_para = C2GC.concat_dic(default_wsclean_para,additional_imaging_para)
    else:
        full_default_wsclean_para = default_wsclean_para
    # ===

    

    # ============================================================================================================
    # =========  S E L F - C A L I B R A T I O N process starts here 
    # ============================================================================================================
    #
    #
    if do_selfcal: 

        #
        # Get the default selcal parameter from json file 
        #
        default_selfcal_para = C2GC.get_json(iminputjson,homedir+'2GC/')['SELFCAL_PARAMETER'] 
        #
        selfcal_modes        = default_selfcal_para['selfcal_modes']
        selfcal_solint       = default_selfcal_para['selfcal_solint']
        selfcal_threshold    = default_selfcal_para['selfcal_threshold']
        selfcal_weighting    = default_selfcal_para['selfcal_weighting']

        selfcal_uvrange      = default_selfcal_para['uvrange']
        selfcal_refant       = default_selfcal_para['ref_ant']

        # Enlarge some of the self-calibration input 
        #
        selfcal_data         = C2GC.enlarge_selcal_input(selfcal_modes,default_selfcal_para['selfcal_data'])
        selfcal_interp       = C2GC.enlarge_selcal_input(selfcal_modes,default_selfcal_para['selfcal_interp'])
        selfcal_niter        = C2GC.enlarge_selcal_input(selfcal_modes,default_selfcal_para['selfcal_niter'])
        selfcal_gain         = C2GC.enlarge_selcal_input(selfcal_modes,default_selfcal_para['selfcal_gain'])
        selfcal_mgain        = C2GC.enlarge_selcal_input(selfcal_modes,default_selfcal_para['selfcal_mgain'])
        selfcal_usemaskfile  = C2GC.enlarge_selcal_input(selfcal_modes,default_selfcal_para['selfcal_usemaskfile'])

        # being conservative delete the model in the MS dataset
        #
        C2GC.delmodel(MSFILE,homedir)

        
        # Do 2GC self-calibration using CASA and PYBDSF as source finder 
        #
        addgaintable, addinterp = [],[]

        for sc in range(len(selfcal_modes)):

            # bookeeping
            #
            print('Performing selfcalibration step ',sc,' ',selfcal_modes[sc])
            #
            selfcal_information['SC'+str(sc)] = {}
            sc_marker = sc

            # set imaging parameter for masking 
            #
            additional_wsclean_para_ma = {}
            additional_wsclean_para_ma['-weight briggs']            = str(selfcal_weighting)
            additional_wsclean_para_ma['-threshold']                = str(selfcal_threshold)
            additional_wsclean_para_ma['-data-column']              = selfcal_data[sc]
            additional_wsclean_para_ma['-niter']                    = str(selfcal_niter[sc])
            additional_wsclean_para_ma['-gain']                     = str(selfcal_gain[sc])
            additional_wsclean_para_ma['-mgain']                    = str(selfcal_mgain[sc])
            additional_wsclean_para_ma['-no-update-model-required'] = ''
            #
            if chan_out > 1:
                additional_wsclean_para_ma['-join-channels']        = ''
                additional_wsclean_para_ma['-no-mf-weighting']      = ''

            # === 


            # add additional inputs from user
            #
            additional_sc_imaging_para = C2GC.get_json(iminputjson,homedir+'2GC/')['ADD_SELFCAL_WSCLEAN_COMMAND']['wsclean_para']
            #
            if len(additional_sc_imaging_para) > 0:
                f_additional_wsclean_para_ma = C2GC.concat_dic(additional_wsclean_para_ma,additional_sc_imaging_para)
            else:
                f_additional_wsclean_para_ma = additional_wsclean_para_ma
            # ===

            
            # get the full set of imaging parameter
            #
            full_set_of_wsclean_para_ma = C2GC.concat_dic(full_default_wsclean_para,f_additional_wsclean_para_ma)


            # Generates a mask files
            #
            outname                            = 'MKMASK'+str(sc_marker)
            mask_file,tot_flux_model,std_resi  = C2GC.masking(MSFILE,outname,homedir,full_set_of_wsclean_para_ma,sc_marker,dodelmaskimages)

            # here we collect information on the model, the noise etc.
            #
            selfcal_information['SC'+str(sc)]['pybdsf_info_b4_masking'] = [tot_flux_model,std_resi]

            # If needed add a mask to be used instead
            #
            if len(selfcal_usemaskfile[sc]) > 0:
                mask_file = selfcal_usemaskfile[sc]

            selfcal_information['SC'+str(sc)]['MASK'] = mask_file


            # set imaging parameter for model generation
            #
            additional_wsclean_para_sc = {} 
            additional_wsclean_para_sc['-weight briggs']            = str(selfcal_weighting)
            additional_wsclean_para_sc['-threshold']                = str(selfcal_threshold)
            additional_wsclean_para_sc['-data-column']              = selfcal_data[sc]
            additional_wsclean_para_sc['-niter']                    = str(selfcal_niter[sc])
            additional_wsclean_para_sc['-mgain']                    = str(selfcal_mgain[sc])
            additional_wsclean_para_sc['-fits-mask']                = homedir+mask_file

            if chan_out > 1:
                additional_wsclean_para_sc['-join-channels']        = ''
                additional_wsclean_para_sc['-no-mf-weighting']      = ''


            # add additional inputs from user
            #
            additional_sc_imaging_para = C2GC.get_json(iminputjson,homedir+'2GC/')['ADD_SELFCAL_WSCLEAN_COMMAND']['wsclean_para']
            #
            if len(additional_sc_imaging_para) > 0:
                f_additional_wsclean_para_sc = C2GC.concat_dic(additional_wsclean_para_sc,additional_sc_imaging_para)
            else:
                f_additional_wsclean_para_sc = additional_wsclean_para_sc
            
            # get the full set of imaging parameter
            #
            full_set_of_wsclean_para_sc = C2GC.concat_dic(full_default_wsclean_para,f_additional_wsclean_para_sc)

            # ===


            # Add model into the MS file
            #
            outname        = 'MODIM'+str(sc_marker)
            images         = C2GC.make_image(MSFILE,outname,homedir,full_set_of_wsclean_para_sc)

            # determine the stats of the model subtracted image
            #
            if chan_out > 1:
                stats_image    = outname+'-MFS-residual.fits'
            else:
                stats_image    = outname+'-residual.fits'

            selfcal_information['SC'+str(sc)]['Stats'] = C2GC.get_imagestats(stats_image,homedir)

            # provide the entire flux density of the model
            #
            if chan_out > 1:
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
            print('\nStart calibration SC-step ',sc,' mode ',selfcal_modes[sc],'\n')
            
            CALTAB  = 'SC'+str(sc_marker)+'_CALTAB_'+selfcal_modes[sc]

            addgaintable, addinterp = C2GC.calib_data(MSFILE,CALTAB,homedir,selfcal_solint[sc],selfcal_modes[sc],selfcal_refant,selfcal_uvrange,selfcal_interp[sc],addgaintable,addinterp)

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
    if do_imaging: 

        # that for the time being ok, but need source name here
        #
        outname       = 'FINAL_SC_IMAGE_'+source_name


        # Set the imaging parameters
        #
        additional_wsclean_para = {} 
        #
        if do_selfcal:
            additional_wsclean_para['-data-column']              = selfcal_data[-1]
        else:
            additional_wsclean_para['-data-column']              = datacol

        additional_wsclean_para['-weight briggs']            = str(weighting)
        additional_wsclean_para['-niter']                    = str(imniter)
        additional_wsclean_para['-gain']                     = str(imagegain)
        additional_wsclean_para['-threshold']                = str(imthreshold)
        additional_wsclean_para['-no-update-model-required'] = ''
        if chan_out > 1:
            additional_wsclean_para['-join-channels']        = ''
            additional_wsclean_para['-no-mf-weighting']      = ''
        

        # add additional inputs from user
        #
        additional_imaging_para = C2GC.get_json(iminputjson,homedir+'2GC/')['ADD_WSCLEAN_COMMAND']['wsclean_para']
        #
        if len(additional_imaging_para) > 0:
                f_additional_wsclean_para = C2GC.concat_dic(additional_wsclean_para,additional_imaging_para)
        else:
                f_additional_wsclean_para = additional_wsclean_para
            
        # get the full set of imaging parameter
        #
        final_set_of_wsclean_para = C2GC.concat_dic(full_default_wsclean_para,f_additional_wsclean_para)
        # ===


        # produce the final image
        #
        images = C2GC.make_image(MSFILE,outname,homedir,final_set_of_wsclean_para)

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
        if chan_out > 1:
            final_image    = outname+'-MFS-image.fits'
        homedir,pybdsf_dir,pybdsf_log = C2GC.cataloging_fits(final_image,homedir)
        pybdsf_info = C2GC.get_info_from_pybdsflog(pybdsf_log,pybdsf_dir+'/',homedir+'/')

        # collect information on the model, the noise etc.
        #
        selfcal_information['FINALIMAGES']['pybdsf_info'] = pybdsf_info

        # need to clean up the images
        #
        scdir = 'FINAL_'+source_name+'_IMAGES'+fim_imagedir_ext+'/'
        os.mkdir(homedir+scdir)
        get_files = sorted(glob.glob(homedir+outname+'*'),key=os.path.getmtime)
        for im in get_files:
            shutil.move(im,homedir+scdir)


    # ============================================================================================================
    # =========  S A V E  I N F O R M A T I O N 
    # ============================================================================================================
    #
    self_cal_info = 'FINAL_IMAGE_'+source_name+'_SELFCALINFO'+fim_imagedir_ext+'.json'
    if len(self_cal_info) > 0:
        C2GC.save_to_json(selfcal_information,self_cal_info,homedir)

    print('finish !')

if __name__ == "__main__":
    main()
