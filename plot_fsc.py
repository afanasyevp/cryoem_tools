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
from pathlib import Path, PurePosixPath, PurePath
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom

PROG = Path(__file__).name
VER = 20240310
TOPHALFLINE = ("=" * 35)
UNDERLINE = ("=" * 70) + ("=" * (len(PROG) + 2))  # line for the output
COLOR_MAIN='#4bd1a0'
CISTEM_FSCFILE_NUM_OF_COLUMNS=7


def fraction_of_nyqist(pixel_size, resolution):
    return 2*pixel_size/resolution

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
        res_val= 1/float(x[0].childNodes[0].nodeValue)
        res.append(res_val)
        frac_of_nq.append(fraction_of_nyqist(pix, res_val))
    curve["curve_name"] = filename          
    curve["fsc"] = fsc
    curve["res"] = res
    curve["frac_of_nq"] = frac_of_nq
    return [curve]

def import_fsc_relion_dat(filename, pix):
    '''
    For a single-curve relion .dat file outputs a fsc dictionary like in import_fsc_xml
    '''
    with open(filename, 'r') as f1:
        lines = f1.readlines()
        fsc=[]
        res=[]
        frac_of_nq=[]
        for line in lines:
            values=line.split()
            res_value = 1/float(values[0])
            res.append(res_value)
            fsc.append(float(values[1]))
            frac_of_nq.append(fraction_of_nyqist(pix, res_val))
    return [{"curve_name": filename, "fsc": fsc, "frac_of_nq": frac_of_nq}]
       
def import_fsc_cistem(filename, pix):
    '''
    For a cistem file outputs a fsc dictionary like in import_fsc_xml
    standard cisTEM v1 header:
    Class 1 - Estimated Res = 3.01 Å (Refinement Limit = 4.00 Å)
    -------------------------------------------------------------
    
    Shell | Res.(Å) | Radius |  FSC  | Part. FSC | √Part. SSNR | √Rec. SSNR
    -----   -------   ------    ---   ----------   -----------   ----------
    '''
    curves=[]
    curve={}
    with open(filename, 'r') as f1:
        lines = f1.readlines()
        fsc=[]
        res=[]
        frac_of_nq=[]
        class_number = 1
        for line in lines:
            values=line.split()
            if values:
                if len(values) != CISTEM_FSCFILE_NUM_OF_COLUMNS:
                    # ignores header of the table. Assumes CISTEM_FSCFILE_NUM_OF_COLUMNS in cistem files like in cisTEM ver 1
                    if values[0] == "Class":
                        curve_name = PurePosixPath(filename).stem+f" class {class_number}"
                        if values[1] == "1":
                            # write out for #1
                            pass
                        else:
                            # write out for #2 and further 
                            curve["curve_name"] = curve_name
                            curve["fsc"] = fsc
                            curve["res"] = res
                            curve["frac_of_nq"] = frac_of_nq
                            curves.append(curve)
                            # delete values for previous curve
                            fsc = []
                            res = []
                            frac_of_nq=[]
                            curve={}
                            class_number += 1
                    else:
                        continue
                elif "-" in values[0]:
                    # ignores ['-----', '-------', '------', '---', '----------', '-----------', '----------'] 
                    continue
                else:
                    res_value=float(values[1])
                    res.append(res_value)
                    fsc.append(float(values[4]))
                    frac_of_nq.append(fraction_of_nyqist(pix, res_val))
        curve["curve_name"] = PurePosixPath(filename).stem+f" class {class_number}"
        curve["fsc"] = fsc
        curve["res"] = res
        curve["frac_of_nq"] = frac_of_nq
        curves.append(curve)
    return curves

