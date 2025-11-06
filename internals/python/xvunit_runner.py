import os, sys
import subprocess
import threading 
import time
from pathlib import Path
from typing import Optional, Dict, List

sys.path.append(os.path.dirname(__file__))
from paths import *
from parser import Parser

class XVUnitRunner:
    def __init__(self):
        self.parser = Parser()
        self.project_dir = PROJECT_DIR
        self.sim_dir    = SIM_DIR
        self.testbench_build_dir = None
        self.setup_cmd  = f'call "{VIVADO_SETUP}" && '
        
        self.sim_running = threading.Event()
        
        
    def is_simulation_running(self):
        """Check if simulation is currently running."""
        return self.sim_running.is_set()

    
    def run_test(self, testbench_file, test_names : list, force_recompile : bool = False):
        """Run a single testbench with the XVUnit framework"""
        
       
        self.sim_running.clear()
        module_name = Path(testbench_file).stem
        prj_path = os.path.join(SIM_DIR, module_name[:-3], f'{module_name[:-3]}.prj')
        self.testbench_build_dir = os.path.join(BUILD_DIR, module_name[:-3])


        self.__makedir(BUILD_DIR)
        self.__makedir(self.testbench_build_dir)
        
        
        if force_recompile or self.__needs_recompile(prj_path, module_name):
            print("Compiling...")
            self.__compile(prj_path)

        if force_recompile or self.__needs_reelaboration():
            print("Elaborating...")
            self.__elaborate(module_name)

        if test_names == []:
            print(f"No tests were run")
        else:
            print("Running simulation...")
            
        # note - when passing [] this will execute with __all__ parameter
        self.__simulate(module_name, self.__generate_runner_cfg(test_names))

        
    
    def __compile(self, prj_path):
        
        compile_cmd = (
            f'{self.setup_cmd} xvlog --incr --relax --sv '
            f'-i {os.path.join(self.project_dir, "XVunit/internals/verilog")} '
            f'-prj {prj_path} '
            f'-L uvm -L unisims_ver'
        )
        
        result = subprocess.run(compile_cmd, shell=True, cwd=self.testbench_build_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Compilation failed: {result.stderr}")
            print(f"STDOUT: {result.stdout}")
        
    def __elaborate(self, module_name : str):
        
        elaborate_cmd = (
            f'{self.setup_cmd} xelab --incr --relax --debug typical '
            f'work.{module_name} '
            f'-L uvm -L unisims_ver'
        )
        
        result = subprocess.run(elaborate_cmd, shell=True, cwd=self.testbench_build_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Elaboration failed: {result.stdout}")
        
        
    def __simulate(self, module_name : str, runner_cfg):
        run_cmd = (
            f'{self.setup_cmd} xsim work.{module_name} '
            f'-testplusarg "runner_cfg={runner_cfg}" --runall'
        )
        
        try:
            self.sim_running.set()
            result = subprocess.run(run_cmd, shell=True, cwd=self.testbench_build_dir, capture_output=True, text=True)
        finally:
            self.sim_running.clear()
    
    def __needs_recompile(self, prj_path, module_name):
        """Check if recompilation is needed based on file timestamps."""
        source_files = self.parser.parse_prj(prj_path)
        xvlog_log = os.path.join(self.testbench_build_dir, "xvlog.log")
        
        if not os.path.exists(xvlog_log):
            print("xvlog.log doesn't exist - recompiling")
            return True
        
        compile_time = os.path.getmtime(xvlog_log)
        for source_file in source_files:
            if os.path.exists(source_file):
                source_time = os.path.getmtime(source_file)
                if source_time > compile_time:
                    print(f"Recompiling")
                    return True
        
        
        module_work_dir = os.path.join(self.testbench_build_dir, "xsim.dir", f'work.{module_name}')
        if not os.path.exists(module_work_dir):
            print(f"work.{module_name} doesn't exist - recompiling")
            return True    
        
        compile_log_age = os.path.getmtime(xvlog_log)
        
        # Check if .prj is newer than compilation
        if os.path.exists(prj_path) and os.path.getmtime(prj_path) > compile_log_age:
            return True
        
        return False
        
        
    def __needs_reelaboration(self):
        """Check if re-elaboration is needed."""
        # Check if xelab.log exists (indicates elaboration happened)
        xelab_log = os.path.join(self.testbench_build_dir, "xelab.log")
        if not os.path.exists(xelab_log):
            print("xelab.log doesn't exist - need to elaborate")
            return True
        
        # Get elaboration time from xelab.log
        elab_time = os.path.getmtime(xelab_log)
        
        # Check if compilation is newer than elaboration
        xvlog_log = os.path.join(self.testbench_build_dir, "xvlog.log")
        if os.path.exists(xvlog_log):
            compile_log_age = os.path.getmtime(xvlog_log)
            if compile_log_age > elab_time:
                print("Compilation is newer than elaboration - need to re-elaborate")
                return True
        
        print("No re-elaboration needed - using cached elaboration")
        return False
    
    
    def __generate_runner_cfg(self, test_names : list) -> str:
        """
        Generate the runner configuration string.
        & is used as a denominator between test case names and output path
        """
        enabled_tests = ",".join(test_names) if test_names else "__all__"
        output_path = f"{self.testbench_build_dir}/".replace('\\', '//')
        
        # This format MUST match what your SV parser expects
        return f"enabled_test_cases:{enabled_tests},&output_path:{output_path}"
    
    
    def __makedir(self, path):
        if not Path.is_dir(Path(path)):
            os.makedirs(path, exist_ok=True)
