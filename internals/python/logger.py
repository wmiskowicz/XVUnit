import colorama
from typing import List, Dict

from test_bench import Testbench



class Logger:
    def __init__(self):
        pass

    def print_summary(self, all_tb_dict : Dict[str, Testbench]):
        print(f'\n\n ----- SUMMARY -----')
        all_passed = True
        
        for tb_name, tb_class in all_tb_dict.items():
            if tb_class.tb_selected:
                for tc_name, tc_class in tb_class.test_cases_dict.items(): 
                    
                    print(f'{tb_name}.{tc_name} -', end='')
                    if tc_class.ready:
                        if tc_class.passed:
                            print(f'{colorama.Fore.GREEN} passed')
                        else:
                            all_passed = False
                            print(f'{colorama.Fore.RED} failed')
        
        if all_passed:
            print(f'\n{colorama.Fore.GREEN} All passed')