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

VER=20241105

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

class TS:
    def __init__(self, options, mdocfile):
        self.args = None
        self.mdocfile = None
        self.tilts = {}
        self.general_info = {}
        self.movies_tiff = False

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

