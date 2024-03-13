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
import os
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter
from pathlib import Path, PurePosixPath, PurePath
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom
import numpy as np
from scipy.interpolate import interp1d
from scipy import optimize

PROG = Path(__file__).name
VER = 20240313
TOPHALFLINE = "=" * 35 # line for the output
UNDERLINE = ("=" * 70) + ("=" * (len(PROG) + 2))  # line for the output
CISTEM_FSCFILE_NUM_OF_COLUMNS = 7

FIXED_THRESHOLD=0.143
FIXED_THRESHOLD_LINEWIDTH=0.5
FIXED_THRESHOLD_COLOR="black"
FIXED_THRESHOLD_LINESTYLE="dashed"

THREE_SIGMA_LINEWIDTH=0.5
HALF_BIT_LINEWIDTH=0.5
CURVE_LINEWIDTH = 1


GRID_LINEWIDTH=0.25
PLOT_TITLE = ""
GRID_LINESTYLE= "-"
FONTWEIGHT = "bold"
Y_LABEL = "Fourier Shell Correlation"
X_LABEL_FRAC_OF_NQ = "Fraction of Nyquist" 
X_TICKS_FRAC_OF_NQ = ["0", "", "0.2", "", "0.4", "", "0.6", "", "0.8", "", "1"]
X_LABEL_RESOLUTION = "1/Frequency (1/Å)"
X_LEFT = 0
X_RIGHT = 1
X_TICKS = [i * 0.1 for i in range(11)]

Y_TICKS_SIMPLE = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
Y_TICKS_LABELS_SIMPLE = ["0", "", "0.2", "", "0.4", "", "0.6", "", "0.8", "", "1"]
Y_TICKS_0143 = [0, 0.1, 0.143, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1]
Y_TICKS_LABELS_0143 = ["0", "", "0.143", "0.2", "", "0.4", "", "0.6", "", "0.8", "", "1"]
Y_BOTTOM = -0.1
Y_TOP = 1


def fraction_of_nyqist(pixel_size, reverce_frequency):
    return 2 * pixel_size / reverce_frequency

# Later here, I refer to reverce frequency as "res" - (resolution), which is not really a resolution of the map!
def reverse_frequency(pixel_size, fraction_of_nyqist):
    return f"{(2*pixel_size/fraction_of_nyqist):.1f}"

def import_fsc_xml(filename, pix):
    """
    Reads a standard .xml files of FSC (EMDB format) and returns a single dictionary of FSC values for building the curve

    For a single-curve cistem file outputs a fsc dictionary:
    {"curve_name": "fsc_01",
    "fsc"        : [list_of_fsc_values],
    "res"        : [list_of_res_values],
    "frac_of_nq" : [list_of_frac_of_nq_val] 
    "curve_type"  : "fsc_relion"/"fsc_cryosparc_XXX"/"fsc_cistem"/"fsc_imagic"/"half_bit"/"three_sigma"
    }
    """
    fsc = []
    res = []
    frac_of_nq = []
    xmldata = minidom.parse(filename)
    fsc_items_list = xmldata.getElementsByTagName("coordinate")
    software = xmldata.getElementsByTagName('fsc')[0].getAttribute('title').split()[0].lower()
    print(f" => Working on {software} data in {filename} file\n")
    curve = {}
    for i in fsc_items_list:
        x = i.getElementsByTagName("x")
        y = i.getElementsByTagName("y")
        fsc.append(float(y[0].childNodes[0].nodeValue))
        res_val = 1 / float(x[0].childNodes[0].nodeValue)
        res.append(res_val)
        frac_of_nq.append(fraction_of_nyqist(pix, res_val))
    curve = {"curve_name": PurePosixPath(filename).stem, "fsc": fsc, "res": res, "frac_of_nq": frac_of_nq, "curve_type": f"fsc_{software}"}
    return [curve]

def import_fsc_relion_dat(filename, pix, software="relion"):
    """
    For a single-curve relion .dat file outputs a fsc dictionary like in import_fsc_xml
    """
    print(f" => Working on {filename} file\n")
    with open(filename, "r") as f1:
        lines = f1.readlines()
        fsc = []
        res = []
        frac_of_nq = []
        for line in lines:
            values = line.split()
            res_value = 1 / float(values[0])
            res.append(res_value)
            fsc.append(float(values[1]))
            frac_of_nq.append(fraction_of_nyqist(pix, res_value))
    return [{"curve_name": filename, "fsc": fsc, "frac_of_nq": frac_of_nq, "res": res,  "curve_type": f"fsc_{software}"}]

