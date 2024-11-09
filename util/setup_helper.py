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
#
# Written by Pavel Afanasyev
# afanasyev.code@gmail.com
# https://github.com/afanasyevp/cryoem_tools

import shutil
import subprocess
import sys
import os
from pathlib import Path
from textwrap import fill
import glob 
import argparse

ver=20241109
OUTPUT_WIDTH = 120 

class Helper_I_O:
    def __init__(self, args):
        self.args = args
        if hasattr(self.args, 'software'):
            self.software=args.software
            args.software=self.software

    @property
    def software(self):
        return self._software
    
    @software.setter
    def software(self, software):
        '''
        For a sting (software name) searches for available software in the system
        '''
        #not sure this should be static yet...
        if Path(software).is_file():
            software=Path(software).absolute()
            if os.access(software, os.X_OK):
                print(f"\n  => Using {software} program")
                self._software=software
                return self._software
            else:
                sys.exit(f'=> ERROR: {software} is not executable! Check the input or permissions of the file!' )
        else:
           software_found = shutil.which(software)
           if software_found:
               print(f"\n => Using {software_found} program")
               self._software=software_found
               return self._software
           else:
               # in some cases shutil doesn't work
               # for a given pattern searches among all executables for a command and returns one or an error
               executable_search_cmd = f"which `compgen -c  | grep {software}`"
               p = subprocess.Popen(
                    executable_search_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    shell=True,
                    executable="/bin/bash",
               )
                # (output, err) = p.communicate()
               executables = set()
               # executables.remove('')
               while True:
                   line = p.stdout.readline()
                   candidate = line.decode("utf-8").rstrip("\n")
                   if len(candidate) > 0:
                       executables.add(candidate)
                   if not line:
                       break
               # print("executables: ", executables)
               #executables.remove(shutil.which("t_aretomo.py"))
               if len(executables) == 0:
                   sys.exit(f" => {software} software was not found!")
               elif len(executables) > 1:
                   print(f" => ERROR! The following papckages were found based on pattern '{software}': ")
                   [print(executable) for executable in iter(executables)]
                   sys.exit(f"Please modify '{software}' pattern to address more specific program name")
               else:
                   if "which" in list(executables)[0]:
                       sys.exit(f" => ERROR!! {software} software was not found!")
                   else:
                       print(f" => {list(executables)[0]} software will be used")
                       self._software=list(executables)[0]
                       return self._software
               sys.exit(
                   f"\n => ERRROR! {software} is not found! Check if it is sourced! "
               )
	
    @staticmethod
    def find_targets(path_in=".", path_out=".", prefix_in="", suffix_in="", prefix_out="", suffix_out=""):
        '''
        In a given path searches for files with specific names "input". Compares with other group of files "output", and returns the difference list of tuples - "unfinished targets" (input_name, output_name).
    	Note: suffix contains extension!! 
	    '''
        path_in=str(Path(path_in).absolute())
        path_out=str(Path(path_out).absolute())
        list_all = glob.glob(path_in + "/" + prefix_in+"*" + suffix_in)
        list_done = glob.glob(path_out + "/" + prefix_out + "*" +suffix_out)
        targets=[]
        if len(list_all) > 0:
            set_all = set([os.path.basename(i)[:-len(suffix_in)] for i in list_all])
            set_done = set(
                [
                    os.path.basename(i)[:-len(suffix_out)]
                    for i in list_done
                ]
            )
            list_to_do = sorted(set_all - set_done)
            for target in list_to_do:
                target_input = path_in + "/" + target + suffix_in
                target_output = (
                    path_out
                    + "/"
                    + target
                    + suffix_out
                )
                targets.append((target_input, target_output))
        else:
            sys.exit(("ERROR! No input files found!"))
        print(f" ")
        return targets

    @staticmethod
    def mkdir(outdirname):
        if not os.path.exists(outdirname):
            os.mkdir(outdirname)
        return Path(outdirname).absolute()
    
    @staticmethod
    def list_to_file(data, out_filename):
        with open(out_filename, "w") as f:
            for line in data:
                f.write(line)
        print(f" => File {out_filename} is created.")


    @staticmethod
    def strtobool(val):
        """Convert a string representation of truth to true (1) or false (0). 
        True values are 'y', 'yes', 't', 'true', 'on', and '1'; false values
        are 'n', 'no', 'f', 'false', 'off', and '0'.  Raises ValueError if
        'val' is anything else.
        """
        if isinstance(val, (bool)):
            return val
        else:
            val = val.lower()
            if val in ('y', 'yes', 't', 'true', 'on', '1') or val==True:
                return True
            elif val in ('n', 'no', 'f', 'false', 'off', '0') or val==False:
                return False
            else:
                raise ValueError("invalid input value %r" % (val,))


class Helper_Run:
    def __init__(self, args, cmds):
        self.args = args
        self.cmds = cmds

    def run_cmds(self, out=None):
        if out:
            Helper_I_O.list_to_file(self.cmds, out)
        for cmd in self.cmds:
            p=subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
            for line in p.stdout:
                print(line.decode("utf-8").strip())    




#For argparse
class UltimateHelpFormatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    # RawDescriptionHelpFormatter as formatter_class= indicates that description and epilog are already correctly formatted and should not be line-wrapped:
    # ArgumentDefaultsHelpFormatter automatically adds information about default values to each of the argument help messages
    # RawTextHelpFormatter maintains whitespace for all sorts of help text, including argument descriptions
    #pass
    def __init__(self, prog,*args, **kwargs):
        kwargs['width'] = OUTPUT_WIDTH  # Set the desired width of "usage"
        kwargs['max_help_position'] = 40	
        super().__init__(prog, *args, **kwargs)
        #super().__init__(prog, max_help_position=40, width=OUTPUT_WIDTH)

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


class Helper_Prog_Info:
    def __init__(self, prog, version=None, description=None, examples=None):
        """
        See cryoemt_ctffind.py as an example of use.
        Note: "examples" must be a list of strings
        """
        self.underline_n = OUTPUT_WIDTH # considering formating of textwrap and PIP it is 79
        self.prog  = prog
        self.version = version
        self.description = description 
        self.underline = "="*self.underline_n
        self.examples = examples
        if self.examples:
            self.examples = "\n".join(fill(line, width=self.underline_n) for line in self.examples)
        if (self.underline_n -len(self.prog)) % 2 == 0:
            self.halfline1 = "=" * int((self.underline_n - len(self.prog))/2 - 1)
            self.halfline2 = self.halfline1
        else:
            self.halfline1 = "=" * int((self.underline_n - len(self.prog) - 1)/2 - 1)
            self.halfline2 =  self.halfline1 + "=" 

    def make_description(self):
        output = f'''
{self.halfline1} {self.prog} {self.halfline2}
{self.description}

{self.examples}

 See full list of options with:
 {self.prog} --help



 Version {self.version} 
 Written by Pavel Afanasyev
 afanasyev.code@gmail.com
 https://github.com/afanasyevp/cryoem_tools
{self.underline}

'''
        return output


