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
VER = 20240311
TOPHALFLINE = "=" * 35
UNDERLINE = ("=" * 70) + ("=" * (len(PROG) + 2))  # line for the output
COLOR_MAIN = "#4bd1a0"
CISTEM_FSCFILE_NUM_OF_COLUMNS = 7
LINEWIDTH = 1
PLOT_TITLE = ""# "Fourier Shell Correlation"
Y_LABEL = "Fourier Shell Correlation"
X_LABEL_FRAC_OF_NQ = "Fraction of Nyquist" 
X_LABEL_RESOLUTION = "1/Frequency (1/Å)"


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

    "fsc": [list_of_fsc_values],
    "res": [list_of_res_values],
    "frac_of_nq" [list_of_frac_of_nq_val] }
    """
    fsc = []
    res = []
    frac_of_nq = []
    xmldata = minidom.parse(filename)
    fsc_items_list = xmldata.getElementsByTagName("coordinate")
    print(f" => Working on {xmldata.getElementsByTagName('fsc')[0].getAttribute('title').split()[0]} data in {filename} file\n")
    curve = {}
    for i in fsc_items_list:
        x = i.getElementsByTagName("x")
        y = i.getElementsByTagName("y")
        fsc.append(float(y[0].childNodes[0].nodeValue))
        res_val = 1 / float(x[0].childNodes[0].nodeValue)
        res.append(res_val)
        frac_of_nq.append(fraction_of_nyqist(pix, res_val))
    curve["curve_name"] = PurePosixPath(filename).stem
    curve["fsc"] = fsc
    curve["res"] = res
    curve["frac_of_nq"] = frac_of_nq
    return [curve]


def import_fsc_relion_dat(filename, pix):
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
    return [{"curve_name": filename, "fsc": fsc, "frac_of_nq": frac_of_nq, "res": res}]


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
                            curve["curve_name"] = curve_name
                            curve["fsc"] = fsc
                            curve["res"] = res
                            curve["frac_of_nq"] = frac_of_nq
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
        curve["curve_name"] = PurePosixPath(filename).stem + f" class {class_number}"
        curve["fsc"] = fsc
        curve["res"] = res
        curve["frac_of_nq"] = frac_of_nq
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
    curve_nomask = {}
    curve_sphericalmask = {}
    curve_loosemask = {}
    curve_tightmask = {}
    curve_noisesub_true = {}
    curve_noisesub_raw = {}
    curve_corrected = {}
    curves = [
        curve_nomask,
        curve_sphericalmask,
        curve_loosemask,
        curve_tightmask,
        curve_corrected,
    ]

    wave_number = []
    res = []
    frac_of_nq = []

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

    with open(filename, "r") as f:
        lines = f.readlines()
        column_names = lines[0].split()

        for line in lines[1:]:
            values = line.split()
            wave_number.append(float(values[0]))
            res_val = box * pix / float(values[0])
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


def make_fsc_plots(curves, units, pix, resolution):
    """Plots curves based from a list of dictionaries:
    {"curve_name": "fsc_01",
    "fsc": [list_of_fsc_values],
    "res": [list_of_res_values],
    "frac_of_nq" [list_of_frac_of_nq_val] }
    """
    if len(curves) == 0:
        sys.exit(" => ERROR in make_plots! No curves found, check your input!")

    plt.figure()
    plt.ylabel(Y_LABEL, fontweight="bold")
    plt.title(PLOT_TITLE, fontweight="bold")
    plt.ylim(bottom=-0.1, top=1)  # adjust the bottom leaving top unchanged
    
    if args.threshold:
        plt.plot([0, 1], [0.143, 0.143], linewidth=1, color="black", linestyle="dashed")
        y_formatter = FixedFormatter(["0", "", "0.143", "0.2", "", "0.4", "", "0.6", "", "0.8", "", "1"])
        y_locator = FixedLocator([0, 0.1, 0.143, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1])
    else:
        y_formatter = FixedFormatter(["0", "", "0.2", "", "0.4", "", "0.6", "", "0.8", "", "1"])
        y_locator = FixedLocator([0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1])
    plt.grid(linestyle="-", linewidth=0.25)
    plt.xlim(right=1)  # adjust the right leaving left unchanged
    plt.xlim(left=0)  # adjust the left leaving right unchanged
    x_tick_values = [i * 0.1 for i in range(11)]
    x_locator = FixedLocator(x_tick_values)

    # 0.143 cut-off
    if units == "frac_of_nq":
        plt.xlabel(X_LABEL_FRAC_OF_NQ, fontweight="bold")
        x_formatter = FixedFormatter(
            ["0", "", "0.2", "", "0.4", "", "0.6", "", "0.8", "", "1"]
        )
        
    elif units == "angstrom":
        plt.xlabel(X_LABEL_RESOLUTION, fontweight="bold")
        # max value in the list of dictionaries
        #all_res_values = [res_val for curve in curves for res_val in curve["res"]]
        #max_res = max(all_res_values)
        #min_res = min(all_res_values)
        x_tick_values[0] = ""
        x_tick_values[1:] = [f"{reverse_frequency(pix, val)}" for val in x_tick_values[1:]]
        x_formatter = FixedFormatter(x_tick_values)

        for i, curve in enumerate(curves):
            custom_plot_command(curve, f"C{i}", args)

    ax = plt.gca()
    ax.xaxis.set_major_formatter(x_formatter)
    ax.xaxis.set_major_locator(x_locator)
    ax.yaxis.set_major_formatter(y_formatter)
    ax.yaxis.set_major_locator(y_locator)
    plt.axhline(0, color='black', linewidth=0.5)
    plt.show()

def custom_plot_command(curve, color, args, linewidth=LINEWIDTH):
    if args.label == True:
        if args.resolution:
            label_text = curve["curve_name"] +  " (" + determine_resolution_0143(curve['frac_of_nq'], curve['fsc'], args.pix) + "Å)"
        else:
            label_text = curve["curve_name"]
        plt.plot(curve["frac_of_nq"], curve["fsc"], linewidth=linewidth, color=color, label=label_text)
        plt.legend() 
    else:
        plt.plot(curve["frac_of_nq"], curve["fsc"], linewidth=linewidth, color=color)


def run_file_analysis(filename, args):
    if not os.path.exists(filename):
        sys.exit(f" => ERROR! File {filename} does not exist")
    if filename[-4:] == ".xml":
        return import_fsc_xml(filename, args.pix)
    elif filename[-4:] == ".dat":
        return import_fsc_relion_dat(filename, args.pix)
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
        return import_fsc_relion_dat(filename, args.pix)
def determine_resolution_0143(x_curve, y_curve, pix, y_threshold=0.143):
    '''
    For two lists determining a FSC curve determines resolution based on 0.143 threshold
    '''
    # Interpolate the y-values of the curve
    f_curve = interp1d(x_curve, y_curve, fill_value='extrapolate')

    # Generate x-values for the threshold curve
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

    resolution_angstrom = 2*pix/min(intersection_x_values)
    
    return f'{resolution_angstrom:.1f}'


def main(args):
    """
    Files should be read into a list of dictionaries (curves)
    {"curve_name": "fsc_01",
    "fsc": [list_of_fsc_values],
    "res": [list_of_res_values],
 
    "frac_of_nq" [list_of_frac_of_nq_val] }
    """
    fsc_files = args.i
    pix = args.pix

    # controls file extensions and extracts fsc curves
    curves = []
    for fsc_file in fsc_files:
        curves.extend(run_file_analysis(fsc_file, args))
    make_fsc_plots(curves, args.units, pix, args.resolution)


if __name__ == "__main__":
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

    examples = f"""EXAMPLES:
 relion/cryosparc (.xml files): {PROG} --i postprocess_fsc.xml --pix 1.09 --units angstrom --resolution --threshold --label
 cryosparc (.xml files): {PROG} --i JXXX_fsc_iteration_YYY.txt --pix 1.09 --box 420 --resolution --threshold --label
 cistem (.txt files): {PROG} --i fsc1.txt fsc2.txt fsc3.txt --pix 1.09 --units frac_of_nq --resolution --threshold --label
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
    add("--resolution", default=False, action="store_true", help="Show resolution on the plot")
    add("--label",  default=False, action="store_true", help="Label on the plot")
    add("--threshold", default=False, action="store_true", help="0.143 threshold on the plot")
    args = parser.parse_args()
    print(description)

    print(f"\n\n => Input parameters: ")
    for key, value in vars(args).items():
        print(f"  --{key}  {value}")
    print()

    main(args)