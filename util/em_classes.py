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
from pathlib import Path, PureWindowsPath

VER=20241122

class FSC:
	pass

class Starfile:
	pass

class Map:
	pass

class Tomogram:
	pass

class Movie:
	pass

class Micrograph:
	pass


class Dataset:
    def __init__(self, name, targets=None):
        self.name=name
        self.data = {}  


class TS:
    def __init__(self, mdocfile, framespath):
        self.mdocfile = str(Path(mdocfile).absolute())
        self.name=Path(self.mdocfile).stem
        self.tilts = []
        self.general_info = {}
        self.framespath = framespath
    
    def fetch_info_from_mdoc(self):
        """
        Fetches info from mdoc files, writes it out into Tilt instances.
        """
        print(f"  Fetching info from {self.mdocfile}  file...")
        with open(self.mdocfile, "r") as f:
            lines = f.readlines()
            ts_start = False
            for i, line in enumerate(lines, start=1):
                # Assume each non-empty line has a "=" sign
                line = line.strip()
                if len(line) == 0:
                    continue
                if ts_start:
                    line_list = line.split("=")
                    if  line_list[0] == "[ZValue ":
                        ZValue = int(line_list[-1].split("]")[0][1:])
                        #print(tilt.__dict__)
                        tilt = Tilt(self.mdocfile, ZValue)
                        self.tilts.append(tilt)
                    else:
                        k = line_list[0].split()[0].strip()
                        v = " ".join(line_list[1:])
                        if k == "SubFramePath":
                            """
                            Example of the old SubFramePath: [full_path_to_the_dataset]\frames\YYMMDD_dataset_3931.tif
                            NewSubFramePath would be: [full_path_to_frames_folder]/YYMMDD_dataset_3931.tif
                            """
                            if self.framespath:
                                newdir = os.path.dirname(self.framespath)
                                NewSubFramePath = newdir + "/" + PureWindowsPath(v).name
                            else:
                                NewSubFramePath = "frames/" + PureWindowsPath(v).name
                            setattr(tilt, "NewSubFramePath", NewSubFramePath)
                        else:
                            v=v.split()
                            setattr(tilt, k, v)
                else:
                    if "[ZValue" in line:
                        ts_start = True
                        line_list = line.split("=")
                        ZValue = int(line_list[-1].split("]")[0][1:])
                        tilt = Tilt(self.mdocfile, ZValue)
                        self.tilts.append(tilt)
                    else:
                    # general header info (first ~10 lines
                        if "=" in line and line[0] != "[":
                            line_list = line.split("=")
                            k = line_list[0].split()[0].strip()
                            v = " ".join(line_list[1:])
                            self.general_info[k] = v
                        else:
                            self.general_info["other_info_line_" + str(i)] = line
            
class Tilt:
    def __init__(self, mdoc_file, ZValue):
        self.mdoc_file=mdoc_file 
        self.ZValue = ZValue
        self.NewSubFramePath = None # => to be set by TS.fetch_info_from_mdoc()

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
        self.ProbeMode = None
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
        self.TimeStamp = None

