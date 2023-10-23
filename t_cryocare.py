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

prog='t_cryocare.py'
ver=231023
underline=("="*70)+("="*(len(prog)+2))

import sys
import os
import re
import glob
import time
import shutil
import argparse
import subprocess
from itertools import chain

if os.getenv('IMOD_DIR') != None:
    sys.path.insert(0, os.path.join(os.environ['IMOD_DIR'], 'pylib'))
    from imodpy import *
    #Adds IMOD_DIR/bin to front of PATH and ignores SIGHUP
    addIMODbinIgnoreSIGHUP()
else:
	sys.exit('ERROR: IMOD_DIR is not defined\n')

def argparse_list_to_str_commas(input_list):
    my_string=''
    my_string=','.join(input_list)
    return my_string

def get_filename(filename, suffix):
    '''for a filename returns name without a path and suffix'''
    basename = os.path.basename(filename)
    pattern = re.escape(suffix) + r"$"
    #print("pattern: ", pattern)
    regex = re.compile(pattern)
    match = regex.search(basename)
    if match:
        return basename[:match.start()]
    else:
        print(f"Match not found in get_filename({filename}, {suffix}) function! ")

def get_folders(inputdir):
    '''returns folders in a given directory'''
    return [f for f in os.listdir(inputdir) if os.path.isdir(os.path.join(inputdir, f))]

def get_common_stem(filenames):
    ''' Function returning common stem from files '''
    stem_pattern = r"^(.+?)(?:\.[^.]+)?$"  # Regular expression pattern to match the stem
    stems = [re.match(stem_pattern, filename).group(1) for filename in filenames]
    common_stem = os.path.commonprefix(stems)
    return common_stem

def mkdir(outdirname):
    '''Checks if the folder exist, creates a new one if it does not; returns full path of that directory'''
    if not os.path.isdir(outdirname):
        print("folder "+ outdirname+ "does not exist")
        os.mkdir(outdirname)
    outdir=os.path.abspath(outdirname)
    return outdir

def fix_path(pathname):
    # for the input path checks if it starts with "~" and returns absolute path
    if pathname[0] == "~": newpath=os.path.abspath(os.path.expanduser(pathname))
    else: newpath=os.path.abspath(pathname)
    return newpath

def checkfile(filename, mdocfile=None):
    if not os.path.exists(filename):
        if mdocfile is not None:
            sys.exit(f" => ERROR! File {filename} does not exist; it corresponds to {mdocfile} file")
        else:
            sys.exit(f" => ERROR! File {filename} does not exist")

def check_mdocname_aliname(mdoc_list, ali_list, alioutsuff, mdocsuffix):
    '''
    By default, mdoc files should be named as TS_01.mrc.mdoc when the aligned file is TS_01_ali.mrc
    if it is different, the function will report an error and suggest new input suffixes
    '''
    if len(mdoc_list) == 0:
        print("mdoc_list: ", mdoc_list)
        sys.exit(f" => Error in check_mdocname_aliname! No {input['mdocsuffix']} files found!")
    if len(ali_list) ==0:
        print("ali_list: ", ali_list)
        sys.exit(f"=> Error in check_mdocname_aliname! No {input['alioutsuff']} files found!")
    if len(mdoc_list) != len(ali_list):
        print("mdoc_list: ", mdoc_list)
        print("ali_list: ", ali_list)
        sys.exit(f" => Error in check_mdocname_aliname! Number of .mdoc files {len(mdoc_list)} and ali.mrc files {len(ali_list)} are different!")
    real_stem=os.path.basename(ali_list[0][:-len(alioutsuff)])
    suggested_mdocsuffix=os.path.basename(mdoc_list[0])[len(real_stem):]
    suggested_alioutsuff=os.path.basename(ali_list[0])[len(real_stem):]
    if real_stem != get_common_stem([os.path.basename(mdoc_list[0]), os.path.basename(ali_list[0])]):
        #print("get_common_stem([mdoc_list[0], ali_list[0]]):" , get_common_stem([os.path.basename(mdoc_list[0]), os.path.basename(ali_list[0])]))
        print(f" => WARNING from check_mdocname_aliname! Inconsistency in namings of the _ali.mrc and .mrc.mdoc files: Check the suffixes!")
        print(f"    For example, given two files {os.path.basename(mdoc_list[0])} and {os.path.basename(ali_list[0])}: the stem is {real_stem}. \n    The following input parameters are used: \n    --mdocsuffix {mdocsuffix}  \n    --alioutsuff {alioutsuff} ")
        if os.path.basename(mdoc_list[0])[:(-len(mdocsuffix))] != real_stem:
            sys.exit(f" = > ERROR! Consider using the following options: --mdocsuffix {suggested_mdocsuffix} --alioutsuff {suggested_alioutsuff}")

