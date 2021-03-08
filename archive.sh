#!/bin/bash
#set -x
program_message='
===================================== archive.sh ===============================================
archive.sh archives the given folder and splits the output into the files of given size (in TB).
Also, creates a text file with the structure of the archived folder.
Requires UNIX tools "tree", "bc".

Pavel Afanasyev
version: 210309
https://github.com/afanasyevp/cryoem_tools
================================================================================================
'

printf "\n$program_message" 

usage_message='Usage example command:    archive.sh foldername 1.5 

The option above archives and splits the folder into a set of 1.5 TB files
Use option "0" instead of "1.5" in the example above to get a single file
Optionally, use the output folder as the third argument: archive.sh foldername 1.5 outputfolder
'

other_commands='
======= Other commands =======
Join back all files:                   cat filename.tar.gz.part_* > filename.tar.gz.joined
Extract files from the archive:        tar -xvf filename.tar.gz.joined
'

if [ $# -lt 1 ] ; then
    printf "\n => ERROR!!! Check your input - two or three input arguments required\n\n"
    printf "$usage_message"
    printf "$other_commands"
    exit 1
fi

if [ -d "$1" ]; then
    folder=$(basename $1)
    else 
        printf "\n => ERROR!!! Folder $1 does not exist\n\n"
        printf "$usage_message"
        printf "$other_commands"
        exit 1
fi

if [ $# -eq 1 ] ; then
    sizesub_h=$(du -hcs $1 | grep total | cut  -f 1)
    else
        if [[ $2 = 0 ]]; then
            sizesub_h=10000000
        else
            case $2 in
                ''|*[!0-9]|'.'|*.*.*) printf "\n => ERROR!!! The second argument in the input should be a number (float or integer)\n\n"
                             printf "$usage_message"
                             printf "$other_commands"
                             exit 1;;
                '.'|*) sizesub_h=$2 ;;
            esac
        fi

fi

if [ -d "$3" ]; then
    outfolder=$(realpath -s $3)
    printf " => Output folder: $outfolder"
    else
        outfolder="."
        printf "\n\n => WARNING!!! Output folder: $3 not found. The output will be written in the current folder\n"
fi

if test -f $folder.tartree; then
    printf "\n\n => ERROR!!! $outfolder/$folder.tartree file exists. If you want to create a new archive and continue, rename or delete this file.\n\n"
    printf "$usage_message"
    printf "\n======= Other commands =======\nJoin back all files:                   cat $outfolder/$folder.tar.gz.part_* > $outfolder/$folder.tar.gz.joined\n"
    printf "Extract files from the archive:        tar -xvf $outfolder/$folder.tar.gz.joined\n\n"
    exit 1
fi


printf "\n => Calculating the size of the $1 folder...\n"
sizeori_h=$(du -hcs $1 | grep total | cut  -f 1)
sizeori=$(du -csb $1 | grep total | cut  -f 1)
tb_in_bytes=1000000000000
sizesub=$(echo $sizesub_h*$tb_in_bytes | bc)
#echo "sizesub: $sizesub"
#echo "sizesub_h: $sizesub_h"
#echo "sizeori: $sizeori"
sizesub_int=${sizesub%.*}
#echo "sizesub_int: $sizesub_int"
tree $1 -h > $folder.tartree
du -hcs $1 >> $folder.tartree
num_of_outfiles=$(( sizeori / sizesub_int + 1 ))
#echo "num_of_outfiles: $num_of_outfiles"
if (( $(echo "$sizesub > $sizeori" |bc -l) )); then
    printf "\n\n => WARNING!!! The size of $1 folder is $sizeori_h (requested to split into $2 TB files). A single $folder.tar.gz file will be used as an output\n"
    printf "\n => Archiving in progress...\n"
    tar -cvzf  $outfolder/$1.tar.gz $1
    printf "\n => Counting the total size of the compressed data...\n"
    sizefinal=$(du -hcs $outfolder/$folder.tar.gz | grep total$ | cut -f 1)
    printf "\n => Program finished \n"
    printf "    The content of the folder $1 is in the $outfolder/$folder.tartree file\n"
    printf "    The folder size before archiving: $sizeori_h\n"
    printf "    The data size after archiving: $sizefinal"
    printf "\n\n => To extract files from the archive run: tar -xvf $folder.tar.gz\n\n"
    else
        printf "\n\n  => Archiving $sizeori_h of data in the $1 folder...\n"
        printf "$num_of_outfiles or less output files will be used as an output \n"
        tar -cvzf - $1 | split -b $sizesub_int - "$outfolder/$folder.tar.gz.part_"
        printf "\n => Counting the total size of the compressed data..."
        sizefinal=$(find $outfolder -type f -name $folder.tar.gz.part_\* -exec du -ch {} + | grep total$ | cut -f 1)
        printf "\n => Program finished \n"
        printf "    The content of the folder $1 is in the $outfolder/$folder.tartree file\n"
        printf "    The folder size before archiving: $sizeori_h\n"
        printf "    The data size (in all tar folders) after archiving: $sizefinal\n"
        num_of_outfiles_true=$(ls $outfolder/$folder.tar.gz.part_* | wc -l)
        if [[ $num_of_outfiles_true -eq 1 ]]; then 
            printf "\n => A single file was created after the split. The output will be renamed to $outfolder/$folder.tar.gz\n"
            mv $outfolder/$folder.tar.gz.part_aa $outfolder/$folder.tar.gz
            printf "\n======= Other commands =======\n"
            printf "Extract files from the archive:        tar -xvf $outfolder/$folder.tar.gz\n\n"
        else
            printf "\n======= Other commands =======\nJoin back all files:                   cat $outfolder/$folder.tar.gz.part_* > $outfolder/$folder.tar.gz.joined\n"
            printf "Extract files from the archive:        tar -xvf $outfolder/$folder.tar.gz.joined\n\n"
    fi
fi
