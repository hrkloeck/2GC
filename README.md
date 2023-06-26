# 2GC
Self-calibration of radio interferometer dataset 

Please note that this is a working version for the moment and all the wsclean parameter are hardly coded in the code!!!
Having this in mind we expect 16 spwd being present in the dataset.



# How to run the self-calibration 

1. Prepare the working directory

    git clone https://github.com/JonahDW/Image-processing.git
   
    git clone https://github.com/hrkloeck/DASKMSWERKZEUGKASTEN.git

    git clone https://github.com/hrkloeck/2GC.git

2. cp 2GC/*py into your working directory

3. copy your MS file into your working directory

4. Edit the Self_calibration_2GC.py file      # THIS WILL CHANGE IN THE FUTURE

Start the singularity (important with bind) 

use HRK_CASA_6.5_DASK_WSC3.3.simg (for local people at the MPIfR)

or if you want to build it by your own (need fakeroot privileges)

singularity build --fakeroot CONTAINER_NAME.simg singularity.meerkat_hrk.recipe_NEW_JUNE

run the thing with (CAUTION YOU NEED EXACTLY THAT BINDING):

singularity exec --bind ${PWD}:/data CONTAINER.simg python /data/IMAGING_SELFCAL.py

