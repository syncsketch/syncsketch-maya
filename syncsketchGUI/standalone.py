import os
import sys

main_folder = os.path.dirname(__file__)
parent_folder = os.path.dirname(main_folder)
if parent_folder not in sys.path:
    sys.path.append(parent_folder)

try:
    from importlib import reload
except ImportError:
    pass

import syncsketchGUI

reload(syncsketchGUI)
syncsketchGUI.reload_toolkit()
syncsketchGUI.show_main_window()
