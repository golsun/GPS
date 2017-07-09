
import sys
import os
import cantera as ct
import json
import time
import shutil
import copy

from PyQt4 import uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

from def_dialog import common
from src.core.def_tools import keys_sorted
from src.ct.ck2cti_GPS import ck2cti

import os






class dialog_about(common):


	# init ============================



	def __init__(self,parent):

		ui_name = 'about.ui'
		self.w = uic.loadUi(os.path.join(parent.dir_ui, ui_name))
		self.w.setFixedSize(self.w.width(), self.w.height())
		self.w.exec_()


