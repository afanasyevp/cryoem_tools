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

ver=230430
prog='t_aretomo.py'
underline=("="*70)+("="*(len(prog)+2))

import os
import sys
import argparse
import glob
import subprocess
import shutil
import time

def argparse_list_to_str_commas(input_list):
    my_string=''
    my_string=','.join(input_list)
    return my_string

def find_executable(pattern):
    #for a given pattern searches among all executables for a command and returns one or an error
    executable_search_cmd=F"which `compgen -c  | grep {pattern}`"
    p=subprocess.Popen(executable_search_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, executable='/bin/bash')
    #(output, err) = p.communicate()
    executables=set()
    #executables.remove('')
    while True:
        line = p.stdout.readline()
        #print("line: ",line)
        candidate=line.decode('utf-8').rstrip('\n')
        if len(candidate)>0: executables.add(candidate)
        if not line: break
    #print("executables: ", executables)
    executables.remove(shutil.which("t_aretomo.py"))
    if len(executables) == 0:
        print(f" => {pattern} software was not found!")
        sys.exit(1)
    elif len(executables) > 1:
        print(f" = > ERROR! The following papckages were found based on pattern '{pattern}': ")
        [print(executable) for executable in iter(executables)]
        print(f"Please modify '{pattern}' pattern to address more specific program name")
        sys.exit(1)
    else:
        if "which" in list(executables)[0]:
            print(f" => ERROR!! {pattern} software was not found!")
            sys.exit(1)
        else:
            return list(executables)[0]


def create_aretomo_command(args_dict):
    # for a dictionary of arguments, creates a sting - command template for bash without inputs and outputs
    filtered_dict = {k: v for k, v in args_dict.items() if v is not None}
    #print("soft: ", filtered_dict['Software'])
    if not filtered_dict['Software']:
        print(" => Error! The software/command is not found in the dictionary of input arguments")
        sys.exit(1)

    cmd_list=[]
    if args_dict["AngFileDir"]:
        targets, list_todo_angfiles=find_targets_aretomo(filtered_dict['InDir'], filtered_dict['InSuffix'], filtered_dict['OutDir'], filtered_dict['OutSuffix'], angfile=True, angfiledir=filtered_dict['AngFileDir'], angfilesuffix=filtered_dict['AngFileSuffix'])
    else:
        targets, list_todo_angfiles=find_targets_aretomo(filtered_dict['InDir'], filtered_dict['InSuffix'], filtered_dict['OutDir'], filtered_dict['OutSuffix'], angfile=False)


    #print("targets: ", targets)
    #print("list_todo_angfiles: ", list_todo_angfiles)
    #print("targets: ", targets)
    for n, target in enumerate(targets):
        if args_dict["AngFileDir"]:
        	cmd=F"{filtered_dict['Software']} -InMrc {target} -OutMrc {filtered_dict['OutDir']}/{os.path.splitext(os.path.basename(target))[0]}{filtered_dict['OutSuffix']} -AngFile {list_todo_angfiles[n]}  "
        else:
            cmd=F"{filtered_dict['Software']} -InMrc {target} -OutMrc {filtered_dict['OutDir']}/{os.path.splitext(os.path.basename(target))[0]}{filtered_dict['OutSuffix']}  "
        for key, value in filtered_dict.items():
            if key in filtered_dict:
                # check for aretomo-only options
                if key == 'Software': pass
                elif key == 'InDir': pass
                elif key == 'OutDir': pass
                elif key == 'OutSuffix': pass
                elif key == 'InSuffix': pass
                elif key == 'AngFileDir': pass
                elif key == 'AngFileSuffix': pass
                else:
                    cmd += F" -{key} {value} "
        cmd_list.append(cmd)
    #print("cmd:", cmd_list)
    return cmd_list

def mkdir(outdirname):
    # Checks if the folder exist, creates a new one if it does not; returns full path of that directory
    if not os.path.exists(outdirname):
        os.mkdir(outdirname)
    outdir=os.path.abspath(outdirname)
    return outdir