def import_fsc_imagic_csv(filename, pix):
    '''
    Reads imagic.csv file with 1/2-bit and 3-sigma cut-offs and outputs a list of 3 curves. 
    Imagic header: "Ring in Fourier Space";"1 / Resolution [1/A]"; "Fourier Shell Correlation"; Half-bit;Sigma
    '''
    print(f" => Working on {filename} file\n")
    
    with open(filename, "r") as f:
        lines = f.readlines()
        # The first value in the lists below corresponds ro DC
        fsc = [1]
        res = [np.nan]
        frac_of_nq = [0]
        half_bit = [1]
        sigma= [np.nan]
        for line in lines[2:]:
            values = line.split(";")
            res_value = 1 / float(values[1])
            res.append(res_value)
            fsc.append(float(values[2]))
            frac_of_nq.append(fraction_of_nyqist(pix, res_value))
            half_bit.append(float(values[3]))
            if float(values[4]) !=0:
                sigma.append(float(values[4]))
            else:
                sigma.append(np.nan)

    curve_fsc = {"curve_name": f"FSC {PurePosixPath(filename).stem}",
                 "fsc": fsc,
                 "res": res,
                 "frac_of_nq": frac_of_nq,
                 "curve_type": "fsc_imagic"}
    curve_half_bit = {"curve_name": "Half-bit cut-off",
                 "fsc": half_bit,
                 "res": res,
                 "frac_of_nq": frac_of_nq,
                 "curve_type": "half_bit"}
    curve_sigma = {"curve_name": "3-sigma cut-off",
                 "fsc": sigma,
                 "res": res,
                 "frac_of_nq": frac_of_nq,
                 "curve_type": "three_sigma"}
    return [curve_fsc, curve_half_bit, curve_sigma]
      
def import_fsc_cistem(filename, pix):
    """
    For a cistem file outputs a fsc dictionary like in import_fsc_xml
    standard cisTEM v1 header:
    Class 1 - Estimated Res = 3.01 Å (Refinement Limit = 4.00 Å)
    -------------------------------------------------------------

    Shell | Res.(Å) | Radius |  FSC  | Part. FSC | √Part. SSNR | √Rec. SSNR
    -----   -------   ------    ---   ----------   -----------   ----------
    """
    curves = []
    curve = {}
    print(f" => Working on {filename} file\n")
    with open(filename, "r") as f1:
        lines = f1.readlines()
        fsc = []
        res = []
        frac_of_nq = []
        class_number = 1
        for line in lines:
            values = line.split()
            if values:
                if len(values) != CISTEM_FSCFILE_NUM_OF_COLUMNS:
                    # ignores header of the table. Assumes CISTEM_FSCFILE_NUM_OF_COLUMNS in cistem files like in cisTEM ver 1
                    if values[0] == "Class":
                        curve_name = (
                            PurePosixPath(filename).stem + f" class {class_number}"
                        )
                        if values[1] == "1":
                            # write out for #1
                            pass
                        else:
                            # write out for #2 and further
                            curve = {"curve_name": curve_name, "fsc": fsc, "res": res, "frac_of_nq": frac_of_nq, "curve_type": "fsc"}
                            curves.append(curve)
                            # delete values for previous curve
                            fsc = []
                            res = []
                            frac_of_nq = []
                            curve = {}
                            class_number += 1
                    else:
                        continue
                elif "-" in values[0]:
                    # ignores ['-----', '-------', '------', '---', '----------', '-----------', '----------']
                    continue
                else:
                    res_value = float(values[1])
                    res.append(res_value)
                    fsc.append(float(values[4]))
                    frac_of_nq.append(fraction_of_nyqist(pix, res_value))
        curve = {"curve_name": PurePosixPath(filename).stem + f" class {class_number}", "fsc": fsc, "res": res, "frac_of_nq": frac_of_nq, "curve_type": "fsc_cistem"}
        curves.append(curve)
    return curves

