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

ver=221106

import os
import sys
import argparse
import glob
import pathlib
import subprocess
import shutil
import time

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
        return files_to_do, files_output
    else:
        print("ERROR! No input files found!")
        sys.exit()

def main(input):
    outdir=mkdir(input['outdir'])
    cwd=os.getcwd()
    os.chdir(input['path'])
    print(f" => Working in {input['path']} directory")
    targets, output_files=find_targets(input['path'], input['label'], input['outdir'], input['outsuffix'])
    print(f'{len(targets)} targets were found')
    time.sleep(1)
    if 'gain' not in input:
        for target, output_file in zip(targets, output_files):
            cmd=F"{input['software']} -gpu {input['gpu']} -vary {input['vary']} -bin {input['bin']} -mdoc {target} -output {output_file}"
            print(f" => Running command: {cmd}")
            p=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()  
            p_status = p.wait()
    else:
        for target, output_file in zip(targets, output_files):
            cmd=F"{input['software']} -gpu {input['gpu']} -vary {input['vary']} -bin {input['bin']} -mdoc {target} -output {output_file} -gain {input['gain']}"
            print(f" => Running command: {cmd}")
            p=subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            (output, err) = p.communicate()  
            p_status = p.wait()
    os.chdir(cwd)
    print(f" => Returning to {cwd} directory")
          
if __name__== '__main__':
    output_text='''
==================================== t_alignframes.py =================================================
batch processing for the movie alignments: for now, only aliframes (IMOD) implemented
All arguments should be space separated.

[version %s]
Written and tested in python3.8.5
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools
====================================================================================================

Example: t_alignframes.py --label .mdoc --path ./ --vary 0.25 --bin 2 1 --outdir ../aligned_TS --gain gain.mrc --gpu 0 --alignframes''' % (ver)

    parser = argparse.ArgumentParser(description="")
    add = parser.add_argument
    add('--bin', default='2 1', help="bin option in alignframes. Space separated")
    add('--gain', help="gain file for non-normalised frames")
    add('--gpu', default="0", help="which GPUs to use. Space separated")
    add('--label', default=".mdoc", help="Files to run alignments on")
    add('--log', default=True, action='store_true', help='Create t_alignframes_XXX.log file')
    add('--path', default="./",
        help="Path to the folder with your mdoc files. Default value: ./ ")
    add('--restart', default=False, action='store_true', help='Exclude the completed results (after crash)')
    add('--software', default="alignframes", action='store_true', help='Software of choise')
    add('--outdir', default="../aligned_TS", help="Output directory name. By default (when running from frames folder), ../aligned_TS will be created")
    add('--outsuff', default="_ali", help="Suffix of the output files: for stacktilt_01.mrc.mdoc this will mean stacktilt_01_ali.mrc")
    add('--vary', default=0.25, help="vary option in alignframes")
    args = parser.parse_args()
    print(output_text)
    parser.print_help()
    cwd=os.getcwd()
    
    input={}
    if args.software != "alignframes":
        print('Function is not implemented yet')
        sys.exit()
    input['software']=shutil.which(args.software)
    if not input['software']:
        print(f" => ERROR! Software {args.software} is not found. Make sure it is sourced or check the input!")
        sys.exit()
    print(f"\n => Using {input['software']} program to align frames")
    input['path']=os.path.normpath(args.path) # trims "/" from the path
    outdir_raw=args.outdir
    if outdir_raw[0] == "~":
        outdir=os.path.abspath(os.path.expanduser(outdir_raw))
    else:
        outdir=os.path.abspath(outdir_raw)
    input['outdir']=os.path.normpath(outdir)
    input['outsuffix']=args.outsuff
    input['label']=args.label
    input['vary']=float(args.vary)
    input['bin']=','.join((args.bin).split())
    if args.gain:
        input['gain']=args.gain
    else:
        print("\n => WARNING! No gain file has been provided. No gain normalisation will be applied.")
    input['gpu']=','.join((str(args.gpu)).split())

    print(f"\n => Input library: {input} ")
    time.sleep(2)
    main(input)
    print("\n => Program completed")