def find_targets_aretomo(path, label, outdir, outsuffix, angfile=True, angfiledir='./', angfilesuffix='_tlt.txt'):
    '''
    In a given path finds unfinished targets to process with. For example:
    Input folder: input/stacktilt_01_ali.mrc  input/stacktilt_02_ali.mrc input/stacktilt_03_ali.mrc
    Output folder/files: input/aretomo/stacktilt_01_ali_rec.mrc input/aretomo/stacktilt_02_ali_rec.mrc input/aretomo/stacktilt_03_ali_rec.mrc
    [label] is a pattern to search; here it is "_ali.mrc" [outsuffix] is "_rec.mrc"

    The last three arguments are needed to search for the _tlt.txt files and creating a separate list of those.
    '''

    list_all = glob.glob(path+"/*"+label)
    list_all = [os.path.abspath(path) for path in list_all]
    #print(list_all)
    if len(list_all) == 0:
        print("ERROR! No input files found!")
        sys.exit(1)
    list_done = glob.glob(outdir+"/**/*"+outsuffix, recursive=True)
    list_done = [os.path.abspath(path) for path in list_done]

    #print("list_done: ", list_done)
    list_todo=[]
    dict_all={}
    dict_done={}
    dict_todo={}
    # for /code_workplace/cryoem_tools/b87_ts22_ali.mrc
    # will create key-value pair {b87_ts22_ali: /code_workplace/cryoem_tools/b87_ts22_ali.mrc}
    # here outsuffix is _rec.mrc
    for i in list_all: dict_all[os.path.splitext(os.path.basename(i))[0]]=i
    # for /code_workplace/cryoem_tools/aretomo/b87_ts22_ali/b87_ts22_ali_rec.mrc
    # will create key-value pair {b87_ts22_ali: /code_workplace/cryoem_tools/aretomo/b87_ts22_ali/b87_ts22_ali_rec.mrc}
    for i in list_done: dict_done[(os.path.basename(i))[:-len(outsuffix)]]=i
    # exclude key, values from  dict_all if a key is in dict_done
    dict_todo = {key: value for key, value in dict_all.items() if key not in dict_done}
    list_todo=sorted(list(dict_todo.values()))
    #print(list_todo)
    #Now, let's search for _tlt.txt files for undone list and build an additional list
    list_todo_angfiles=[]
    if angfile==True:
        for i in list_todo:
            angfile_found=glob.glob(angfiledir+"/"+os.path.basename(i[:-len(label)]+angfilesuffix))
            list_todo_angfiles.append(angfile_found[0])
            if not angfile_found:
                print(F' => ERROR! AngFile {os.path.basename(i[:-len(label)]+angfilesuffix)} not found in{angfiledir} \n Check the inputs!')
                sys.exit(1)
    return list_todo, list_todo_angfiles


def main(input):
    outdir=mkdir(input['OutDir'])
    cwd=os.getcwd()
    os.chdir(input['InDir'])
    print(f" \n => Working in {input['InDir']} directory")
    cmd_list=create_aretomo_command(input)
    print(f' \n => {len(cmd_list)} files to process were found  \n => Starting the process...\n')
    time.sleep(1)
    for cmd in cmd_list:
        print(f" => Running command: {cmd}")
        p=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        (output, err) = p.communicate()
        p_status = p.wait()
        #for line in p.stdout:
        #    sys.stdout.write(line.decode("utf-8"))
            #print(line)
    os.chdir(cwd)
    print(f" => Returning to {cwd} directory")