def check_headers(images):
    # for a list of images, checks their headers
    headers=[]
    header_temp=read_header(images[0])
    headers.append(header_temp)
    for i in range(1, len(images)):
        header=read_header(images[i])
        # check for consistency of the frame number/size/pixel size: check if two dictionaries are equal. if not, return key value pairs
        if input['check_headers']:
            diff_header = {k: (v, [k]) for k, v in header.items() if k in header_temp and header_temp[k] != v and k != 'filename'}
            if diff_header:
                print(f" => WARNING!!! Header of {images[i]} file is different from {images[i-1]}! The following key-value pairs are different:")
                with open("warning_tiff_files.log", "a") as outputFile:
                    outputFile.write(f' => WARNING!!! Header of {images[i]} file is different from {images[i-1]}! The following key-value pairs are different:')
                for k, (v1, v2) in diff_header.items():
                    print(f"{k}: {v1} != {v2}")
                    with open("warning_tiff_files.log", "a") as outputFile:
                        outputFile.write(f'{k}: {v1} != {v2}')
                    sys.exit(1)
        headers.append(header)
        header_temp=header
    return headers

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

def exclude_targets(targets, list_to_exclude, targets_suffix=".mrc.mdoc", exclude_suffix="_ali.mrc"):
    new_targets=targets
    set_to_exclude={os.path.basename(x)[: -len(exclude_suffix)]+targets_suffix for x in list_to_exclude}
    new_targets = [x for x in targets if x not in set_to_exclude]
    return new_targets

def find_targets(mdocpath, framespath, outdir, cryocareDir_even="even", cryocareDir_odd="odd", label=".mdoc", donesuffix="_ali.mrc"):
    #In a given path with .mdoc files finds unfinished targets to process. Returns a list of ufinished mdoc files and corresponding tiff files.
    list_all = glob.glob(mdocpath+"/*"+label)
    #print("list_all: ", list_all)
    list_all = [os.path.abspath(mdocpath) for mdocpath in list_all]
    if len(list_all) == 0: sys.exit("ERROR! No input files found!")

    #search for mdoc(_ali) not tiff!
    list_done_even = glob.glob(cryocareDir_even+ "/*" + donesuffix, recursive=True)
    list_done_odd = glob.glob(cryocareDir_odd+ "/*" + donesuffix, recursive=True)
    #print("list_done_even: ", list_done_even)
    list_undone=exclude_targets(list_all, list_done_odd, targets_suffix=".mrc.mdoc", exclude_suffix=donesuffix)
    mdoc_tif_dict={}
    for i in list_undone:
        mdoc_tif_dict[i]=fetch_frames_from_mdoc(i, framespath)
    return mdoc_tif_dict

def create_mdoc_etomo_dict(mdoc_list, aligned_ts_dir, etomooutsuf, mdocsuffix, mtffilter):
    ''' Creates a dictionary with k,v: {mdoc file, [newst.com, tilt.com, mtffilter.com]} based on mdoc list'''
    mdoc_etomo_dict={}
    for i in sorted(mdoc_list):
        etomodir=aligned_ts_dir+"/"+os.path.basename(i)[:-(len(mdocsuffix))]+etomooutsuf
        newst=etomodir+"/newst.com"
        checkfile(newst)
        tilt=etomodir+"/tilt.com"
        checkfile(tilt)
        if mtffilter == True:
            mtffilt=etomodir+"/mtffilter.com"
            checkfile(mtffilt)
            mdoc_etomo_dict[i]=[newst, tilt, mtffilt]
        else:
            mdoc_etomo_dict[i]=[newst, tilt]
    #print("create_mdoc_etomo_dict ran successfuly")
    return mdoc_etomo_dict

def split_odd_even(num):
    #Given a number (for example, of frames) splits that into two lists of strings comma-separated starting with 0: for 5 will return ('0,2', '1,3'). Last number (in case of odd input will be ommited)
    if num %2 != 0:
        print(f" \n=> WARNING! Odd number of frames detected! Frame {num} will be discarded from the analysis!\n")
    odd=''
    even=''
    for i in range(num):
        if i %2 ==0:
            even+=str(i)+","
        else:
            odd+=str(i)+","
    if num >1:
        result=(even[:-1], odd[:-1])
    else:
        sys.exit(f" => ERROR in split_odd_even! The input number {num} is not more than 1. Split into odd/even can't be done. ")
    #print(result)
    return result

######################## Creating  specific commands
def create_newstack_split_odd_even_command(target, cryocareDir_even, cryocareDir_odd, frames_even, frames_odd):
    # creates two commands for bash
    cmd_even=f"newstack -input {target} -output {cryocareDir_even}/{os.path.basename(target)} -secs {frames_even}  "
    cmd_odd=f"newstack -input {target} -output {cryocareDir_odd}/{os.path.basename(target)} -secs {frames_odd}  "
    return cmd_even, cmd_odd

