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

#from collections import OrderedDict

#
# LIBS
#


# this class is for json dump
# https://stackoverflow.com/questions/75475315/python-return-json-dumps-got-error-typeerror-object-of-type-int32-is-not-json
# https://docs.python.org/3/library/json.html
#
class NumpyArrayEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        else:
            return super().default(obj)

def save_to_json(data,dodatainfoutput,homedir):
    """
    safe information into a json file
    """

    with open(homedir + dodatainfoutput, 'w') as fout:
        json_dumps_str = json.dumps(data,indent=4,sort_keys=False,separators=(',', ': '),cls=NumpyArrayEncoder)
        print(json_dumps_str, file=fout)
    return homedir + dodatainfoutput



def get_list_index(list,value):
    """
    Still strange that there is not a good function to do that
    """

    indices = [i for i, x in enumerate(list) if x == value]

    return indices



def make_mask(image_fits_file,regionfile,fitsoutput_mask,sc_marker=0,homedir='',delete_ms_images=False):
    """
    generates a mask from an image file
    requires need a region file
    """
    
    casa_image_file     = homedir + image_fits_file.replace('.fits','').replace('.FITS','') +'_ORG.IM'

    image_fits_file     = homedir + image_fits_file

    regionfile          = homedir + regionfile
    
    fitsoutput_filename =  fitsoutput_mask + '_' + str(sc_marker)+'.fits'

    fitsoutput_mask     = homedir + fitsoutput_mask + '_' + str(sc_marker)


    # import a fits image
    casatasks.importfits(fitsimage=image_fits_file,imagename=casa_image_file,whichrep=0,whichhdu=-1,zeroblanks=True,overwrite=False,defaultaxes=False,defaultaxesvalues=[],beam=[])
    
    # generate a mask with the imagea nd a region file
    casatasks.makemask(mode='copy',inpimage=casa_image_file,inpmask=regionfile,output=fitsoutput_mask,overwrite=False,inpfreqs=[],outfreqs=[])

    # export the mask file
    casatasks.exportfits(imagename=fitsoutput_mask,fitsimage=homedir+fitsoutput_filename,velocity=False,optical=False,bitpix=-32,minpix=0,maxpix=-1,overwrite=False,dropstokes=False,stokeslast=True,history=True,dropdeg=False)


    # delete all produced files except the outfile
    #
    if delete_ms_images == True:
        files_to_remove = [casa_image_file,fitsoutput_mask]
        for delfiles in files_to_remove:
            os.system('rm -fr '+delfiles)

    return fitsoutput_filename

def make_region_file(imagename,homedir=''):
    """
    uses pybdsf and Jonah's source finding with mask setup
    """

    # set settings
    #
    filename       = homedir + imagename
    sfinding_dir   = homedir + imagename.replace('.fits','').replace('.FITS','')
    pybdsf_dir     = imagename.replace('.fits','').replace('.FITS','')+'_pybdsf'
    source_finding = 'python ' + homedir + 'Image-processing/sourcefinding.py mask ' + filename + ' -o fits:srl kvis --plot'

    # start the source finding stuff from Jonah
    # using the mask setting
    #
    os.system(source_finding)

    # optain information of the total flux density of the model
    #
    info    = os.popen('grep "Total flux density in model" '+homedir+pybdsf_dir+'/'+imagename+'.pybdsf.log')
    getinfo = info.read().split()
    info.close()
    #idx_jy         = getinfo.index('Jy')
    idx_jy         = get_list_index(getinfo,'Jy')
    tot_flux_model = getinfo[idx_jy[-1]-1]

    # optain information of the total flux density of the model
    #
    stdinfo = os.popen('grep "std. dev:" '+homedir+pybdsf_dir+'/'+imagename+'.pybdsf.log')
    stdgetinfo = stdinfo.read().split()
    stdinfo.close()
    #idx_std  = stdgetinfo.index('(Jy/beam)')
    idx_std        = get_list_index(stdgetinfo,'(Jy/beam)')
    std_resi       = stdgetinfo[idx_std[-1]-1]

    return pybdsf_dir, imagename.replace('.fits','').replace('.FITS','')+'_mask.crtf', eval(tot_flux_model), eval(std_resi)



