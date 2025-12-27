import glob
import re
import colorama
from typing import List
from typing import Dict, Optional

import os
from pathlib import Path

from XVunit.internals.python.logger import Logger
from paths import *
from test_bench import Testbench, TestCase


class Parser:
  
    def __init__(self):
                
        colorama.init(autoreset=True)
        self.logger = Logger()
        self.current_testbench = None
        self.finished_parsing = False
        self.testbench_build_dir = None
        self.current_log = None
        self.current_test = None
        
        self.previous_line = None
        self.print_stdout = False
        self.failed_printed = False
    
    def set_current_parser_testbench(self, testbench : Testbench):
        self.current_testbench = testbench
        self.testbench_build_dir = os.path.join(BUILD_DIR, testbench.name)
        self.finished_parsing = False
         
    def check_log(self, last_file_position: int = 0) -> int:
        """Monitor log file for changes and create/update <tc_name>.log files in real-time.
        
        Args:
            last_file_position: Last read position in the file for incremental reading
            
        Returns:
            The new file position for next call (returns last_file_position on error)
        """
        xsim_log = os.path.join(BUILD_DIR, self.current_testbench.name, "xsim.log")
        if not os.path.exists(xsim_log):
            print(f"Warning: {xsim_log} not found")
            return last_file_position
        
        
        try:
            with open(xsim_log, 'r') as f:
                # Seek to the last read position
                f.seek(last_file_position)
                
                # Read only new content
                new_content = f.read()
                new_file_position = f.tell()
                
            # If no new content, return original position
            if not new_content:
                return last_file_position
                
            lines = new_content.split('\n')
            
            for line in lines:
                line = line.strip()
                
                if line.startswith('test_start:'):
                    # Save previous test log before starting new one
                    if self.current_test and self.current_log:
                        self._write_test_log(self.current_test, '\n'.join(self.current_log))
                    
                    # Start new test section
                    test_name = line.split('test_start:')[1].strip()
                    self.current_test = test_name
                    self.current_log = [f"// Test: {test_name}"]
                    print(f"\nRunning test: {self.current_testbench.name}.{test_name}")
                    
                elif line == 'test_suite_done':
                    # Finalize current test and break
                    
                    self._write_test_log(self.current_test, '\n'.join(self.current_log))
                    self.finished_parsing = True
                    
                    break
                    
                elif self.current_test:
                    if line:
                        self.current_log.append(line)
                        
            return new_file_position if 'new_file_position' in locals() else last_file_position
                
        except Exception as e:
            print(f"Error reading log file: {e}")
            return last_file_position 
        
    
    def is_parsing_done(self) -> bool:
        return self.finished_parsing

    def _write_test_log(self, test_name: str, log_content: str):
        """Write individual test log to file"""
        
        test_dir = os.path.join(self.testbench_build_dir, self.current_testbench.name, test_name)
        os.makedirs(test_dir, exist_ok=True)
        
        log_file_path = os.path.join(test_dir, f"{test_name}.log")
        self.current_testbench.test_cases_dict[test_name].ready = True
        
        try:
            print(f'Test output file: {log_file_path}')
            
            with open(log_file_path, 'w') as f:
                if 'ERROR' in log_content.upper():
                    self.current_testbench.test_cases_dict[test_name].passed = False
                    print(f"{test_name} {colorama.Fore.RED}failed")
                else:
                    self.current_testbench.test_cases_dict[test_name].passed = True
                    print(f"{test_name} {colorama.Fore.GREEN}passed")
                f.write(log_content)
            
            self.__print_error_message(log_file_path)
                    
        except Exception as e:
            print(f"Error writing log file for {test_name}: {e}")
            
            
    def __print_error_message(self, log_file_path):
        with open(log_file_path, 'r') as f:
            lines = f.readlines()
            error_lines = []
            file = None
            for index, line in enumerate(lines):
                if 'ERROR' in line.upper():
                    file = lines[index+1].split("File:")[1]
                    error_string = f'{line.strip()}, \nFile: {file}'
                    error_lines.append(error_string)
            
            if file:      
                print(error_lines[0])
                file_path, line_ind = file.split('Line: ')
                self.__print_code_around_failed_line(file_path.strip(), int(line_ind)-1)
            

    def __print_code_around_failed_line(self, file_path, line_ind):
        span = 4
                
        with open(file_path, 'r') as f:
            lines = f.readlines()
            # print(lines)
            for index in range(-span, span):
                if index == 0:
                    prefix = '->'
                else:
                    prefix = ' '
                print(prefix, lines[line_ind+index], end='')
                
    
    def create_testbench_dict(self, source_file_paths : list) -> Dict[str, Testbench]:
        testbench_dict = {}
        
        for file_path in source_file_paths:
            name = os.path.basename(file_path.split('.')[0]) 
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Check if testbench uses XVUnit framework
                    if ('`TEST_CASE' in content and 
                        'xvunit_defines.svh' in content):

                        testbench = Testbench(name, file_path)
                        
                        if name in testbench_dict:
                            raise Exception(f'Found testbench duplicates: {name}')
                        else:
                            testbench_dict[name] = testbench
                        
            except (UnicodeDecodeError, IOError):
                continue
                        
        return testbench_dict
    
    def _match_sources(self, source_patterns_dict : dict):
        """
        List files using fnmatch with os.walk for more control.
        """
        source_file_list = []
    
        for category, patterns in source_patterns_dict.items():
            for pattern in patterns:
                if '*' in pattern:
                    matched_files = glob.glob(pattern, recursive=True)
                    matched_files.sort()
                    source_file_list.extend(matched_files)
                else:
                    if os.path.exists(pattern):
                        source_file_list.append(pattern)
        
        return source_file_list
        
    def parse_line(self, line : str):
        
        # Initial case
        if 'ECHO is off' in line and self.previous_line is None:
            self.previous_line = line
        # Regular case
        if line.startswith('INFO: [VRFC 10-2263]'):
            if self.previous_line.startswith('INFO: [VRFC 10-2263]') or self.previous_line.startswith('INFO: [VRFC 10-311]'):
                print(f'{colorama.Fore.GREEN} [pass]')
            else:
                print('')
                
            match = re.search(r'"([^"]+)"', line)
            path = match.group(1)
            print(f"Compiling {path}", end='')
            self.previous_line = line
            
        elif line.startswith('ERROR:') and not self.failed_printed:
            print(f'{colorama.Fore.RED} [fail]')
            self.failed_printed = True
            
        else:
            self.previous_line = line
            
            
    def reset_parser(self):
        self.finished_parsing = False
        self.current_log = None
        self.current_test = None
        self.previous_line = None
        self.print_stdout = False
        self.failed_printed = False
                    

        
