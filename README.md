# Tools for cryo-EM data processing

### archive.sh
Archives a folder and splits it into a set of files of given size. Saves the full content of the folder into a new file using the tool "tree".

### batch_prepare_images.ijm
Fiji script for batch operations (currently for binning and adjustment of brightness/contrast) on images in various formats. 

##### How to run
Download the script on your local machine, where you have Fiji installed. Run Fiji and run in Fiji Plugins=>Macros=>Run. In the appearing window select the downloaded script.

For the latest versions of MacOS, the second appearing window does not contain the title (known Fiji issue), just choose the folder with your images or modify the script by uncommenting the line "//setOption("JFileChooser", true); // enable for MacOS" in the script - remove the first two slashes. More features can be implemented upon request.

The script is useful for preparing reports and batch processing of cryo-LM data. For czi images, consider preventing the Bio-formats Importer window from displaying by:
1. Open FIJI2. Navigate to Plugins > Bio-Formats > Bio-Formats Plugins Configuration
3. Select Formats
4. Select your desired file format (e.g. “Zeiss CZI”) and select “Windowless”
5. Close the Bio-Formats Plugins Configuration window Now the importer window won’t open for this file-type. 
- To restore this, simply untick ‘Windowless”. 
- To have composite images, make sure the following options are selected in the Bio-Formats Import Options: View stack with: Hyperstack; Color mode: Composite; Autoscale selected.
  
### coarsen.py 
Allows binning all the movie-aligned micrographs in a given folder (including subfolders). Useful for manual data screening (to be used with star_modif.py).
##### Manual data screening in Relion
1.	Select bad binned micrographs (output from coarsen.py) in relion (for screening use Sigma=3). Go to Select/jobXXX and copy micrographs.star as micrographs_save.star
2.	Run “_modif.py -h” without arguments to see the usage instructions.
3.	Run “star_modif.py --i micrographs.star --o bad.txt   --list_of_micro” to create the original list of bad micrographs (unbinned). Check the output (should be called micrographs_bad.txt). 
4.	Select good micrographs based on the power spectra (criteria: CTF FOM and resolution).
5.	Perform particle picking in Topaz or Cryolo.
6.	Go to the Motioncorr/jobXXX/frames folder (or another name - with aligned movie averages) and create symbolic links to the picked particles:
“find [path to cryolo/topaz folder with picked particles] -name “*_cryolo.star”[or another suffix] | xargs -I {} ln -s {} . ”
7.	Make sure by ls -l each micrograph (xxxx_fractions.mrc file) has the corresponding (xxx_fractions_cryolo.star coordinate file). Now, copy the micrographs_bad.txt file from p.2 to the current folder. Open that file (vim/gedit/nano) and replace the suffixes of the names of bad micrographs by the corresponding particle coordinate names like:
Foilhole_xxxx_fractions.mrc => Foilhole_xxxx_fractions_cryolo.star so that they match the coordinate names in the given folder and the file as coordinates_bad.txt  . 
8.	mkdir bad_coord 
9.	cat coordinates_bad.txt  | xargs -I {} mv {} bad_coord
This will move coordinates of particles from bad micrograph into  bad_coord foder 
10.	Import only good particle coordinate files in Relion though Import job from the folder you were just working in. 


### compress_tiff.sh
Batch LZW compression of .tiff files using ImageMagick. Might require modification of the /etc/ImageMagick-6/policy.xml file to allow more RAM (comment out the limits). Current memory limit in the images in the script: -limit memory 15GiB -limit disk 15GiB (for super-resolution K3 data).

### convert_to_tif.sh  
Batch coverter of the mrc movies to tif (LZW compression by IMOD)

### invert.sh
Inverts handedness of the 3D-reconstruction using relion_image_handler

### plot_fsc.py
Plots FSC from cisTEM output (.txt file) or relion postprocess_fsc.xml file 

### star_modif.py 
Excludes/extracts micrographs (after manual selection) from micrographs.star or particles.star file. Also, for a given star file, can return a list of micrographs. See instructions for coarsen.py

### uncoa_star.py
multiplies X,Y coordinates from the star files in the working folder by the given multiplication factor
