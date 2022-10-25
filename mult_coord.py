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

ver=221025

import os
import sys
import argparse
import glob
import pathlib
import subprocess

def is_number(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def find_index(line):
    #For a header line in a star file like _CoordinateZ #3 returns its index (=> 3 in this case)
    return int(line.split()[-1].split("#")[-1])

def mult_by(x, mult_factor):
    #Multiplies input by a multiplication factor and returns string with a 2-digit precision
    return "%.2f" % (float(x)*mult_factor)

def mult_coord(filename, mult_factor, fil_to_part):
    'Multiplies coordinates in star, box or cbox files'
    file_extension=pathlib.Path(filename).suffix
    file_stem=pathlib.Path(filename).stem
    new_file = file_stem + "_modified" + file_extension
    write_last_particle=False # for --fil_to_part option : once it detects the first empty line in the cbox file, it returns the last particle in the buffer of temp_tulip 
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
                    _rlnCoordinateX_index=find_index(line)
                    #print ("_rlnCoordinateX_index:", _rlnCoordinateX_index)
                elif '_rlnCoordinateY' in line:
                    _rlnCoordinateY_index=find_index(line)
                f2.write(line+'\n')
            elif len(line)==0: # ignore empty lines
                f2.write(line+'\n')
            elif not line.startswith("#"):
                line=line.strip()
                line=line.split()
                for count, line_element in enumerate(line):
                    if count == _rlnCoordinateX_index-1:
                        line[count]= mult_by(line_element, mult_factor)
                    elif count == _rlnCoordinateY_index-1:
                        line[count]= mult_by(line_element, mult_factor)
                temp=' '.join(line)
                f2.write(temp+'\n')
    # multiplication of the coordinates of the CBOX file:     
    elif file_extension == ".cbox" or file_extension == "cbox":
        #this section is for --fil_to_part option 
        write_line=True
        #define temp_tulip: (filamentid, line) for comparison filament_id and writing them as an output
        temp_tulip=(-1, " ")
        for line in lines:
            line=line.strip()
            if len(line) == 0: # ignore empty lines, or, for the first empty line after the dataread, include the last particle for the --fil_to_part option
                if write_last_particle == True and fil_to_part == True:
                    f2.write(temp_tulip[1]+'\n')
                    write_last_particle = False
                else:
                    f2.write(line+'\n')
            elif line.startswith('data_'): # ignore CBOX structure
                f2.write(line+"\n")
            elif line.startswith('loop_'): # still ignore
                f2.write(line+"\n")
            elif line.startswith('_'):
                if '_CoordinateX' in line:
                    _CoordinateX_index=find_index(line)
                    f2.write(line+"\n")
                elif '_CoordinateY' in line:
                    _CoordinateY_index=find_index(line)
                    f2.write(line+"\n")
                elif '_CoordinateZ' in line:
                    _CoordinateZ_index=find_index(line)
                    f2.write(line+"\n")
                elif '_Width' in line:
                    _Width_index=find_index(line)
                    f2.write(line+"\n")
                elif '_Height' in line:
                    _Height_index=find_index(line)
                    f2.write(line+"\n")
                elif '_Depth' in line:
                    _Depth_index=find_index(line)
                    f2.write(line+"\n")
                elif '_EstWidth' in line:
                    _EstWidth_index=find_index(line)
                    f2.write(line+"\n")
                elif '_EstHeight' in line:
                    _EstHeight_index=find_index(line)
                    f2.write(line+"\n")
                elif '_filamentid' in line:
                    _filamentid_index=find_index(line)
                    if fil_to_part == False:
                        f2.write(line+"\n")
                else:
                    f2.write(line+"\n")
            elif not line.startswith("#"):
                line=line.strip()
                line=line.split()
                for count, line_element in enumerate(line):
                    #print(count, line_element)
                    if count == _CoordinateX_index-1:
                        line[count]= mult_by(line_element, mult_factor)
                    elif count == _CoordinateY_index-1:
                        line[count]= mult_by(line_element, mult_factor)
                    elif count == _CoordinateZ_index-1:
                        if is_number(line_element):
                            line[count]= mult_by(line_element, mult_factor)
                    elif count == _Width_index-1:
                        line[count]= mult_by(line_element, mult_factor)
                    elif count == _Height_index-1:
                        line[count]= mult_by(line_element, mult_factor)
                    elif count == _Depth_index-1:
                        if is_number(line_element):
                            line[count]= mult_by(line_element, mult_factor)
                    elif count == _EstWidth_index-1:
                        if is_number(line_element):
                            line[count]= mult_by(line_element, mult_factor)
                    elif count == _EstHeight_index-1:
                        if is_number(line_element):
                            line[count]= mult_by(line_element, mult_factor)
                    elif fil_to_part == True:
                         if count == _filamentid_index-1:
                            #print(line_element)
                             if fil_to_part:
                                write_last_particle=True
                                temp=' '.join(line[:-1])
                                if line[count] != temp_tulip[0]:
                                    if temp_tulip[0] == -1:
                                        #print("case -1 :", temp)
                                        f2.write(temp+'\n')
                                    else:
                                        #print("case else than -1: ", temp_tulip[1])
                                        f2.write(temp_tulip[1]+'\n')
                                        f2.write(temp+'\n')
                                #else:
                                    #print("case else else: ", "print nothing")
    
                                write_line=False
                                temp_tulip=(line[count], temp)
                                #print("temp_tulip", temp_tulip)
    
                                    
                temp=' '.join(line)
                if write_line:
                    f2.write(temp+'\n')
            #if fil_to_part:
            #    f2.write(temp_tulip[1]+'\n')
 
    elif file_extension == ".box":
        for line in lines:
            line=line.strip()
            line=line.split()
            for count, line_element in enumerate(line):
                line[count]= mult_by(line_element, mult_factor)
            temp=' '.join(line)
            f2.write(temp+'\n')
    else:
        print(" =>  ERROR! The program works only with .star .box and .cbox filetypes")
    f1.close()
    f2.close()
    print("%s file created" %new_file)


def main(mult_factor, path, label, fil_to_part):
    files = glob.glob(path+"*"+label)
    for file in files:
        mult_coord(file, mult_factor, fil_to_part)
          
if __name__== '__main__':
    output_text='''
==================================== mult_coord.py =================================================
mult_coord.py multiplies X,Y coordinates from the star file by the given multiplication factor

[version %s]
Written and tested in python3.8.5
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools
====================================================================================================

Example: mult_coord.py --label star --path ./ --mult 0.25 --fil_to_part''' % (ver)

    parser = argparse.ArgumentParser(description="")
    add = parser.add_argument
    add('--label', default="star", help="File extension")
    add('--path', default="./",
        help="Path to the folder with your files. Default value: ./ ")
    add('--mult', default=1,
        help="Multiplication factor")
    add('--fil_to_part', default=False, action='store_true', help='Converts filament coordinates to particles by removing the _filamentid and considering only beginning and the end of the filament. Works for .cbox files only')
    args = parser.parse_args()
    print(output_text)
    parser.print_help()

    mult_factor=float(args.mult)
    path=args.path
    label=args.label
    #p=subprocess.Popen('rm *modified.cbox', stdout=subprocess.PIPE, shell=True)
    #(output, err) = p.communicate()  
    #p_status = p.wait()
    main(mult_factor, path, label, args.fil_to_part)
        
    print(" => Program completed")
