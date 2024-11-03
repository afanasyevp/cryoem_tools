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
import re
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FixedFormatter
from pathlib import Path, PurePosixPath, PurePath
import argparse
import xml.etree.ElementTree as ET
from xml.dom import minidom
import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import root_scalar
import numpy as np

PROG = Path(__file__).name
VER = 20240321
TOPHALFLINE = "=" * 35  # line for the output
UNDERLINE = ("=" * 70) + ("=" * (len(PROG) + 2))  # line for the output
CISTEM_FSCFILE_NUM_OF_COLUMNS = 7

FIXED_THRESHOLD = 0.143
FIXED_THRESHOLD_LINEWIDTH = 0.5
FIXED_THRESHOLD_COLOR = "black"
FIXED_THRESHOLD_LINESTYLE = "dashed"

THREE_SIGMA_LINEWIDTH = 0.5
HALF_BIT_LINEWIDTH = 0.5
CURVE_LINEWIDTH = 1


GRID_LINEWIDTH = 0.25
PLOT_TITLE = ""
GRID_LINESTYLE = "-"
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
Y_TICKS_LABELS_0143 = [
    "0",
    "",
    "0.143",
    "0.2",
    "",
    "0.4",
    "",
    "0.6",
    "",
    "0.8",
    "",
    "1",
]
Y_BOTTOM = -0.1
Y_TOP = 1

class Curve:
    def __init__(self, name, pix, fsc=None, res=None, frac_of_nq=None, curve_type=None, fixed_0143=None, halfbit=None, threesigma=None, label=None):
        self.name = name
        self.pix = pix
        self.fsc = fsc
        self.res = res # reverse resolution
        self.frac_of_nq = frac_of_nq
        self.curve_type = curve_type
        self.fixed_0143 = fixed_0143
        self.halfbit = halfbit
        self.threesigma = threesigma
        self.label = label

    @property
    def frac_of_nq(self):
        return self._frac_of_nq

    @frac_of_nq.setter
    def frac_of_nq(self, frac_of_nq):
        if not self.res:
            raise ValueError(f"No resolution values found in {self.name} curve")
        frac_of_nq=[]
        for res_val in self.res:
            if res_val == 0:
                frac_of_nq.append(0)
            else:
                frac_of_nq.append(2 * self.pix / res_val)
        self._frac_of_nq=frac_of_nq

