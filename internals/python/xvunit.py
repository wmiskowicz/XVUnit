import threading
import time
import os, sys
import colorama
from typing import List
from typing import Dict, Optional

sys.path.append(os.path.dirname(__file__))

from paths import *
from test_bench import Testbench, TestCase
from xvunit_runner import XVUnitRunner
from parser import Parser


class XVunit:
  
    def __init__(self):
    
        colorama.init(autoreset=True)
        
        self.parser = Parser()
        self.runner = XVUnitRunner()
        
        self._stop_refresh_thread = threading.Event()
        self.refresh_thread = None
        
        self.current_testbench_name = None
        self.all_tb_dict = self.parser.get_xvunit_testbenches_dict()
        self.line_ind = 0
        
        
    def run_testbench(self, testbench_name: str, tests_to_run: List[str]):
        self.parser.set_current_testbench_name(testbench_name)
        matched_testbench = self.match_testbench(testbench_name, tests_to_run)
        print(matched_testbench.file_path)
        
        self._stop_refresh_thread.clear()
        self.refresh_thread = threading.Thread(target=self._refresh_worker)
        self.refresh_thread.start()
        
        try:
            self.runner.run_test(matched_testbench.file_path, matched_testbench.get_selected_test_cases_names())
        finally:
            self._stop_refresh_thread.set()
            if self.refresh_thread:
                self.refresh_thread.join()
        
    def _refresh_worker(self):
        while not self._stop_refresh_thread.is_set():
            if self.runner.is_simulation_running() and not self.parser.is_parsing_done():
                time.sleep(2) # wait for log to clear
                self.parser.check_log()
            time.sleep(0.5)
        
        
        
        
    def match_testbench(self, testbench_name : str, tc_to_run : list) -> Testbench: 
               
        for tb_name, tb_class in self.all_tb_dict.items():
            if tb_name == testbench_name:
                matched_tb = tb_class
        
        tests_to_run_set = set(tc_to_run)
        matched_test_cases = [
            tc_key for tc_key in matched_tb.get_test_cases_dict().keys()
            if tc_key in tests_to_run_set
        ]
        
        matched_tb.select_test_cases_to_run(matched_test_cases)
        return matched_tb
        
    def list(self):
        for tb_name, tb_class in self.all_tb_dict.items():
            for tc_name in tb_class.get_test_cases_dict().keys():
                print(f'{tb_name}.{tc_name}')
    

# For testing purposes
xvunit = XVunit()
xvunit.run_testbench('xvunit_test', ["TC001"])
# xvunit.run_testbench('new_test', ["TC005"])