def cataloging_fits(imagename,homedir=''):
    """
    uses pybdsf and Jonah's source finding to generate a catalouge
    """

    # set settings
    #
    filename       = homedir + imagename
    pybdsf_dir     = imagename.replace('.fits','').replace('.FITS','')+'_pybdsf'
    source_finding = 'python ' + homedir + 'Image-processing/sourcefinding.py cataloging ' + filename + ' -o fits:srl kvis --plot'

    # start the source finding stuff from Jonah
    # using the mask setting
    #
    os.system(source_finding)

    # pybdsf log file
    #
    pybdsf_log = imagename+'.pybdsf.log'

    return homedir,pybdsf_dir,pybdsf_log



def get_info_from_pybdsflog(pybdsf_log,pybdsf_dir='',homedir=''):
    """
    extract information out of the pybdsf log files
    and return a dic with relevant information
    """
    pybdsf_info = {}

    # optain information of the number of sources
    #
    info    = os.popen('grep "Number of sources formed from Gaussians" '+homedir+pybdsf_dir+pybdsf_log)
    ngausgetinfo = info.read().split()
    info.close()
    #
    idx_ng          = get_list_index(ngausgetinfo,'Gaussians')
    tot_num_sources = ngausgetinfo[idx_ng[-1]+2]     # take the last entry
    
    pybdsf_info['nsource'] = eval(tot_num_sources)

    # optain information of the total flux density of the model
    #
    info    = os.popen('grep "Total flux density in model" '+homedir+pybdsf_dir+pybdsf_log)
    jygetinfo = info.read().split()
    info.close()
    #
    idx_jy         = get_list_index(jygetinfo,'Jy')
    tot_flux_model = jygetinfo[idx_jy[-1]-1]     # take the last entry

    pybdsf_info['nsource_flux_jy'] = eval(tot_flux_model)

    # optain information of the final std in the image
    #
    stdinfo = os.popen('grep "std. dev:" '+homedir+pybdsf_dir+pybdsf_log)
    stdgetinfo = stdinfo.read().split()
    stdinfo.close()
    #
    idx_std   = get_list_index(stdgetinfo,'(Jy/beam)')
    std_resi  = stdgetinfo[idx_std[-1]-1]     # take the last entry

    pybdsf_info['residual_image_noise_jy'] = eval(std_resi)


    # optain information of the beam shape 
    #
    beaminfo = os.popen('grep "Beam shape (major, minor, pos angle)" '+homedir+pybdsf_dir+pybdsf_log)
    beamgetinfo = beaminfo.read().split()
    beaminfo.close()
    #
    idx_beam   = get_list_index(beamgetinfo,'degrees')
    bmaj       = eval(str(beamgetinfo[idx_beam[-1]-3]).replace('(','').replace(')','').replace(',',''))
    bmin       = eval(beamgetinfo[idx_beam[-1]-2].replace('(','').replace(')','').replace(',',''))
    PA         = eval(beamgetinfo[idx_beam[-1]-1].replace(')',''))
    #
    pybdsf_info['bmaj_deg'] = bmaj
    pybdsf_info['bmin_deg'] = bmin
    pybdsf_info['PA_deg']   = PA
    

    return pybdsf_info


def make_image(MSFILE,outname,homedir,wsc_para):
    """
    combines the wsclean parameter and start the imaging
    """

    #full_set_of_wsclean_para = concat_dic(get_wsclean_para(),wsc_para)

    wsclean_command = 'wsclean '

    #para_keys = full_set_of_wsclean_para.keys()
    para_keys = wsc_para.keys()

    for k in para_keys:
        #wsclean_command += ' '+ k + ' ' + str(full_set_of_wsclean_para[k])
        wsclean_command += ' '+ k + ' ' + str(wsc_para[k])

    wsclean_command += ' -name '+homedir+outname
    wsclean_command += ' '+homedir+MSFILE

    os.system(wsclean_command)
    
    return glob.glob(homedir+outname+'*fits')


