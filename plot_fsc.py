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

import sys
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter
from pathlib import Path
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom

PROG = Path(__file__).name
VER = 20240306
TOPHALFLINE = ("=" * 35)
UNDERLINE = ("=" * 70) + ("=" * (len(PROG) + 2))  # line for the output
COLOR='#4bd1a0'


def import_fsc_xml(filename, pix):
    '''
    Reads a standard .xml files of FSC (EMDB format) and returns a single dictionary of FSC values for building the curve

    For a single-curve cistem file outputs a fsc dictionary:
    {"curve_name": "fsc_01",
    
    "fsc": [list_of_fsc_values],
    "res": [list_of_res_values],
    "frac_of_nq" [list_of_frac_of_nq_val] }
    '''
    fsc=[]
    res=[]
    frac_of_nq=[]
    xmldata = minidom.parse(filename)
    fsc_items_list=xmldata.getElementsByTagName("coordinate")
    curve={}
    for i in fsc_items_list:
        x = i.getElementsByTagName("x")
        y = i.getElementsByTagName("y")
        fsc.append(float(y[0].childNodes[0].nodeValue))
        res.append(1/float(x[0].childNodes[0].nodeValue))
        frac_of_nq.append(2*pix*float(x[0].childNodes[0].nodeValue) )
    curve["curve_name"] = filename          
    curve["fsc"] = fsc
    curve["res"] = res
    curve["frac_of_nq"] = frac_of_nq
    return curve
       
def import_fsc_cistem(filename, pix):
    '''
    For a single-curve cistem file outputs a fsc dictionary:
    {"curve_name": "fsc_01",
    
    "fsc": [list_of_fsc_values],
    "res": [list_of_res_values],
    "frac_of_nq" [list_of_frac_of_nq_val] }
    '''
    # TODO: implement reading files with multiple classes 
    curve={}
    with open(filename, 'Ur') as f1:
        lines = f1.readlines()
        fsc=[]
        res=[]
        frac_of_nq=[]
        for line in lines[5:-1]:
            values=line.split()
            res.append(float(values[1]))
            fsc.append(float(values[4]))
            frac_of_nq.append(2*pix/float(values[1]))
        curve["curve_name"] = filename
        curve["fsc"] = fsc
        curve["res"] = res
        curve["frac_of_nq"] = frac_of_nq
    return [curve]

def import_fsc_cryosparc(filename, pix):
    '''
    For a single-curve cistem file outputs a fsc dictionary:
    {"curve_name": "fsc_01",
    
    "fsc": [list_of_fsc_values],
    "res": [list_of_res_values],
    "frac_of_nq" [list_of_frac_of_nq_val] }

    Cryosparc txt first line: wave_number	fsc_nomask	fsc_sphericalmask	fsc_loosemask	fsc_tightmask	fsc_noisesub_raw	fsc_noisesub_true	fsc_noisesub
    ''' 
    curve={}
    with open(filename, 'Ur') as f:
        lines = f.readlines()
        fsc=[]
        res=[]
        frac_of_nq=[]
        column_names=lines[0].split()
        for line in lines[1:]:
            values=line.split()
            res.append(float(values[1]))
            fsc.append(float(values[4]))
            frac_of_nq.append(2*pix/float(values[1]))
        curve["curve_name"] = filename
        curve["fsc"] = fsc
        curve["res"] = res
        curve["frac_of_nq"] = frac_of_nq
    return [curve]