def create_newstack_command(command, input, output, args_dict):
    # for a dictionary of arguments, creates a sting - a command
    filtered_dict = {k: v for k, v in args_dict.items() if v is not None}


    if args_dict["AngFileDir"]:
        targets, list_todo_angfiles=find_targets_aretomo(filtered_dict['InDir'], filtered_dict['InSuffix'], filtered_dict['OutDir'], filtered_dict['OutSuffix'], angfile=True, angfiledir=filtered_dict['AngFileDir'], angfilesuffix=filtered_dict['AngFileSuffix'])
    else:
        targets, list_todo_angfiles=find_targets_aretomo(filtered_dict['InDir'], filtered_dict['InSuffix'], filtered_dict['OutDir'], filtered_dict['OutSuffix'], angfile=False)

    #print("targets: ", targets)
    print("list_todo_angfiles: ", list_todo_angfiles)

    for target, angfile in zip(targets, list_todo_angfiles):
        cmd=F"{filtered_dict['Software']} -InMrc {target} -OutMrc {filtered_dict['OutDir']}/{os.path.splitext(os.path.basename(target))[0]}{filtered_dict['OutSuffix']} -AngFile {angfile}  "
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
    #print("cmd:", cmd)
    return cmd_list

def create_aliframes_command(framespath, mdoc, cryocareDir, output_file, bin="2,1", vary=0.25, gpu=None, gain=None):
    # creates a sting - command template for bash without inputs and outputs
    cmd=f"alignframes -vary {vary} -bin {bin} -path {framespath} -mdoc {mdoc} -output {cryocareDir}/{output_file} "
    #print("gpu: ", gpu)
    if gain is not None:
        cmd += f" -gain {gain} "
    if gpu is not None:
        cmd += f" -gpu {gpu} "
    #print("aliframes cmd: ", cmd)
    return cmd


#to fix below and one above:
def create_aretomo_rec_command(aligned_TS_dir, prefix, ali_tilt, binning, volumeZ, pixsize, dose_weight, mdoc_file, dose_rate):
    #if dose_weight:
	#	mdoc2dose_cmd = "python2.7 /scopem/prog/JX_scripts/mdoc2dose_weight.py %s --dose_rate %.2f"%(mdoc_file, dose_rate)
	#	os.system(mdoc2dose_cmd)
	imod_folder = "%s/%s_ali"%(aligned_TS_dir, prefix)
	aln_file = "%s/%s_ali.aln"%(aligned_TS_dir, prefix)
	if not(os.path.exists(aln_file)):
		print("ERROR: %s is not found! Please check it. Exit!"%(aln_file))
		sys.exit(1)
	out_ali_tilt_name = "%s_ali_rec.mrc"%(prefix)
	print ("Generating the reconstructed tomogram now!")
	aretomo_cmd = "AreTomo_1.2.0_Cuda112_06-23-2022 -InMrc %s -OutMrc %s -VolZ %s -OutBin %s -FlipVol 1 -Wbp 1 -AlnFile %s"%(ali_tilt, out_ali_tilt_name, volumeZ, binning, aln_file)
	if dose_weight:
		tlt_file = "%s_tlt.txt"%(prefix)
		aretomo_cmd += " -AngFile %s -Kv 300 -PixSize %.3f"%(tlt_file, pixsize)
	os.system(aretomo_cmd)

def create_postprocess_rotate_command(binning, dim_x, dim_y, dim_z, prefix, rec_tomo_name, swap_yz=None):
    cmd=""
    trim_x = dim_x / binning
    trim_y = dim_y / binning
    if trim_y % 2 != 0: trim_y += 1
    trim_z = dim_z / binning
    post_tomo_name = f"{prefix}_ali_rec.mrc"
    cmd = f"trimvol -x 1,{trim_y} -y 1,{trim_x} -z 1,{trim_z} -f -rx {rec_tomo_name} {post_tomo_name} "
    if swap_yz is not None:
        cmd = f"trimvol -x 1,{trim_y} -y 1,{trim_x} -z 1,{trim_z} -f -yz {rec_tomo_name} {post_tomo_name} "
    return cmd

####################################################

def cmd_dict_to_str(cmd_name, cmd_options):
    # combines command name and a dictionary of options into a string
    cmd=cmd_name
    for key,value in cmd_options.items():
        if value is not None:
            cmd += f" {key} {value}"
        else:
            cmd += f" {key}"
    return cmd

def modify_dict(old_dict, new_dict):
    #checks key, values of the old dictionary and replaces with the new values
    old_dict.update(new_dict)
    return old_dict

def run_cmd(cmd):
    # Given a bash command, runs it with a proper output
    print(f" => Running command: {cmd}")
    p=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
    #(output, err) = p.communicate()
    for line in p.stdout:
        #print(line.decode("utf-8").strip())
        sys.stdout.write(line.decode("utf-8"))
        p_status = p.wait()

########################### Fetching data from the files
def fetch_frames_from_mdoc(mdocfile, framespath):
    #for given mdoc file return corresponding tiff files
    frame_list=[]
    with open(mdocfile, 'r') as f:
        for line in f:
            if re.search(r"\.tif$", line):
                tif=line.strip().split("\\")[-1]
                frame_list.append(framespath+"/"+tif)
    return frame_list


