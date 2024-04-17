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
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import time
from pathlib import Path, PurePath
import sys
import re
import os

PROG = Path(__file__).name
VER = 20240417
UNDERLINE = ("=" * 70) + ("=" * (len(PROG) + 2))  # line for the output

def input_analyse(filename):
    # for an input files retuns its type: "particles_star", "micrographs_star", "micrographs_coarsened_star", "micrographs_txt", "unknown"
    inputType = 'unknown_inputType'
    if filename[-5:] == ".star":
        MainHeader, OpticsGroupData, OpticsHeader, StarData, StarFileType = star_analyze(
            filename, 10000)
        #print("MainHeader:", MainHeader)
        #print("OpticsGroupData:", OpticsGroupData)
        #print("OpticsHeader:", OpticsHeader)
        #print("StarData", StarData)
        #print("StarFileType", StarFileType)
        if StarFileType == "particles":
            inputType = "particles_star"
        elif StarFileType == "micrographs":
            #print(len(MainHeader))
            if len(MainHeader) == 3:
                random_kv = StarData.popitem()  # randomly picks one key, value
                # checks of k has a coarsening factor in the micrograph name
                match = re.search(r'(.+)(_c\d+)', random_kv[0])
                if match:
                    # print(match.group(2))
                    inputType = "micrographs_coarsened_star"
            else:
                inputType = "micrographs_star"
        else:
            print("\n => ERROR! Check your input: unknown star-file type. micrographs.star or particles.star can be used")
    else:
        print("\n => WARNING: Unknown file-type of the %s file is used: will be considered as a list of micrographs" % filename)
        inputType = "micrographs_txt"
    # print(inputType)
    return inputType


def star_analyze(star_filename, lim=0):
    '''
    creates dicrionaries from the star files: 
        OpticsHeader: everything starting with _rlnXXXX, corresponding to the data_optics section
        "# version 30001
        data_optics
        loop_
        _rlnOpticsGroupName #1" etc
        OpticsGroupData:  all the data after the previous section like:  
        "opticsGroup1           1     0.43   300     2.7     0.1"

        MainHeader:  everything starting with _rlnXXXX, corresponding to the data_movies or data_particles section
        "# version 30001
        data_particles
        loop_
        _rlnCoordinateX #1"

        StarData:  main data (alignments data for particles.star) after the previous section like:   
        "mov1.tiff 25" (movies.star) or "3.43 6.2 0.1 10 8.2 000001@Extract/job044/Micro/mov1.mrcs MotionCorr/job034 /Micro/mov1.mrc 1 0.1 6.1 6.4 44.8 0.0 1.0 0.0 " (particles.star)

    lim argument is used to limit the number of analysed lines (in bytes)

    '''
    # optics header dictionaries
    OpticsHeader = {}
    OpticsGroupData = {}
    # main header dictionaries
    MainHeader = {}
    StarData = {}
    with open(star_filename, 'r') as star_file:
        if lim == 0:
            lines = star_file.readlines()
        else:
            # to limit the number of analysed lines in bytes
            lines = star_file.readlines(lim)
    # create OpticsHeader and OpticGroupData dictionary
    for line in lines[:]:
        # print(line)
        star_line = line.split()
        #print("splitline:", star_line)
        if len(star_line) > 0:
            if line[:10] == "# version ":
                OpticsHeader['# version'] = star_line[2]
                # print("version:", OpticsHeader['# version'])
            elif line[:5] == "loop_":
                continue
            elif line[:11] == "data_optics":
                #print("Data_optics found!")
                continue
            elif line[:4] == "_rln":
                OpticsHeader[star_line[0]] = int(star_line[1][1:])
            elif line[:11] == "opticsGroup":
                OpticsGroupData[star_line[0]] = line[:-1]
                # print(OpticsGroupData)
            elif line[:5] == "data_":
                data_type = line[:-1].split("_")[1]
                #print("Data_%s found!" %data_type)
                lines.pop(0)
                break
            else:
                continue
        lines.pop(0)
    if '# version' not in OpticsHeader.keys():
        OpticsHeader['# version'] = "unknown"
    # create MainHeader dictionary with the main Header
    for line in lines[:]:
        star_line = line.split()
        if len(star_line) > 0:
            if line[:10] == "# version ":
                MainHeader['# version'] = star_line[2]
            elif line[:5] == "data_":
                data_type = line[:-1].split("_")[1]
                #print("Data_%s found!" %data_type)
                continue
            elif line[:5] == "loop_":
                continue
            elif line[:4] == "_rln":
                MainHeader[star_line[0]] = int(star_line[1][1:])
                if line[:24] == "_rlnMicrographMovieName ":
                    _rlnMicrographMovieName_index = int(
                        star_line[-1].split("#")[-1])
                    # print("_rlnMicrographMovieName_index", star_line[-1].split("#")[-1])
                elif line[:19] == "_rlnMicrographName ":
                    _rlnMicrographName_index = int(
                        star_line[-1].split("#")[-1])
                    # print("_rlnMicrographName_index", star_line[-1].split("#")[-1])
                elif line[:14] == "_rlnImageName ":
                    _rlnImageName_index = int(star_line[-1].split("#")[-1])
                    # print("_rlnImageName_index", star_line[-1].split("#")[-1])
            else:
                # create main StarData dictionary, where the key is the main header
                # identifier is  micrograph/movie/particle name
                if data_type == "micrographs":
                    StarData[star_line[(
                        _rlnMicrographName_index-1)]] = star_line
                elif data_type == "movies":
                    StarData[star_line[(
                        _rlnMicrographMovieName_index-1)]] = star_line
                elif data_type == "particles":
                    StarData[star_line[(_rlnImageName_index-1)]] = star_line
                    continue
                else:
                    print("\n => ERROR in %s file: no data type found in the %s file!" % (
                        star_filename, star_filename))
                    sys.exit(2)
                #print("break at:", line)
                # break
        lines.pop(0)
    if '# version' not in MainHeader.keys():
        MainHeader['# version'] = "unknown"
    StarFileType = data_type
    #print("MainHeader: ", MainHeader, "\n")
    #print("StarData dictionary: ", StarData, "\n")
    #print("OpticsGroupData", OpticsGroupData, "\n")
    #print("OpticsHeader: ", OpticsHeader, "\n")
    return MainHeader, OpticsGroupData, OpticsHeader, StarData, StarFileType


