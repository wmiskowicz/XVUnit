
import sys
import os

sys.path.append(os.path.dirname(__file__))

from xvunit import XVunit


class run_XVUnitCommon:

    def __init__(self):
        self.xvunit = XVunit()
    
    
    def set_parameters(
        self,
        sources,
        compile_flags = None,
        wcfg_file = None,
        test_configs = None
    ) -> None:
    
        self.xvunit.set_parameters(sources)
        
        
    def run(self, argv):
        self.xvunit.run(argv)
            
            
    def list(self):
        self.xvunit.list()
                