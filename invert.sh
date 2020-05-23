#!/bin/bash
ver=200523
printf "\n\n=================================== invert.sh ==================================="
printf "\n\ninvert.sh flips handedness of the input 3D-reconstruction using relion_image_handler\n"
printf "Usage: invert.sh input3d\n\n"
printf "Pavel Afanasyev\n${ver}\n"
printf "https://github.com/afanasyevp/cryoem_tools"
printf "\n\n=================================================================================\n\n"

output=`echo $1 | sed 's/.mrc/_inverthand.mrc/'`
relion_image_handler --i $1 --o $output --invert_hand


echo "Done! Output file: ${output}"