def extract_from_dict(StarData, list_to_extract):
    # returns new dictionary with keys matching those in the list. Distinguishes particles from micrographs by "@"
    if "@" in list_to_extract[0]:
        return ({k: v for k, v in StarData.items() if k in list_to_extract})
    else:
        return ({k: v for k, v in StarData.items() if Path(k).stem in list_to_extract})


def exclude_from_dict(StarData, list_to_exclude):
    # returns new dictionary without keys matching those in the list
    # slower solution:
    # for i in list_of_binned_micrographs:
    #    for k,v in list(StarData.items()):
    #            if i in k: del(StarData[k])§
    if "@" in list_to_exclude[0]:
        return ({k: v for k, v in StarData.items() if k not in list_to_exclude})
    else:
        return ({k: v for k, v in StarData.items() if Path(k).stem not in list_to_exclude})


def export_from_coarsened_file(star_filename):
    # Operates on the output from Select jobs: extracts only basenames of the micrographs and returns a list of those without path or extension
    #print("\n => Analysing %s file"% star_filename)
    list_of_micrographs = []
    MainHeader, OpticsGroupData, OpticsHeader, StarData, StarFileType = star_analyze(
        star_filename)
    for i in StarData.keys():
        # returns the stem of the micrograph name (no path, with extension)
        temp = PurePath(i).name
        match = re.search(r'(.+)(_c\d+.mrc)', temp)
        if match:
            origname = Path(match.group(1)).stem  # optional+".mrc"
        else:
            print("WARNING! Coarsened data not found!!!")
            origname = temp
        list_of_micrographs.append(origname)
        # print(list_of_micrographs)
    return list_of_micrographs


def export_from_txt_file(txt_micrographs_filename):
    # opens txt_micrographs file and returns a list with stem-names; no extensions
    print("\n => Analysing %s file" % txt_micrographs_filename)
    list_of_micrographs = []
    with open(txt_micrographs_filename, 'r') as txt_file:
        lines = txt_file.readlines()
    for line in lines[:]:
        if len(line) != 1:
            # returns the stem of the micrograph name (no path, no extension)
            temp = Path(line).stem
            list_of_micrographs.append(temp)
    return list_of_micrographs