def import_fsc_cryosparc_txt(filename, pix, box):
    """
    For a single-curve cistem file outputs a fsc dictionary like in import_fsc_xml
    Cryosparc txt first line: wave_number	fsc_nomask	fsc_sphericalmask	fsc_loosemask	fsc_tightmask	fsc_noisesub_raw	fsc_noisesub_true	fsc_noisesub
    the last column (fsc_noisesub) is "Corrected FSC"
    Resolution = (box size * pixel size) / wave number
    """
    print(f" => Working on {filename} file\n")
    wave_number = []
    res = []
    frac_of_nq = []

    fsc_nomask = []
    fsc_sphericalmask = []
    fsc_loosemask = []
    fsc_tightmask = []
    fsc_noisesub_raw = []
    fsc_noisesub_true = []
    fsc_corrected = []

    with open(filename, "r") as f:
        lines = f.readlines()
        first_line = lines[0].split()
        wave_number_ind=first_line.index("wave_number")
        fsc_nomask_ind=first_line.index("fsc_nomask")
        fsc_sphericalmask_ind=first_line.index("fsc_sphericalmask")
        fsc_loosemask_ind=first_line.index("fsc_loosemask")
        fsc_tightmask_ind=first_line.index("fsc_tightmask")
        fsc_noisesub_raw_ind=first_line.index("fsc_noisesub_raw")
        fsc_noisesub_true_ind=first_line.index("fsc_noisesub_true")
        fsc_noisesub_ind=first_line.index("fsc_noisesub")
        for line in lines[1:]:
            values = line.split()
            wave_number.append(float(values[wave_number_ind]))
            res_val = box * pix / float(values[wave_number_ind])
            res.append(res_val)
            frac_of_nq.append(fraction_of_nyqist(pix, res_val))
            for value in values:
                if value == "nan" or value == "-inf" or value == "inf":
                    value = 0
            fsc_nomask.append(float(values[fsc_nomask_ind]))
            fsc_sphericalmask.append(float(values[fsc_sphericalmask_ind]))
            fsc_loosemask.append(float(values[fsc_loosemask_ind]))
            fsc_tightmask.append(float(values[fsc_tightmask_ind]))
            fsc_noisesub_raw.append(float(values[fsc_noisesub_raw_ind]))
            fsc_noisesub_true.append(float(values[fsc_noisesub_true_ind]))
            fsc_corrected.append(float(values[fsc_noisesub_ind]))

        curve_nomask={"curve_name": "No mask", "fsc": fsc_nomask, "res": res, "frac_of_nq": frac_of_nq,  "curve_type": "fsc_cryosparc_nomask"}

        curve_sphericalmask = {"curve_name": "Spherical mask", "fsc": fsc_sphericalmask, "res": res, "frac_of_nq": frac_of_nq, "curve_type": "fsc_cryosparc_sphericalmask"}

        curve_loosemask = {"curve_name": "Loose mask", "fsc": fsc_loosemask, "res": res, "frac_of_nq": frac_of_nq, "curve_type": "fsc_cryosparc_loosemask"}

        curve_tightmask = {"curve_name": "Tight mask", "fsc": fsc_tightmask, "res": res, "frac_of_nq": frac_of_nq,  "curve_type": "fsc_cryosparc_tightmask"}

        # The function won't return the next two two
        curve_noisesub_raw = {"curve_name": "noisesub_raw", "fsc": fsc_noisesub_raw, "res": res, "frac_of_nq": frac_of_nq, "curve_type": "fsc_cryosparc_noisesub_raw" } 
        curve_noisesub_true = {"curve_name": "noisesub_true", "fsc": fsc_noisesub_true, "res": res, "frac_of_nq": frac_of_nq, "curve_type": "fsc_cryosparc_noisesub_true" }

        curve_corrected = {"curve_name": "Corrected", "fsc": fsc_corrected, "res": res, "frac_of_nq": frac_of_nq, "curve_type": "fsc_cryosparc_noisesub_ind"}
        curves = [
            curve_nomask,
            curve_sphericalmask,
            curve_loosemask,
            curve_tightmask,
            curve_corrected,
        ]

    return curves

