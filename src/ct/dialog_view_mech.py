
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

from def_tools_gui import *
from src.core.def_tools import keys_sorted
from src.ct.ck2cti_GPS import ck2cti


class dialog_view_mech(object):

	

	def set_soln(self, mech_name):
		dir_desk = os.path.join(self.wm.project['dir_public'],mech_name)
		dir_desk_mech = os.path.join(dir_desk,'mech')
		path_cti = os.path.join(dir_desk,'chem.cti')
		if not os.path.exists(path_cti):
			ctOK = ck2cti(dir_desk_mech)
			if ctOK not True:
				msg = 'errors in reading mech files, \nplease check output files'
				QMessageBox.information(QWidget(),'',msg)
				return None

		if mech_name not in self.wm.sk_soln.keys():
			self.wm.soln[mech_name] = ct.Solution(path_cti)
			self.wm.soln_in[mech_name] = ct.Solution(path_cti)

		self.soln = self.wm.soln[mech_name]


	def set_summary():
		self.w.txt_n_e.setText(': ' + str(len(self.soln.element_names)))
		self.w.txt_n_sp.setText(': ' + str(len(self.soln.species_names)))
		self.w.txt_n_rxn.setText(': ' + str(len(self.soln.reaction_names)))



	def __init__(self, window_main, mech_name=None):

		ui_name = 'view_mech.ui'
		self.wm = window_main
		self.mech_name = mech_name

		# load ui and set connection ====================

		self.w = uic.loadUi(os.path.join(window_main.dir_ui, ui_name))
		#self.w.btn_path_chem.clicked.connect(self.act_path_chem)

		# set initial values =============================
		
		self.w.show()
		self.w.set_soln(mech_name)
		self.w.txt_name.setText(': '+ mech_name)
		self.w.set_summary()

		# exec and return =============================

		self.w.exec_()
