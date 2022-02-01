# Tools for cryo-EM data processing

### archive.sh
Archives a folder and splits it into a set of files of given size. Saves the full content of the folder into a new file using the tool "tree".

### batch_prepare_images.ijm
Fiji script for batch operations (currently for binning and adjustment of brightness/contrast) on images in various formats. For the latest versions of MacOS, the second appearing window does not contain the title (known Fiji issue), just choose the folder with your images or modify the script by uncommenting the line "//setOption("JFileChooser", true); // enable for MacOS" in the script - remove the first two slashes. More features can be implemented upon request.

The script is useful for preparing reports and batch processing of cryo-LM data. In case of czi images, consider preventing the Bio-formats Importer window from displaying by:
1. Open FIJI2. Navigate to Plugins > Bio-Formats > Bio-Formats Plugins Configuration
3. Select Formats
4. Select your desired file format (e.g. “Zeiss CZI”) and select “Windowless”
5. Close the Bio-Formats Plugins Configuration window Now the importer window won’t open for this file-type. 
To restore this, simply untick ‘Windowless”. To have composite images, make sure the following options are selected in the Bio-Formats Import Options: View stack with: Hyperstack; Color mode: Composite; Autoscale selected.
  
### coarsen.py
Allows binning all the movie-aligned micrographs in a given folder (including subfolders). Useful for manual data screening.

### compress_tiff.sh
Batch LZW compression of .tiff files using ImageMagick. Might require modification of the /etc/ImageMagick-6/policy.xml file to allow more RAM (comment out the limits). Current memory limit in the images in the script: -limit memory 15GiB -limit disk 15GiB (for super-resolution K3 data).

### convert_to_tif.sh  
Batch coverter of the mrc movies to tif (LZW compression by IMOD)

### invert.sh
Inverts handedness of the 3D-reconstruction using relion_image_handler

### plot_fsc.py
Plots FSC from cisTEM output (.txt file) or relion postprocess_fsc.xml file 

### star_modif.py
Excludes/extracts micrographs (after manual selection) from micrographs.star or particles.star file. Also, for a given star file, can return a list of micrographs.

### uncoa_star.py
multiplies X,Y coordinates from the star files in the working folder by the given multiplication factor
