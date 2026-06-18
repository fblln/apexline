#!/usr/bin/env python3

from pathlib import Path
import sys


PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "src"))

from apexline.plot_canada_examples import main


if __name__ == "__main__":
    main()