def make_fsc_plots(curves):
    '''Plots curves based from a list of dictionaries:
    {"curve_name": "fsc_01",
    "fsc": [list_of_fsc_values],
    "res": [list_of_res_values],
    "frac_of_nq" [list_of_frac_of_nq_val] }
    '''
    plt.figure()
    plt.xlabel('Fraction of Nyquist', fontweight="bold")
    plt.ylabel('FSC', fontweight="bold")
    plt.title('Fourier Shell Correlation', fontweight="bold")
    plt.xlim(right=1)  # adjust the right leaving left unchanged
    plt.xlim(left=0)  # adjust the left leaving right unchanged
    plt.ylim(top=1)  # adjust the top leaving bottom unchanged
    plt.ylim(bottom=0)  # adjust the bottom leaving top unchanged
    
    if len(curves) == 0:
        sys.exit(" => ERROR in make_plots! No curves found!")
    elif len(curves) == 1:
        plt.plot(curves[0]["frac_of_nq"], curves[0]["fsc"], color=COLOR, linewidth=2)
    else:
        for curve in curves:
            plt.plot(curve["frac_of_nq"], curve["fsc"], linewidth=2)

    ax = plt.gca()
    x_formatter = FixedFormatter(["", "", "0.2", "",  "0.4", "", "0.6", "", "0.8","", "1"])
    y_formatter = FixedFormatter(["0", "", "0.143", "0.2", "","0.4","", "0.6", "", "0.8", "","1"])
    x_locator = FixedLocator([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1])
    y_locator = FixedLocator([0, 0.1, 0.143, 0.2, 0.3,  0.4,0.5,  0.6,0.7, 0.8,0.9, 1])
    plt.plot([0, 1], [0.143, 0.143], linewidth=1, color='black')
    ax.xaxis.set_major_formatter(x_formatter)
    ax.yaxis.set_major_formatter(y_formatter)
    ax.xaxis.set_major_locator(x_locator)
    ax.yaxis.set_major_locator(y_locator)
    plt.grid(linestyle='-', linewidth=0.5)
    plt.show()

   
def main(fsc_files, pix, software):
    '''
    Files should be read into a list of dictionaries (curves)
    {"curve_name": "fsc_01",
    "fsc": [list_of_fsc_values],
    "res": [list_of_res_values],
    
    "frac_of_nq" [list_of_frac_of_nq_val] }
    '''
    # controls file extensions and extracts fsc curves
    curves=[]
    if software == "cistem":
        for fsc_file in fsc_files:
            if fsc_file[-4:] != ".txt":
                sys.exit(f" => ERROR in checking the type of cisTEM file {fsc_file}! Must be .txt")
            curves.extend(import_fsc_cistem(fsc_file, pix))
    elif software == "relion" or "cryosparc":
        for fsc_file in fsc_files:
            if fsc_file[-4:] == ".xml":
                # relion and cryoscarc use the same EMDB .xml format
                curves.append(import_fsc_xml(fsc_file, pix))
            elif fsc_file[-4:] == ".dat":
                # relion format
                # TODO
                ...
            elif fsc_file[-4:] == ".txt":
                # cryosparc format
                # TODO
                ...
         
    else: 
        sys.exit(f" => ERROR: {software} is not a standard input")

    
    make_fsc_plots(curves)

    
if __name__ == '__main__':
    description = f"""
{TOPHALFLINE} {PROG} {TOPHALFLINE}
 Builds FSC plot(s) from exported files.
 
    Software   | Extension
   ------------+-----------
    relion     |   .xml .dat
    cryosparc  |   .xml 
    cisTEM     |   .txt

  See full list of options with:
  {PROG} --help

 [version {VER}]
 Written and tested in python3.11
 Pavel Afanasyev
 https://github.com/afanasyevp/cryoem_tools 
{UNDERLINE}"""

    examples=f"""EXAMPLES:
 relion/cryosparc (.xml files): {PROG} --i postprocess_fsc.xml --pix 1.09
 cistem (.txt files): {PROG} --i fsc1.txt fsc2.txt fsc3.txt --pix 1.09
"""
    class UltimateHelpFormatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
        pass
    parser = argparse.ArgumentParser(prog=PROG, formatter_class=UltimateHelpFormatter, description=description, epilog=examples)
    add=parser.add_argument
    add('--i', nargs="+",  help="Saved FSC table from cisTEM software", metavar="")
    add('--software', default="relion", choices=["relion", "cistem", "cryosparc"], help="From which software the files were exported (relion/cryosparc/cistem)", metavar="")
    add('--pix', type=float, required=True, help="Pixel size", metavar="")
    args = parser.parse_args()
    print(description)
    fsc_files=args.i
    pix=args.pix
    software=args.software

    main(fsc_files, pix, software)