def write_out_star(MainHeader, OpticsGroupData, OpticsHeader, StarData, StarFileType, Output):
    "Writes out the modified star file"
    with open(Output, "w") as outputFile:
        outputFile.write('''
# version %s
data_optics
loop_ 
''' % OpticsHeader['# version'])
        OpticsHeader_output = OpticsHeader
        OpticsGroupData_output = OpticsGroupData
        relionVersion = OpticsHeader_output.pop("# version")
        for k, v in sorted(OpticsHeader_output.items(), key=lambda item: item[1]):
            outputFile.write("%s #%s \n" % (k, v))
        for k, v in sorted(OpticsGroupData_output.items(), key=lambda item: item[1][1]):
            outputFile.write("%s\n" % v)
        outputFile.write('''
# version %s
data_%s
loop_ 
''' % (relionVersion,  StarFileType))
        MainHeader.pop("# version")
        #print("MainHeader:", sorted(MainHeader.items()))
        for k, v in sorted(MainHeader.items(), key=lambda item: item[1]):
            outputFile.write("%s #%s \n" % (k, v))
        for k, v in StarData.items():
            for item in v:
                outputFile.write("%s " % item)
            outputFile.write("\n")
        outputFile.write("\n")
    print(" => %s created!" % Output)


def write_out_list(StarData, Output):
    "Writes out the list of micrographs from the input dictionary"
    with open(Output, "w") as outputFile:
        for k, v in StarData.items():
            outputFile.write("%s\n" % Path(k).name)
        outputFile.write("\n")
    print(" => %s created!" % Output)


def check_outputname(filename):
    "Returns prefix and suffix"
    return Path(filename).stem, Path(filename).suffix


