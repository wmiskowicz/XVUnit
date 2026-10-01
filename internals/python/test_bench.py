import os
import re
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Dict, List

from path_settings import BUILD_DIR

@dataclass
class TestCase:
    name: str
    selected_to_run : bool = False
    passed: bool = False
    ready: bool = False
    simulation_time: float = 0
    log_path: str = ''
    error_msg: Optional[str] = None
    
    
    
class Testbench:
    def __init__(self, name: str, file_path : str):
        self.name = name
        self.file_path = file_path
        self.tb_selected = False
        self.prj_path = self.__get_prj_path(file_path)
        self.test_cases_dict = self.get_test_cases_dict()
        
    
    def get_test_cases_dict(self) -> Dict[str, TestCase]:
        """Extract all test case names from TEST_CASE macros in a testbench."""
        test_cases = {}
        
        if self.file_path.endswith(('.sv', '.v')):
            
            try:
                with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    pattern = r'`TEST_CASE\s*\(\s*"([^"]+)"\s*\)'
                    matches = re.findall(pattern, content)
                    
                    for test_name in matches:
                        
                        if test_name in test_cases:
                            raise Exception(f'Found testbench duplicates in {self.name}: {test_name}')
                        else:
                            tc_log_path = os.path.join(BUILD_DIR, self.name, test_name, f"{test_name}.log")
                            test_cases[test_name] = TestCase(test_name, log_path=tc_log_path)


            except (UnicodeDecodeError, IOError) as e:
                print(f"Warning: Could not read {self.file_path}: {e}")
                    
        return test_cases  
    
    
    def select_test_cases_to_run(self, test_case_name_list : List[str]):
        
        for test_name in test_case_name_list:
            if test_name in self.test_cases_dict:
                self.test_cases_dict[test_name].selected_to_run = True
                
    def get_selected_test_cases_names(self) -> list:
        selected_tc = []
        
        for tc_name, tc_class in self.test_cases_dict.items():
            if tc_class.selected_to_run:
                selected_tc.append(tc_name)
        
        return selected_tc
    
    def __get_prj_path(self, testbench_path):
        testbench_path = Path(testbench_path)
        tb_dir = testbench_path.parent
        test_name = testbench_path.stem[:-3]
        
        prj_path = os.path.join(tb_dir, f'{test_name}.prj')
        return prj_path
        