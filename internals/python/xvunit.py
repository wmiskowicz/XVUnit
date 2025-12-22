import threading
import time
import os, sys
import colorama
import fnmatch
from typing import List

sys.path.append(os.path.dirname(__file__))

from paths import *
from test_bench import Testbench
from xvunit_runner import XVUnitRunner
from parser import Parser
from file_manager import FileManager
from logger import Logger


class XVunit:
  
    def __init__(self):
    
        colorama.init(autoreset=True)
        
        self.parser = Parser()
        self.fm = FileManager()
        self.runner = XVUnitRunner()
        self.logger = Logger()
        self.verbose = False
        
        self._stop_refresh_thread = threading.Event()
        self.refresh_thread = None
        
        self.all_tb_dict = {}       
        self.source_file_paths = [] 
        self.line_ind = 0
        
        
    def run_testbench(self, testbench: Testbench, tests_to_run: List[str], run_all : bool = False, enable_gui=False):
        self.parser.set_current_parser_testbench(testbench)
        testbench.select_test_cases_to_run(tests_to_run)
        
        
        self._stop_refresh_thread.clear()
        self.refresh_thread = threading.Thread(target=self._refresh_worker)
        self.refresh_thread.start()
        
        try:
            self.runner.run_test(testbench.file_path, testbench.get_selected_test_cases_names(), run_all=run_all, enable_gui=enable_gui)
        finally:
            self._stop_refresh_thread.set()
            if self.refresh_thread:
                self.refresh_thread.join()
                
    def set_parameters(self, sources : dict):
        self.source_file_paths = self.parser._match_sources(sources)
        self.runner.source_file_paths = self.source_file_paths
        self.all_tb_dict = self.parser.create_testbench_dict(self.source_file_paths)
        
    def run(self, argv):

        found_any_testbench = False
        if len(argv) < 2:
            for tb_name, tb_class in  self.all_tb_dict.items():
                tb_class.tb_selected = True
                self.run_testbench(tb_class, [], run_all=True, enable_gui=False)
                found_any_testbench = True
            sys.exit()
        test_parts = argv[1].split('.')
        enable_gui = ('-g' in argv)
        self.verbose = ('-v' in argv)
        self.runner.verbose = self.verbose
        
        if '-h' in argv:
            print("-h - Print help")
            print("-v - Verbose output")
            print("-l - List available tests")
            print("-g - Run with gui")
            sys.exit()
        if '-l' in argv:
            self.list()
            sys.exit()
        
        
        if len(test_parts) == 1:
            for tb_name, tb_class in self.all_tb_dict.items():                
                if fnmatch.fnmatch(tb_name, test_parts[0]):
                    tb_class.tb_selected = True
                    self.run_testbench(tb_class, [], run_all=True, enable_gui=enable_gui)
                    found_any_testbench = True
                    self.logger.print_summary(self.all_tb_dict)
                else:
                    for tc_key in tb_class.get_test_cases_dict().keys():
                        if fnmatch.fnmatch(tc_key, test_parts[0]):
                            found_any_testbench = True
                            self.run_testbench(tb_class, [tc_key], run_all=True, enable_gui=enable_gui)
                            tb_class.tb_selected
                    
            if not found_any_testbench:   
                print(colorama.Fore.YELLOW + f"No testbench match found!")
                sys.exit()
              
        elif len(test_parts) == 2:
            for tb_name, tb_class in self.all_tb_dict.items():
                if fnmatch.fnmatch(tb_name, test_parts[0]):
                    found_any_testbench = True
                    tb_class.tb_selected = True
                    
                    matched_test_cases = [
                        tc_key for tc_key in tb_class.get_test_cases_dict().keys()
                        if fnmatch.fnmatch(tc_key, test_parts[1])
                    ]
                    self.run_testbench(tb_class, matched_test_cases, enable_gui=enable_gui)
                    
            if not found_any_testbench:   
                print(colorama.Fore.YELLOW + f"No testbench match found!")
                sys.exit()
        else:
            print(colorama.Fore.YELLOW + f"No test found")
            sys.exit()
  
    
    def _refresh_worker(self):
        first_iteration = True
        line_ind = 0
        while not self._stop_refresh_thread.is_set():
            if self.runner.is_simulation_running() and not self.parser.is_parsing_done():
                if first_iteration:
                    time.sleep(2) # wait for log to be created
                    first_iteration = False
                    
                line_ind = self.parser.check_log(line_ind)
                
            time.sleep(0.5)
            
        
    def list(self):
        for tb_name, tb_class in self.all_tb_dict.items():
            for tc_name in tb_class.get_test_cases_dict().keys():
                print(f'{tb_name}.{tc_name}')
    
