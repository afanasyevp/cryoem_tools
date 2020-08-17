# Tools for cryo-EM data processing

### coarsen.py
Allows binning all the movie-aligned micrographs in a given folder (including subfolders). Useful for manual data screening.

### compress_tiff.sh
Batch LZW compression of .tiff files using ImageMagick. Might require modification of the /etc/ImageMagick-6/policy.xml file to allow more RAM (comment out the limits). Current memory limit in the images in the script: -limit memory 15GiB -limit disk 15GiB (for super-resolution K3 data).

### convert_to_tif.sh  
Batch coverter of the mrc movies to tif (LZW compression by IMOD). For counting data only!

### invert.sh
Inverts handedness of the 3D-reconstruction using relion_image_handler

### plot_fsc.py
Plots FSC from cisTEM output (.txt file) or relion postprocess_fsc.xml file 