def make_fsc_plots(curves, units, pix, resolution):
    """Plots curves from a list of dictionaries:
    """
    if len(curves) == 0:
        sys.exit(" => ERROR in make_plots! No curves found, check your input!")

    plt.figure()
    plt.ylabel(Y_LABEL, fontweight=FONTWEIGHT)
    plt.title(PLOT_TITLE, fontweight=FONTWEIGHT)
    plt.ylim(bottom=Y_BOTTOM, top=Y_TOP)  # adjust the bottom leaving top unchanged
    plt.grid(linestyle=GRID_LINESTYLE, linewidth=GRID_LINEWIDTH)
    plt.xlim(right=X_RIGHT)  # adjust the right leaving left unchanged
    plt.xlim(left=X_LEFT)  # adjust the left leaving right unchanged
    x_tick_values = X_TICKS
    x_locator = FixedLocator(x_tick_values)
    

    # 0.143 cut-off
    if units == "frac_of_nq":
        plt.xlabel(X_LABEL_FRAC_OF_NQ, fontweight=FONTWEIGHT)
        x_formatter = FixedFormatter(X_TICKS_FRAC_OF_NQ)
        
    elif units == "angstrom":
        plt.xlabel(X_LABEL_RESOLUTION, fontweight=FONTWEIGHT)
        # max value in the list of dictionaries
        #all_res_values = [res_val for curve in curves for res_val in curve["res"]]
        #max_res = max(all_res_values)
        #min_res = min(all_res_values)
        x_tick_values[0] = ""
        x_tick_values[1:] = [f"{reverse_frequency(pix, val)}" for val in x_tick_values[1:]]
        x_formatter = FixedFormatter(x_tick_values)

    half_bit_fsc = None
    three_sigma_fsc = None
    for curve in curves:
        if curve["curve_type"] == "half_bit":
            half_bit_fsc = curve["fsc"]
        elif curve["curve_type"] == "three_sigma":
            three_sigma_fsc = curve["fsc"]
    
    for i, curve in enumerate(curves):
        custom_plot_command(curve, f"C{i}", args,  halfbit_curve=half_bit_fsc, three_sigma_curve=three_sigma_fsc)
        # if curve["curve_name"].split()[0] == "FSC":
        #     # imagic-created FSC curves only
        #     curve_index=curves.index(curve)
        #     sigma = curves[curve_index+1]
        #     half_bit = curves[curve_index+2]
        #     custom_plot_command(curve, f"C{i}", args, fixed_res=True, halfbit_curve=half_bit, sigma_curve=sigma)
        # else:
        #     if curve["curve_type"] == "Half-bit cut-off" or curve["curve_name"] == "3-sigma cut-off":
        #         custom_plot_command(curve, f"C{i}", args, fixed_res=False, halfbit_curve=None, sigma_curve=None)
        #     else:
        #         custom_plot_command(curve, f"C{i}", args, fixed_res=True)

    if args.no_threshold == False:
        plt.plot([X_RIGHT, X_LEFT], [FIXED_THRESHOLD, FIXED_THRESHOLD], linewidth=FIXED_THRESHOLD_LINEWIDTH, color=FIXED_THRESHOLD_COLOR, linestyle=FIXED_THRESHOLD_LINESTYLE)
        y_formatter = FixedFormatter(Y_TICKS_LABELS_0143)
        y_locator = FixedLocator(Y_TICKS_0143)
        
    else:
        y_formatter = FixedFormatter(Y_TICKS_LABELS_SIMPLE)
        y_locator = FixedLocator(Y_TICKS_SIMPLE)

    ax = plt.gca()
    ax.xaxis.set_major_formatter(x_formatter)
    ax.xaxis.set_major_locator(x_locator)
    ax.yaxis.set_major_formatter(y_formatter)
    ax.yaxis.set_major_locator(y_locator)
    plt.axhline(0, color='black', linewidth=0.5)
    plt.show()

