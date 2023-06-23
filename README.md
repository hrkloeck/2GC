# 2GC
Self-calibration of radio interferometer dataset 

Please note that this is a working version for the moment and all the wsclean parameter are hardly coded in the code!!!
Having this in mind we expect 16 spwd being present in the dataset.



# How to run the self-calibration 

1. Prepare the working directory

    git clone https://github.com/JonahDW/Image-processing.git
   
    git clone https://github.com/hrkloeck/DASKMSWERKZEUGKASTEN.git

3. copy your MS file into the directory

4. Edit the IMAGING_SELFCAL.py file      # THIS WILL CHANGE IN THE FUTURE

Start the singularity (important with bind) 

use HRK_CASA_6.5_DASK_WSC3.3.simg

singularity exec --bind ${PWD}:/data CONTAINER.simg python /data/IMAGING_SELFCAL.py

