import threading
import time
import colorama
import glob
from typing import List
from typing import Dict, Optional

import os
from pathlib import Path
from paths import *
from test_bench import Testbench, TestCase


class FileManager:
  
    def __init__(self):
        pass
    
    
    def collect_hdl_files(self, paths_to_search: list):
        extensions = [".sv", ".v", ".vhd"]
        collected = []
        
        for path in paths_to_search:
            # Fixed: check 'path' instead of 'paths_to_search'
            if not os.path.isdir(path):
                print(f"Warning: '{path}' is not a directory, skipping")
                continue 

            for base, dirs, files in os.walk(path):
                for filename in files:
                    _, ext = os.path.splitext(filename)
                    if ext.lower() in extensions:
                        full_path = os.path.join(base, filename)
                        collected.append(os.path.abspath(full_path))
        
        return sorted(collected)
    
    
    def create_prj(self, prj_path : str, source_files : List[str]):
        
        sv_files    = []
        v_files     = []
        vhdl_files  = []
        
        for file in source_files:
            if file.endswith(".sv"):
                sv_files.append(file)
            if file.endswith(".v"):
                v_files.append(file)
            if file.endswith(".vhd"):
                vhdl_files.append(file)
                
        sv_files = self.__prioritize_pkg_and_if(sv_files)
        
        
        
        with open(prj_path, "w") as f:
            f.write("# List of files defining the modules used during the test.\n")
            f.write("# This file can be auto-generated using -prj flag of run.py script.\n")
            f.write("# For syntax detail see AMD Xilinx UG 900:\n")
            f.write("# https://docs.xilinx.com/r/en-US/ug900-vivado-logic-simulation/Project-File-.prj-Syntax\n")
            f.write("\n")

            if sv_files:
                f.write("sv work ")
                f.write(" \\\n        ".join(sv_files))
                f.write(" \\\n\n")

            if v_files:
                f.write("verilog work ")
                f.write(" \\\n            ".join(v_files))
                f.write(" \\\n\n")

            if vhdl_files:
                f.write("vhdl work ")
                f.write(" \\\n          ".join(vhdl_files))
                f.write(" \\\n")
                
                
    def __prioritize_pkg_and_if(self, files):
        """Sort so that '_pkg' and '_if' files come first."""
        pkg_if_files = [f for f in files if "_pkg" in f or "_if" in f]
        other_files = [f for f in files if "_pkg" not in f and "_if" not in f]
        return sorted(pkg_if_files) + sorted(other_files)
    
    def get_wcfg_file(self, module_name) -> str:
        wcfg_files = glob.glob(os.path.join(SIM_DIR, module_name[:-3], "*.wcfg"))
        return wcfg_files[0] if wcfg_files else None