def custom_plot_command(curve, color, args, curve_linewidth=CURVE_LINEWIDTH, three_sigma_linewidth=THREE_SIGMA_LINEWIDTH, half_bit_linewidth=HALF_BIT_LINEWIDTH, halfbit_curve=None, three_sigma_curve=None):
    '''
    Helper function to accomodate customisation of the plot creation: 
    - curve labels
    - resolution/fraction of Nyquist representation in the X-axis 
    '''
    
    if args.label == True:
        
        
        
        if args.resolution:    
            if args.thresholds_all:
            
                if halfbit_curve and sigma_curve: 
                    resolution_0143 = determine_resolution(curve, args.pix)
                    resolution_sigma = determine_resolution(curve, args.pix, three_sigma_curve["fsc"])
                    resolution_halfbit = determine_resolution(curve, args.pix, halfbit_curve["fsc"])
                    label_text = curve["curve_name"]
                else:
                    sys.exit("=> ERROR! No 3-sigma and/or half-bit curve (usually from the imagic.csv file) was parsed to be displayed. Consider running program ")

                #elif curve["curve_name"] != :
                #    label_text = curve["curve_name"] 

            elif args.no_threshold == False:
                label_text = curve["curve_name"] +  determine_resolution(curve, args.pix) 
        else:
            label_text = curve["curve_name"]
        plt.plot(curve["frac_of_nq"], curve["fsc"], linewidth=CURVE_LINEWIDTH, color=color, label=label_text)
        plt.legend() 
    else:
        plt.plot(curve["frac_of_nq"], curve["fsc"], linewidth=CURVE_LINEWIDTH, color=color)



# def determine_resolution(x_curve, y_curve, pix, y_threshold=0.143):
#     '''
#     For two lists determining a FSC curve determines resolution based on 0.143 threshold
#     '''
#     # Interpolate the y-values of the curve
#     f_curve = interp1d(x_curve, y_curve, fill_value='extrapolate')

#     # Generate x-values for the threshold curve
#     x_threshold = np.linspace(min(x_curve), max(x_curve), 1000)
#     y_threshold_values = np.full_like(x_threshold, y_threshold)

#     # Interpolate the y-values of the threshold curve
#     f_threshold = interp1d(x_threshold, y_threshold_values, fill_value='extrapolate')

#     # Find the intersection points by finding the x-values where the absolute difference between the interpolated y-values is minimized
#     intersection_x_values = []
#     try:
#         for x in x_curve:
#             intersection = optimize.root_scalar(lambda x: f_curve(x) - f_threshold(x), bracket=[min(x_curve), max(x_curve)])
#             if intersection.converged:
#                 intersection_x_values.append(intersection.root)
#     except Exception as e:
#         print(" => ERROR! Error occurred during intersection calculation of resolution estimation:", e)
#         sys.exit("Consider running without --resolution option")

#     resolution_angstrom = 2*pix/min(intersection_x_values)
    
#     return f'{resolution_angstrom:.1f}'
        
def determine_resolution(curve, pix, y_threshold=FIXED_THRESHOLD, x_threshold=None, y_threshold_values=None, label=True):
    '''
    For two lists determining a FSC curve determines resolution based on the specified threshold
    '''
    # Interpolate the y-values of the curve
    if curve["curve_type"] == "three_sigma" or curve["curve_type"] == "half_bit":
        return ""
    x_curve = curve['frac_of_nq']
    y_curve = curve['fsc']

    f_curve = interp1d(x_curve, y_curve, fill_value='extrapolate')

    # If the threshold curve is not provided, generate it
    if x_threshold is None or y_threshold_values is None:
        x_threshold = np.linspace(min(x_curve), max(x_curve), 1000)
        y_threshold_values = np.full_like(x_threshold, y_threshold)

    # Interpolate the y-values of the threshold curve
    f_threshold = interp1d(x_threshold, y_threshold_values, fill_value='extrapolate')

    # Find the intersection points by finding the x-values where the absolute difference between the interpolated y-values is minimized
    intersection_x_values = []
    try:
        for x in x_curve:
            intersection = optimize.root_scalar(lambda x: f_curve(x) - f_threshold(x), bracket=[min(x_curve), max(x_curve)])
            if intersection.converged:
                intersection_x_values.append(intersection.root)
    except Exception as e:
        print(" => ERROR! Error occurred during intersection calculation of resolution estimation:", e)
        sys.exit("Consider running without --resolution option")

    resolution_angstrom = 2 * pix / min(intersection_x_values)
    
    if label:
        return f' ({resolution_angstrom:.1f}Å)'
    else:
        return resolution_angstrom



