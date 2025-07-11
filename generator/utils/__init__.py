from io import StringIO
from pathlib import Path
from typing import List

import os
import runpy
import sys

def call_external_module(package_root_path : Path, module_name : str, arguments : List[str]):
    """
    Call a function from an external module given its path
    """
    original_argv = sys.argv
    original_path = sys.path.copy()
    old_stdout = sys.stdout
    sys.stdout = captured_output = StringIO()
    
    try:
        abs_package_root = os.path.abspath(package_root_path)
        if abs_package_root not in sys.path:
            sys.path.insert(0, abs_package_root)
        
        if arguments:
            sys.argv = [module_name] + arguments
        else:
            sys.argv = [module_name]
        
        result = runpy.run_module(module_name, run_name='__main__')
        
        output = captured_output.getvalue().strip()
        
        return output, result
    finally:
        sys.argv = original_argv
        sys.path = original_path
        sys.stdout = old_stdout