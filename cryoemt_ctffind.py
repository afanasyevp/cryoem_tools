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
from util.setup_helper import Helper_Prog_Info
from util.setup_helper import Helper_I_O
from util.setup_helper import Helper_Run
from util.setup_helper import _HelpAction, UltimateHelpFormatter
from util.ctffind_helper import Helper_ctffind5

#import string
#import pandas
import time
import argparse

PROG = Path(__file__).name
VER = 20241110

def main(args):

    inputs = Helper_I_O(args)
    if args.mode == "run":
        targets = inputs.find_targets(
            path_in=args.path_in,
            path_out=args.path_out,
            suffix_in=args.insuff,
            suffix_out=args.outsuff,
        )
        ctffind = Helper_ctffind5(args, targets)
        ctffind_cmds=ctffind.create_cmds()
        cmds=Helper_Run(args, ctffind_cmds)
        time.sleep(1)
        cmd_log=str(Path(args.path_out).resolve()) + "/cryoemt_ctffind_cmds.txt"
        #cmds.run_cmds(out=cmd_log)
        cmds.run_cmds()

    else:
        targets = inputs.find_targets(
            path_in=args.path_in,
            suffix_in=args.insuff,
        )
        ctffind = Helper_ctffind5(args, targets)
        results = ctffind.analyse_ctffind_results(str(Path(args.path_out).resolve()) + "/" + args.csv, property=args.property)
    



