import threading
import time
import colorama
from typing import List
from typing import Dict, Optional

import os
from pathlib import Path
from paths import *
from test_bench import Testbench, TestCase
from xvunit_runner import XVUnitRunner


class ThreadXVunit:
    def __init__(self):
        self.runner = XVUnitRunner()
        colorama.init(autoreset=True)
        self.__set_paths()
        self.tb_list = self.__collect_testbenches()
        self._stop_refresh = threading.Event()
        self.refresh_thread = None
        self.current_testbench_name = None
        self.line_ind = 0
    
    def run_testbench(self, testbench_name: str, tests_to_run: List[str]):
        self.current_testbench_name = testbench_name
        matched_testbench = self.match_testbench(testbench_name, tests_to_run)
        
        # Start refresh in a separate thread
        self._stop_refresh.clear()
        self.refresh_thread = threading.Thread(target=self._refresh_worker)
        self.refresh_thread.start()
        
        try:
            # Run the test in the main thread
            self.runner.run_test(matched_testbench.file_path, matched_testbench.get_test_cases().keys())
        finally:
            # Stop the refresh thread when test completes
            self._stop_refresh.set()
            if self.refresh_thread:
                self.refresh_thread.join()
    
    def _refresh_worker(self):
        """Worker function that runs refresh until stopped"""
        while not self._stop_refresh.is_set():
            self.refresh()
    
    def refresh(self):
        self.check_log(self.line_ind)
        time.sleep(1)

    def check_log(self, last_file_position: int = 0) -> Dict[str, str]:
        """Monitor log file for changes and create/update <tc_name>.log files in real-time.
        
        Args:
            last_file_position: Last read position in the file for incremental reading
            
        Returns:
            Dictionary with test names as keys and log contents as values
            Also returns the new file position for next call
        """
        
        if not os.path.exists(self.xsim_log):
            print(f"Warning: path:{self.xsim_log} ]'not found")
            return 
        
        current_test: Optional[str] = None
        current_log = []
        
        try:
            with open(self.xsim_log, 'r') as f:
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
                    print("Test suite completed")
                    break
                    
                elif current_test:
                    if line:
                        current_log.append(line)
                
        except Exception as e:
            print(f"Error reading log file: {e}")
        

    def _write_test_log(self, test_name: str, log_content: str):
        """Write individual test log to file"""
        test_dir = os.path.join(self.build_dir, self.current_testbench_name, test_name)
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
        
    def stop_all(self):
        """Method to stop refresh thread if needed"""
        self._stop_refresh.set()
        if self.refresh_thread and self.refresh_thread.is_alive():
            self.refresh_thread.join()
            
        

        
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

    def list(self):
        for tb in self.tb_list:
            for tc in tb.get_test_cases():
                print(f'{tb.name}.{tc.name}')
        
    def __set_paths(self):
        self.project_path = PROJECT_DIR
        self.sim_dir = SIM_DIR
        self.build_dir = BUILD_DIR
        self.xsim_log = os.path.join(self.build_dir, "xsim.log")

        
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


xvunit = ThreadXVunit()
xvunit.run_testbench('xvunit_test', ["TC003", "TC001"])