class FSC_analyser:
    def __init__(self, pix, box=None, filename=None, software=None, curves=[], **kwargs):
        self.pix = pix
        self.box=box
        self.filename = filename
        self.software = software
        self.curves = curves
    
    def run_file_analysis(self):
        """Determines the software, which produced the input file, and extracts FSC curve(s) from it"""
        if not os.path.exists(self.filename):
            sys.exit(f" => ERROR! File {self.filename} does not exist")
        if self.filename[-4:] == ".xml":
            return import_fsc_xml(self.filename, self.pix)
        elif self.filename[-4:] == ".dat":
            return import_fsc_relion_dat(self.filename, self.pix)
        elif self.filename[-4:] == ".csv":
            return import_fsc_imagic_csv(self.filename, self.pix)
        elif self.filename[-4:] == ".txt":
            with open(self.filename, "r") as f:
                first_line = f.readline()
                if first_line.split()[0] == "Class":
                    return import_fsc_cistem(self.filename, self.pix)
                elif first_line.split()[0] == "wave_number":
                    if args.box == None:
                        sys.exit(
                            " => ERROR! No --box provided! Please specify your box size for cryosparc {self.filename} file"
                        )
                    return import_fsc_cryosparc_txt(self.filename, self.pix, self.box)
                else:
                    print(
                        f" => WARNING! File type in {self.filename} not detected. Considering general 2-column type like in relion.dat files"
                    )
        else:
            print(
                f" => WARNING! File type in {self.filename} not detected. Considering general 2-column type like in relion.dat files"
            )
            return import_fsc_relion_dat(self.filename, self.pix, software="unknown_software")

    def import_fsc_xml(self):
        """
        Reads a standard .xml files of FSC (EMDB format) and returns a single dictionary of FSC values for building the curve
        """
        fsc = []
        res = []
        xmldata = minidom.parse(self.filename)
        fsc_items_list = xmldata.getElementsByTagName("coordinate")
        self.software = (
            xmldata.getElementsByTagName("fsc")[0].getAttribute("title").split()[0].lower()
        )
        print(f" => Working on {self.software} data in {self.filename} file\n")
        for i in fsc_items_list:
            x = i.getElementsByTagName("x")
            y = i.getElementsByTagName("y")
            fsc.append(float(y[0].childNodes[0].nodeValue))
            res_val = 1 / float(x[0].childNodes[0].nodeValue)
            res.append(res_val)
        return [Curve(self.filename, self.pix, fsc=fsc, res=res, curve_type=f"fsc_{self.software}", label=PurePosixPath(self.filename).stem)]


    def import_fsc_relion_dat(self, software="relion"):
        """
        For a single-curve relion .dat file outputs a fsc dictionary like in import_fsc_xml
        """
        print(f" => Working on {self.filename} file\n")
        with open(self.filename, "r") as f1:
            lines = f1.readlines()
            fsc = []
            res = []
            for line in lines:
                values = line.split()
                res_value = 1 / float(values[0])
                res.append(res_value)
                fsc.append(float(values[1]))
        return [Curve(self.filename, self.pix, fsc=fsc, res=res, curve_type=f"fsc_{self.software}", label=PurePosixPath(self.filename).stem)]


    def import_fsc_imagic_csv(self):
        """
        Reads imagic.csv file with 1/2-bit and 3-sigma cut-offs and outputs a list of 3 curves.
        Imagic header: "Ring in Fourier Space";"1 / Resolution [1/A]"; "Fourier Shell Correlation"; halfbit;Sigma
        """
        print(f" => Working on {self.filename} file\n")

        with open(self.filename, "r") as f:
            lines = f.readlines()
            # The first value in the lists below corresponds ro DC
            fsc = [1]
            res = [np.nan]
            halfbit = [1]
            threesigma = [np.nan]
            for line in lines[2:]:
                values = line.split(";")
                res_value = 1 / float(values[1])
                res.append(res_value)
                fsc.append(float(values[2]))
                halfbit.append(float(values[3]))
                if float(values[4]) != 0:
                    threesigma.append(float(values[4]))
                else:
                    threesigma.append(np.nan)

        curve_fsc = Curve(self.filename, self.pix, fsc=fsc, res=res, curve_type="fsc_imagic", label="FSC " + PurePosixPath(self.filename).stem)
        curve_halfbit = Curve(f"halfbit {self.filename}", self.pix, fsc=halfbit, res=res, curve_type="halfbit", label="Half-Bit") 
        curve_threesigma = Curve(f"threesigma {self.filename}", self.pix, fsc=threesigma, res=res, curve_type="threesigma", label="3-Sigma")
        return [curve_fsc, curve_halfbit, curve_threesigma]


    def import_fsc_cistem(self):
        """
        For a cistem file outputs a fsc dictionary like in import_fsc_xml
        standard cisTEM v1 header:
        Class 1 - Estimated Res = 3.01 Å (Refinement Limit = 4.00 Å)
        -------------------------------------------------------------

        Shell | Res.(Å) | Radius |  FSC  | Part. FSC | √Part. SSNR | √Rec. SSNR
        -----   -------   ------    ---   ----------   -----------   ----------
        """

        curves = []
        print(f" => Working on {self.filename} file\n")
        # pattern for estimated resolution search:
        pattern = r"Estimated Res = (\d+\.\d+)"
        with open(self.filename, "r") as f1:
            lines = f1.readlines()
            fsc = []
            res = []
            class_number = 1
            class_number_res = 1
            for line in lines:
                values = line.split()
                if values:
                    if len(values) != CISTEM_FSCFILE_NUM_OF_COLUMNS:
                        # ignores header of the table. Assumes CISTEM_FSCFILE_NUM_OF_COLUMNS in cistem files like in cisTEM ver 1
                        if values[0] == "Class":
                            curve=Curve(f"{self.filename} Class {class_number_res}")
                            match = re.search(pattern, line)
                            if match:
                                estimated_res = match.group(1)
                                print(
                                    f"Estimated resolution of Class {class_number_res} by cisTEM: {estimated_res} Å "
                                )  # Output: 3.01
                            else:
                                print(
                                    " => Warning! No estimated resolution found in the cisTEM {self.filename} file"
                                )
                            class_number_res += 1
                            if values[1] == "1":
                                # write out for #1
                                pass
                            else:
                                # write out for #2 and further
                                curve = Curve(f"{self.filename} Class {class_number_res}", fsc=fsc, res=res, curve_type="fsc_cistem", label=PurePosixPath(self.filename).stem + f" Class {class_number}")
                                curves.append(curve)
                                # delete values for previous curve
                                fsc = []
                                res = []
                                frac_of_nq = []
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
            curve = Curve(f"{self.filename} Class {class_number_res}", self.pix, fsc=fsc, res=res, curve_type="fsc_cistem", label=PurePosixPath(self.filename).stem + f" Class {class_number}")
            curves.append(curve)
        return curves


    def import_fsc_cryosparc_txt(self):
        """
        For a single-curve cistem file outputs a fsc dictionary like in import_fsc_xml
        Cryosparc txt first line: wave_number	fsc_nomask	fsc_sphericalmask	fsc_loosemask	fsc_tightmask	fsc_noisesub_raw	fsc_noisesub_true	fsc_noisesub
        the last column (fsc_noisesub) is "Corrected FSC"
        Resolution = (box size * pixel size) / wave number
        """
        print(f" => Working on {self.filename} file\n")
        wave_number = []
        res = []

        fsc_nomask = []
        fsc_sphericalmask = []
        fsc_loosemask = []
        fsc_tightmask = []
        fsc_noisesub_raw = []
        fsc_noisesub_true = []
        fsc_corrected = []

        with open(self.filename, "r") as f:
            lines = f.readlines()
            first_line = lines[0].split()
            wave_number_ind = first_line.index("wave_number")
            fsc_nomask_ind = first_line.index("fsc_nomask")
            fsc_sphericalmask_ind = first_line.index("fsc_sphericalmask")
            fsc_loosemask_ind = first_line.index("fsc_loosemask")
            fsc_tightmask_ind = first_line.index("fsc_tightmask")
            fsc_noisesub_raw_ind = first_line.index("fsc_noisesub_raw")
            fsc_noisesub_true_ind = first_line.index("fsc_noisesub_true")
            fsc_noisesub_ind = first_line.index("fsc_noisesub")
            for line in lines[1:]:
                values = line.split()
                wave_number.append(float(values[wave_number_ind]))
                res_val = box * pix / float(values[wave_number_ind])
                res.append(res_val)
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

        curve_nomask = Curve(self.filename + " nomask", self.pix, fsc=fsc_nomask, res=res, curve_type="fsc_cryosparc_nomask", label="No mask")

        curve_sphericalmask = Curve(self.filename + " sphericalmask", self.pix, fsc=fsc_sphericalmask, res=res, curve_type="fsc_cryosparc_sphericalmask", label="Spherical mask")

        curve_loosemask = Curve(self.filename + " loosemask", self.pix, fsc=fsc_loosemask, res=res, curve_type="fsc_cryosparc_loosemask", label="Loose mask")

        curve_tightmask = Curve(self.filename + " tightmask", self.pix, fsc=fsc_tightmask, res=res, curve_type="fsc_cryosparc_tightmask", label="Tight mask")

        # The function won't return the next two two
        curve_noisesub_raw = Curve(self.filename + " noisesub_raw", self.pix, fsc=fsc_noisesub_raw, res=res, curve_type="fsc_cryosparc_noisesub_raw", label="noisesub_raw")
        curve_noisesub_true = Curve(self.filename + " noisesub_true", self.pix, fsc=fsc_noisesub_true, res=res, curve_type="fsc_cryosparc_noisesub_true", label="noisesub_true")

        curve_corrected = Curve(self.filename + " noisesub_ind", self.pix, fsc=fsc_corrected, res=res, curve_type="fsc_cryosparc_noisesub_ind", label="Corrected")
        
        return [
            curve_nomask,
            curve_sphericalmask,
            curve_loosemask,
            curve_tightmask,
            curve_corrected,
        ]