def import_fsc_cryosparc_txt(filename, pix, box):
    '''
    For a single-curve cistem file outputs a fsc dictionary like in import_fsc_xml
    Cryosparc txt first line: wave_number	fsc_nomask	fsc_sphericalmask	fsc_loosemask	fsc_tightmask	fsc_noisesub_raw	fsc_noisesub_true	fsc_noisesub
    the last column (fsc_noisesub) is "Corrected FSC"
    Resolution = (box size * pixel size) / wave number
    ''' 
    curve_nomask = {}
    curve_sphericalmask = {}
    curve_loosemask = {}
    curve_tightmask = {}
    curve_noisesub_true ={}
    curve_noisesub_raw = {}
    curve_corrected = {}
    curves=[curve_nomask, curve_sphericalmask, curve_loosemask, curve_tightmask, curve_corrected]

    wave_number = []
    res = []
    frac_of_nq = []

    def resol(wave_number, box, pix):
        return box*pix/wave_number
    
    curve_nomask["curve_name"] = "No mask"
    fsc_nomask = []    
    curve_sphericalmask["curve_name"] = "Spherical mask"
    fsc_sphericalmask = []
    curve_loosemask["curve_name"] = "Loose mask"
    fsc_loosemask = []
    curve_tightmask["curve_name"] = "Tight mask"
    fsc_tightmask = []
    # The function won't return this
    curve_noisesub_raw["curve_name"] = "noisesub_raw"
    fsc_noisesub_raw = []
    # The function won't return this
    curve_noisesub_true["curve_name"] = "noisesub_true"
    fsc_noisesub_true = []
    curve_corrected["curve_name"] = "Corrected"
    fsc_corrected = []

    with open(filename, 'r') as f:
        lines = f.readlines()
        column_names=lines[0].split()

        for line in lines[1:]:
            values=line.split()
            wave_number.append(float(values[0]))
            res_val = box*pix/float(values[0])
            res.append(res_val)
            frac_of_nq.append(fraction_of_nyqist(pix, res_val))
            for value in values:
                if value == "nan" or value == "-inf" or value == "inf":
                    value = 0
            fsc_nomask.append(float(values[1]))
            fsc_sphericalmask.append(float(values[2]))
            fsc_loosemask.append(float(values[3]))
            fsc_tightmask.append(float(values[4]))
            fsc_noisesub_raw.append(float(values[5]))
            fsc_noisesub_true.append(float(values[6]))
            fsc_corrected.append(float(values[7]))
    
        curve_nomask["fsc"] = fsc_nomask
        curve_nomask["res"] = res
        curve_nomask["frac_of_nq"] = frac_of_nq
        
        curve_sphericalmask["fsc"] = fsc_sphericalmask
        curve_sphericalmask["res"] = res
        curve_sphericalmask["frac_of_nq"] = frac_of_nq
        
        curve_loosemask["fsc"] = fsc_loosemask
        curve_loosemask["res"] = res
        curve_loosemask["frac_of_nq"] = frac_of_nq

        curve_tightmask["fsc"] = fsc_tightmask
        curve_tightmask["res"] = res
        curve_tightmask["frac_of_nq"] = frac_of_nq
        
        curve_corrected["fsc"] = fsc_corrected
        curve_corrected["res"] = res
        curve_corrected["frac_of_nq"] = frac_of_nq

    return curves

def make_fsc_plots(curves, units):
    '''Plots curves based from a list of dictionaries:
    {"curve_name": "fsc_01",
    "fsc": [list_of_fsc_values],
    "res": [list_of_res_values],
    "frac_of_nq" [list_of_frac_of_nq_val] }
    '''
    if len(curves) == 0:
        sys.exit(" => ERROR in make_plots! No curves found, check your input!")
    
    
    plt.figure()
    plt.ylabel('FSC', fontweight="bold")
    plt.title('Fourier Shell Correlation', fontweight="bold")
    plt.ylim(top=1)  # adjust the top leaving bottom unchanged
    plt.ylim(bottom=-0.1)  # adjust the bottom leaving top unchanged

    y_formatter = FixedFormatter(["0", "", "0.143", "0.2", "","0.4","", "0.6", "", "0.8", "","1"])
    y_locator = FixedLocator([0, 0.1, 0.143, 0.2, 0.3,  0.4,0.5,  0.6,0.7, 0.8,0.9, 1])
    plt.plot([0, 1], [0.143, 0.143], linewidth=1, color='black', linestyle='dashed')
    plt.plot([0, 1], [0, 0], linewidth=1, color='black')
    plt.grid(linestyle='-', linewidth=0.5)
    print(units)
    if units == "frac_of_nq":
        plt.xlabel('Fraction of Nyquist', fontweight="bold")
        plt.xlim(right=1)  # adjust the right leaving left unchanged
        plt.xlim(left=0)  # adjust the left leaving right unchanged
        x_formatter = FixedFormatter(["0", "", "0.2", "",  "0.4", "", "0.6", "", "0.8","", "1"])
        x_locator = FixedLocator([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1])
        for curve in curves:
            plt.plot(curve["frac_of_nq"], curve["fsc"], linewidth=2)
    elif units == "angstrom":
        plt.xlabel('1/Frequency (1/Å)', fontweight="bold")
        min_x = min(curve["res"] for curve in curves)
        max_x = max(curve["res"] for curve in curves)
        plt.xlim(left=min_x, right=max_x) 
        x_locator = FixedLocator([min_x, 0, max_x]) 
        for curve in curves:
            plt.plot(curve["res"], curve["fsc"], linewidth=2)

    
    ax = plt.gca()
    ax.xaxis.set_major_formatter(x_formatter)        
    ax.yaxis.set_major_formatter(y_formatter)
    ax.xaxis.set_major_locator(x_locator)
    ax.yaxis.set_major_locator(y_locator)

    plt.show()

   