if __name__== '__main__':
    output_text='''
=================================== %s ===================================
Batch processing for AreTomo. Assumes all reconstructions to be in the
--InDir (input) folder. Arguments are based on Aretomo version 1.3.4

Don't use --InMrc argument, the program will search for reconstructions
in a given folder (--InDir) based on (--InSuffix) pattern.

All arguments should be space separated
[version %s]

Written and tested in python3.11.2
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools\n%s''' % (prog, ver,underline)

    parser = argparse.ArgumentParser(description="")
    add = parser.add_argument
    # to add:
    #add('--log', default=True, action='store_true', help=F'Create {prog}.log file')
    add('--InDir', default="./", help="Default: ./ | Path to the folder with your TS files.")
    add('--Software', default="aretomo", help="Default: aretomo | Software of choise")
    add('--OutDir', default="./aretomo", help="Default: ./ | Output directory name.")
    add('--InSuffix', default="_ali.mrc", help="Default: _ali.mrc | Suffix of the input files to search for: ts01_ali.mrc will be searching for *_ali.mrc")
    add('--OutSuffix', default="_rec.mrc", help="Default: _rec.mrc | Suffix of the output files to search for: ts01_ali.mrc will be searching for *_ali.mrc")
    add('--OutBin', default=4, help="Default: 4 | Output binning")
    add('--TiltRange', help="Default: none | Should be followed by two end angles as: -60 60")
    add('--AngFileDir',  help="Default: ./ | Folder with single-column text file with all the tilt angles. The second column can be the dose for dose-weighting")
    add('--AngFileSuffix', default="_tlt.txt", help="Default: _tlt.txt | Suffix of the files with tilt angles.")
    add('--VolZ', default="1600", help="Default: 1600 | Height of the reconstructed volume")
    add('--Align', default="1", help="Default: 1 | When 0, prevents the alignments")
    add('--TiltAxis', nargs="+", help="Deafault: none | The orientation of tilt axis. See official manual. ")
    add('--TiltCor', help="Deafault: none | Correction of tilt axis.")
    add('--FlipInt', help="Default: 0 | Flip intensities")
    add('--FlipVol', default="1", help="Default: 1 | Flip volume")
    add('--Wbp', default="1", help="Default: 1 | Enable weighted back projection (opposed to SART)")
    add('--Patch', default="5 4", nargs="+", help="Default: 5 4 | Number of patches in x and y")
    add('--RotFile', help="Default: none | List of x, y coordinates - ROI")
    add('--ReconRange', help="Default: none | Specifies the min and max tilt angles from which a 3D volume will be reconstructed.")
    add('--Kv', default=300, help="Default: 300 | Voltage")
    add('--Cs', default=2.7, help="Default: 2.7 | Cs")
    add('--PixSize', help="Default: none | Pixel size", required=True)
    add('--AlnFile', help="Default: none | Alignment .aln file ")
    add('--ImgDose', help="Default: none | Dose on sample in each image exposure in e/A2 ")
    add('--Defocus', help="Default: none | Defocus in Angstrom. It is only required for defocus correction")
    add('--TiltScheme', nargs="+", help="Default: none | Secat e the official manual")
    add('--Bft', nargs="+", help="Default: none | B-factors for LP filter. First, for global measurement, second - for local")
    add('--AlgnZ', help="Default: none | Z height of the temporary volume reconstructed for projection matching as part of the alignment process ")
    add('--OutImod', nargs="+", default=1, help="Default: 1 | Output the files needed for Relion4 and Warp to start subtomogram averaging. 1 - for relion4; 2 - for Warp; 3 - global and local-aligned tilt axis")
    add('--DarkTol', default=0.7, help="Default: 0.7 | Dark tolerance threshold")
    add('--OutXF', help="Default: none | When set by giving no-zero value, IMOD compatible")
    add('--Gpu', nargs="+", help="Default: none | GPU IDs. Space separated")
    add('--LogFile', help="Default: none | Generate logfile storing alignment data")
    add('--IntpCor', help="Default: none | the correction for information loss due to linear interpolation")

    args = parser.parse_args()
    print(output_text)
    #parser.print_help()
    print(f"\n Example: {prog} --Software aretomo --InDir ./ --OutDir ./aretomo  --InSuffix _ali.mrc --OutSuffix _rec.mrc --AngFileDir ./ --AngFileSuffix _tlt.txt --PixSize 2.678 --Kv 300 --Cs 2.7 --ImgDose 3.4 --OutBin 4 --VolZ 1600 --Patch 5 4 --Gpu 0 ")
    cwd=os.getcwd()

    input=vars(args)
    input['Software']=find_executable(args.Software)
    #input['Software']=shutil.which(args.software)
    print(f"\n => Using {input['Software']} program to align frames")

    if args.OutDir[0] == "~":
        input['OutDir']=os.path.abspath(os.path.expanduser(args.OutDir))
    else:
        input['OutDir']=os.path.abspath(args.OutDir)

    input['InDir']=os.path.abspath(args.InDir)
    if args.AngFileDir:
        input['AngFileDir']=os.path.abspath(args.AngFileDir)
    print(f"\n\n => Input parameters: ")
    for key, value in input.items():
        print(f"  --{key}  {value}")
    time.sleep(1)
    main(input)
    print("\n => Program %s (version %s) completed"%(prog, ver))
