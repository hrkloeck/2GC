# 2GC

Self-calibration of radio interferometer dataset 

This includes imaging (wsclean), source finding (pybdfs) to generate a local sky model (LSM), 
and calibration (casa task) steps (some phase and a final amplitude calibration). 

The tool also allows to just single image the MS-data set (default).

# Setting up the infrastructure in your directory 

mkdir YOUR_NEW_DIR
copy the MS data file into the directory

git clone https://github.com/JonahDW/Image-processing.git
   
git clone https://github.com/hrkloeck/DASKMSWERKZEUGKASTEN.git

git clone https://github.com/hrkloeck/2GC.git

# Running the self-calibration 

The self-calibration is configured in the IMAGING_2GC_DEFAULTS.json default file in addition to 
some of the imaging parameter of wsclean.


singularity exec --bind ${PWD}:/data CONTAINER.simg python3 /data/2GC/IMAGING_and_2GC.py

```
Usage: IMAGING_and_2GC.py [options]

Options:
  -h, --help            show this help message and exit
  --MS_FILE=MSFILE      MS - file name e.g. 1491291289.1ghz.1.1ghz.4hrs.ms
  --WORK_DIR=CWD        Points to the working directory (e.g. useful for
                        containers)
  --IMAGING_DEFAULT_FILE=IMINPUTJSON
                        Input imaging default file name in JSON format
                        [default: IMAGING_2GC_DEFAULTS.json].
  --IMAG_PARA_DATACOLUMN=DATACOL
                        Data column for imaging [default: DATA] also possible
                        CORRECTED_DATA
  --IMAG_PARA_IMSTOKES=IMSTOKES
                        Stokes output image [default I]
  --IMAG_PARA_IMSIZE=IMSIZE
                        imsize in pixel [default 8192 pixel]
  --IMAG_PARA_SCALE=IMSCALE
                        scale in arcsec [default: 1]
  --IMAG_PARA_ROBUST=ROBUST
                        robust weighting [default -0.5]
  --IMAG_PARA_NITER=IMNITER
                        niter parameter for cleaning [default 1]
  --IMAG_PARA_THRESHOLD=IMTHRESHOLD
                        threshold parameter for cleaning [default 1E-6]
  --IMAG_PARA_SPWDS=IMSPWDS
                        default '0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15'
  --DOSELFCAL           switch to include 2GC self-calibration. [default no
                        self-calibration]
  --DOIMAGING           switch to exclude final imaging. [default do final
                        imaging]
  --DODELMAKSIMAGES     delete mask images for LSM modeling. [default delete
                        them]
```

Example to run a self-calibration of useing only 3 spectral windows

```
singularity exec --bind ${PWD}:/data  python3 /data/2GC/IMAGING_and_2GC.py
 --MS_FILE=MS_FILE --WORK_DIR=/data/ --IMAG_PARA_IMSIZE=512 --IMAG_PARA_SPWDS="1,2,3," --DOSELFCAL --IMAG_PARA_ROBUST=0.3
```

# Building the container

singularity build --fakeroot CONTAINER_NAME.simg singularity.meerkat_hrk.recipe_NEW_JUNE


Enjoy !
