import os
import sys
import subprocess
import glob
import argparse
import colorama
import time
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from pathlib import Path

import os
from pathlib import Path
from internals.python.test_bench import Testbench, TestCase
from internals.python.xvunit_runner import XVUnitRunner


class XVunit():
    
    def __init__(self):
        self.runner = XVUnitRunner()
        self.__set_paths()
        self.tb_list = self.__collect_testbenches()
    
    def list(self):
        for tb in self.tb_list:
            for tc in tb.get_test_cases():
                print(f'{tb.name}.{tc.name}')
                
    def run_testbench(self, testbench_name : str, tests_to_run : list):
        matched_testbench = self.match_testbench(testbench_name, tests_to_run)

        self.runner.run_test(matched_testbench.file_path, matched_testbench.get_test_cases().keys())
        self.process_test_results(matched_testbench)
                
    def process_test_results(self, testbench : Testbench):
        
        self.__create_tc_folders(testbench.name)
        self.__create_tc_log_files(testbench) 
        self.__fill_all_tests_results(testbench)
        
    def __fill_all_tests_results(self, testbench : Testbench):        
        for tc in testbench.get_test_cases():
            self.__fill_test_results(tc)
            
            
    def __fill_test_results(self, tc : TestCase):
        print(tc)
        sys.exit()
        # tc.passed = not ('ERROR' in tc.log_file)
        
    def match_testbench(self, testbench_name : str, tc_to_run : list) -> Testbench:        
        for tb in self.tb_list:
            if tb.name == testbench_name:
                matched_tb = tb
        
        tests_to_run_set = set(tc_to_run)
        matched_test_cases = [
            tc_val for tc_key, tc_val in matched_tb.get_test_cases().items()
            if tc_key in tests_to_run_set
        ]
        
        matched_tb.set_test_cases(matched_test_cases)
        
        return matched_tb

        
        
    def __set_paths(self):
        this_script_dir = os.path.dirname(os.path.abspath(__file__))
        self.project_path = Path(this_script_dir).parent.resolve()
        self.sim_dir = os.path.join(self.project_path, "sim")
        self.build_dir = os.path.join(self.sim_dir, "build")
        self.build_dir = os.path.join(self.sim_dir, "build")
        self.xsim_log = os.path.join(self.build_dir, "xsim.log")
        
    def __create_tc_folders(self, testbench_name):
        """Create folders for each test case found in vunit_results file."""
        test_cases = []
        
        try:
            with open(self.xsim_log, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('test_start:'):
                        test_name = line.split('test_start:')[1].strip()
                        test_cases.append(test_name)
                    elif line == 'test_suite_done':
                        break  # Stop reading after test_suite_done
                        
        except FileNotFoundError:
            print(f"Warning: VUnit results file not found: {self.xsim_log}")
        
        # Create folders for each test case
        for test_name in test_cases:
            test_dir = os.path.join(self.build_dir, testbench_name, test_name)
            os.makedirs(test_dir, exist_ok=True)
        
    
    def __create_tc_log_files(self, testbench : Testbench):
        """Create <tc_name>.log files - everything after test_start: goes to that log until next test_start:"""
        
        if not os.path.exists(self.xsim_log):
            print("Warning: Required files not found")
            return {}
        
        with open(self.xsim_log, 'r') as f:
            full_log = f.read()
        
        test_logs = {}
        test_cases = testbench.get_test_cases()
        current_test = None
        current_log = []
        
        lines = full_log.split('\n')
        
        for line in lines:
            if line.strip().startswith('test_start:'):
                # Save previous test log
                if current_test and current_log:
                    test_logs[current_test] = '\n'.join(current_log)
                
                test_name = line.split('test_start:')[1].strip()
                current_test = test_name
                current_log = [f"// Test: {test_name}"]
                
            elif line.strip() == 'test_suite_done':
                if current_test and current_log:
                    test_logs[current_test] = '\n'.join(current_log)
                break
                
            elif current_test:
                current_log.append(line)
        
        # Create log files
        for test_name, log_content in test_logs.items():
            test_dir = os.path.join(self.build_dir, testbench.name, test_name)
            os.makedirs(test_dir, exist_ok=True)
            
            log_file_path = os.path.join(test_dir, f"{test_name}.log")
            with open(log_file_path, 'w') as f:
                f.write(log_content)
                    
        return test_logs
        
    def __collect_testbenches(self) -> List[Testbench]:
        """List all testbenches in the sim directory with ."""
        tests = []
        
        for name in os.listdir(self.sim_dir):
            test_dir = os.path.join(self.sim_dir, name)
                
            for file in os.listdir(test_dir):
                if file.endswith(('.sv', '.v')):
                    file_path = os.path.join(test_dir, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Check if it uses XVUnit framework
                            if ('`TEST_CASE' in content and 
                                'xvunit_defines.svh' in content):
                                tests.append(Testbench(name, file_path))
                                break
                                
                    except (UnicodeDecodeError, IOError):
                        continue
                        
        return tests
        
        

xvunit = XVunit()
xvunit.run_testbench('xvunit_test', ["TC0003", "TC001"])