def fetch_cmd_from_comfile(comfile, dict_out=False):
    #read the .com file and returns a command as a string (default) or a tulip: comand name and  dictionary with k,v as option, value. Assumes -StandardInput in the .com file
    cmd_str=""
    cmd_dict={}
    with open(comfile, 'r') as f:
        for line in f:
            if line.startswith("#"): continue
            elif line.startswith("$setenv"): continue
            elif line.startswith("$if"): continue
            elif line.startswith("$"):
                cmd=line.strip()[1:].split()[0]
                cmd_str+= cmd + " "
            else:
                #print("line: ", line)
                line_clean=line.strip()
                #print("line_clean: ", line_clean)
                cmd_str+="-"+line_clean+" "
                line_list=line_clean.split()
                #print("line_list", line_list)
                if len(line_list)>2:
                    cmd_dict["-"+line_list[0].strip()]=",".join(line_list[1:])
                else:
                    cmd_dict["-"+line_list[0].strip()]=" ".join(line_list[1:])
    if dict_out: return  cmd, cmd_dict
    else: return cmd_str





#run header (IMOD)
def read_header(filename, command='header '):
    #Reads the header of the image stack with IMOD header program and returns a dictionary with info
    header={}
    header["filename"]= filename
    #checkfile(filename)
    #print("filemname: ", filename)
    output=subprocess.run(command +" " + filename, capture_output=True, shell=True).stdout
    if output is not None:
        output = output.decode('utf-8')
        lines=output.splitlines()
        for i, line in enumerate(lines):
            if i == 5:
                header["dim_x"]=int(line.split()[-3])
                header["dim_y"]=int(line.split()[-2])
                header["dim_z"]=int(line.split()[-1])
            elif i==8:
                header["pixsize"]=float(line.split()[-1])
    else:
        sys.exit(f" => Error in read_header: problem {filename} ")
    return header

def main(input):
    #1. Preparation
        # Check if headers command exists
        # Organisation of folders: create new folders
        # Find unfinished .mdoc files
        # Check if headers are consistent
    #2. Create odd/even frames (together with #3)
    #3. Align at the same time (alignframes)
    #4. Etomo (AreTomo) reconstruction
        # read newst.com + modify
        # read mtffilter.com + modify
        # read tilt.com + modify
        # trimvol

    ### 0. Preparation
    input['outdir']=fix_path(input['outdir'])
    input['mdocpath']=fix_path(input['mdocpath'])
    input['framespath']=fix_path(input['framespath'])
    input['aligned_ts_dir']=fix_path(input['aligned_ts_dir'])

    #check consistency of names (mdoc and ali files)
    mdoc_list = sorted(glob.glob(input['mdocpath']+"/*"+input['mdocsuffix']))
    ali_list = sorted(glob.glob(input['aligned_ts_dir']+"/*"+input['alioutsuff']))
    #print("ALILIST ", ali_list)
    check_mdocname_aliname(mdoc_list, ali_list, input['alioutsuff'], input['mdocsuffix'])

    cmd_header=f"header"
    if shutil.which(cmd_header.split()[0]) is None:
        raise ValueError(f" => ERROR!Command '{cmd_header.split()[0]}' not found in PATH!")

    cryocareDir=mkdir(input["outdir"])
    cryocareDir_odd=mkdir(cryocareDir+"/odd")
    cryocareDir_even=mkdir(cryocareDir+"/even")

    #Create a list of headers of the tiff files
    targets_dict=find_targets(input['mdocpath'], input['framespath'], input["outdir"], cryocareDir_even, cryocareDir_odd, label=".mdoc", donesuffix=input['alioutsuff'])
    #print("targets_dict: ", targets_dict)
    print(f"\n => {len(targets_dict)} .mdoc files found\n")

    #zip values into a sorted list:
    #targets=list(chain(*sorted(targets_dict.values())))
    targets_tiff=[]
    for k,v in sorted(targets_dict.items()):
        for i in v:
            checkfile(i, k)
            targets_tiff.append(i)
    #print("targets_tiff: ", targets_tiff)
    if len(targets_tiff) < 2: sys.exit(f" => ERROR! {len(targets_tiff)} tiff files found! Please check the input")
    check_headers(targets_tiff)

    # create odd/even stack for tiff files
    frames_number=read_header(targets_tiff[0])["dim_z"]
    (frames_even, frames_odd) = split_odd_even(frames_number)
    pixsize_nm=read_header(targets_tiff[0])["pixsize"]
    pixsize_a=round(read_header(targets_tiff[0])["pixsize"]/10.0, 4)
    dim_x=read_header(targets_tiff[0])["dim_x"]
    dim_y=read_header(targets_tiff[0])["dim_y"]
    #print("pixsize: ", pixsize)

    # dictionary with the filenames of cryocare TS files (aligned TS): {rootname_001_ali.mrc: fullpath_even/rootname_001_ali.mrc, fullpath_odd/rootname_001_ali.mrc}
    cryocare_even_odd_TS={}

    #Creating commands to run:
    # - newstack
    # - alignframes
    cmd_newstack_all=[]
    cmd_aliframes_odd_all=[]
    cmd_aliframes_even_all=[]
    cmd_mkdirOdd_cryocareEtomo=[]
    cmd_mkdirEven_cryocareEtomo=[]
    cmd_newst_even=[]
    cmd_newst_odd=[]
    cmd_mtffilter_even=[]
    cmd_mtffilter_odd=[]
    cmd_tilt_even=[]
    cmd_tilt_odd=[]
    cmd_postproc_even=[]
    cmd_postproc_odd=[]


    for k,v in sorted(targets_dict.items()):
        #print("k, v :", k,v)
        for i in v:
            cmd_newstack=create_newstack_split_odd_even_command(i, cryocareDir_even, cryocareDir_odd, frames_even, frames_odd)
            cmd_newstack_all.append(cmd_newstack[0])
            cmd_newstack_all.append(cmd_newstack[1])
            cryocare_output_filename=get_filename(k, input['mdocsuffix'])+input['alioutsuff']
            #print("cryocare_output_filename",cryocare_output_filename)
            #print("output_file_even: ", output_file_even)
        temp=cryocareDir_even+"/"+cryocare_output_filename
        if os.path.exists(temp) and os.path.getsize(temp) > 0:
            print(f'File {cryocareDir_even}/{cryocare_output_filename} exists. Skipping...')
        else:
            cmd_aliframes_even_all.append(create_aliframes_command(cryocareDir_even, k, cryocareDir_even, cryocare_output_filename, input['alifrbin'], input['alifrvary'], input['gpu']))
        temp=cryocareDir_odd+"/"+cryocare_output_filename
        if os.path.exists(temp) and os.path.getsize(temp) > 0:
            print(f'File {cryocareDir_odd}/{cryocare_output_filename} exists. Skipping...')
        else:
            cmd_aliframes_odd_all.append(create_aliframes_command(cryocareDir_odd, k, cryocareDir_odd, cryocare_output_filename, input['alifrbin'], input['alifrvary'], input['gpu']))
            #output_file_odd=get_filename(k, input['mdocsuffix'])+input['alioutsuff']
                #print(create_aliframes_command(cryocareDir_odd, k, cryocareDir_odd, cryocare_output_filename, input['alifrbin'], input['alifrvary'], input['gpu']))
        cryocare_even_odd_TS[cryocare_output_filename]=(cryocareDir_even+"/"+cryocare_output_filename, cryocareDir_odd+"/"+cryocare_output_filename)

    #print("cryocare_even_odd_TS: ", cryocare_even_odd_TS)