def get_wsclean_para():
    """
    """
    wsclean_para = {} #OrderedDict()
    
    wsclean_para['-j']                     = 14
    wsclean_para['-mem']                   = 75
    wsclean_para['-reorder']               = ''
    wsclean_para['-parallel-reordering']   = 8
    wsclean_para['-parallel-gridding']     = 8
    wsclean_para['-gridder']               = 'wgridder'
    wsclean_para['-weighting-rank-filter'] = 3
    wsclean_para['-auto-mask']             = 3
    wsclean_para['-auto-threshold']        = 0.3

    wkeys = wsclean_para.keys()

    return wsclean_para

def concat_dic(dic_a,dic_b):
    """
    """
    c_dic = {} #OrderedDict()
    
    for w in dic_a.keys():
        c_dic[w] = dic_a[w]

    for w in dic_b.keys():
        c_dic[w] = dic_b[w]
    
    return c_dic


def delmodel(MSFILE,homedir):
    """
    use the casa task do delete the model data
    """
    msfile = homedir + MSFILE
    casatasks.delmod(vis=msfile,otf=True,scr=False)

    return []


def calib_data(MSFILE,CALTAB,homedir,solint,calmode,refant,inter='nearest',addgaintable=[],addinterp=[]):
    """
    calibrates the data and applies it
    """

    msfile = homedir + MSFILE
    caltab = homedir + CALTAB

    #refant  = 'm061'
    myuvrange = '>100m'


    casatasks.gaincal(vis=msfile,uvrange=myuvrange,caltable=caltab,gaintype='T',solnorm=False,solint=solint,refant=refant,\
                          calmode=calmode,combine='',minsnr=3,gaintable=addgaintable,interp=addinterp)

    # optain the calibration sequence
    #
    addgaintable.append(caltab)
    addinterp.append(inter)
    

    # need to check if calib table is produced
    checkiftabpresent = glob.glob(caltab)

    if len(checkiftabpresent) == 0:
        print('Seems that the calibration table has not been proceed',caltab)
        sys.exit(-1)

    casatasks.applycal(vis=msfile,gaintable=addgaintable,interp=addinterp,parang=False, calwt=False, flagbackup=False)

    return addgaintable,addinterp


def apply_calibration(MSFILE,MSOUTPUT,homedir,fieldid,gaintable=[],interp=[]):
    """
    Apply the calibration and split the data
    """

    msfile    = homedir + MSFILE
    outmsfile = homedir + MSOUTPUT

    # apply all the calibration
    casatasks.applycal(vis=msfile,gaintable=gaintable,interp=interp,parang=False, calwt=False, flagbackup=False)

    # generates a new dataset with corrected DATA column 
    casatasks.split(vis=msfile,outputvis=outmsfile,keepmms=True,field=fieldid,spw="",scan="",antenna="",correlation="",timerange="",intent="",array="",uvrange="",observation="",feed="",datacolumn="corrected",keepflags=True,width=1,timebin="0s",combine="")



