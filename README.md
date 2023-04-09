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
  
### coarsen.py (as a part of manual data screening in Relion)
Unfortunately, Relion does not have a convenient tool to quickly screen your micrographs. This scriptllows binning all the movie-aligned micrographs in a given folder (including subfolders). Useful for manual data screening (to be used with star_modif.py).
##### Why you should not use "Scale" option in the Display pop-up window of Relion:
Scaling in Relion does not bin micrographs (which preserves low-frequency information, corespomnding to the particle features). Instead, it skips the lines in the images. For example, if you have a raw 4096x4096 image (from Falcon 3 camera) and display it in relion with the scale parameter of 0.25, you will get a 1024x1024 image on your screen, where 75% of the image cololumn-lines and 75% of the image row-lines will be hidden. This results in a very poor contrast of the displayed image. Also, though this data is not used for display, but it is used in the program and therefore, makes the screening slow.
Solution: You can bin (coarsen) micrographs before screening. This will facilitate and speed up the screening of your data and further processing. Moreover, often you might learn something important about your dataset, which might be a cause of problems in the image processing.
In the main project-folder, your micrographs should be in the MotionCorr folder (output from the movie-alignments). 
##### Exclude particles from bad micrographs
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

### data_collection_alarm.py 
monitors changes in the number of movie-files in the folder. In case the number of movie-files is constant over certain period of time (20 min by default), it will send you an email. It can also send you an email to confirm the data collection is OK. 

### invert.sh
Inverts handedness of the 3D-reconstruction using relion_image_handler

### mult_coord.py
multiplies coordinates from the particle-picking files (.cbox, .star, .box) in the working folder by the given multiplication factor

### plot_fsc.py
Plots FSC from cisTEM output (.txt file) or relion postprocess_fsc.xml file 

### star_modif.py 
Excludes/extracts micrographs (after manual selection) from micrographs.star or particles.star file. Also, for a given star file, can return a list of micrographs. See instructions for coarsen.py

### star_rand_col.py
Replaces one column in a star file with random numbers

### t_alignframes.py
Batch processing for movie alignments on tomography data

