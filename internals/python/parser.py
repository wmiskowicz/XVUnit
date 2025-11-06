import threading
import time
import colorama
from typing import List
from typing import Dict, Optional

import os
from pathlib import Path
from paths import *
from test_bench import Testbench, TestCase


class Parser:
  
    def __init__(self):
                
        colorama.init(autoreset=True)
        self.current_testbench_name = None
        self.finished_parsing = False
        self.testbench_build_dir = None
    
    def set_current_testbench_name(self, testbench_name : str):
        self.current_testbench_name = testbench_name
        self.testbench_build_dir = os.path.join(BUILD_DIR, testbench_name)
        self.finished_parsing = False

    def check_log(self, last_file_position: int = 0) -> Dict[str, str]:
        """Monitor log file for changes and create/update <tc_name>.log files in real-time.
        
        Args:
            last_file_position: Last read position in the file for incremental reading
            
        Returns:
            Dictionary with test names as keys and log contents as values
            Also returns the new file position for next call
        """
        xsim_log = os.path.join(BUILD_DIR, self.current_testbench_name, "xsim.log")
        if not os.path.exists(xsim_log):
            print(f"Warning: path:{xsim_log} ]'not found")
            return 
        
        current_test: Optional[str] = None
        current_log = []
        
        try:
            with open(xsim_log, 'r') as f:
                # Seek to the last read position
                f.seek(last_file_position)
                
                # Read only new content
                new_content = f.read()
                new_file_position = f.tell()
                
            # If no new content, return current state
            if not new_content:
                return 
                
            lines = new_content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('test_start:'):
                    # Save previous test log before starting new one
                    if current_test and current_log:
                        self._write_test_log(current_test, '\n'.join(current_log))
                    
                    # Start new test section
                    test_name = line.split('test_start:')[1].strip()
                    current_test = test_name
                    current_log = [f"// Test: {test_name}"]
                    print(f"Started monitoring test: {test_name}")
                    
                elif line == 'test_suite_done':
                    # Finalize current test and break
                    if current_test and current_log:
                        self._write_test_log(current_test, '\n'.join(current_log))
                    self.finished_parsing = True
                    print("Test suite completed")
                    
                    break
                    
                elif current_test:
                    if line:
                        current_log.append(line)
                
        except Exception as e:
            print(f"Error reading log file: {e}")
        
    
    def is_parsing_done(self) -> bool:
        return self.finished_parsing

    def _write_test_log(self, test_name: str, log_content: str):
        """Write individual test log to file"""
        test_dir = os.path.join(self.testbench_build_dir, self.current_testbench_name, test_name)
        os.makedirs(test_dir, exist_ok=True)
        
        log_file_path = os.path.join(test_dir, f"{test_name}.log")
        try:
            with open(log_file_path, 'w') as f:
                if 'ERROR' in log_content.upper():
                    print(f"{test_name} {colorama.Fore.RED}failed")
                else:
                    print(f"{test_name} {colorama.Fore.GREEN}passed")
                f.write(log_content)
        except Exception as e:
            print(f"Error writing log file for {test_name}: {e}")
    
    def get_xvunit_testbenches_dict(self) -> Dict[str, Testbench]:
        """List all testbenches in the sim directory with ."""
        testbench_dict = {}
        
        for name in os.listdir(SIM_DIR):
            test_dir = os.path.join(SIM_DIR, name)
                
            for file in os.listdir(test_dir):
                if file.endswith(('.sv', '.v')):
                    file_path = os.path.join(test_dir, file)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            
                            # Check if it uses XVUnit framework
                            if ('`TEST_CASE' in content and 
                                'xvunit_defines.svh' in content):
                                testbench = Testbench(name, file_path)
                                
                                if name in testbench_dict:
                                    raise Exception(f'Found testbench duplicates: {name}')
                                else:
                                    testbench_dict[name] = testbench
                                    break
                                
                    except (UnicodeDecodeError, IOError):
                        continue
                        
        return testbench_dict
    
    def parse_prj(self, prj_path) -> list:
        """Parse project file and return list of file paths."""
        file_paths = []
        
        try:
            with open(prj_path, 'r') as f:
                for line in f:
                    line = line.replace(' \\', "").strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith('#'):
                        continue
                    
                    if line.startswith('sv work '):
                        line = line.replace("sv work ", "").strip()
                    elif line.startswith('verilog work'):
                        line = line.replace("verilog work", "").strip()
                    elif line.startswith('vhdl work'):
                        line = line.replace("vhdl work", "").strip()
                                            
                    if os.path.exists(line):
                        file_paths.append(line)
                        
        
        except FileNotFoundError:
            print(f"Error: Project file not found: {prj_path}")
        except Exception as e:
            print(f"Error parsing project file: {e}")
                    
        return file_paths
    