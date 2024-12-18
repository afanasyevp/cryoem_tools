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


import re
import string
import math
import pandas as pd
from util.setup_helper import Helper_I_O
from pathlib import Path
ver=20241110

class Helper_ctffind5:
    def __init__(self, args, targets):
        self.args = args
        self.targets = targets
        self.ctffind_data = None
        self.ctffind_data_avrot = None
        self.ctffind_data_full = None
        if self.args.mode == "run":
            self.cmds = []
		    #Deal with boolean inputs separately
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
            self.resam = Helper_I_O.strtobool(args.resam) 
            self.know_defocus = Helper_I_O.strtobool(args.know_defocus) 
            self.weight_lowres = Helper_I_O.strtobool(args.weight_lowres) 
            self.comscript = Helper_I_O.strtobool(args.comscript)
       

    def create_ctffind_cmd(self, target):
        '''
        For given options, create a scffind script. 
        Actually this should be re-written catching exact options, rather than trees/sequences.
        '''
        cmd=f"# The script was created by {Path(__file__).name} version {ver}\n# https://github.com/afanasyevp/cryoem_tools \n# \n"
        cmd+=f"{self.args.software} <<EOF\n"
        # Input image file name
        cmd+=f"{target[0]}\n"
        # Ctffind checks for the number of frames in the input
        if self.args.data_type=="ts" or self.args.data_type=="mov" or self.args.data_type=="mics":
        # Input is a movie (stack of frames) No
            if self.args.data_type=="mov":
                cmd+=f"Yes\n"
                # Number of frames to average together [1]
                cmd+=f"{self.args.num_frames}\n"    
            else:
                cmd+=f"No\n"
                
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
            cmd+=f"{self.convert_to_str(self.resam)}\n"
            if self.resam:
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
    
    def analyse_ctffind_results(self, csv_output, property):
        # define a dictionary of micrograph(s), corresponding to a single .mrc file, on which ctffind was running
        # Below are the assumptions on the results file. If the program output changes, consider re-implementing using regex
         
        dataset_results = []
        dataset_results_avrot = []
       
        # results of all files:
        headers_lines=5 # number of lines in headers of the output file
    
        line1_word1="Output"
        line2_word1="Input"
        line3_word1="Pixel"
        line4_word1="Box"
        line5_word1="Columns"

        line1_option1="CTFFind version"
        line1_option2="run on"
        line2_option1="Input file"
        line2_option2="Number of micrographs"
        line3_option1="Pixel size"
        line3_option2="acceleration voltage"
        line3_option3="spherical aberration"
        line3_option4="amplitude contrast"
        line4_option1="Box size"
        line4_option2="min. res."
        line4_option3="max. res"
        line4_option4="min. def"
        line4_option5="max. def"
        
        line5_option1="micrograph number"
        line5_option2="defocus 1 [Angstroms]"
        line5_option3="defocus 2"
        line5_option4="azimuth of astigmatism"
        line5_option5="additional phase shift [radians]"
        line5_option6="cross correlation"
        line5_option7="spacing (in Angstroms) up to which CTF rings were fit successfully"
        line5_option8="Estimated tilt axis angle"
        line5_option9="Estimated tilt angle"
        line5_option10="Estimated sample thickness (in Angstroms)"

        # These are in the _avrot.txt files
        line5_option11="spatial frequency (1/Angstroms)"
        line5_option12="1D rotational average of spectrum (assuming no astigmatism)"
        line5_option13="1D rotational average of spectrum"
        line5_option14="CTF fit"
        line5_option15="cross-correlation between spectrum and CTF fit"
        line5_option16="2sigma of expected cross correlation of noise"
        line5_option17="lines per micrograph"
        
        for target in self.targets:
            params={}
            data_headers={}
            filename=target[0]
            with open(filename, "r") as f:
                lines = f.readlines()
            for count, line in enumerate(lines, start=1):
                line=line.strip()
                words=line.split()
                if line.startswith("#"):
                    if count == 1:
                        if words[1].translate(str.maketrans('', '', string.punctuation)) ==  line1_word1:
                            params[line1_option1] = words[5]
                            params[line1_option2] = words[8] + " " + words[9]
                        else:
                            print( f"=> Warning! Line {count} in the {filename} does not contain word \'{line1_word1}\'")
                            break
                    elif count == 2:
                        if words[1].translate(str.maketrans('', '', string.punctuation))  ==  line2_word1:
                            params[line2_option1] = words[3]
                            params[line2_option2] = int(words[8])
                            if params[line2_option2] > 1:
                                print(f" => Number of micrographs in {params[line2_option1]} is {params[line2_option2]}. This is a stack of micrographs or tilt series.")
                        else:
                            print( f"=> Warning! Line {count} in the {filename} does not contain word \'{line2_word1}\'")
                            break
                    elif count == 3:
                        if words[1].translate(str.maketrans('', '', string.punctuation))  ==  line3_word1:
                            params[line3_option1] = float(words[3])
                            params[line3_option2] = float(words[8])
                            params[line3_option3] = float(words[13])
                            params[line3_option4] = float(words[18])                          
                        else:
                            print( f"=> Warning! Line {count} in the {filename} does not contain word \'{line3_word1}\'")
                            break
                    elif count == 4:
                        if words[1].translate(str.maketrans('', '', string.punctuation))  ==  line4_word1:
                            params[line4_option1] = int(words[3])                          
                            params[line4_option2] = float(words[8])                          
                            params[line4_option3] = float(words[13])                          
                            params[line4_option4] = float(words[18])                          
                            params[line4_option5] = float(words[22])                              
                        else:
                            print( f"=> Warning! Line {count} in the {filename} does not contain word \'{line4_word1}\'")
                            break
                    elif count == 5:
                        match = re.search(r"#\s*(\d+)\s+lines per micrograph", line)
                        if not match:
                            avrot = False
                            if words[1].translate(str.maketrans('', '', string.punctuation))  !=  line5_word1:
                                #Assume it is the last header line in the .txt file
                                print(f"Warning!! : this line #{count} in the {filename} is problematic: \n{line}\n ") 
                        else:
                            avrot=True
                            lines_per_micrograph=match.group(1)
                        columns_assignment=self.determine_columns_assignment(line)
                            
                        for key, value in columns_assignment.items():
                            if key == line5_option1:
                                data_headers[line5_option1] = value
                            elif key == line5_option2:
                                data_headers[line5_option2] = value
                            elif key == line5_option3:
                                data_headers[line5_option3] = value  
                            elif key == line5_option4:
                                data_headers[line5_option4] = value 
                            elif key == line5_option5:
                                data_headers[line5_option5] = value 
                            elif key == line5_option6:
                                data_headers[line5_option6] = value 
                            elif key == line5_option7:
                                data_headers[line5_option7] = value 
                            elif key == line5_option8:
                                data_headers[line5_option8] = value 
                            elif key == line5_option9:
                                data_headers[line5_option9] = value 
                            elif key == line5_option10:
                                data_headers[line5_option10] = value
                            # These are in the _avrot.txt files
                            elif key == line5_option11:
                                data_headers[line5_option11] = value
                            elif key == line5_option12:
                                data_headers[line5_option12] = value
                            elif key == line5_option13:
                                data_headers[line5_option13] = value
                            elif key == line5_option14:
                                data_headers[line5_option14] = value
                            elif key == line5_option15:
                                data_headers[line5_option15] = value
                            elif key == line5_option16:
                                data_headers[line5_option16] = value
                            else:
                                print(f"Warning from ctffind_helper.py (analyse_ctffind_result)! Unknown header value ({key}) in {target} file. Please report to afanasyevp.code@gmail.com")
                    else:
                        print(f" +> Warning Line {count} in the {filename} contains \'#\' symbol, which is suspicious. This line will be ignored.")
                        break
                else:
                    # Check for accumulation of the header info
                    if params != {} and data_headers != {}:
                        if avrot==False:
                            # Collecting the data
                            # Swap keys and values. It is a lazy way - otherwise one could sort by values like: sorted(data_headers.items(), key=lambda x: x[1])) or swap it above during assignment
                            data_headers_swapped = {value: key for key, value in data_headers.items()}
                            # Assign to a dictionary sorted by values:
                            data_headers_sorted=dict(sorted(data_headers_swapped.items()))
                            # Define a dictionary for each micrograph:
                            ctffind_results={}
                            if len(data_headers) != len(words):
                                print(f" => Warning!! The number of data fields in the {filename} is not equal to the determined header information {data_headers_sorted}")
                            else:
                                zipped_list = list(zip(data_headers_sorted, words))
                                for item in zipped_list:
                                    ctffind_results[data_headers_sorted[item[0]]] = item[1]
                                ctffind_results.update(params)
                                dataset_results.append(ctffind_results)
                        else:
                            counter_data_line= 1+(count - headers_lines-1) % int(lines_per_micrograph)
                            counter_micrograph_number = 1+math.floor((count - headers_lines - 1) / int(lines_per_micrograph))
                            ctffind_results_avrot={}
                            ctffind_results_avrot[line2_option1] = filename
                            ctffind_results_avrot[line5_option1] = counter_micrograph_number
                            for k,v in data_headers.items():
                                ctffind_results_avrot[k] = words
                            ctffind_results_avrot.update(params)
                            dataset_results_avrot.append(ctffind_results_avrot)
                    else:
                        print(f"\n => Warning! The header information for the {filename} is missing. Check the input!")
                        break

        # convert radians to angles for phase shift 
        if dataset_results == {}:
            print(f"No ctffind output data found in {self.args.path_in} ")
        for i in dataset_results:
            if i[line5_option5]:
                angle=round(math.degrees(float(i[line5_option5])),1)
                if angle>90: angle = 180 - angle
                i["additional phase shift [ang]"]=angle
        
        #convert str to integer for micrograph number
        for i in dataset_results:
            i[line5_option1] = int(float(i[line5_option1]))

        # Create pandas dataframes
        self.ctffind_data=pd.DataFrame(dataset_results)
        self.ctffind_data_avrot=pd.DataFrame(dataset_results_avrot)
        # combine two datasets based on keys "Input file" and "micrograph number "
        combined = self.combine_data(dataset_results_avrot, dataset_results, [line5_option1, line2_option1])
        self.ctffind_data_full=pd.DataFrame(combined)

        print(f"\n => Data is read...\n")
        if csv_output:
            csv_output_avrot=csv_output[:-4]+"_avrot.csv"
            self.ctffind_data_avrot.to_csv(csv_output_avrot, index=False)
            self.ctffind_data.to_csv(csv_output, index=False)
            print(f" => Data is written to csv files {csv_output_avrot} (full output) and {csv_output} (compact output)\n\n")
            #print(self.ctffind_data_full)   
        else:
            print(f"\n => No output will be saved", self.ctffind_data)
        print(self.ctffind_data)
        return self.ctffind_data_full
     
    @staticmethod
    def determine_columns_assignment(line):
        """Takes a line like:

        {'micrograph number': 1, 'defocus 1 [Angstroms]': 2, 'defocus 2': 3, 'azimuth of astigmatism': 4, 'additional phase shift [radians]': 5, 'cross correlation': 6, 'spacing (in Angstroms) up to which CTF rings were fit successfully': 7, 'Estimated tilt axis angle': 8, 'Estimated tilt angle': 9}
        """
        pattern=r"#(\d+)\s*-?\s*([^;]+)"
        matches = re.findall(pattern, line)
        column_dict = {description.strip(): int(number)  for number, description in matches}

        return column_dict
    
    @staticmethod
    def convert_to_str(val):
        return "Yes" if val else "No"

    @staticmethod
    def combine_data(list1, list2, matching_keys):
        """
        Combines two lists of dictionaries based on keys
        """
        merged_list=[]
        for dict1 in list1:
            # Find matching dictionaries in list2 based on all matching keys
            match = next(
                (dict2 for dict2 in list2 if all(dict1.get(key) == dict2.get(key) for key in matching_keys)),
                None
            )
            if match:
                # Merge dictionaries when a match is found
                merged_dict = {**dict1, **match}
                merged_list.append(merged_dict)
            else:
                # Add dictionary as is if no match is found
                merged_list.append(dict1)

        # Append any dictionaries from list2 without matches in list1
        for dict2 in list2:
            if not any(all(dict1.get(key) == dict2.get(key) for key in matching_keys) for dict1 in list1):
                merged_list.append(dict2)

        return merged_list

