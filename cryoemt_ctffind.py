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


from pathlib import Path
from util.setup_helper import *

# from util.setup_helper import Helper_I_O
# from util.setup_helper import Helper_commands
# from util.setup_helper import _HelpAction
from util.ctffind_helper import Helper_ctffind5
import subprocess
import argparse
import time

PROG = Path(__file__).name
VER = 20241103


def main(args):

    inputs = Helper_I_O(args)
    if not args.analyse:
        targets = inputs.find_targets(
            path_in=args.path_in,
            path_out=args.path_out,
            suffix_in=args.insuff,
            suffix_out=args.outsuff,
        )
        ctffind = Helper_ctffind5(args, targets)
        # ctffind_cmds=ctffind.create_cmds()
    else:
        targets = inputs.find_targets(
            path_in=args.path_in,
            path_out=args.path_out,
            suffix_in=args.insuff,
            suffix_out=args.outsuff,
        )
    time.sleep(2)

    # cmds=Helper_commands(args, ctffind_cmds)
    # run_cmds = cmds.run_cmds()


if __name__ == "__main__":

    description_text = f"""
  Option 1: Batch run of CTFFIND5 (ver 5.0.2) on aligned image stacks. 
  For the other versions, the program might have to be modified.

  Option 2: Analyse phase shifts
"""

    examples = [
        f"*** EXAMPLES  ***\n",
        f" Estimation of phase shifts:\n",
        f" {PROG} --software ctffind --pix 2.67 --path_in ./ --path_out . --insuff _alifr.mrc --outsuff _alifr_ctf.mrc --stacks 1 --exhaus_search 1 --threads 12 --find_phase_shift 1 --find_tilt 0 --thickness 0 --comscript 1\n\n",
        "",
        f" Estimation of CTF only (standard SPA  script): \n",
        f" {PROG} --software ctffind --pix 1.08 --path_in ./ --path_out . --insuff _fractions.mrc --outsuff _fractions_ctf.mrc --stacks 0 --exhaus_search 1 --threads 12 --find_phase_shift 0 --find_tilt 0 --thickness 0 --min_res 30 --max_res 3 --min_def 5000 --max_def 50000 --exhaus_search 0 --threads 12 --comscript 1\n\n",
        "",
        f" Analysis of phase shifts:\n",
        f" {PROG}  --analyse phase_shifts  --path_in . --out phase_shifts.txt --insuff _ctf.txt --tilts 51",
    ]
    decoration = Helper_Decor(PROG, VER, description_text, examples)
    parser = argparse.ArgumentParser(
        prog=PROG,
        # description=description,
        # epilog=examples
    )
    add = parser.add_argument
    # Input for the input/output check
    add(
        "--path_in",
        default="./",
        help="Default: ./ | Path to the folder with micrographs",
    )
    add(
        "--insuff",
        default="_alifr.mrc",
        help="Default: _alifr.mrc | Suffix of the input files",
    )

    # --analyse options
    add(
        "--analyse",
        default=None,
        choices=["phase_shift"],
        help="Default: None | Analyse phase shifts.",
    )
    add(
        "--out",
        default="phase_sfifts.txt",
        help="Default: phase_shifts.txt | Output file with phase shifts.",
    )

    # CTFFIND5 options
    add(
        "--stacks",
        default=False,
        help="Default: False | Are the input images stacks of files?",
    )
    add(
        "--comscript",
        default=True,
        help="Default: True | Create .com script for each micrograph",
    )
    add(
        "--software",
        default="ctffind",
        help="Default: ctffind | Software to use",
    )
    add("--outsuff", default="_alifr_ctf.mrc", help="Suffix of the output files")
    add(
        "--path_out",
        default="./",
        help="Default: ./ | Path to the output folder",
    )
    add("--pix", type=float, required=True, help="Pixel size")
    add("--voltage", default=300, help="Default: 300 | Acceleration voltage")
    add(
        "--cs",
        default=2.7,
        type=float,
        help="Default: 2.7 | Spherical aberration",
    )
    add(
        "--amp",
        default=0.07,
        type=float,
        help="Default: 0.07| Amplitude contrast",
    )
    add(
        "--amp_size",
        default=512,
        type=int,
        help="Default: 512| Size of amplitude spectrum to compute",
    )
    add(
        "--min_res",
        default=30,
        type=int,
        help="Default: 30 | Minimum resolution",
    )
    add("--max_res", default=5, type=int, help="Default: 5 | Maximum resolution")
    add(
        "--min_def",
        default=2000,
        type=int,
        help="Default: 2000 | Minimum defocus",
    )
    add(
        "--max_def",
        default=50000,
        type=int,
        help="Default: 70000 | Maximum defocus",
    )
    add(
        "--def_step",
        default=100,
        type=int,
        help="Default: 100 | Defocus search step",
    )
    add(
        "--exhaus_search",
        default=False,
        help="Default: False | Slower, more exhaustive search?",
    )
    add(
        "--threads",
        default=12,
        type=int,
        help="Desired number of parallel threads",
    )
    add(
        "--frames",
        default=False,
        help="Default: False | Do you know what astigmatism is present?",
    )
    add(
        "--num_frames",
        default=1,
        help="Default: 1 | Number of frames to average together",
    )
    add(
        "--astig_present",
        default=False,
        help="Default: False | Do you know what astigmatism is present?",
    )
    add(
        "--astig_known",
        default=0,
        type=float,
        help="Default: 0 | Known present astigmatism",
    )
    add(
        "--astigang_known",
        default=0,
        type=float,
        help="Default: 0 | Known present astigmatism angle",
    )
    add(
        "--restr_on_ast",
        default=False,
        help="Default: False | Use a restrain on astigmatism",
    )
    add(
        "--tol_ast",
        default=200,
        type=float,
        help="Default: 200 | Expected (tolerated) astigmatism",
    )
    add(
        "--find_phase_shift",
        default=True,
        help="Default: True | Find additional phase shift?",
    )
    add(
        "--min_phase_shift",
        default=0,
        type=float,
        help="Default: 0 | Minimum phase shift (rad)",
    )
    add(
        "--max_phase_shift",
        default=3.15,
        type=float,
        help="Default: 0 | Maximum phase shift (rad)",
    )
    add(
        "--phase_shift_step",
        default=0.5,
        help="Default: 0.5 | Phase shift search step",
    )
    add(
        "--find_tilt",
        default=True,
        help="Default: False | Determine sample tilt?",
    )
    add(
        "--thickness",
        default=False,
        help="Default: False | Determine samnple thickness?",
    )
    add(
        "--oned_search",
        default=True,
        help="Default: True | Use brute force 1D search?",
    )
    add("--twod_ref", default=True, help="Default: True | Use 2D refinement?")
    add(
        "--nodes_lowres",
        default=30,
        type=float,
        help="Default: 30 | Low resolution limit for nodes",
    )
    add(
        "--nodes_highres",
        default=3,
        type=float,
        help="Default: 3 | High resolution limit for nodes",
    )
    add(
        "--nodes_roundsq",
        default=False,
        help="Default: False | Use rounded square for nodes?",
    )
    add(
        "--nodes_downweight",
        default=False,
        help="Default: False | Downweight nodes?",
    )
    add(
        "--expert",
        default=True,
        help="Default: False | Do you want to set expert options?",
    )
    add(
        "--resample_micrograph",
        default=True,
        help="Default: True | Resample micrograph if pixel size too small?",
    )
    add(
        "--target_pixsize",
        default=1.4,
        type=float,
        help="Default: 1.4 | Target pixel size after resampling",
    )
    add(
        "--know_defocus",
        default=False,
        help="Default: False | Do you already know the defocus?",
    )
    add("--known_defocus1", default=0, help="Default: 0 | Known defocus1")
    add("--known_defocus2", default=0, help="Default: 0 | Known defocus2")
    add(
        "--known_astangle",
        default=0,
        help="Default: 0 | Known astigmatism angle",
    )
    add(
        "--weight_lowres",
        default=True,
        help="Default: True | Weight down low resolution signal?",
    )

    args = parser.parse_args()
    print(decoration.make_description())

    print(f" => Input parameters: ")
    if not args.analyse:
        for key, value in vars(args).items():
            print(f"  --{key}  {value}")

    main(args)
