"""Opens the Battle Cats save editor (graphical interface for BCSFE).

Double-click this file (or "Start Editor.vbs") to open it."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bcsfe_gui.app import main  # noqa: E402

sys.exit(main())
