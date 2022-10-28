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

ver=221027

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

def cbox_to_star(filename, mult_factor):
    file_extension=pathlib.Path(filename).suffix
    file_stem=pathlib.Path(filename).stem
    new_file = file_stem + ".star"
    f1=open(filename, 'r')
    f2=open(new_file, 'w')
    lines=f1.readlines()
    # multiplication of the coordinates of the STAR file:
    if file_extension == ".cbox" or file_extension == "cbox":
        f2.write("\ndata_\n\nloop_\n")
        for line in lines:
            line=line.strip() 
            if line.startswith('_'):
                if '_CoordinateX' in line:
                    _CoordinateX_index=find_index(line)
                    f2.write("_rlnCoordinateX #1 \n")
                elif '_CoordinateY' in line:
                    _CoordinateY_index=find_index(line)
                    f2.write("_rlnCoordinateY #2 \n")
            elif not line.startswith("#") and len(line.split()) > 4:
                line=line.strip()
                line=line.split()
                for count, line_element in enumerate(line):
                    #print(count, line_element)
                        if count == _CoordinateX_index-1:
                            line[count]= mult_by(line_element, mult_factor)
                        elif count == _CoordinateY_index-1:
                            line[count]= mult_by(line_element, mult_factor)
                temp=' '.join(line[:2])
                f2.write(temp+'\n')
    else:
        print(" =>  ERROR! The program works only with .cbox filetypes")
    f1.close()
    f2.write("\n")
    f2.close()
    print("%s file created" %new_file)


def main(path, label, mult_factor):
    files = glob.glob(path+"*"+label)
    for file in files:
        cbox_to_star(file, mult_factor)
          
if __name__== '__main__':
    output_text='''
==================================== cbox_to_star.py =================================================
cbox_to_star.py converts .cbox files to .star files

[version %s]
Written and tested in python3.8.5
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools
====================================================================================================

Example: cbox_to_star.py  --path ./ --mult 8 ''' % (ver)

    parser = argparse.ArgumentParser(description="")
    add = parser.add_argument
    add('--label', default="cbox", help="File extension")
    add('--path', default="./",
        help="Path to the folder with your files. Default value: ./ ")
    add('--mult', default=1, help="Multiplication factor")
    args = parser.parse_args()
    print(output_text)
    parser.print_help()
    label=args.label
    path=args.path
    mult_factor=float(args.mult)
    #p=subprocess.Popen('rm *modified.cbox', stdout=subprocess.PIPE, shell=True)
    #(output, err) = p.communicate()  
    #p_status = p.wait()
    main(path, label, mult_factor)    
    print(" => Program completed")