def run_file_analysis(filename, args):
    '''Determines the software, which produced the input file, and extracts FSC curve(s) from it
    '''
    if not os.path.exists(filename):
        sys.exit(f" => ERROR! File {filename} does not exist")
    if filename[-4:] == ".xml":
        return import_fsc_xml(filename, args.pix)
    elif filename[-4:] == ".dat":
        return import_fsc_relion_dat(filename, args.pix)
    elif filename[-4:] == ".csv":
        return import_fsc_imagic_csv(filename, args.pix)
    elif filename[-4:] == ".txt":
        with open(filename, "r") as f:
            first_line = f.readline()
            if first_line.split()[0]  == "Class":
                return import_fsc_cistem(filename, args.pix)
            elif first_line.split()[0] == "wave_number":
                if args.box == None:
                    sys.exit(" => ERROR! No --box provided! Please specify your box size for cryosparc {filename} file")
                return import_fsc_cryosparc_txt(filename, args.pix, args.box)
            else:
                print(f" => WARNING! File type in {filename} not detected. Considering general 2-column type like in relion.dat files")
    else:
        print(f" => WARNING! File type in {filename} not detected. Considering general 2-column type like in relion.dat files")
        return import_fsc_relion_dat(filename, args.pix, software="unknown_software")
    

def main(args):
    """
    Files should be read into a list of dictionaries (curves)
    {"curve_name": "fsc_01",
    "fsc": [list_of_fsc_values],
    "res": [list_of_res_values],
 
    "frac_of_nq" [list_of_frac_of_nq_val] }
    """

    curves = []
    # extracts fsc curves
    for fsc_file in args.i:
        curves.extend(run_file_analysis(fsc_file, args))
    # plots them
    make_fsc_plots(curves, args.units, args.pix, args.resolution)


if __name__ == "__main__":
    description = f"""
{TOPHALFLINE} {PROG} {TOPHALFLINE}
 Builds FSC plot(s) from exported files.
 
    Software   | Extension
   ------------+-----------
    relion     |   .xml .dat
    cryosparc  |   .xml 
    cisTEM     |   .txt
    imagic     |   .csv
   
   Other files are expected to be in relion.dat format,
   with 2 columns: Fraction of Nyqist; FSC value. 

  Note: Be careful with multiple files: 
        pixel size/box size should be the same!


  See full list of options with:
  {PROG} --help

 [version {VER}]
 Written and tested in python3.11 on Unix/Mac
 Pavel Afanasyev
 https://github.com/afanasyevp/cryoem_tools 
{UNDERLINE}"""

    examples = f"""EXAMPLES:

 relion/cryosparc (.xml files): {PROG} --i postprocess_fsc.xml --pix 1.09 --units angstrom --resolution  --label

 cryosparc (.xml files): {PROG} --i JXXX_fsc_iteration_YYY.txt --pix 1.09 --box 420 --resolution  --label

 cistem (.txt files): {PROG} --i fsc1.txt fsc2.txt fsc3.txt --pix 1.09 --units frac_of_nq --resolution --label

"""

    class UltimateHelpFormatter(
        argparse.RawTextHelpFormatter,
        argparse.ArgumentDefaultsHelpFormatter,
        argparse.RawDescriptionHelpFormatter,
    ):
        pass

    parser = argparse.ArgumentParser(
        prog=PROG,
        formatter_class=UltimateHelpFormatter,
        description=description,
        epilog=examples,
    )
    add = parser.add_argument
    add("--i", nargs="+", help="Saved FSC table from cisTEM software")
    add("--pix", type=float, required=True, help="Pixel size", metavar="")
    add("--box", type=int, help="Box size for cryosparc .txt files", metavar="")
    add(
        "--units",
        choices=["frac_of_nq", "angstrom"],
        default="angstrom",
        help='Options: angstrom/frac_of_nq | X-axis as a "Fraction of Nyquist" or "1/Frequency"',
        metavar="",
    )
    add("--label",  default=False, action="store_true", help="Label on the plot")
    add("--resolution", default=False, action="store_true", help="Show resolution and 0.143 curve on the plot")
    add("--no_threshold", default=False, action="store_true", help="Hide 0.143 threshold on the plot")
    add("--thresholds_all", default=False, action="store_true", help='Include half-bit and 3-sigma thresholds generated by Imagic "FSC" program (free)')
    args = parser.parse_args()
    print(description)

    if args.label == False and args.resolution == True:
        sys.exit(" => ERROR! --resolution option can't be used without --label option")

    print(f"\n\n => Input parameters: ")
    for key, value in vars(args).items():
        print(f"  --{key}  {value}")
    print()
    if len(args.i)>1:
        print(" => WARNING! Multiple files are used! Pixel size and box sizes (for cryosparc .txt files) should be the same!")
    

    main(args)