def make_fsc_plots(curves, units, pix, threesigma_fsc=None, halfbit_fsc=None):
    """Plots curves from a list of dictionaries:"""
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
    if units == "nq":
        plt.xlabel(X_LABEL_FRAC_OF_NQ, fontweight=FONTWEIGHT)
        x_formatter = FixedFormatter(X_TICKS_FRAC_OF_NQ)

    elif units == "angstrom":
        plt.xlabel(X_LABEL_RESOLUTION, fontweight=FONTWEIGHT)
        # max value in the list of dictionaries
        # all_res_values = [res_val for curve in curves for res_val in curve["res"]]
        # max_res = max(all_res_values)
        # min_res = min(all_res_values)
        x_tick_values[0] = ""
        x_tick_values[1:] = [
            f"{(2*pix/val):.1f}" for val in x_tick_values[1:]
        ]
        x_formatter = FixedFormatter(x_tick_values)

    for i, curve in enumerate(curves):
        if args.label:
            plt.plot(
                curve.frac_of_nq,
                curve.fsc,
                linewidth=CURVE_LINEWIDTH,
                color=f"C{i}",
                label=curve.label,
            )
            plt.legend()
        else:
            plt.plot(
                curve.frac_of_nq,
                curve.fsc,
                linewidth=CURVE_LINEWIDTH,
                color=f"C{i}",
            )

    if args.no_threshold == False:
        plt.plot(
            [X_RIGHT, X_LEFT],
            [FIXED_THRESHOLD, FIXED_THRESHOLD],
            linewidth=FIXED_THRESHOLD_LINEWIDTH,
            color=FIXED_THRESHOLD_COLOR,
            linestyle=FIXED_THRESHOLD_LINESTYLE,
        )
        y_formatter = FixedFormatter(Y_TICKS_LABELS_0143)
        y_locator = FixedLocator(Y_TICKS_0143)

    else:
        y_formatter = FixedFormatter(Y_TICKS_LABELS_SIMPLE)
        y_locator = FixedLocator(Y_TICKS_SIMPLE)

    ax = plt.gca()
    ax.xaxis.set_major_formatter(x_formatter)
    ax.yaxis.set_major_formatter(y_formatter)
    ax.xaxis.set_major_locator(x_locator)
    ax.yaxis.set_major_locator(y_locator)
    plt.axhline(0, color="black", linewidth=0.5)
    plt.show()


