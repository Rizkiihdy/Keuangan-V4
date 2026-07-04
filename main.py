import sys
import os

# Add bot folder to path so modules are importable directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

from bot import main

if __name__ == "__main__":
    main()