if __name__ == "__main__":

    description_text = f"""
  Mode 1 ("run"): Batch run of CTFFIND5 (ver 5.0.2) on aligned image stacks. 
  For the other versions, the program might have to be modified.

  Mode 2 ("ana"): Analyse results (phase shifts, etc.)

  Dependencies: pandas
"""

    examples = [
        f"\n*** EXAMPLES ***\n",
        f" Estimation of phase shifts:\n",
        f" {PROG} run --software ctffind --pix 2.67 --path_in ./ --path_out . --insuff _alifr.mrc --outsuff _alifr_ctf.mrc --data_type ts --exhaus_search 1 --threads 12 --find_phase_shift 1 --find_tilt 0 --thickness 0 --comscript 1\n\n",
        "",
        f" Estimation of CTF only (standard SPA  script): \n",
        f" {PROG} run --software ctffind --pix 1.08 --path_in ./ --path_out . --insuff _fractions.mrc --outsuff _fractions_ctf.mrc --stacks 0 --exhaus_search 1 --threads 12 --find_phase_shift 0 --find_tilt 0 --thickness 0 --min_res 30 --max_res 3 --min_def 5000 --max_def 50000 --exhaus_search 0 --threads 12 --comscript 1\n\n",
        "",
        f" Analysis of phase shifts:\n",
        f" {PROG} ana  --property phase_shift  --path_in . --path_out . --insuff .txt",
    ]
    description = Helper_Prog_Info(PROG, VER, description_text, examples).make_description()

    parser = argparse.ArgumentParser(prog=PROG, formatter_class=UltimateHelpFormatter, add_help=False, description=description) 
    parser.add_argument ('-h', '--help', action=_HelpAction, help='show help message with a full list of arguments')
    
    subparsers = parser.add_subparsers(dest="mode", required=True)   
    run_parser=subparsers.add_parser("run", help="CTFFIND5-run mode", formatter_class=UltimateHelpFormatter)

    ana_parser=subparsers.add_parser("ana",  help="CTFFIND5-analyse mode", formatter_class=UltimateHelpFormatter)
    add_ana=ana_parser.add_argument
    add_run=run_parser.add_argument

    # --analyse options
    add_ana(
        "--path_in",
        default=".",
        help="Default: . | Path to the folder with the CTFFIND5 outputs",
    )
    add_ana(
        "--insuff",
        default="_ctf.txt",
        help="Default: _ctf.txt | Suffix of the input CTFFIND5 txt files",
    )
    add_ana(
        "--property",
        default=None,
        choices=["phase_shift"],
        help="Default: phase_shift | Analyse phase shifts or other property (phase_shift)",
    )
    add_ana(
        "--path_out",
        default="./",
        help="Default: . | Path to the folder with the output of this script",
    )
    add_ana(
        "--csv",
        default="cryoemt_ctffind_results.csv",
        help="Default: cryoemt_ctffind_results.csv | Name of the output csv file",
    )
    add_ana(
        "--csv_name",
        default=True,
        help="Default: True | Generate csv file with the output data?",
    )
    #add_ana("--data_type", default="mic", choices=["mic", "mics", "mov", "ts"], help="Default: mic (micrographs) | Data type: micrograph(s), movies, tilt series. (Options: mic, mics, mov, ts)")
    
    # CTFFIND5 options
    add_run(
        "--path_in",
        default="./",
        help="Default: ./ | Path to the folder with micrographs",
    )
    add_run(
        "--insuff",
        default="_alifr.mrc",
        help="Default: _alifr.mrc | Suffix of the input files",
    )
    add_run("--data_type", default="mic", choices=["mic", "mics", "mov", "ts"], help="Default: mic (micrographs) | Data type: micrograph(s), movies, tilt series. (Options: mic, mics, mov, ts)")
    add_run(
        "--stacks",
        default=False,
        help="Default: False | Are the input images stacks of files?",
    )
    add_run(
        "--comscript",
        default=True,
        help="Default: True | Create .com script for each micrograph",
    )
    add_run(
        "--software",
        default="ctffind",
        help="Default: ctffind | Software to use",
    )
    add_run("--outsuff", default="_alifr_ctf.mrc", help="Suffix of the output files")
    add_run(
        "--path_out",
        default="./",
        help="Default: ./ | Path to the output folder",
    )
    add_run("--pix", type=float, required=True, help="Pixel size")
    add_run("--voltage", default=300, help="Default: 300 | Acceleration voltage")
    add_run(
        "--cs",
        default=2.7,
        type=float,
        help="Default: 2.7 | Spherical aberration",
    )
    add_run(
        "--amp",
        default=0.07,
        type=float,
        help="Default: 0.07| Amplitude contrast",
    )
    add_run(
        "--amp_size",
        default=512,
        type=int,
        help="Default: 512| Size of amplitude spectrum to compute",
    )
    add_run(
        "--min_res",
        default=30,
        type=int,
        help="Default: 30 | Minimum resolution",
    )
    add_run("--max_res", default=5, type=int, help="Default: 5 | Maximum resolution")
    add_run(
        "--min_def",
        default=2000,
        type=int,
        help="Default: 2000 | Minimum defocus",
    )
    add_run(
        "--max_def",
        default=50000,
        type=int,
        help="Default: 70000 | Maximum defocus",
    )
    add_run(
        "--def_step",
        default=100,
        type=int,
        help="Default: 100 | Defocus search step",
    )
    add_run(
        "--exhaus_search",
        default=False,
        help="Default: False | Slower, more exhaustive search?",
    )
    add_run(
        "--threads",
        default=12,
        type=int,
        help="Desired number of parallel threads",
    )
    add_run(
        "--frames",
        default=1,
        help="Default: 1 | Number of frames to average together",
    )
    add_run(
        "--astig_present",
        default=False,
        help="Default: False | Do you know what astigmatism is present?",
    )
    add_run(
        "--astig_known",
        default=0,
        type=float,
        help="Default: 0 | Known present astigmatism",
    )
    add_run(
        "--astigang_known",
        default=0,
        type=float,
        help="Default: 0 | Known present astigmatism angle",
    )
    add_run(
        "--restr_on_ast",
        default=False,
        help="Default: False | Use a restrain on astigmatism",
    )
    add_run(
        "--tol_ast",
        default=200,
        type=float,
        help="Default: 200 | Expected (tolerated) astigmatism",
    )
    add_run(
        "--find_phase_shift",
        default=True,
        help="Default: True | Find add_runitional phase shift?",
    )
    add_run(
        "--min_phase_shift",
        default=0,
        type=float,
        help="Default: 0 | Minimum phase shift (rad)",
    )
    add_run(
        "--max_phase_shift",
        default=3.15,
        type=float,
        help="Default: 0 | Maximum phase shift (rad)",
    )
    add_run(
        "--phase_shift_step",
        default=0.5,
        help="Default: 0.5 | Phase shift search step",
    )
    add_run(
        "--find_tilt",
        default=True,
        help="Default: False | Determine sample tilt?",
    )
    add_run(
        "--thickness",
        default=False,
        help="Default: False | Determine samnple thickness?",
    )
    add_run(
        "--oned_search",
        default=True,
        help="Default: True | Use brute force 1D search?",
    )
    add_run("--twod_ref", default=True, help="Default: True | Use 2D refinement?")
    add_run(
        "--nodes_lowres",
        default=30,
        type=float,
        help="Default: 30 | Low resolution limit for nodes",
    )
    add_run(
        "--nodes_highres",
        default=3,
        type=float,
        help="Default: 3 | High resolution limit for nodes",
    )
    add_run(
        "--nodes_roundsq",
        default=False,
        help="Default: False | Use rounded square for nodes?",
    )
    add_run(
        "--nodes_downweight",
        default=False,
        help="Default: False | Downweight nodes?",
    )
    add_run(
        "--expert",
        default=True,
        help="Default: False | Do you want to set expert options?",
    )
    add_run(
        "--resam",
        default=True,
        help="Default: True | Resample micrograph if pixel size too small?",
    )
    add_run(
        "--target_pixsize",
        default=1.4,
        type=float,
        help="Default: 1.4 | Target pixel size after resampling",
    )
    add_run(
        "--know_defocus",
        default=False,
        help="Default: False | Do you already know the defocus?",
    )
    add_run("--known_defocus1", default=0, help="Default: 0 | Known defocus1")
    add_run("--known_defocus2", default=0, help="Default: 0 | Known defocus2")
    add_run(
        "--known_astangle",
        default=0,
        help="Default: 0 | Known astigmatism angle",
    )
    add_run(
        "--weight_lowres",
        default=True,
        help="Default: True | Weight down low resolution signal?",
    )

    args = parser.parse_args()
    print(description)

    print(f" => Input parameters: ")
    for key, value in vars(args).items():
            print(f"  --{key}  {value}")

    main(args)