def determine_resolution(
    curve,
    pix,
    y_threshold=FIXED_THRESHOLD,
    x_threshold_values=None,
    y_threshold_values=None,
    output_as_text=True,
):
    """
    For two lists determining a FSC curve determines resolution based on the specified threshold
    """
    # Interpolate the y-values of the curve
    if curve.curve_type == "threesigma" or curve.curve_type == "halfbit":
        return ""
    x_curve = curve.frac_of_nq
    y_curve = curve.fsc

    f_curve = interp1d(x_curve, y_curve, fill_value="extrapolate")
    if x_threshold_values == None:
        x_threshold_values = np.linspace(min(x_curve), max(x_curve), 1000)
    # If the threshold curve is not provided, generate it
    if y_threshold_values is None:
        y_threshold_values = np.full_like(x_threshold_values, y_threshold)

    # Interpolate the y-values of the threshold curve
    f_threshold = interp1d(
        x_threshold_values, y_threshold_values, fill_value="extrapolate"
    )

    # Calculate the difference between the two curves for all x values
    intersection_diff = f_curve(x_curve) - f_threshold(x_curve)

    # Find indices where the difference changes sign, indicating a root
    root_indices = np.where(np.diff(np.sign(intersection_diff)))[0]

    # Iterate over the indices and use root_scalar to refine the roots
    intersection_x_values = []
    for idx in root_indices:
        root = root_scalar(
            lambda x: f_curve(x) - f_threshold(x),
            bracket=[x_curve[idx], x_curve[idx + 1]],
        )
        if root.converged:
            if root.root != 0:
                intersection_x_values.append(root.root)

    # Calculate resolution
    if intersection_x_values:
        resolution_angstrom = 2 * pix / min(intersection_x_values)
    else:
        resolution_angstrom = np.nan

    if output_as_text:
        return f" ({resolution_angstrom:.1f}Å)"
    else:
        return resolution_angstrom