######## ETOMO ##########
    #check if newst.com, mtffilter.com, tilt.com exist
    #Checks for etomo files
    mdoc_etomo_dict=create_mdoc_etomo_dict(targets_dict.keys(), input['aligned_ts_dir'], input['etomooutsuf'], input['mdocsuffix'], input['etomomtffilter'])
    #print("mdoc_etomo_dict: ", mdoc_etomo_dict)
    mdoc_dim_z={}
    for k,v in mdoc_etomo_dict.items():
        #print("k,v: ", k,v)
        #read newst.com + modify
        cmd_newstack, newst_cmd_old= fetch_cmd_from_comfile((v[0]), True)
        #make folders in cryocare folder - the same how it is in etomo
        cryocareEtomo_dirOdd=cryocareDir+ "/odd/" + os.path.dirname(v[0]).split('/')[-1]+"_cryocare_odd"
        cryocareEtomo_dirEven=cryocareDir+ "/even/" + os.path.dirname(v[0]).split('/')[-1]+"_cryocare_even"
        cmd_mkdirOdd_cryocareEtomo.append("mkdir "+cryocareEtomo_dirOdd)
        cmd_mkdirEven_cryocareEtomo.append("mkdir "+cryocareEtomo_dirEven)
        #print("cmd_mkdirOdd_cryocareEtomo: " , cmd_mkdirOdd_cryocareEtomo)
        #print("cmd_newstack: ", cmd_newstack):
        ##newstack
        #print("newst_cmd_old", newst_cmd_old)
        # Detemine original size of the camera based on -BinByFactor and -SizeToOutputInXandY
        camera_size =[int(x)*int(newst_cmd_old['-BinByFactor']) for x in newst_cmd_old['-SizeToOutputInXandY'].split(",")]
        #print("camera size: ", camera_size)
        ##camera size:  [4096, 5760]

        TSFileName=os.path.basename(k)[:-len(input['mdocsuffix'])]+input['alioutsuff']
        #print("TSFileName: ", TSFileName)
        # OutputFileName=TSFileName.replace(".mrc", "_ali.mrc")

        #Important:
        etomoDir=input["aligned_ts_dir"]+"/"+TSFileName[:-len(input['alioutsuff'])]
        #print("etomoDir", etomoDir)
        newst_InputFile_even=cryocare_even_odd_TS[TSFileName][0]
        #print("cryocare_even_odd_TS: ", cryocare_even_odd_TS)
        newst_OutputFile_even=newst_InputFile_even.replace(".mrc", f'_ali_bin{input["binning"]}.mrc')
        newst_InputFile_odd=cryocare_even_odd_TS[TSFileName][1]
        #print("newst_InputFile_even: ", newst_InputFile_even)
        #print("newst_InputFile_odd: ", newst_InputFile_odd)
        newst_OutputFile_odd= cryocareEtomo_dirOdd +"/"+ os.path.basename(newst_InputFile_odd).replace(".mrc", f'_ali_bin{input["binning"]}.mrc')
        newst_OutputFile_even= cryocareEtomo_dirEven +"/"+ os.path.basename(newst_InputFile_even).replace(".mrc", f'_ali_bin{input["binning"]}.mrc')
        #print("newst_OutputFile_odd: ", newst_OutputFile_odd)
        #print("newst_OutputFile_even: ", newst_OutputFile_even)
        newst_TransformFile=etomoDir+"/"+os.path.basename(k.replace(f"{input['mdocsuffix']}", "_ali.xf"))
        #print("newst_TransformFile:", newst_TransformFile)
        newst_newOptions_even={"-InputFile": os.path.dirname(cryocareEtomo_dirEven)+"/"+os.path.basename(newst_InputFile_even), "-OutputFile": newst_OutputFile_even, "-BinByFactor": f'{input["binning"]}', "-TransformFile": newst_TransformFile, '-SizeToOutputInXandY': ",".join([str(int(x/input["binning"])) for x in camera_size])}
        #print("newst_newOptions_even: ", newst_newOptions_even)
        #print("newst_cmd_old: ", newst_cmd_old)
        newst_newOptions_odd={"-InputFile": os.path.dirname(cryocareEtomo_dirOdd)+"/"+os.path.basename(newst_InputFile_odd), "-OutputFile": newst_OutputFile_odd, "-BinByFactor": f'{input["binning"]}', "-TransformFile": newst_TransformFile, '-SizeToOutputInXandY': ",".join([str(int(x/input["binning"])) for x in camera_size])}
        #print("newst_newOptions_odd: ", newst_newOptions_odd)
        newst_cmd_old_even=newst_cmd_old.copy()
        newst_cmd_old_odd=newst_cmd_old.copy()
        newst_cmd_new_even=modify_dict(newst_cmd_old_even, newst_newOptions_even)
        newst_cmd_new_odd=modify_dict(newst_cmd_old_odd, newst_newOptions_odd)
        cmd_newst_even.append(cmd_dict_to_str("newstack", newst_cmd_new_even))
        cmd_newst_odd.append(cmd_dict_to_str("newstack", newst_cmd_new_odd))
        #print("newst_cmd_new_even: ", newst_cmd_new_even)
        #print("newst_cmd_new_odd: ", newst_cmd_new_odd)
        if input['etomomtffilter'] == True:
            #read mtffilter.com + modify
            #print("fetch_cmd_from_comfile(v[2]: ", fetch_cmd_from_comfile(v[2]))
            cmd_mtffilter, mtffilter_cmd_old= fetch_cmd_from_comfile((v[2]), True)
            #print("mtffilter_cmd_old: ", mtffilter_cmd_old)
            mtffilter_OutputFile_even=newst_OutputFile_even.replace(f'_ali_bin{input["binning"]}.mrc', f'_EF_bin{input["binning"]}.mrc')
            mtffilter_OutputFile_odd=newst_OutputFile_odd.replace(f'_ali_bin{input["binning"]}.mrc', f'_EF_bin{input["binning"]}.mrc')
            mtffilter_newOptions_even={"-InputFile": newst_OutputFile_even, "-OutputFile": mtffilter_OutputFile_even, "-PixelSize": f"{pixsize_nm}", "-DoseWeightingFile": k}
            mtffilter_newOptions_odd={"-InputFile": newst_OutputFile_odd, "-OutputFile": mtffilter_OutputFile_odd, "-PixelSize": f"{pixsize_nm}", "-DoseWeightingFile": k}
            mtffilter_cmd_old_even=mtffilter_cmd_old.copy()
            mtffilter_cmd_old_odd=mtffilter_cmd_old.copy()
            mtffilter_cmd_new_even=modify_dict(mtffilter_cmd_old_even,  mtffilter_newOptions_even)
            mtffilter_cmd_new_odd=modify_dict(mtffilter_cmd_old_odd,  mtffilter_newOptions_odd)
            cmd_mtffilter_even.append(cmd_dict_to_str("mtffilter", mtffilter_cmd_new_even))
            cmd_mtffilter_odd.append(cmd_dict_to_str("mtffilter", mtffilter_cmd_new_odd))
            #print("mtffilter_cmd_new_even: ", mtffilter_cmd_new_even)
            #print("mtffilter_cmd_new_odd: ", mtffilter_cmd_new_odd)
            newst_OutputFile_even=mtffilter_OutputFile_even
            #print("newst_OutputFile_odd: ", newst_OutputFile_odd)
            newst_OutputFile_odd=mtffilter_OutputFile_odd
        #read tilt.com + modify
        cmd_tilt, tilt_cmd_old= fetch_cmd_from_comfile((v[1]), True)
        #print("tilt_cmd_old: ", tilt_cmd_old)
        mdoc_dim_z[k]=float(tilt_cmd_old["-THICKNESS"])
        tilt_OutputFile_even=newst_InputFile_even.replace(".mrc", f'_bin{input["binning"]}_full_rec.mrc')
        tilt_OutputFile_odd= newst_InputFile_odd.replace(".mrc", f'_bin{input["binning"]}_full_rec.mrc')
        tilt_TILTFILE=etomoDir+"/"+os.path.basename(k.replace(f"{input['mdocsuffix']}", "_ali.tlt"))
        tilt_XTILTFILE=etomoDir+"/"+os.path.basename(k.replace(f"{input['mdocsuffix']}", "_ali.xtilt"))
        tilt_newOptions_even={"-InputProjections": newst_OutputFile_even, "-OutputFile": tilt_OutputFile_even, "-IMAGEBINNED": f'{input["binning"]}', "-TILTFILE": tilt_TILTFILE, "-XTILTFILE": tilt_XTILTFILE}
        #print("tilt_newOptions_even", tilt_newOptions_even)
        tilt_newOptions_odd={"-InputProjections": newst_OutputFile_odd, "-OutputFile": tilt_OutputFile_odd, "-IMAGEBINNED": f'{input["binning"]}', "-TILTFILE": tilt_TILTFILE, "-XTILTFILE": tilt_XTILTFILE}
        #print("tilt_newOptions_odd", tilt_newOptions_odd)
        tilt_cmd_old_even= tilt_cmd_old.copy()
        tilt_cmd_old_odd= tilt_cmd_old.copy()
        tilt_cmd_new_even=modify_dict(tilt_cmd_old_even, tilt_newOptions_even)
        tilt_cmd_new_odd=modify_dict(tilt_cmd_old_odd, tilt_newOptions_odd)

        cmd_tilt_even.append(cmd_dict_to_str("tilt", tilt_cmd_new_even))
        cmd_tilt_odd.append(cmd_dict_to_str("tilt", tilt_cmd_new_odd))
        #print("tilt_cmd_new_even", tilt_cmd_new_even)
        # Postprocessing
        trim_x = int(dim_x / input["binning"])
        trim_y = int(dim_y / input["binning"])
        if trim_x % 2 != 0: trim_x += 1
        if trim_y % 2 != 0: trim_y += 1
        trim_z = int(mdoc_dim_z[k] / input["binning"])
        postProcess_OutputFile_even = newst_InputFile_even.replace(".mrc", f'_rec.mrc')
        postProcess_OutputFile_odd = newst_InputFile_odd.replace(".mrc", f'_rec.mrc')
        #print("trim_x", trim_x)
        postprocess_cmd_even = f'trimvol -x 1,{trim_y} -y 1,{trim_x} -z 1 {trim_z} -f -rx {tilt_OutputFile_even} {postProcess_OutputFile_even}'
        postprocess_cmd_odd = f'trimvol -x 1,{trim_y} -y 1,{trim_x} -z 1,{trim_z} -f -rx {tilt_OutputFile_odd} {postProcess_OutputFile_odd}'
        if input["swap_yz"]:
            postprocess_cmd_even = f'trimvol -x 1,{trim_y} -y 1,{trim_x} -z 1,{trim_z} -f -yz {tilt_OutputFile_even} {postProcess_OutputFile_even}'
            postprocess_cmd_odd = f'trimvol -x 1,{trim_y} -y 1,{trim_x} -z 1,{trim_z} -f -yz {tilt_OutputFile_odd} {postProcess_OutputFile_odd}'
        #print("postprocess_cmd_even: ", postprocess_cmd_even)
        cmd_postproc_even.append(postprocess_cmd_even)
        cmd_postproc_odd.append(postprocess_cmd_odd)
    #print(cmd_newstack_all)
    for i in cmd_newstack_all: run_cmd(i)
    for i in cmd_aliframes_odd_all: run_cmd(i)
    for i in cmd_aliframes_even_all: run_cmd(i)
    #print(cmd_aliframes_odd_all)
    #print(cmd_aliframes_even_all)
    for i in cmd_mkdirOdd_cryocareEtomo: run_cmd(i)
    #print(cmd_mkdirOdd_cryocareEtomo)
    for i in cmd_mkdirEven_cryocareEtomo: run_cmd(i)
    #print(cmd_mkdirEven_cryocareEtomo)
    for i in cmd_newst_odd: run_cmd(i)
    #print(cmd_newst_odd)
    for i in cmd_newst_even: run_cmd(i)
    #print(cmd_newst_even)
    for i in cmd_mtffilter_even: run_cmd(i)
    #print(cmd_mtffilter_even)
    for i in cmd_mtffilter_odd: run_cmd(i)
    #print(cmd_mtffilter_odd)
    for i in cmd_tilt_even: run_cmd(i)
    #print(cmd_tilt_even)
    for i in cmd_tilt_odd: run_cmd(i)
    #print(cmd_postproc_even)
    for i in cmd_postproc_even: run_cmd(i)
    for i in cmd_postproc_odd: run_cmd(i)

