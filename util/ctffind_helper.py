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
from util.setup_helper import Helper_I_O
from pathlib import Path
ver=20241103

class Helper_ctffind5:
    def __init__(self, args, targets):
        self.args = args
        self.targets = targets
        self.cmds = []
		#Deal with boolean inputs separately
        self.frames = Helper_I_O.strtobool(args.frames)
        self.stacks = Helper_I_O.strtobool(args.stacks)
        self.exhaus_search = Helper_I_O.strtobool(args.exhaus_search)
        self.astig_present = Helper_I_O.strtobool(args.astig_present) 
        self.restr_on_ast = Helper_I_O.strtobool(args.restr_on_ast) 
        self.find_phase_shift = Helper_I_O.strtobool(args.find_phase_shift) 
        self.find_tilt = Helper_I_O.strtobool(args.find_tilt) 
        self.thickness = Helper_I_O.strtobool(args.thickness) 
        self.oned_search = Helper_I_O.strtobool(args.oned_search) 
        self.twod_ref = Helper_I_O.strtobool(args.twod_ref) 
        self.nodes_roundsq = Helper_I_O.strtobool(args.nodes_roundsq) 
        self.nodes_downweight = Helper_I_O.strtobool(args.nodes_downweight) 
        self.expert = Helper_I_O.strtobool(args.expert) 
        self.resample_micrograph = Helper_I_O.strtobool(args.resample_micrograph) 
        self.know_defocus = Helper_I_O.strtobool(args.know_defocus) 
        self.weight_lowres = Helper_I_O.strtobool(args.weight_lowres) 
        self.comscript = Helper_I_O.strtobool(args.comscript)

    @staticmethod
    def convert_to_str(val):
        return "Yes" if val else "No"

    def create_ctffind_cmd(self, target):
        '''
        For given options, create a scffind script. 
        Actually this should be re-written catching exact options, rather than trees/sequences.
        '''
        cmd=f"{self.args.software} <<EOF\n"
        # Input image file name
        cmd+=f"{target[0]}\n"
        # Ctffind checks for the number of frames in the input
        if self.stacks:
            # Input is a movie (stack of frames) No
            cmd+=f"{self.convert_to_str(self.frames)}\n"
            if self.frames:
            # Number of frames to average together [1]
                cmd+=f"{self.args.num_frames}\n"    
        # Output diagnostic image file name
        cmd+=f"{target[1]}\n"
        # Pixel size
        cmd+=f"{self.args.pix}\n"
        # Acceleration voltage [300]
        cmd+=f"{self.args.voltage}\n"
        # Spherical aberration [2.70]
        cmd+=f"{self.args.cs}\n"    
        # Amplitude contrast [0.07]
        cmd+=f"{self.args.amp}\n"
        # Size of amplitude spectrum to compute [512]
        cmd+=f"{self.args.amp_size}\n"    
        # Minimum resolution [30.0]    
        cmd+=f"{self.args.min_res}\n"
        # Maximum resolution [5.0]
        cmd+=f"{self.args.max_res}\n"    
        # Minimum defocus [5000.0]
        cmd+=f"{self.args.min_def}\n"
        # Maximum defocus [50000.0]
        cmd+=f"{self.args.max_def}\n"
        # Defocus search step [100.0]
        cmd+=f"{self.args.def_step}\n"
        # Do you know what astigmatism is present? [No]
        cmd+=f"{self.convert_to_str(self.astig_present)}\n"
        # Slower, more exhaustive search? [No]
        cmd+=f"{self.convert_to_str(self.exhaus_search)}\n"
        if self.astig_present:
            # Known astigmatism [0.0]:
            cmd+=f"{self.args.astig_known}\n"
            # Known astigmatism angle [0.0]
            cmd+=f"{self.args.astigang_known}\n"
        else:
            # Use a restraint on astigmatism? [No]
            cmd+=f"{self.convert_to_str(self.restr_on_ast)}\n"
            if self.restr_on_ast:
                # Expected (tolerated) astigmatism [200.0]
                cmd+=f"{self.args.self.tol_ast}\n"
        # Find additional phase shift? [No]
        cmd+=f"{self.convert_to_str(self.find_phase_shift)}\n"
        if self.find_phase_shift:
            # Minimum phase shift (rad) [0.0]
            cmd+=f"{self.args.min_phase_shift}\n"
            # Maximum phase shift (rad) [3.15]
            cmd+=f"{self.args.max_phase_shift}\n"
            # Phase shift search step [0.5]
            cmd+=f"{self.args.phase_shift_step}\n"
        else:
            # Determine sample tilt? [No]
            cmd+=f"{self.convert_to_str(self.find_tilt)}\n"
        # Determine samnple thickness? [No]
        cmd+=f"{self.convert_to_str(self.thickness)}\n"
        if self.thickness:
                 # Use brute force 1D search? [Yes]
                cmd+=f"{self.convert_to_str(self.oned_search)}\n"
                # Use 2D refinement? [Yes]
                cmd+=f"{self.convert_to_str(self.twod_ref)}\n"
                # Low resolution limit for nodes [30.0]
                cmd+=f"{self.args.nodes_lowres}\n"
                # High resolution limit for nodes [3.0]
                cmd+=f"{self.args.nodes_highres}\n"
                # Use rounded square for nodes? [No]
                cmd+=f"{self.convert_to_str(self.nodes_roundsq)}\n"
                # Downweight nodes? [No]
                cmd+=f"{self.convert_to_str(self.nodes_downweight)}\n"

        # Do you want to set expert options? [No]
        cmd+=f"{self.convert_to_str(self.expert)}\n"
        if self.expert:
            # Resample micrograph if pixel size too small? [Yes]
            cmd+=f"{self.convert_to_str(self.resample_micrograph)}\n"
            if self.resample_micrograph:
                # Target pixel size after resampling [1.4]
                cmd+=f"{self.args.target_pixsize}\n"
            # Do you already know the defocus? [No]
            cmd+=f"{self.convert_to_str(self.know_defocus)}\n"
            if self.know_defocus:
                # Known defocus 1 [0.0]
                cmd+=f"{self.args.known_defocus1}\n"
                # Known defocus 2 [0.0]
                cmd+=f"{self.args.known_defocus2}\n"
                # Known astangle [0.0]
                cmd+=f"{self.args.known_astangle}\n"
            # Weight down low resolution signal? [Yes]
            cmd+=f"{self.convert_to_str(self.weight_lowres)}\n"
            
            # Desired number of parallel threads [1]
            cmd+=f"{self.args.threads}\n"
                    
        cmd+="EOF\n"
        if self.comscript:
            with open(target[0]+".com", "w") as f:
                f.write(cmd)
        self.cmds.append(cmd)
        return cmd

    def create_cmds(self):
        for target in self.targets:
            cmd = self.create_ctffind_cmd(target)
        return self.cmds
    
