#!/bin/bash
ver=210303
#set -x
if [ $# -ne 2 ] ; then
    echo "ERROR! Check your input!"
    printf "Usage (archive and split into a set of 1TB files): archive.sh yourfolder 1000\n"
        exit 1
        fi

if [ -d "$1" ]; then
    folder=$(basename $1)
    else 
        echo "$1 does not exist."
        fi

printf "\n\n===================================== archive.sh ==============================================="
printf "\n\narchive.sh archives the given folder and splits the output into the files of given size (in GB). \nAlso, creates a text file with the structure of the archived folder.\nRequires UNIX tool \"tree\"\n\n"
printf "Usage (archive and split into a set of 1TB files): archive.sh yourfolder 1000\n"
printf "\nOther commands\nJoin back all files: cat $folder.tar.gz.part_* > $folder.tar.gz.joined\n"
printf "Extract files from the archive: tar -xvf $folder.tar.gz.joined\n\n"
printf "Pavel Afanasyev\n${ver}\n"
printf "https://github.com/afanasyevp/cryoem_tools"
printf "\n\n================================================================================================\n\n"
#set -x #echo on
if test -f $folder.tartree; then                                                                                                                                                          
 printf "\n\n WARNING! $folder.tartree file exists. If you want to create a new archive, rename this file.\n\n"
 exit 1
 fi
echo -e "\n => Calculating the size of the $1 folder..."
sizeori=$(du -hcs $1 | grep total | cut  -f 1)
tree $1 -h > $folder.tartree
du -hcs $1 >> $folder.tartree
echo -e " => Archiving $sizeori of data in the $1 folder...\n" 
tar -cvzf - $1 | split -b $2G - "$folder.tar.gz.part_"
echo -e "\n => Counting the total size of the compressed data..."
sizefinal=$(find . -type f -name $folder.tar.gz.part_\* -exec du -ch {} + | grep total$ | cut -f 1)
echo -e "\n => Program finished \n"
echo "    The content of the folder $1 is in the $folder.tartree file"
echo "    The folder size before archiving: $sizeori"
echo "    The data size after archiving: $sizefinal"
echo -e "\n\n => Further commands\n   Join back all files: cat $folder.tar.gz.part_* > $folder.tar.gz.joined"
echo -e "   Extract files from the archive: tar -xvf $folder.tar.gz.joined\n\n"
