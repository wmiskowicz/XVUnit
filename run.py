import argparse
import sys

from internals.python.xvunit import XVunit


def main():
    parser = argparse.ArgumentParser(description="Run Vivado simulations outside Vivado for faster execution.")
    parser.add_argument("-l", '--list',action="store_true", help="List available tests")
    parser.add_argument("-t", '--test', type=str, help="Run the specified test")
    parser.add_argument("-g", '--gui', action="store_true", help="Show GUI (use with -t)")
    parser.add_argument("-prj", action="store_true", help="Update .prj file of run test. (use with -t)")
    
    args = parser.parse_args()
    xvunit = XVunit()
    
    if args.list:
        xvunit.list()
    elif args.test:
        xvunit.match_and_run(args.test)
    else:
        parser.print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()