#def masking_old(MSFILE,outname,homedir,weighting=-0.5,imsize=256,bin_size=0.7,niter=1,data='DATA',mgain=0.8,sc_marker=0,dodelmaskimages=False):
#    """
#    generates a fits image mask
#    """
#
#    # Generate an image via (wsclean)
#    #
#    image_files         = make_image(MSFILE,outname,homedir,weighting,imsize,bin_size,niter,data,mgain,maskfile='',updatemodel=False,add_command='')
#    
#    if len(image_files) > 5:
#        for f in image_files:
#            if f == homedir+outname+'-MFS-image.fits':
#                # indicate image to be used for source finiding
#                MFS_image      = image_files[image_files.index(homedir+outname+'-MFS-image.fits')].replace(homedir,'')
#    else:
#        MFS_image      = image_files[image_files.index(homedir+outname+'-image.fits')].replace(homedir,'')
#
#    # source finding useing Jonah's software and setting (pybdsf)
#    pybdsf_dir,region_file,tot_flux_model,std_resi  = make_region_file(MFS_image,homedir)
#
#    # copy region file 
#    #
#    shutil.copy(homedir+pybdsf_dir+'/'+region_file,homedir)
#
#
#    # generate FITS image mask
#    #
#    delete_ms_images = True
#    fitsoutput_mask  = 'SC'+str(sc_marker)+'_MASK'
#    mask_fits_file   = make_mask(MFS_image,region_file,fitsoutput_mask,sc_marker,homedir,delete_ms_images)
#
#
#    # clean up all the files
#    #
#    scdir = 'SC_'+str(sc_marker)+'_MK'+'/'
#    os.mkdir(homedir+scdir)
#    get_files = glob.glob(homedir+outname+'*')
#    for im in get_files:
#        shutil.move(im,homedir+scdir)
#
#    if dodelmaskimages == True:
#            delimages = 'rm -fr '+homedir+scdir
#            os.system(delimages)
#
#
#    return mask_fits_file,tot_flux_model,std_resi


def masking(MSFILE,outname,homedir,wsclean_para_ma,sc_marker=0,dodelmaskimages=False):
    """
    generates a fits image mask
    """

    # Generate an image via (wsclean)
    #
    image_files         = make_image(MSFILE,outname,homedir,wsclean_para_ma)
    
    if len(image_files) > 5:
        for f in image_files:
            if f == homedir+outname+'-MFS-image.fits':
                # indicate image to be used for source finiding
                MFS_image      = image_files[image_files.index(homedir+outname+'-MFS-image.fits')].replace(homedir,'')
    else:
        MFS_image      = image_files[image_files.index(homedir+outname+'-image.fits')].replace(homedir,'')

    # source finding useing Jonah's software and setting (pybdsf)
    pybdsf_dir,region_file,tot_flux_model,std_resi  = make_region_file(MFS_image,homedir)

    # copy region file 
    #
    shutil.copy(homedir+pybdsf_dir+'/'+region_file,homedir)


    # generate FITS image mask
    #
    delete_ms_images = True
    fitsoutput_mask  = 'SC'+str(sc_marker)+'_MASK'
    mask_fits_file   = make_mask(MFS_image,region_file,fitsoutput_mask,sc_marker,homedir,delete_ms_images)


    # clean up all the files
    #
    scdir = 'SC_'+str(sc_marker)+'_MK'+'/'
    os.mkdir(homedir+scdir)
    get_files = glob.glob(homedir+outname+'*')
    for im in get_files:
        shutil.move(im,homedir+scdir)

    if dodelmaskimages == True:
            delimages = 'rm -fr '+homedir+scdir
            os.system(delimages)


    return mask_fits_file,tot_flux_model,std_resi



def DOESNOTWORK_plot_calsolutions(caltab,homedir,caltype,figurename):
    """
    Cannot mount AppImage, please check your FUSE setup

    """

    import casaplotms


    # good source for plots https://www.jb.man.ac.uk/DARA/ERIS22/3C277_full.html

    figtyp = '.png'   # export format type of the figures [jpg, png, ps, pdf]
    dpi    = -1

    caltable = homedir+caltab

    if caltype == 'p':
        plotfigfile = homedir+figurename+'_phase'+figtyp

        casaplotms.plotms(vis=caltable,xaxis='time',yaxis='amp',gridrows=3,gridcols=2,iteraxis='antenna', coloraxis='spw',xselfscale=True,yselfscale=True,plotfile=plotfigfile,showgui=False, overwrite=False)
        sys.exit(-1)

    if caltype == 'ap':
        plotfigfile = figfile+'_phase'+figtyp
        casatasks.plotcal(caltable=caltable,antenna='0',axis='time',yaxis='phase',interation='antenna',subplot=231,dpi=dpi,showgui=False,plotfile=plotfigfile)
        plotfigfile = figfile+'_amp'+figtyp
        casatasks.plotcal(caltable=caltable,antenna='0',axis='time',yaxis='amp',interation='antenna',subplot=231,dpi=dpi,showgui=False,plotfile=plotfigfile)


