import os
import re
import sys
from dataclasses import dataclass
from typing import Optional

@dataclass
class TestCase:
    name: str
    passed: bool
    simulation_time: float
    log_file: str
    error_msg: Optional[str] = None
    
    
    
class Testbench:
    def __init__(self, name: str, file_path):
        self.name = name
        self.file_path = file_path
        self.test_cases = []
        self.shared_config = {}
        
    
    def get_test_cases(self) -> list[TestCase]:
        """Extract all test case names from TEST_CASE macros in a testbench."""
        test_cases = []
        
        if self.file_path.endswith(('.sv', '.v')):
            
            try:
                with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                    pattern = r'`TEST_CASE\s*\(\s*"([^"]+)"\s*\)'
                    matches = re.findall(pattern, content)
                    
                    for test_name in matches:
                        test_cases.append(TestCase(test_name))

            except (UnicodeDecodeError, IOError) as e:
                print(f"Warning: Could not read {self.file_path}: {e}")
                    
        return test_cases  
    