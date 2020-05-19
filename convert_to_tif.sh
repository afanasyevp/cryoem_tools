#!/bin/bash
ver=200520
printf "\n\n============================== convert_to_tif.sh =============================="
printf "\n\nconvert_to_tif.sh converts all the .mrc files in the current folder \nand its subfolders to LZW compressed tif using standard IMOD routine\n\nRequires IMOD (mrc2tif -c 5 -O 1)\n\n"
printf "Usage: ./convert_to_tif.mrc\nPress q or Ctrl+C to quit when completed \n\n"
printf "Pavel Afanasyev\n${ver}\n"
printf "https://github.com/afanasyevp/cryoem_tools"
printf "\n\n================================================================================\n\n"

mrc2tif_function () {
num_of_mrc=`find . -name '*.mrc' | wc -l`
num_of_tif=`find . -name '*.tif' | wc -l`
folder=`pwd`
printf "\nFolder $folder contains:\n .mrc files: $num_of_mrc \n .tif files: $num_of_tif\n\n"

for i in `find . -name "*.mrc" | sort `
    do
        if test -f "${i%%.mrc}.tif"; then
            #printf "${i%%.mrc}.tif file exists\n\n"
            continue
        else
            progress=`bc <<<"scale=2; $(( num_of_tif  * 100 )) / $num_of_mrc "` 
            printf "Working on ${i}         Completed: ${progress} %%  \n" 
            mrc2tif -c 5 -O 1 -s "$i" "${i%%.mrc}.tif" 
            num_of_tif=$(( num_of_tif + 1  ))
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
    mrc2tif_function
    printf "\nUpdating the list of files..........\n"
    
done