def plot_check_cal(MSFILE,homedir,plotype,figurename):
    """
    """
    # plot mean of the corrected data and the model
    shadeit = 'shadems --corr XX,YY --iter-corr -x ANTENNA1 -y ANTENNA2 --cmap coolwarm --aaxis CORRECTED_DATA-MODEL_DATA:'+plotype+' --ared mean --dir '+homedir+' --suffix '+figurename+' '+MSFILE
    os.system(shadeit)
    # plot the std 
    shadeit = 'shadems --corr XX,YY --iter-corr -x ANTENNA1 -y ANTENNA2 --cmap coolwarm --aaxis CORRECTED_DATA-MODEL_DATA:'+plotype+' --ared std --dir '+homedir+' --suffix '+figurename+' '+MSFILE
    os.system(shadeit)

    get_files = glob.glob(homedir+'*'+figurename+'.png')

    return get_files

def get_imagestats(imagename,homedir):
    """
    provide stats information of the image 
    """
    from astropy.io import fits
    
    imageandpath = homedir+imagename
    
    # open the fits file
    #
    hdu_list       = fits.open(imageandpath) 
    im_data        = hdu_list[0].data
    im_data_header = hdu_list[0].header

    return im_data.mean(),im_data.std(),im_data.min(),im_data.max(),im_data_header['BUNIT']


def sum_imageflux(imagename,homedir,threshold=0):
    """
    return the integrated flux above the threshold 
    """
    from astropy.io import fits
    
    imageandpath = homedir+imagename
    
    # open the fits file
    #
    hdu_list       = fits.open(imageandpath) 
    im_data        = hdu_list[0].data
    im_data_header = hdu_list[0].header

    selthreshold = im_data > threshold

    return np.sum(im_data[selthreshold]),im_data_header['BUNIT']



def get_some_info(MSFILE,homedir):
    """
    us the dask werkzeug
    """
    dask_werkzeug_dir = homedir+'DASKMSWERKZEUGKASTEN'

    sys.path.insert(1, dask_werkzeug_dir)

    import DASK_MS_WERKZEUGKASTEN as INFMS

    msfile = homedir + MSFILE

    msource_info  = INFMS.ms_source_info(msfile)

    return msource_info


def find_CASA_logfile(checkdir='HOME',homedir=''):
    """
    """

    import os
    import datetime

    user_home_dir  = os.environ[checkdir]
    casa_log_files = sorted(glob.glob(user_home_dir+'/casa*log'), key=os.path.getmtime)
    if len(casa_log_files) > 0:
        latest_logfile = casa_log_files[-1]
    else:
        latest_logfile = ''

    return latest_logfile


def make_self_calinput_check(selfcal_modes,selfcal_solint,selfcal_interp,selfcal_niter,selfcal_mgain,selfcal_data,selfcal_usemaskfile,selfcal_addcommand):
    """
    check the input of the selfcalibration 
    an error would result in a lot of waisted 
    processing time
    """
    
    sc_length    = len(selfcal_modes)

    sc_settings  = [selfcal_solint,selfcal_interp,selfcal_niter,selfcal_mgain,selfcal_data,selfcal_usemaskfile,selfcal_addcommand]

    bad_settings = []
    for scm in sc_settings:
        if len(scm) != sc_length:
            bad_settings.append(scm)

    
    if len(bad_settings) > 0:
        print('Something in the Self-Calibration setting is not correct, please check: ')
        print(bad_settings)
        sys.exit(-1)


