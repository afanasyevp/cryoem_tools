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
prog='t_alignframes.py'
ver=230419
underline=("="*70)+("="*(len(prog)+2))
 
import os
import sys
import argparse
import glob
import pathlib
import subprocess
import shutil
import time


def argparse_list_to_str_commas(input_list):
    my_string=''
    my_string=','.join(input_list)
    return my_string

def create_aliframes_command(args_dict):
    # for a dictionary of arguments, creates a sting - command template for bash without inputs and outputs
    filtered_dict = {k: v for k, v in args_dict.items() if v is not None}
    if not filtered_dict['software']:
        print(" => Error! The software/command is not found in the dictionary of input arguments")
        sys.exit()

    #check for gain
    if 'gain' not in filtered_dict:
        cmd=F"{filtered_dict['software']}  -vary {filtered_dict['vary']} -bin {filtered_dict['bin']} -path {filtered_dict['framespath'] }"
    else:
        cmd=F"{filtered_dict['software']}  -vary {filtered_dict['vary']} -bin {filtered_dict['bin']}  -gain {filtered_dict['gain']} -path {filtered_dict['framespath'] }"
    
    #check for gpu
    if 'gpu' in filtered_dict:
        cmd += F" -gpu { filtered_dict['gpu']} "
    #print("cmd", cmd)

    return cmd


def mkdir(outdirname):
    # Checks if the folder exist, creates a new one if it does not; returns full path of that directory
    if not os.path.exists(outdirname):
        os.mkdir(outdirname)
    outdir=os.path.abspath(outdirname)
    return outdir

def find_targets(path, label, outdir, outsuffix):
    '''
    In the given path finds unfinished targets to process. For example:

    #Input folder: input/stacktilt_01.mrc.mdoc  input/stacktilt_02.mrc.mdoc input/stacktilt_03.mrc.mdoc
    #Output folder: ../aligned_TS/stacktilt_01_ali.mrc

    find_targets("input", "mdoc", "../aligned_TS", "_ali")
    #will return: ['input/stacktilt_02.mrc.mdoc', 'input/stacktilt_03.mrc.mdoc'] , ['../aligned_TS/stacktilt_02_ali.mrc', '../aligned_TS/stacktilt_03_ali.mrc']
    '''
    list_all = glob.glob(path+"/*"+label)
    list_done = glob.glob(outdir+"/*"+outsuffix+".mrc")
    if len(list_all) > 0:
        #print("list_all: ", list_all)
        insuffix=''.join(pathlib.Path(list_all[0]).suffixes)
        set_all = set([os.path.basename(i).split(".")[0] for i in list_all])
        set_done=set([os.path.basename(i).split(".")[0].split(outsuffix)[0] for i in list_done])
        #print("set_done: ", set_done)
        list_to_do= sorted(set_all - set_done)
        #print("list_to_do", list_to_do)
        files_to_do=[path+"/"+i+insuffix for i in list_to_do]
        files_output=[outdir+"/"+i+outsuffix+".mrc" for i in list_to_do]
    #print("files to do: ", files_to_do)
        return files_to_do, files_output, len(list_all)
    else:
        print("ERROR! No input files found!")
        sys.exit()

def main(input):
    outdir=mkdir(input['outdir'])
    cwd=os.getcwd()
    os.chdir(input['mdocpath'])
    print(f" \n => Working in {input['mdocpath']} directory")
    #print("input:", input)
    targets, output_files, number_of_ts=find_targets(input['mdocpath'], input['label'], input['outdir'], input['outsuff'])
    print(f' \n => {len(targets)} TS to process were found (out of {number_of_ts}) ')
    #time.sleep(1)
    cmd_template=create_aliframes_command(input)
    for target, output_file in zip(targets, output_files):
        cmd=cmd_template + F" -mdoc {target} -output {output_file} "
        print(f" => Running command: {cmd}")
        p=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
        #(output, err) = p.communicate()
        #p_status = p.wait()
        for line in p.stdout:
            sys.stdout.write(line.decode("utf-8"))
        #    #print(line)
    os.chdir(cwd)
    print(f" => Returning to {cwd} directory")

if __name__== '__main__':
    output_text='''
=================================== %s ===================================
batch processing for the movie alignments: for now, only aliframes (IMOD) 
implemented. All arguments should be space separated.

[version %s]
Written and tested in python3.11
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools \n%s''' % (prog, ver, underline)

    parser = argparse.ArgumentParser(description="")
    add = parser.add_argument
    add('--bin', default=["2", "1"], nargs="+", help="bin option in alignframes. Space separated")
    add('--gain', help="gain file for non-normalised frames")
    add('--label', default=".mdoc", help="Files to run alignments on")
    add('--log', default=True, action='store_true', help='Create t_alignframes_XXX.log file')
    add('--mdocpath', default="./",
        help="Path to the folder with your mdoc files. Default value: ./ ")
    add('--framespath', default="./",
        help="Path to the folder with your frames files. Default value: ./ ")
    add('--software', default="alignframes", help='Software of choise')
    add('--outdir', help="Output directory name.")
    add('--outsuff', default="_ali", help="Suffix of the output files: for stacktilt_01.mrc.mdoc this will mean stacktilt_01_ali.mrc")
    add('--vary', default=0.25, help="vary option in alignframes")
    add('--gpu', nargs="+", help="which GPUs to use. Space separated. For alignframes: GPU 0 to use the best GPU on the system, or the number of a specific GPU (numbered from 1)")
    add('--pixel', help="Pixel size. mdoc value will be overwritten.")
    args = parser.parse_args()
    #print(vars(args))
    print(output_text)
    parser.print_help()
    print(f"\n Example: {prog} --software alignframes --label .mdoc --mdocpath ./ --framespath ./ --vary 0.25 --bin 2 1 --outdir ../aligned_TS --gain gain.mrc \n")
    print(underline)
    cwd=os.getcwd()
    if not args.outdir:
        print(" \n => ERROR! No input provided! Please find usage instruction above or run: t_alignframes.py --help")
        sys.exit()
    
    input=vars(args)
    # Check arguments and modify
    #print("before", input)
    if args.software != "alignframes":
        print('Function is not implemented yet')
        sys.exit()
    input['software']=shutil.which(args.software)
    if not input['software']:
        print(f" => ERROR! Software {args.software} is not found. Make sure it is sourced or check the input!")
        sys.exit()
    #print(f"\n => Using {input['software']} program to align frames")
    input['mdocpath']=os.path.abspath(args.mdocpath)
    input['framespath']=os.path.abspath(args.framespath)

    outdir_raw=args.outdir
    if outdir_raw[0] == "~":
        outdir=os.path.abspath(os.path.expanduser(outdir_raw))
    else:
        outdir=os.path.abspath(outdir_raw)
    input['outdir']=os.path.normpath(outdir)
    if args.gain:
        input['gain']=os.path.abspath(os.path.expanduser(args.gain))
    else:
        print("\n => WARNING! No gain file has been provided. No gain normalisation will be applied.")
    input['bin']=argparse_list_to_str_commas(args.bin)
    input['gpu']=argparse_list_to_str_commas(args.gpu)

    
    #print("after", input)
    print(f"\n\n Input parameters: ")
    for key, value in input.items():
        print(f"  --{key}  {value}")
    #print(input)
    time.sleep(1)
    main(input)
    print("\n => Program %s (version %s) completed"%(prog, ver))

