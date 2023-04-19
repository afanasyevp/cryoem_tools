#!/bin/bash
ver=200817
printf "\n\n================================ compress_tiff.sh ================================"
printf "\n\ncompress_tiff.sh compresses all the .tiff files in the current folder \nand its subfolders by LZW compression \n\nRequires ImageMagick\n\n"
printf "Usage: ./compress_tiff.mrc\nPress q or Ctrl+C to quit when completed \n\n"
printf "Pavel Afanasyev\n${ver}\n"
printf "https://github.com/afanasyevp/cryoem_tools"
printf "\n\n==================================================================================\n\n"

compress_function () {
num_of_tiff=`find . -name '*.tiff' | wc -l`
num_of_lzw_tif=`find . -name '*lzw.tif' | wc -l`
folder=`pwd`
printf "\nFolder $folder contains:\n .tiff files: $num_of_tiff \n lzw.tif files: $num_of_lzw_tif\n\n"

for i in `find . -name "*.tiff" | sort `
    do
        if test -f "${i%%.tiff}_lzw.tif"; then
            #printf "${i%%.tiff}_lzw.tif file exists\n\n"
            continue
        else
            progress=`bc <<<"scale=2; $(( num_of_lzw_tif  * 100 )) / $num_of_tiff "`
            printf "Working on ${i}         Completed: ${progress} %%  \n"
            convert -limit memory 15GiB -limit disk 15GiB "$i" -compress lzw "${i%%.tiff}_lzw.tif"
            num_of_lzw_tif=$(( num_of_lzw_tif + 1  ))
        fi
done
}
printf "\nUpdating the list of files..........\n"
while true; do
    read  -t 3 -N 1 input
    if [[ $input = "q" ]] || [[ $input = "Q" ]]; then
    # The following line is for the prompt to appear on a new line.
        echo
        break
    fi
    compress_function
    printf "\nUpdating the list of files..........\n"

done
