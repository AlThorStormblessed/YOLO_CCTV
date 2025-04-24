"""
Web interface module for face recognition system. 
Provides a simple web UI for monitoring and managing the system remotely.
"""

import os
import sys
from pathlib import Path

# Allow module to be run directly
if __name__ == '__main__':
    # Add the parent directory to the path so we can import the prod package
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from prod.web_interface.app import main
    main() 