def main(args):
    """
    Files should be read into a list of dictionaries (curves)
    {"curve_name": "fsc_01",
    "fsc"        : [list_of_fsc_values],
    "res"        : [list_of_res_values],
    "frac_of_nq" : [list_of_frac_of_nq_val]
    "curve_type" : "fsc_relion"/"fsc_cryosparc_XXX"/"fsc_cistem"/"fsc_imagic"/"halfbit"/"threesigma"
    "0.143"      : resolution according to 0.143
    "halfbit"    : resolution according to halfbit
    "threesigma" : resolution according to threesigma
    "label"      : label in the plot
    }
    """

    curves = []
    halfbit_fsc = None
    threesigma_fsc = None

    # Extracts fsc curves
    for fsc_file in args.i:
        FSC_analyser(args.pix, fsc_file)
        #curves.extend(run_file_analysis(fsc_file, args))

    # Determine resolution for all curves
    if args.resolution:
        count_halfbit = 0
        count_threesigma = 0
        resolution_halfbit = None
        resolution_threesigma = None
        # Search for halfbit_curve and threesigma_curve in curves
        for curve in curves:
            if curve.curve_type == "halfbit":
                halfbit_curve = curve
                halfbit_fsc = curve.fsc
                count_halfbit += 1
            elif curve.curve_type == "threesigma":
                threesigma_curve = curve
                threesigma_fsc = curve.fsc
                count_threesigma += 1
        if count_halfbit > 1 or count_threesigma > 1:
            print(
                f" => WARNING! SEVERAL threesigma AND/OR halfbit CURVES DETECTED! Curves corresponding to {curve.curve_name} will be used!"
            )

        for curve in curves:
            if curve.curve_type != "halfbit" and curve.curve_type != "threesigma":
                resolution_0143 = determine_resolution(
                    curve, args.pix, output_as_text=False
                )
                curve.fixed_0143 = resolution_0143
                if args.thresholds_all:
                    if "halfbit_curve" in locals() and "threesigma_curve" in locals():
                        resolution_halfbit = determine_resolution(
                            curve,
                            args.pix,
                            x_threshold_values=halfbit_curve.frac_of_nq,
                            y_threshold_values=halfbit_curve.fsc,
                            output_as_text=False,
                        )
                        resolution_threesigma = determine_resolution(
                            curve,
                            args.pix,
                            x_threshold_values=threesigma_curve.frac_of_nq,
                            y_threshold_values=threesigma_curve.fsc,
                            output_as_text=False,
                        )
                        curve.threesigma = resolution_threesigma
                        curve.halfbit = resolution_halfbit
                        curve.label += f" ({resolution_0143:.1f}Å by 0.143)"
                    else:
                        sys.exit(
                            " => ERROR! No half-bit and/or 3-sigma curve detected! Consider running without --thresholds_all option"
                        )
                elif not args.no_threshold:
                    curve.label += f" ({resolution_0143:.1f}Å)"

            elif (
                curve.curve_type == "threesigma"
                and len(curves) <= 3
                and args.thresholds_all
            ):
                curve.threesigma = resolution_threesigma
                curve.label += f" ({resolution_threesigma:.1f}Å)"
            elif (
                curve.curve_type == "halfbit"
                and len(curves) <= 3
                and args.thresholds_all
            ):
                curve.halfbit = resolution_halfbit
                curve.label += f" ({resolution_halfbit:.1f}Å)"
    # plots them
    make_fsc_plots(curves, args.units, args.pix, threesigma_fsc=threesigma_fsc, halfbit_fsc=halfbit_fsc)


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

 imagic (.txt files): {PROG} --i imagic.csv --pix 1.09 --units angstrom --resolution --label --thresholds_all
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
        choices=["nq", "angstrom"],
        default="angstrom",
        help='Options: angstrom/nq | X-axis as a "Fraction of Nyquist" or "1/Frequency"',
        metavar="",
    )
    add("--label", default=False, action="store_true", help="Label on the plot")
    add(
        "--resolution",
        default=False,
        action="store_true",
        help="Show resolution and 0.143 curve on the plot",
    )
    add(
        "--no_threshold",
        default=False,
        action="store_true",
        help="Hide 0.143 threshold on the plot",
    )
    add(
        "--thresholds_all",
        default=False,
        action="store_true",
        help='Include halfbit and 3-sigma thresholds generated by Imagic "FSC" program (free)',
    )
    args = parser.parse_args()
    print(description)

    if args.label == False and args.resolution == True:
        sys.exit(" => ERROR! --resolution option can't be used without --label option")

    print(f"\n\n => Input parameters: ")
    for key, value in vars(args).items():
        print(f"  --{key}  {value}")
    print()
    if len(args.i) > 1:
        print(
            " => WARNING! Multiple files are used! Pixel size and box sizes (for cryosparc .txt files) should be the same!"
        )

    main(args)
