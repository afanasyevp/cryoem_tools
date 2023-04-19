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

ver=230127

import random
import argparse
import sys

def find_index(filename, column):
    #For a given star file and index like "_CoordinateZ"  searches foe line "_CoordinateZ #3" and returns its index (=> 3 in this case)
    with open(filename, "r") as f:
	    lines=f.readlines(1024)
    for line in lines:
        line=line.strip()
        if line.startswith("_"):
            if column in line:
                index=int(line.split()[-1].split("#")[-1])
                break
    return index

def main(filename, column, range, output):
    mainDataRead=False
    ind_col=find_index(filename, column)
    f2=open(output, "w")
    with open(filename, "r") as f1:
        lines=f1.readlines()
    for line in lines:
        line=line.strip()
        if "data_particles" in line:
            mainDataRead=True
        if not line.startswith("_") and len(line.split()) > 4 and mainDataRead:
            line=line.split()
            #print("before", line)
            line[ind_col-1]="%.2f" % (float(random.uniform(int(range[0]), int(range[1]))))
            #print("after", line)
            f2.write('  '.join(line) + "\n")
        else:
            f2.write(line+"\n")
    f2.close()
    print("File %s created" %output)
            
if __name__== '__main__':
    output_text='''
==================================== star_rand_col.py =================================================
modifies a column in a star file by raplacing it with a random number
[version %s]
Written and tested in python3.9.7
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools
====================================================================================================
Example: ./star_rand_col.py  --i particles.star --o particles_rand_AngleRot.star --col _rlnAngleRot --range -180 180 ''' % (ver)

    parser = argparse.ArgumentParser(description="")
    add = parser.add_argument
    add('--i', default="particles.star", help="Input particle.star file")
    add('--o', default="./",
        help="Output particle_modified.star file ")
    add('--col', help="name of the column to modify, for example: _rlnAngleRot ")
    add('--range', nargs="+", default="-1 1", help="Range for random numbers space separated (integer numbers, for example: -1 1)")
    args = parser.parse_args()
    print(output_text)
    parser.print_help()
    filename=args.i
    output=args.o
    column=args.col
    range=args.range
    if not args.col:
        print(" \n => ERROR! No input provided! Please find usage instruction above")
        sys.exit()
    if not args.range:
        print(" \n => ERROR! No input provided! Please find usage instruction above")
        sys.exit()
    main(filename, column, range, output)
    print(" => Program completed")
