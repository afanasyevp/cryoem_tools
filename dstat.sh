#!/usr/bin/env bash
#set -x
program_message='
===================================== dstat.sh ===============================================
returns statistics of the dataset: size and number of movies (ending with "fractions.tiff")
Usage: dstat.sh /path/to/folder

Pavel Afanasyev
version: 20251216
https://github.com/afanasyevp/cryoem_tools
================================================================================================
'
printf "\n$program_message"

# Use current directory if no argument is provided
DIR="${1:-.}"
if [[ ! -d "$DIR" ]]; then
  echo "Error: '$DIR' is not a directory"
  exit 1
fi

# Folder size
FOLDER_SIZE=$(du -sh "$DIR" | awk '{print $1}')

# Count files ending with "fractions.tiff" in all subfolders
FILE_COUNT=$(find "$DIR" -type f -name "*fractions.tiff" | wc -l)

echo "Folder: $DIR"
echo "Total size: $FOLDER_SIZE"
echo "Number of files ending with 'fractions.tiff': $FILE_COUNT"