def main(args):
    '''
    Files should be read into a list of dictionaries (curves)
    {"curve_name": "fsc_01",
    "fsc": [list_of_fsc_values],
    "res": [list_of_res_values],
    
    "frac_of_nq" [list_of_frac_of_nq_val] }
    '''
    software = args.software
    fsc_files = args.i
    pix = args.pix

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
                curves.append(import_fsc_relion_dat(fsc_file, pix))
            elif fsc_file[-4:] == ".txt":
                if software == "relion":
                    sys.exit(' => ERROR! Wrong input format: "--software relion" option accepts .dat and .xml files')
                # cryosparc .txt format
                else:
                    curves.extend(import_fsc_cryosparc_txt(fsc_file, pix, args.box))
    else: 
        sys.exit(f" => ERROR: {software} is not a standard input")
    make_fsc_plots(curves, args.units)

    
if __name__ == '__main__':
    description = f"""
{TOPHALFLINE} {PROG} {TOPHALFLINE}
 Builds FSC plot(s) from exported files.
 
    Software   | Extension
   ------------+-----------
    relion     |   .xml .dat
    cryosparc  |   .xml 
    cisTEM     |   .txt

  For cryosparc maps, use .xml file for a single curve.
  For cisTEM, only single-curve files can be used.

  Note: Be careful with multiple files. 
        Pixel size/box size should be the same!


  See full list of options with:
  {PROG} --help

 [version {VER}]
 Written and tested in python3.11 on Unix/Mac
 Pavel Afanasyev
 https://github.com/afanasyevp/cryoem_tools 
{UNDERLINE}"""

    examples=f"""EXAMPLES:
 relion/cryosparc (.xml files): {PROG} --i postprocess_fsc.xml --pix 1.09
 cryosparc (.xml files): {PROG} --i JXXX_fsc_iteration_YYY.txt --pix 1.09 --box 420
 cistem (.txt files): {PROG} --i fsc1.txt fsc2.txt fsc3.txt --pix 1.09
"""
    class UltimateHelpFormatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
        pass
    parser = argparse.ArgumentParser(prog=PROG, formatter_class=UltimateHelpFormatter, description=description, epilog=examples)
    add=parser.add_argument
    add('--i', nargs="+",  help="Saved FSC table from cisTEM software", metavar="")
    add('--software', default="relion", choices=["relion", "cistem", "cryosparc"], help="From which software the files were exported (relion/cryosparc/cistem)", metavar="")
    add('--pix', type=float, required=True, help="Pixel size", metavar="")
    add('--box', type=int, help="Box size for cryosparc .txt files", metavar="")
    add('--units', choices=["frac_of_nq", "angstrom"], default="frac_of_nq",  help='X-axis as a "Fraction of Nyquist" or "1/Frequency"', metavar="")
    args = parser.parse_args()
    print(description)

    if args.software == "cryosparc":
        for fsc_file in args.i:
            if PurePath(fsc_file).suffix == ".txt" and args.box == None:
                sys.exit(" => ERROR! No --box provided! Please specify your box size for cryosparc .txt file") 
    

    main(args)