def main():
    output_text = f'''
{("=" * 35)} {PROG} {("=" * 35)}
star_modif.py modifies the micrographs_ctf.star file or particles.star file by 
exctracting/excluding micrographs (for now micrographs only) by performing search on the stem of
the micrograph name

Note:
 - The script will not operate properly on symmetry-expanded particles 
   (only unique particles will be considered)
 - The script works with files from Relion 3.1 version
 - Modify the first line of the script to change the location of the python execultable to 
the installed Anaconda's python 

{VER}

Example: star_modif.py --i particles.star --o particles_new.star --exclude micrographs.star

Written and tested in python3.8.5
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools/
 {UNDERLINE}'''
    print(output_text)
    parser = argparse.ArgumentParser(description="")
    add = parser.add_argument
    add('--i', required=True, metavar="file", nargs=1,
        help="Input file: micrographs_ctf.star or particles.star")
    add('--o', metavar="file", required=True, nargs=1,
        help="Output file: micrographs_new.star or particles_new.star")
    add('--extract', metavar="file", nargs='+',
        help="File(s) with micrograph names to extract")
    add('--exclude', metavar="file", nargs='+',
        help="File(s) with micrograph names to exclude")
    add('--list_of_micro', action="store_true",
        help="Returns just a list of unique micrographs from the input star file or the resulting one")
    add('--list_of_micro_unbinned', action="store_true",
        help="Returns just a list of unique unbinned micrographs from the input star file or the resulting one")
    args = parser.parse_args()

    parser.print_help()
    if args.extract and args.exclude:
        print("\n => ERROR!!! Check your input: only one option (--extract or --exclude can be used)")
        sys.exit(2)

    # case 1: simple modification of args.i only
    if args.extract == None and args.exclude == None:
        # output: just micrograph names
        # MotionCorr/job005/frames/FoilHole_20196805_Data_20193268_20193270_20220620_172317_fractions.mrc  => FoilHole_20196805_Data_20193268_20193270_20220620_172317_fractions.mrc
        if args.list_of_micro:
            print("\n => Writing out the list of unique micrographs")
            MainHeader, OpticsGroupData, OpticsHeader, StarData, StarFileType = star_analyze(args.i[0])
            write_out_list(StarData, args.o[0])
            sys.exit(2)
        # output: unbinned micrograph names
        # MotionCorr/job005/frames/FoilHole_20196805_Data_20193268_20193270_20220620_172317_fractions_c8.mrc  =>
        # FoilHole_20196805_Data_20193268_20193270_20220620_172317_fractions.mrc
        elif args.list_of_micro_unbinned:
            print("\n => Writing out the list of unique unbinned micrographs")
            out_list = export_from_coarsened_file(args.i[0])
            with open(args.o[0], "w") as outputFile:
                for i in out_list:
                    outputFile.write("%s.mrc\n" % i)
            # print(StarData)
            sys.exit(2)
        else:
            print("\n => ERROR!!! Check your input: Please indicate an option (--extract or --exclude) and the file with locations to extract/exclude")
            MainHeader, OpticsGroupData, OpticsHeader, StarData, StarFileType = star_analyze(
                args.i[0])
            sys.exit(2)

    MainHeader, OpticsGroupData, OpticsHeader, StarData, StarFileType = star_analyze(args.i[0])

    # check if the input types are the same: micrographs/particles
    list_of_inputTypes = []
    if args.extract:
        for argExtr in args.extract:
            inputType = input_analyse(argExtr)
            list_of_inputTypes.append(inputType)
        temp = list_of_inputTypes.pop()
        for i in list_of_inputTypes:
            if len(list_of_inputTypes) > 0:
                if i.split("_")[0] == "micrographs" and temp[:11] == "micrographs":
                    continue
                elif i.split("_")[0] == "particles" and temp[:9] == "particles":
                    continue
                else:
                    print(
                        "\n => ERROR! Different input types detected! The --extract input arguments should be micrographs-only or particles-only")
                    sys.exit(2)
    if args.exclude:
        for argExcl in args.exclude:
            inputType = input_analyse(argExcl)
            list_of_inputTypes.append(inputType)
        temp = list_of_inputTypes.pop()
        for i in list_of_inputTypes:
            if len(list_of_inputTypes) > 0:
                #print("temp :", temp)
                if i.split("_")[0] == "micrographs" and temp[:11] == "micrographs":
                    continue
                elif i.split("_")[0] == "particles" and temp[:9] == "particles":
                    continue
                else:
                    print(
                        "\n => ERROR! Different input types detected! The --exclude input arguments should be micrographs-only or particles-only")
                    sys.exit(2)

    if args.extract:
        NewStarData = []
        list_to_extract = []
        for argExtr in args.extract:
            inputType = input_analyse(argExtr)
            if inputType == "micrographs_coarsened_star":
                list_to_extract = list_to_extract + \
                    export_from_coarsened_file(argExtr)
            elif inputType == "micrographs_star":
                MainHeader_extr, OpticsGroupData_extr, OpticsHeader_extr, StarData_extr, StarFileType_extr = star_analyze(
                    argExtr)
                list_to_extract = list_to_extract + \
                    [Path(k).stem for k, v in StarData_extr.items()]
                # print(list_to_extract)
            elif inputType == "particles_star":
                MainHeader_extr, OpticsGroupData_extr, OpticsHeader_extr, StarData_extr, StarFileType_extr = star_analyze(
                    argExtr)
                list_to_extract = list_to_extract + \
                    [k for k, v in StarData_extr.items()]
                #print("list_to_extract:", list_to_extract)
                #print("StarData_extr:", StarData_extr)
            elif inputType == "micrographs_txt":
                list_to_extract = list_to_extract + \
                    export_from_txt_file(argExtr)
            else:
                print(
                    "\n => ERROR in the analysis of the --extract input! inputType is not detected")
                sys.exit(2)
        print("\n => Extracting %d %s" %
              (len(list_to_extract), inputType.split("_")[0]))
        NewStarData = extract_from_dict(StarData, list(set(list_to_extract)))

    if args.exclude:
        NewStarData = []
        list_to_exclude = []
        for argExcl in args.exclude:
            inputType = input_analyse(argExcl)
            #print(f"inputType: {inputType}")
            if inputType == "micrographs_coarsened_star":
                list_to_exclude = list_to_exclude + \
                    export_from_coarsened_file(argExcl)
            elif inputType == "micrographs_star":
                MainHeader_excl, OpticsGroupData_excl, OpticsHeader_excl, StarData_excl, StarFileType_excl = star_analyze(
                    argExcl)
                list_to_exclude = list_to_exclude + \
                    [Path(k).stem for k, v in StarData_excl.items()]
                # print(list_to_exclude)
            elif inputType == "particles_star":
                MainHeader_excl, OpticsGroupData_excl, OpticsHeader_excl, StarData_excl, StarFileType_excl = star_analyze(
                    argExcl)
                list_to_exclude = list_to_exclude + \
                    [k for k, v in StarData_excl.items()]
            elif inputType == "micrographs_txt":
                list_to_exclude = list_to_exclude + \
                    export_from_txt_file(argExcl)
            else:
                print(
                    "\n => ERROR in the analysis of the --exclude input! inputType is not detected")
                sys.exit(2)
        print("\n => Excluding %d %s" %
              (len(list_to_exclude), inputType.split("_")[0]))
        NewStarData = exclude_from_dict(StarData, list(set(list_to_exclude)))

    write_out_star(MainHeader, OpticsGroupData, OpticsHeader,
                   NewStarData, StarFileType, args.o[0])

    if args.list_of_micro:
        # create an additional file with micrograph filenames
        output_stem, output_suffix = check_outputname(args.o[0])
        list_of_micro_filename = output_stem+"_micrographs.txt"
        # print(list_of_micro_filename)
        #print("NewStarData: ", NewStarData)
        write_out_list(NewStarData, list_of_micro_filename)


if __name__ == '__main__':
    #start_time= time.time()
    main()
    #print("--- %s seconds ---" % (time.time() - start_time))