if __name__== '__main__':
    output_text='''
=================================== %s ===================================
Setup for cryocare. prerequisites: IMOD, Aretomo (to be implemented)
mode 1: prepare
mode 2: config - to be implemented

Assumes the following organisation:
XXX to add XXX

All arguments should be space separated
[version %s]

Based on cryocare_setup_v2.py script by Jingwei Xu
Written and tested in python3.11.2
Pavel Afanasyev
https://github.com/afanasyevp/cryoem_tools\n%s''' % (prog, ver,underline)

    parser = argparse.ArgumentParser(description=output_text)
    add = parser.add_argument
    #group1 = parser.add_mutually_exclusive_group(required=True)
    #group2 = parser.add_mutually_exclusive_group(required=True)
    # positional arguments
    add("mode", choices=["prepare", "config"], help="Mode 1: prepare cryoCARE by splitting/aligning frames and reconstructing. Mode 2: prepare config file.")
    add("software", choices=["etomo","aretomo"], default="etomo", help="Software for 3D-reconstruction: choose etomo or aretomo")

    #optional arguments
    add("--mdocpath", default="./", help="Default: ./ | Path to the folder with your mdoc files. ")
    add("--mdocsuffix", default=".mrc.mdoc", help="Default: .mrc.mdoc | Suffix of mdoc files. ")
    add("--framespath", default="./frames")
    add("--aligned_ts_dir", default="./", help="Default: ./ | Path to the folder with aligned tilt series.")
    add("--outdir", default="./cryocare", help="Default: ./cryocare | Output directory name.")
    add("--etomooutsuf", default="", help='Default: "" | Suffix of the folders of etomo files')
    add("--etomomtffilter", default=False, action="store_true", help='Default: (False) | If mtffilter was applied in etomo')
    add("--clean", default=False, action="store_true", help="Default: False | Remove the odd/even frames after alignframes.")
    add("--binning", type=int, default=4, help="Default: 4 | Target binning factor used for the tomogram reconstruction.")
    add("--volZ", type=int, default=1600, help="Default: 1600 | The Z value of the reconstructed tomogram at the binning factor of 1.")
    add("--dose_weight", action="store_true", help="Default: False | To filter the tomogram based on the exposure dose?")
    add("--dose_rate", type=float, help="Default: None | The dose rate per tilt.")
    #add("--overwrite", action="store_true", help="Default: False | To overwrite the previous generated files? The default is False.")
	#add("--include_tilt", action="store_true", help="The name of frames includes the tilt angle? The default is False.", default=False)
    add("--swap_yz", action="store_true", default=False, help="Default: False | To swap Y and Z on the tomogram instead of rotate X.")
    add("--gain", help="Default: None | Gain file for alignframes.")
    add("--check_headers", action="store_true", default=False, help="Default: check inputs - dimentions, number of frames, pixels size")
    add("--gpu", nargs="+", help="Default: none | Which GPUs to use. Space separated. For alignframes: GPU 0 to use the best GPU on the system, or the number of a specific GPU (numbered from 1)")
	#add("--tilt_prefix", help="The prefix of the frame. The default is empy, which will be considered as the same as the mdoc file.", default="")
    add("--alioutsuff", default="_ali.mrc", help="Default: _ali.mrc | Suffix of the aliframes output files: for stacktilt_01.mrc.mdoc this will mean stacktilt_01_ali.mrc")
    add("--alifrbin", default=["2", "1"], nargs="+",  help="Default: 2 1 | Binning option for aliframes. Space separated.")
    add("--alifrvary", default=0.25, help="Default: 0.25 | Vary option for the movie alignments.")
    args = parser.parse_args()
    #print(output_text)
    #parser.print_help()
    #print(f"\n Example: {prog} --Software aretomo --InDir ./ --OutDir ./aretomo  --InSuffix _ali.mrc --OutSuffix _rec.mrc --AngFileDir ./ --AngFileSuffix _tlt.txt --PixSize 2.678 --Kv 300 --Cs 2.7 --ImgDose 3.4 --OutBin 4 --VolZ 1600 --Patch 5 4 --Gpu 0 ")
    cwd=os.getcwd()

    input=vars(args)
    #print(f"\n => Using {input['Software']} program to align frames")
    if input['gpu']: input['gpu']=','.join(args.gpu)

    print(f"\n\n => Input parameters: ")
    for key, value in input.items():
        print(f"  --{key}  {value}")
    input['alifrbin']=argparse_list_to_str_commas(args.alifrbin)
    time.sleep(1)
    main(input)
    print("\n => Program %s (version %s) completed"%(prog, ver))
