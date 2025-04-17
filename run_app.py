import sys
import os

# Add the src directory to the path so we can import the main module
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

import main

if __name__ == "__main__":
    main.main() 