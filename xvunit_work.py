# xvunit_runner.py
import os
import subprocess
from pathlib import Path


# -------------------------------------------------------------------------
# Search locations
# -------------------------------------------------------------------------
THIS_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR     = Path(THIS_SCRIPT_DIR).parent.resolve()
FPGA_DIR        = os.path.join(PROJECT_DIR, "fpga")

VIVADO_DIR=r"C:\Xilinx\Vivado\2023.1\bin"
VIVADO_SETUP=r"C:\Xilinx\Vivado\2023.1\settings64.bat"

FPGA_CONSTRAINTS_DIR = os.path.join(FPGA_DIR, "constraints")
FPGA_RTL_DIR         = os.path.join(FPGA_DIR, "rtl")
TOP_RTL_DIR          = os.path.join(PROJECT_DIR, "rtl")

MEM_INIT_DIR         = os.path.join(PROJECT_DIR, "rtl")

OUTPUT_TCL = os.path.join(FPGA_DIR, "scripts", "project_details.tcl")



# xvunit_runner.py
import os
import subprocess
from pathlib import Path

class XVUnitRunner:
    def __init__(self, project_dir, vivado_setup):
        self.project_dir = project_dir
        self.vivado_setup = vivado_setup
        self.sim_dir = os.path.join(project_dir, "sim")
        self.build_dir = os.path.join(self.sim_dir, "build")
        self.setup_cmd = f'call "{vivado_setup}" && '
    
    def generate_runner_cfg(self, test_names):
        """
        Generate the runner configuration string that matches what your SV code expects.
        & is used as a denominator between test case names and output path
        """
        enabled_tests = ",".join(test_names) if test_names else "__all__"
        output_path = f"{self.build_dir}/".replace('\\', '//')
        
        # This format MUST match what your SV parser expects
        return f"enabled_test_cases:{enabled_tests},&output_path:{output_path}"
    
    def run_test(self, testbench_file, test_names=None):
        """Run a single testbench with the XVUnit framework"""
        
        if not os.path.exists(self.build_dir):
            os.makedirs(self.build_dir, exist_ok=True)
        
        # Clean previous builds
        subprocess.run(["git", "clean", "-fXd", "."], cwd=self.sim_dir)
        
        # Generate runner configuration
        runner_cfg = self.generate_runner_cfg(test_names)
        print(f"Runner config: {runner_cfg}")
        
        # Get the module name from the testbench file
        module_name = Path(testbench_file).stem
        
        # COMPILE: Use normal compilation without generic
        prj_path = r"C:\Users\wojte\Documents\Saper_new\sim\xvunit_test\xvunit_test.prj"
        compile_cmd = (
            f'{self.setup_cmd} xvlog --incr --relax --sv '
            f'-i {os.path.join(self.project_dir, "XVunit/internals/verilog")} '
            f'-prj {prj_path} '
            f'-L uvm -L unisims_ver'
        )
        
        # ELABORATE: No changes here
        elaborate_cmd = (
            f'{self.setup_cmd} xelab --incr --relax --debug typical '
            f'work.{module_name} '
            f'-L uvm -L unisims_ver'
        )
        
        # RUN: Pass runner_cfg as plusarg
        run_cmd = (
            f'{self.setup_cmd} xsim work.{module_name} '
            f'-testplusarg "runner_cfg={runner_cfg}" --runall'
        )
        if not Path.is_dir(Path(self.build_dir)):
            os.makedirs(self.build_dir, exist_ok=True)
        
        print("Compiling...")
        # print(compile_cmd)
        print(self.build_dir, Path.is_dir(Path(self.build_dir)))
        
        # os._exit(1)
        result = subprocess.run(compile_cmd, shell=True, cwd=self.build_dir, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Compilation failed: {result.stderr}")
            print(f"STDOUT: {result.stdout}")
            return False
        
        print("Elaborating...")
        result = subprocess.run(elaborate_cmd, shell=True, cwd=self.build_dir, capture_output=True, text=True)
        # result = subprocess.run(elaborate_cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Elaboration failed: {result.stdout}")
            return False
        
        print("Running simulation...")
        print(run_cmd)
        # os._exit(0)
        # result = subprocess.run(run_cmd, shell=True, capture_output=True, text=True)

        result = subprocess.run(run_cmd, shell=True, cwd=self.build_dir, capture_output=True, text=True)
        print(result.stdout)
        
        # Check results
        log_file = os.path.join(self.build_dir, "xsim.log")
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_content = f.read()
                print("Simulation output:")
                print(log_content)
        
        return result.returncode == 0
    
    def find_project_file(self, testbench_file):
        """Find or generate the project file for the testbench"""
        testbench_dir = os.path.dirname(testbench_file)
        testbench_name = Path(testbench_file).stem
        project_file = os.path.join(testbench_dir, f"{testbench_name}.prj")
        
        if os.path.exists(project_file):
            return project_file
        # else:
            # return self.generate_minimal_project_file(testbench_file)


# Simple test
from pathlib import Path
if __name__ == "__main__":
    
    runner = XVUnitRunner(PROJECT_DIR, VIVADO_SETUP)
    
    # Point to your testbench file
    testbench_path = os.path.join(PROJECT_DIR, "sim", "xvunit_test", "xvunit_test_tb.sv")
    print(f"path = {testbench_path}")
    
    success = runner.run_test(testbench_path, test_names=["TC000","TC001"])
    print(f"Test {'PASSED' if success else 'FAILED'}")
    
    
    
#     # Command-line interface (preserving your original argument structure)
# def main():
#     parser = argparse.ArgumentParser(description="Run Vivado simulations outside Vivado for faster execution.")
#     parser.add_argument("-l", action="store_true", help="List available tests")
#     parser.add_argument("-t", type=str, help="Run the specified test")
#     parser.add_argument("-g", action="store_true", help="Show GUI (use with -t)")
#     parser.add_argument("-a", action="store_true", help="Run all available tests")
#     parser.add_argument("-prj", action="store_true", help="Update .prj file of run test. (use with -t)")
    
#     args = parser.parse_args()
    
#     # Create runner instance
#     runner = VivadoTestRunner(PROJECT_DIR, VIVADO_SETUP)
    
#     if args.l:
#         runner.list_available_tests()
#     elif args.a:
#         results = runner.run_all_tests(show_gui=False, update_prj=args.prj)
#         runner.print_summary(results)
#     elif args.t:
#         test_case = TestCase(args.t, runner.sim_dir)
#         if test_case.exists():
#             runner.execute_test(test_case, show_gui=args.g, update_prj=args.prj)
#         else:
#             print(f"Test not found: {args.t}")
#             sys.exit(1)
#     else:
#         parser.print_help()
#         sys.exit(1)

# if __name__ == "__main__":
#     main()