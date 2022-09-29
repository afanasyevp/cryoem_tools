#!/usr/bin/env python3
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# -*- coding: utf-8 -*-

ver=220929

import os
import sys
import argparse
import glob
import pathlib


def mult_coord(filename, mult_factor):
    'Multiplies coordinates in star, box or cbox files'
    file_extension=pathlib.Path(filename).suffix
    file_stem=pathlib.Path(filename).stem
    new_file = file_stem + "_modified" + file_extension
    f1=open(filename, 'r')
    f2=open(new_file, 'w')
    lines=f1.readlines()
    # multiplication of the coordinates of the STAR file:
    if file_extension == ".star":
        for line in lines:
            line=line.strip()
            if line.startswith('data_'): # ignore STAR structure
                f2.write(line+'\n')
            elif line.startswith('loop_'): # still ignore
                f2.write(line+'\n')
            elif line.startswith('_'):
                if '_rlnCoordinateX' in line:
                    _rlnCoordinateX_index=int(line.split()[-1].split("#")[-1])
                    #print ("_rlnCoordinateX_index:", _rlnCoordinateX_index)
                elif '_rlnCoordinateY' in line:
                    _rlnCoordinateY_index=int(line.split()[-1].split("#")[-1])
                f2.write(line+'\n')
            elif len(line)==0: # ignore empty lines
                f2.write(line+'\n')
            elif not line.startswith("#"):
                line=line.strip()
                line=line.split()
                for count, line_element in enumerate(line):
                    if count == _rlnCoordinateX_index-1:
                        line[count]= "%.2f" % (float(line_element)*mult_factor)
                    elif count == _rlnCoordinateY_index-1:
                        line[count]= "%.2f" % (float(line_element)*mult_factor)
                temp=' '.join(line)
                f2.write(temp+'\n')
    # multiplication of the coordinates of the CBOX file:     
    elif file_extension == ".cbox":
        for line in lines:
            line=line.strip()
            if line.startswith('data_'): # ignore CBOX structure
                f2.write(line+'\n')
            elif line.startswith('loop_'): # still ignore
                f2.write(line+'\n')
            elif line.startswith('_'):
                if '_CoordinateX' in line:
                    _CoordinateX_index=int(line.split()[-1].split("#")[-1])
                elif '_CoordinateY' in line:
                    _CoordinateY_index=int(line.split()[-1].split("#")[-1])
                elif '_CoordinateZ' in line:
                    _CoordinateZ_index=int(line.split()[-1].split("#")[-1])
                elif '_Width' in line:
                    _Width_index=int(line.split()[-1].split("#")[-1])
                elif '_Height' in line:
                    _Height_index=int(line.split()[-1].split("#")[-1])
                elif '_Depth' in line:
                    _Depth_index=int(line.split()[-1].split("#")[-1])
                elif '_EstWidth' in line:
                    _EstWidth_index=int(line.split()[-1].split("#")[-1])
                elif '_EstHeight' in line:
                    _EstHeight_index=int(line.split()[-1].split("#")[-1])
                f2.write(line+'\n')
            elif len(line)==0: # ignore empty lines
                f2.write(line+'\n')
            elif not line.startswith("#"):
                line=line.strip()
                line=line.split()
                for count, line_element in enumerate(line):
                    if count == _CoordinateX_index-1:
                        line[count]= "%.2f" % (float(line_element)*mult_factor)
                    elif count == _CoordinateY_index-1:
                        line[count]= "%.2f" % (float(line_element)*mult_factor)
                    elif count == _CoordinateZ_index-1:
                        if line_element.isnumeric():
                            line[count]= "%.2f" % (float(line_element)*mult_factor)
                    elif count == _Width_index-1:
                        line[count]= "%.2f" % (float(line_element)*mult_factor)
                    elif count == _Height_index-1:
                        line[count]= "%.2f" % (float(line_element)*mult_factor)
                    elif count == _Depth_index-1:
                        if line_element.isnumeric():
                            line[count]= "%.2f" % (float(line_element)*mult_factor)
                    elif count == _EstWidth_index-1:
                        line[count]= "%.2f" % (float(line_element)*mult_factor)
                    elif count == _EstHeight_index-1:
                        line[count]= "%.2f" % (float(line_element)*mult_factor)
                temp=' '.join(line)
                f2.write(temp+'\n')
 
    elif file_extension == ".box":
        for line in lines:
            line=line.strip()
            line=line.split()
            for count, line_element in enumerate(line):
                line[count]= "%.2f" % (float(line_element)*mult_factor)
            temp=' '.join(line)
            f2.write(temp+'\n')
    else:
        print(" =>  ERROR! The program works only with .star .box and .cbox filetypes")
    f1.close()
    f2.close()
    print("%s file created" %new_file)


def main(mult_factor, path, label):
    files = glob.glob(path+"*"+label)
    for file in files:
        mult_coord(file, mult_factor)
          
if __name__== '__main__':
    output_text='''
==================================== mult_coord.py =================================================
mult_coord.py multiplies X,Y coordinates from the star file by the given multiplication factor

[version %s]
Written and tested in python3.8.5 (requires python 3.6 or a later version)
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools
====================================================================================================

Example: mult_coord.py --label star --path ./ --mult 0.25 ''' % (ver)

    parser = argparse.ArgumentParser(description="")
    add = parser.add_argument
    add('--label', default="star", help="File extension")
    add('--path', default="./",
        help="Path to the folder with your files. Default value: ./ ")
    add('--mult', default=1,
        help="Multiplication factor")
    args = parser.parse_args()
    print(output_text)
    parser.print_help()

    mult_factor=float(args.mult)
    path=args.path
    label=args.label
    main(mult_factor, path, label)
    print(" => Program completed")
