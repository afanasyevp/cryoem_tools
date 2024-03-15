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

import os
import re
import sys
import argparse
import glob
from pathlib import Path
import subprocess
import shutil
import time

PROG = Path(__file__).name
VER = 20240303
UNDERLINE = ("=" * 70) + ("=" * (len(PROG) + 2))  # line for the output


class _HelpAction(argparse._HelpAction):
    ''' 
    Prints all options for all subparsers in the help 
    From: https://stackoverflow.com/questions/20094215/argparse-subparser-monolithic-help-output
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        parser.print_help()
        # retrieve subparsers from parser
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)]
        # there will probably only be one subparser_action,
        # but better save than sorry
        for subparsers_action in subparsers_actions:
            # get all subparsers and print help
            for choice, subparser in subparsers_action.choices.items():
                print("Subparser '{}'".format(choice))
                print(subparser.format_help())
        parser.exit()

class help_I_O:
    ...
class I_O_motioncorr:
    def __init__(self, options):
        self.motioncorr_suffix = options.motioncorrsuffix
        self.software = options.software
        self.Patch = options.Patch
        self.RotGain = options.RotGain
        self.FlipGain = options.FlipGain
        self.Iter = options.Iter
        self.Tol = options.Tol
        self.SplitSum = options.SplitSum
        self.kV = options.kV
        self.PixSize = options.PixSize
        self.FmDose = options.FmDose
        self.Bft = options.Bft
        self.GpuMemUsage = options.GpuMemUsage
        self.FtBin = options.FtBin
        self.LogDir = options.LogDir
        self.OutStar = options.OutStar
        self.OutStack = options.OutStack
        self.Crop = options.Crop

class I_O_alignframes:
    def __init__(self, options):
        self.framespath = options.framespath
        self.mdocpath = options.mdocpath
        self.outdir = options.outdir
        self.mdocsuffix = options.mdocsuffix
        self.alifrsuffix = options.alifrsuffix 
        self.gpu = options.gpu
        self.pixel = options.pixel
        self.gain = options.gain
        self.defect = options.defect
        self.dark = options.dark
        self.vary = options.vary
        self.software = options.software

        @property
        def binning(self):
            return self._binning

        @binning.setter
        def binning(self, binning):
            if binning:
                res = self.list_to_str_commas(binning)
            self._binning = res

    @property
    def software(self):
        return self._software

    @software.setter
    def software(self, software):
        #if software == "motioncorr":
        #    sys.exit("Function is not implemented yet")
        software_found = shutil.which(software)
        if software_found:
            print(f"\n  Using {software_found} program to align frames")
        else:
            sys.exit(
                f"\n => ERRROR! {software} is not found! Check if it is sourced! "
            )
        self._software = software_found
        return self._software

    # @software.setter
    # def find_executable(pattern):
    #     # for a given pattern searches among all executables for a command and returns one or an error
    #     executable_search_cmd = f"which `compgen -c  | grep {pattern}`"
    #     p = subprocess.Popen(
    #         executable_search_cmd,
    #         stdout=subprocess.PIPE,
    #         stderr=subprocess.STDOUT,
    #         shell=True,
    #         executable="/bin/bash",
    #     )
    #     # (output, err) = p.communicate()
    #     executables = set()
    #     # executables.remove('')
    #     while True:
    #         line = p.stdout.readline()
    #         candidate = line.decode("utf-8").rstrip("\n")
    #         if len(candidate) > 0:
    #             executables.add(candidate)
    #         if not line:
    #             break
    #     # print("executables: ", executables)
    #     #executables.remove(shutil.which("t_aretomo.py"))
    #     if len(executables) == 0:
    #         sys.exit(f" => {pattern} software was not found!")
    #     elif len(executables) > 1:
    #         print(f" => ERROR! The following papckages were found based on pattern '{pattern}': ")
    #         [print(executable) for executable in iter(executables)]
    #         sys.exit(f"Please modify '{pattern}' pattern to address more specific program name")
    #     else:
    #         if "which" in list(executables)[0]:
    #             sys.exit(f" => ERROR!! {pattern} software was not found!")
    #         else:
    #             print(f" => {list(executables)[0]} software will be used")
    #             return list(executables)[0]

    @property
    def framespath(self):
        return self._framespath

    @framespath.setter
    def framespath(self, framespath):
        if os.path.exists(framespath):
            self._framespath = self.fix_path(framespath)
        else:
            sys.exit(f" => ERROR! {framespath} folder does not exist!")
        
    @property
    def mdocpath(self):
        return self._mdocpath

    @mdocpath.setter
    def mdocpath(self, mdocpath):
        if os.path.exists(mdocpath):
            self._mdocpath = self.fix_path(mdocpath)
        else:
            sys.exit(f" => ERROR! {mdocpath} folder does not exist!")

    @property
    def outdir(self):
        return self._outdir

    @outdir.setter
    def outdir(self, outdir):
        self.mkdir(outdir)
        self._outdir = self.fix_path(outdir)

    @property
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, gain):
        if gain:
            if os.path.isfile(gain):
                gain = self.fix_path(gain)
            else:
                print(
                    f" => WARNING: {gain} file is not found! No gain normalisation will be applied!"
                )
                gain = None
        else:
            print(
                " => WARNING! No gain file has been provided! No gain normalisation will be applied."
            )
        self._gain = gain
    
    @property
    def dark(self):
        return self._dark

    @dark.setter
    def dark(self, dark):
        if dark:
            if os.path.isfile(dark):
                dark = self.fix_path(dark)
            else:
                print(
                    f" => WARNING: {dark} file is not found! No dark reference will be applied!"
                )
                dark = None
        #else:
            #print(
            #    " => WARNING! No dark reference has been provided! No dark reference will be applied."
            #)
            
        self._dark = dark

    @property
    def defect(self):
        return self._defect

    @defect.setter
    def defect(self, defect):
        if defect:
            if os.path.isfile(defect):
                defect = self.fix_path(defect)
            else:
                print(
                    f" => WARNING: {defect} file is not found! No defect file will be used!"
                )
                defect = None
        self._defect = defect

    @property
    def gpu(self):
        return self._gpu

    @gpu.setter
    def gpu(self, gpu):
        if gpu:
            gpu = self.list_to_str_commas(gpu)
        self._gpu = gpu

    @staticmethod
    def list_to_str_commas(input_list):
        my_string = ""
        my_string = ",".join(input_list)
        return my_string

    @staticmethod
    def fix_path(old_path):
        """
        fixes for ~ and returns abspath
        """
        new_path = os.path.expanduser(old_path)
        return os.path.abspath(new_path)

    @staticmethod
    def run_cmds(cmds):
        for mdoc, cmd in cmds.items():
            print(f"\n Running command: {cmd} \n")
            try:
                p = subprocess.call(cmd, shell=True)
                # p=subprocess.check_output(cmd, shell=True)
            except subprocess.CalledProcessError:
                sys.exit(
                    f"\n  => ERROR!!! In running command: \n     {cmd} \n\n => Please see the ERROR above and check your inputs. \n"
                )

    def mkdir(self, outdirname):
        if not os.path.exists(outdirname):
            os.mkdir(outdirname)
        return self.fix_path(outdirname)

    def print_output(self):
        """
        Prints values for each attribute
        """
        print(f"\n  === Input parameters === ")
        for attr, value in self.__dict__.items():
            if attr[0] == "_":
                if attr == "_binning":
                    print(f" BIN: {value}")
                else:
                    print(f" {attr[1:].upper()}: {value}")
            else:
                print(f" {attr}: {value}")


class Dataset(I_O_alignframes):
    def __init__(self, options):
        super().__init__(options)
        self.options = options
        self.name = os.path.basename(options.mdocpath)
        self.TSs = {}  # key: mdocfilename value:TS instance
        self.cmds = {}  # commands to run

    @staticmethod
    def get_filename(filename, suffix):
        """for a filename returns name without a path and suffix"""
        basename = os.path.basename(filename)
        pattern = re.escape(suffix) + r"$"
        regex = re.compile(pattern)
        match = regex.search(basename)
        if match:
            return basename[: match.start()]
        else:
            print(f"Match not found in get_filename({filename}, {suffix}) function! ")

    def find_targets(self):
        """
        In the given mdoc_abspath finds unfinished targets to process.
        """
        list_all = glob.glob(
            self.options.mdocpath + "/*" + self.options.mdocsuffix, recursive=False
        )
        list_done = glob.glob(self.options.outdir + "/*" + self.options.alifrsuffix)
        if len(list_all) == 0:
            sys.exit(
                (
                    f" => ERROR! No {self.options.mdocsuffix} input files found in {self.options.mdocpath} folder!"
                )
            )
        list_todo = []
        dict_all = {}
        dict_done = {}
        dict_todo = {}
        for i in list_all:
            dict_all[self.get_filename(i, self.options.mdocsuffix)] = i
        for i in list_done:
            dict_done[(os.path.basename(i))[: -len(self.options.alifrsuffix)]] = i
        dict_todo = {
            key: value for key, value in dict_all.items() if key not in dict_done
        }
        list_todo = sorted(list(dict_todo.values()))
        for _ in list_todo:
            # ts_fullname = self.options.mdocpath + "/" + mdoc_stemname + self.options.mdocsuffix
            ts = TS(self.options, _)
            self.TSs[_] = ts
        print(
            f" \n  {len(list_todo)} TS to process were found (out of {len(list_all)}) "
        )
        return self.TSs


class TS(Dataset):
    def __init__(self, options, mdocfile):
        # super().__init__(options)
        self.options = options
        self.mdocfile = mdocfile
        self.tilts = {}
        self.aliframes_cmd = None
        self.general_info = {}
        self.movies_tiff = False
    
    #def movies_tiff(self, movie_tiff):
    #    if os.path.
    #        self._movies_tiff = True




    def fetch_info_from_mdoc(self):
        # print(f"  Fetching info from {self.mdocfile} mdoc file...")
        general_info = {}
        with open(self.mdocfile, "r") as f:
            lines = f.readlines()
            line_counter = 1
            ts_start = False
            tilt_new = False
            while lines:
                line = lines.pop(0)
                line = line.strip()
                if "[ZValue" in line:
                    ts_start = True
                    line_list = line.split("=")
                    ZValue = int(line_list[-1].split("]")[0][1:])
                    tilt = Tilt(ZValue)
                    tilt_new = False
                if "=" in line and ts_start and tilt_new == False:
                    line_list = line.split("=")
                    k = line_list[0].split()[0].strip()
                    v = " ".join(line_list[1:])
                    if k == "SubFramePath":
                        """
                        Example of the old SubFramePath: [full_path_to_the_dataset]\frames\YYMMDD_dataset_3931.tif
                        NewSubFramePath would be: [full_path_to_frames_folder]/YYMMDD_dataset_3931.tif
                        """
                        newdir = os.path.dirname(self.options.framespath)
                        NewSubFramePath = newdir + "/" + pathlib.PureWindowsPath(v).name
                        setattr(tilt, "NewSubFramePath", NewSubFramePath)
                    setattr(tilt, k, v)
                elif ts_start:
                    self.tilts[tilt.ZValue] = tilt
                    tilt_new = True
                else:  # general header info (first ~10 lines
                    if "=" in line and line[0] != "[":
                        line_list = line.split("=")
                        key = line_list[0].strip()
                        general_info[key] = " ".join(line_list[1:])
                    else:
                        general_info["other_info_line_" + str(line_counter)] = line

    def create_aliframes_cmd(self):
        """
        for args, creates a command template for bash with inputs and outputs
        """
        ts_outputname = (
            self.options.outdir
            + "/"
            + self.get_filename(self.mdocfile, self.options.mdocsuffix)
            + self.options.alifrsuffix
        )

        filtered_options = {
            k: v for k, v in vars(self.options).items() if v is not None
        }
        del filtered_options["_mdocpath"]
        del filtered_options["_outdir"]
        del filtered_options["alifrsuffix"]
        del filtered_options["mdocsuffix"]
        del filtered_options["log"]
        filtered_options["path"] = filtered_options.pop("_framespath")

        cmd = f"{filtered_options.pop('_software')} "
        cmd += f"-mdoc {self.mdocfile} -output {ts_outputname} "
        cmd += f"-binning {filtered_options.pop('_binning')} "
        for key, value in filtered_options.items():
            cmd += f" -{key} {value} "
        self.aliframes_cmd = cmd
        # print( f"\n  aliframes command was generated for {self.mdocfile}: \n {self.aliframes_cmd} ")
        return cmd

    def create_motioncorr_cmd(self):
        """
        for args, creates a command template for bash with inputs and outputs
        """
        ts_outputname = (
            self.options.outdir
            + "/"
            + self.get_filename(self.mdocfile, self.options.mdocsuffix)
            + self.options.motioncorrsuffix
        )
        motioncorr_temp=I_O.mkdir(self.framespath+"/motioncorr_temp")
        tilt_outputname=self.framespath
        filtered_options = {
            k: v for k, v in vars(self.options).items() if v is not None
        }
        del filtered_options["_mdocpath"]
        del filtered_options["_outdir"]
        del filtered_options["motioncorrsuffix"]
        del filtered_options["mdocsuffix"]
        del filtered_options["log"]
        filtered_options["path"] = filtered_options.pop("_framespath")



        
        cmd = f"{filtered_options.pop('_software')} "
        cmd += f"-InTiff"
        cmd += f"-mdoc {self.mdocfile} -output {ts_outputname} "
        cmd += f"-binning {filtered_options.pop('_binning')} "
        for key, value in filtered_options.items():
            cmd += f" -{key} {value} "
        self.aliframes_cmd = cmd
        # print( f"\n  aliframes command was generated for {self.mdocfile}: \n {self.aliframes_cmd} ")
        return cmd

class Tilt(TS):
    def __init__(self, ZValue):
        # super().__init__(stemname, mdocfile, outputname, mdocsuffix, framespath)
        self.NewSubFramePath = None
        self.ZValue = ZValue
        self.MinMaxMean = None
        self.TiltAngle = None
        self.StagePosition = None
        self.StageZ = None
        self.Magnification = None
        self.Intensity = None
        self.ExposureDose = None
        self.DoseRate = None
        self.PixelSpacing = None
        self.SpotSize = None
        self.Defocus = None
        self.ImageShift = None
        self.RotationAngle = None
        self.ExposureTime = None
        self.Binning = None
        self.CameraIndex = None
        self.DividedBy2 = None
        self.OperatingMode = None
        self.UsingCDS = None
        self.MagIndex = None
        self.LowDoseConSet = None
        self.CountsPerElectron = None
        self.TargetDefocus = None
        self.SubFramePath = None
        self.NumSubFrames = None
        self.FrameDosesAndNumber = None
        self.DateTime = None
        self.NavigatorLabel = None
        self.FilterSlitAndLoss = None
        self.UncroppedSize = None
        self.RotationAndFlip = None
        self.SpecimenShift = None
        self.EucentricOffset = None
        self.CtfFind = None

    def __str__(self):
        return f"ZValue: {self.ZValue} TiltAngle: {self.TiltAngle} "


def main():
    description = f"""
=================================== {PROG} ===================================
 batch processing for the movie alignments using: 
  - aliframes (IMOD)
  - MotionCor2_1.6.3 
 
  All arguments should be space separated. See full list of arguments with:
  {PROG} --help

 [version {VER}]
 Written and tested in python3.11
 Pavel Afanasyev
 https://github.com/afanasyevp/cryoem_tools 
 {UNDERLINE}"""

    examples=f'''EXAMPLES:
 {PROG} alignframes --framespath ./ --mdocpath ./ --gain gain.mrc --gpu 0 1
 {PROG} motioncorr --framespath ./ --mdocpath ./ --DefectFile defects.txt
    '''
    # RawDescriptionHelpFormatter as formatter_class= indicates that description and epilog are already correctly formatted and should not be line-wrapped:
    # ArgumentDefaultsHelpFormatter automatically adds information about default values to each of the argument help messages
    # RawTextHelpFormatter maintains whitespace for all sorts of help text, including argument descriptions
    class UltimateHelpFormatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
        pass

    parser = argparse.ArgumentParser(prog=PROG, formatter_class=UltimateHelpFormatter, add_help=False, description=description, epilog=examples) 
    # TODO: add usage='%(prog)s [options]', epilog=output_text
    parser.add_argument ('-h', '--help', action=_HelpAction, help='show help message with a full list of arguments')

    subparsers=parser.add_subparsers(dest="software")
    alignframes_parser=subparsers.add_parser("alignframes", help="Use alignframes", formatter_class=UltimateHelpFormatter)
    motioncorr_parser=subparsers.add_parser("motioncorr",  help="Use motioncorr", formatter_class=UltimateHelpFormatter)
    add_a=alignframes_parser.add_argument
    add_m=motioncorr_parser.add_argument

    # alignframes options
    add_a("--framespath", default="./", help="Path to the folder with your frames files", metavar="")
    add_a("--mdocpath", default="./", help="Path to the folder with your mdoc files", metavar="")
    add_a("--outdir", default="../aliframes_TS", help="Output directory name", metavar="")
    add_a("--mdocsuffix", default=".mrc.mdoc", help="Suffix of the .mdoc files", metavar="")
    add_a("--alifrsuffix", default="_alifr.mrc", help="Suffix of the output files: for stacktilt_01.mrc.mdoc an aligned stack stacktilt_01_alifr.mrc will be created", metavar="")
    add_a("--gpu", nargs="+", default=[], help="Which GPUs to use. Space separated. For alignframes: GPU 0 to use the best GPU on the system, or the number of a specific GPU, numbered from 1", metavar="")
    add_a("--pixel", help="Pixel size. mdoc value will be overwritten", metavar="")
    add_a("--gain", help="Gain file for non-normalised frames", metavar="")
    add_a("--defect", help="Defect file", metavar="")
    add_a("--dark", help="Dark reference file", metavar="")
    add_a("--label", default=".mdoc", help="Files to run alignments on.", metavar="")
    add_a("--binning", default=["2 1"], nargs="+", help="Binning (bin) option in alignframes. Space separated", metavar="")
    add_a("--vary", type=float, default=0.25, help="Vary option in alignframes", metavar="")

    #Motioncorr options
    add_m("--motioncorrsuffix", default="_alimc.mrc", help="Suffix of the output files: for stacktilt_01.mrc.mdoc an aligned stack stacktilt_01_alimc.mrc will be created", metavar="")
    add_m("--framespath", default="./", help="Path to the folder with your frames files", metavar="")
    add_m("--mdocpath", default="./", help="Path to the folder with your mdoc files", metavar="")
    add_m("--outdir", default="../motioncorr_TS", help="Output directory name", metavar="")
    add_m("--mdocsuffix", default=".mrc.mdoc", help="Suffix of the .mdoc files", metavar="")
    add_m("--alifrsuffix", default="_alimc.mrc",help="Suffix of the output files: for stacktilt_01.mrc.mdoc an aligned stack stacktilt_01_alimc.mrc will be created", metavar="")
    add_m("--Patch", nargs="+", default="5 5", help="Patches on which the local motion is measured", metavar="")
    add_m("--DefectFile", default=None, help="Defect file", metavar="")
    add_m("--RotGain", default=0, help="Rotate gain reference: 0 - no rotation; 1 - rotate 90°; 2 - rotate 180°; 3 - rotate 270°",metavar="")
    add_m("--FlipGain", default=0, type=int, help="Flip gain reference: 0 - no flip; 1 - flip upside down; 2 - flip left right", metavar="")
    add_m("--Dark", default=None, help="Subtract dark reference", metavar="")
    add_m("--Iter", default=15, type=int, help="Alignment configuration", metavar="")
    add_m("--Tol", default=0.2, type=float, help="Alignment configuration", metavar="")
    add_m("--SplitSum", default=0, choices=["0", "1"], help='Use "1" to generate partial sums of odd/even', metavar="")
    add_m("--kV", default=300, help="Voltage for dose weighting. Not impemented", metavar="")
    add_m("--PixSize", default=0, help="Pixel size for dose weighting. Not impemented", metavar="")
    add_m("--FmDose", default=0, help="Not recommended to change. Dose weighting is not implemented here", metavar="")
    add_m("--Bft", default="500 100", nargs="+", help="two parameters: for global-motion and local-motion", metavar="")
    add_m("--GpuMemUsage", default=0.75, help="GPU memory is used to buffer movie frames", metavar="")
    add_m("--FtBin", default=1, help="Image binning by Fourier cropping", metavar="")
    add_m("--LogDir", default="./", help="Directory for log files", metavar="")
    add_m("--OutStar", default=0, help="Generate the star file for Relion 4 polishing", metavar="")
    add_m("--OutStack", default=["0 1"], nargs="+", help="First value: create aligned stack. Second: binning", metavar="")
    add_m("--Crop", default=["0 0"], nargs="+", help="Crop to the given size", metavar="")
    #add_m("--UseGpus", default=2, help="", metavar="")
    #add_m("--TiffOrder", default=1, help="", metavar="")

    # Return help with no arguments:
    args = parser.parse_args()
    if len(sys.argv) == 1 :
        parser.print_help()
        sys.exit(1)
        
    print(args)
    cwd = os.getcwd()
    
    args.gpu = "aaa"
    print(args)


    #if args.software == "alignframes":
    #    i_o = I_O_alignframes(args)
    #else:
    #    i_o = I_O_motioncorr(args)
    # # i_o.print_output()
    # os.chdir(i_o.mdocpath)
    # print(f" \n  Working in {i_o.mdocpath} directory")

    # # Check the data: create a dataset class
    # dataset = Dataset(i_o)
    # # check out the unfinished jobs and select targets to process
    # dataset.find_targets()

    # for ts in dataset.TSs.values():
    #     ts.fetch_info_from_mdoc()
    # if args.software == "alignframes":
    #     for mdoc, ts in dataset.TSs.items():
    #         dataset.cmds[mdoc] = ts.create_aliframes_cmd()
    
    #     i_o.run_cmds(dataset.cmds)
    
    # else:
    #     for mdoc, ts in dataset.TSs.items():
    #         dataset.cmds[mdoc] = ts.create_motioncorr_cmd()
        

    # os.chdir(cwd)
    # print(f"\n\n  Returning to {cwd} directory")
    # print(f"    Program {PROG} (version {VER}) completed")


if __name__ == "__main__":
    main()
