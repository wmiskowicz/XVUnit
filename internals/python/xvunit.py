import threading
import time
import os, sys
import colorama
import fnmatch
from typing import List
from typing import Dict, Optional

sys.path.append(os.path.dirname(__file__))

from paths import *
from test_bench import Testbench, TestCase
from xvunit_runner import XVUnitRunner
from parser import Parser
from file_manager import FileManager


class XVunit:
  
    def __init__(self):
    
        colorama.init(autoreset=True)
        
        self.parser = Parser()
        self.fm = FileManager()
        self.runner = XVUnitRunner()
        
        self._stop_refresh_thread = threading.Event()
        self.refresh_thread = None
        
        self.current_testbench_name = None
        self.all_tb_dict = self.parser.get_xvunit_testbenches_dict()        
        self.line_ind = 0
        
        
    def run_testbench(self, testbench: Testbench, tests_to_run: List[str], run_all : bool = False):
        self.parser.set_current_testbench_name(testbench.name)
        testbench.select_test_cases_to_run(tests_to_run)
        self.create_prj(testbench)
        
        self._stop_refresh_thread.clear()
        self.refresh_thread = threading.Thread(target=self._refresh_worker)
        self.refresh_thread.start()
        
        try:
            self.runner.run_test(testbench.file_path, testbench.get_selected_test_cases_names(), run_all)
        finally:
            self._stop_refresh_thread.set()
            if self.refresh_thread:
                self.refresh_thread.join()
        
    
    def create_prj(self, testbench : Testbench):
        
        search_dirs = [
            os.path.join(PROJECT_DIR, 'rtl'),
            os.path.join(PROJECT_DIR, 'XVUnit', 'internals', 'verilog'),
            os.path.join(SIM_DIR, testbench.name),
            os.path.join(SIM_DIR, 'common'),
        ]
        
        source_files = self.fm.collect_hdl_files(search_dirs)
        
        
        self.fm.create_prj(testbench.prj_path, source_files)
        
        

    def match_and_run(self, test_input: list):
        found_any_testbench = False
        test_parts = test_input.split('.')
        
        if len(test_parts) == 1:
            for tb_name, tb_class in self.all_tb_dict.items():
                if fnmatch.fnmatch(tb_name, test_parts[0]):
                    self.run_testbench(tb_class, [], run_all=True)
                    found_any_testbench = True
                    
            if not found_any_testbench:   
                print(colorama.Fore.YELLOW + f"No testbench match found!")
                sys.exit()
              
        elif len(test_parts) == 2:
            for tb_name, tb_class in self.all_tb_dict.items():
                if fnmatch.fnmatch(tb_name, test_parts[0]):
                    found_any_testbench = True
                    
                    matched_test_cases = [
                        tc_key for tc_key in tb_class.get_test_cases_dict().keys()
                        if fnmatch.fnmatch(tc_key, test_parts[1])
                    ]
                    self.run_testbench(tb_class, matched_test_cases)
                    
            if not found_any_testbench:   
                print(colorama.Fore.YELLOW + f"No testbench match found!")
                sys.exit()
        else:
            # Defensive coding - should never happen
            print(colorama.Fore.YELLOW + f"No test found")
            sys.exit()
        
    
    def _refresh_worker(self):
        while not self._stop_refresh_thread.is_set():
            if self.runner.is_simulation_running() and not self.parser.is_parsing_done():
                time.sleep(2) # wait for log to clear
                self.parser.check_log()
            time.sleep(0.5)
        
        
        
        
    def match_testbench(self, testbench_name : str, tc_to_run : list) -> Testbench: 
               
        for tb_name, tb_class in self.all_tb_dict.items():
            if fnmatch.fnmatch(tb_name, testbench_name):
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
    
