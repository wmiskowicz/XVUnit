import os, sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, List

sys.path.append(os.path.dirname(__file__))
from paths import *

class XVUnitRunner:
    def __init__(self):
        self.project_dir = PROJECT_DIR
        self.sim_dir    = SIM_DIR
        self.build_dir  = BUILD_DIR
        self.setup_cmd  = f'call "{VIVADO_SETUP}" && '
    
    def generate_runner_cfg(self, test_names : list) -> str:
        """
        Generate the runner configuration string.
        & is used as a denominator between test case names and output path
        """
        enabled_tests = ",".join(test_names) if test_names else "__all__"
        output_path = f"{self.build_dir}/".replace('\\', '//')
        
        # This format MUST match what your SV parser expects
        return f"enabled_test_cases:{enabled_tests},&output_path:{output_path}"
    
    def run_test(self, testbench_file, test_names : list=None):
        """Run a single testbench with the XVUnit framework"""
        
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir, exist_ok=True)
        
        subprocess.run(["git", "clean", "-fXd", "."], cwd=self.sim_dir)
        
        # Generate runner configuration
        runner_cfg = self.generate_runner_cfg(test_names)
        
        # Get the module name from the testbench file
        module_name = Path(testbench_file).stem
        
        # COMPILE: Use normal compilation without generic
        prj_path = os.path.join(SIM_DIR, module_name[:-3], f'{module_name[:-3]}.prj')
        compile_cmd = (
            f'{self.setup_cmd} xvlog --incr --relax --sv '
            f'-i {os.path.join(self.project_dir, "XVunit/internals/verilog")} '
            f'-prj {prj_path} '
            f'-L uvm -L unisims_ver'
        )
        
        # ELABORATE: No changes here
        elaborate_cmd = (
            f'{self.setup_cmd} xelab --incr --relax --debug typical '
            f'work.{module_name} '
            f'-L uvm -L unisims_ver'
        )
        
        # RUN: Pass runner_cfg as plusarg
        run_cmd = (
            f'{self.setup_cmd} xsim work.{module_name} '
            f'-testplusarg "runner_cfg={runner_cfg}" --runall'
        )
        if not Path.is_dir(Path(self.build_dir)):
            os.makedirs(self.build_dir, exist_ok=True)
        
        print("Compiling...")
        
        result = subprocess.run(compile_cmd, shell=True, cwd=self.build_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Compilation failed: {result.stderr}")
            print(f"STDOUT: {result.stdout}")
            return False        
        
        print("Elaborating...")
        result = subprocess.run(elaborate_cmd, shell=True, cwd=self.build_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Elaboration failed: {result.stdout}")
            return False
        
        print("Running simulation...")

        result = subprocess.run(run_cmd, shell=True, cwd=self.build_dir, capture_output=True, text=True)
        
        return result.returncode == 0


