import os, sys
import subprocess
import threading 
import time
import colorama
from pathlib import Path
from typing import Optional, Dict, List
import select
from queue import Queue, Empty

sys.path.append(os.path.dirname(__file__))
from paths import *
from parser import Parser
from file_manager import FileManager
from test_bench import Testbench

class XVUnitRunner:
    def __init__(self):
        self.parser = Parser()
        self.fm = FileManager()
        self.project_dir = PROJECT_DIR
        self.sim_dir    = SIM_DIR
        self.testbench_build_dir = None
        self.setup_cmd  = f'call "{VIVADO_SETUP}" && '
        
        self.sim_running = threading.Event()
        self.verbose = False
        self.source_file_paths = []
        colorama.init(autoreset=True)
        
        
    def is_simulation_running(self):
        """Check if simulation is currently running."""
        return self.sim_running.is_set()

    
    def run_test(self, testbench_file, test_names : list, run_all : bool = False, force_recompile : bool = False, enable_gui = False):
        """Run a single testbench with the XVUnit framework"""
        
        self.sim_running.clear()
        module_name = Path(testbench_file).stem
        prj_path = os.path.join(SIM_DIR, module_name[:-3], f'{module_name[:-3]}.prj')
        self.testbench_build_dir = os.path.join(BUILD_DIR, module_name)


        self.__makedir(BUILD_DIR)
        self.__makedir(self.testbench_build_dir)
        
        self.compile(force_recompile, prj_path, module_name)
        self.elaborate(force_recompile, module_name)
        self.simulate(module_name, test_names, run_all, enable_gui)

                    

    def compile(self, force_recompile : bool, prj_path : str, module_name : str):
        
        compile_vhdl = False
        for file_path in self.source_file_paths:
            if 'vhd' in file_path.lower():
                compile_vhdl = True
                break
            
        if force_recompile:
            self._create_prj(prj_path, self.source_file_paths)
            self._create_prj(prj_path, self.source_file_paths)
            self._clear_prj(prj_path)
        elif self._list_files_that_need_recompilation(self.source_file_paths) != []:
            self._create_prj(prj_path, self._list_files_that_need_recompilation(self.source_file_paths))
            self.__compile(prj_path, compile_vhdl)
            self._clear_prj(prj_path)
            
            
    def elaborate(self, force_recompile : bool, module_name : str):
        
        compile_glbl = False
        for file_path in self.source_file_paths:
            if 'glbl.v' in file_path.lower():
                compile_glbl = True
                break
            
        if force_recompile or self.__needs_reelaboration():
            self.__elaborate(module_name, compile_glbl)

            
            
    def simulate(self, module_name : str, test_names : list, run_all : bool, enable_gui : bool):
        if run_all:
            print("Running simulation...")
            self.__simulate(module_name, self.__generate_runner_cfg([]), enable_gui)
        elif test_names == [] and not run_all:
            print(f"{colorama.Fore.YELLOW}No tests were run!")
        else:
            print("Running simulation...")
            self.__simulate(module_name, self.__generate_runner_cfg(test_names), enable_gui)    
            
            
    def __compile(self, prj_path, compile_vhdl):
        
        if compile_vhdl:
            vhdl_compile_cmd = (
                f'{self.setup_cmd} xvhdl --incr --relax '
                f'-prj {prj_path} '
            )
            # Compile VHDL files
            self.__run_and_parse(vhdl_compile_cmd, self.testbench_build_dir, fail_message="VHDL Compilation failed", success_message="VHDL Compilation successful")
        
        verilog_compile_cmd = (
            f'{self.setup_cmd} xvlog --incr --relax --sv '
            f'-i {os.path.join(self.project_dir, "XVunit/internals/verilog")} '
            f'-prj {prj_path} '
            f'-L uvm -L unisims_ver'
        )
        # Compile Verilog/SystemVerilog files
        self.__run_and_parse(verilog_compile_cmd, self.testbench_build_dir, fail_message="Verilog Compilation failed", success_message="Verilog Compilation successful", is_compilation=True)
        
    def __elaborate(self, module_name : str, compile_glbl=False):
        
        compile_glbl_cmd = "work.glbl " if compile_glbl else ""

        
        elaborate_cmd = (
            f'{self.setup_cmd} xelab --incr --relax --debug typical '
            f'work.{module_name} '
            f'-snapshot {module_name} '
            f'-L uvm -L unisims_ver '
            f'{compile_glbl_cmd} '
        )
                
        self.__run_and_parse(elaborate_cmd, self.testbench_build_dir, fail_message="Elaboration failed", success_message="Elaboration successful")
        
        
    def __simulate(self, module_name : str, runner_cfg, enable_gui=False):
        if enable_gui:
            
            # Search for wave configuration file
            wcfg_file = self.fm.get_wcfg_file(module_name)
            temp_tcl_file = self.fm.create_temp_tcl(bool(wcfg_file))
                
            
            run_cmd = (
                f'{self.setup_cmd} xsim {module_name} '
                f'-testplusarg "runner_cfg={runner_cfg}" -gui '
                f'-t {temp_tcl_file} '
            )
           
            if wcfg_file:
                run_cmd += f' -view {wcfg_file}'
                
        else:
            run_cmd = (
                f'{self.setup_cmd} xsim {module_name} '
                f'-testplusarg "runner_cfg={runner_cfg}" --runall'
            )
        
        try:
            self.sim_running.set()
            self.__run_and_parse(run_cmd, self.testbench_build_dir, fail_message="Simulation failed", success_message="")
        finally:
            self.sim_running.clear()
            if enable_gui:
                os.unlink(temp_tcl_file)
    
    def _list_files_that_need_recompilation(self, source_files : List[str]) -> List[str]:
        files_to_recompile = []
        work_dir = os.path.join(self.testbench_build_dir, "xsim.dir", "work")
        work_rlx = os.path.join(self.testbench_build_dir, "xsim.dir", "word", "work.rlx")

        for source_file in source_files:
            if os.path.exists(source_file):
                sdb_file = os.path.splitext(os.path.basename(source_file))[0] + '.sdb'
                sdb_path = os.path.join(work_dir, sdb_file)

                if os.path.exists(sdb_path):
                    source_time = os.path.getmtime(source_file)
                    compile_time = os.path.getmtime(sdb_path)
                    if source_time > compile_time:
                        files_to_recompile.append(source_file)
                    
                else:
                    files_to_recompile.append(source_file)
            else:
                files_to_recompile.append(source_file)
                
                
        return files_to_recompile

    def __needs_reelaboration(self):
        """Check if re-elaboration is needed."""
        # Check if xelab.log exists (indicates elaboration happened)
        xelab_log = os.path.join(self.testbench_build_dir, "xelab.log")
        if not os.path.exists(xelab_log):
            return True
        
        # Get elaboration time from xelab.log
        elab_time = os.path.getmtime(xelab_log)
        
        # Check if compilation is newer than elaboration
        xvlog_log = os.path.join(self.testbench_build_dir, "xvlog.log")
        if os.path.exists(xvlog_log):
            compile_log_age = os.path.getmtime(xvlog_log)
            if compile_log_age > elab_time:
                return True
        
        return False
    
    
    def __generate_runner_cfg(self, test_names : list) -> str:
        """
        Generate the runner configuration string.
        & is used as a denominator between test case names and output path
        """
        enabled_tests = ",".join(test_names) if test_names else "__all__"
        output_path = f"{self.testbench_build_dir}/".replace('\\', '//')
        
        # This format MUST match what your SV parser expects
        return f"enabled_test_cases:{enabled_tests},&output_path:{output_path}"
    
    
    def __makedir(self, path):
        if not Path.is_dir(Path(path)):
            os.makedirs(path, exist_ok=True)
            
    def _create_prj(self, prj_path, source_file_paths : list):        
        self.fm.create_prj(prj_path, source_file_paths)
        
    def _clear_prj(self, prj_path):   
        self.fm.clear_prj(prj_path)
            
            
    def __run_and_parse(self, command, build_dir, fail_message="Failed", success_message="Successful", is_compilation=False):

        def read_output(stream, queue, stream_name):
            """Read from a stream and put lines in a queue"""
            try:
                for line in iter(stream.readline, ''):
                    queue.put((stream_name, line))
            except ValueError:
                pass
            finally:
                stream.close()

        process = subprocess.Popen(
            command,
            shell=True,
            cwd=build_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        output_queue = Queue()

        stdout_thread = threading.Thread(
            target=read_output, 
            args=(process.stdout, output_queue, 'stdout')
        )
        stderr_thread = threading.Thread(
            target=read_output, 
            args=(process.stderr, output_queue, 'stderr')
        )

        stdout_thread.daemon = True
        stderr_thread.daemon = True
        stdout_thread.start()
        stderr_thread.start()

        # Process output in real-time
        while True:
            try:
                # Process available output with a small timeout
                stream_name, line = output_queue.get(timeout=0.1)
                
                if line:
                    if self.verbose:
                        print(line, end='')
                    if is_compilation:
                        stripped = line.rstrip('\n')
                        self.parser.parse_line(stripped)
                    sys.stdout.flush()
                    
                if 'ERROR' in line:
                    print(f'{line}', end='')
                    

            # Process any remaining output
            except Empty:
                if process.poll() is not None:
                    while not output_queue.empty():
                        try:
                            stream_name, line = output_queue.get_nowait()
                            if line:
                                if self.verbose:
                                    print(f"OUT: {line}", end='')
                                if is_compilation:
                                    stripped = line.rstrip('\n')
                                    self.parser.parse_line(stripped)
                        except Empty:
                            break
                            
                    # Wait for threads to finish
                    stdout_thread.join(timeout=0.1)
                    stderr_thread.join(timeout=0.1)
                    break

            except KeyboardInterrupt:
                print("\nInterrupted by user")
                process.terminate()
                sys.exit()

        returncode = process.wait()
        if returncode != 0:
            print(f"{fail_message}, return code: {returncode}")
            sys.exit()
        elif success_message != "":
            if is_compilation:
                print(f"{colorama.Fore.GREEN} [pass]")
            print(f"{success_message}")
