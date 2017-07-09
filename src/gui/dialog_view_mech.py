
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

from src.core.def_tools import keys_sorted
from src.ct.ck2cti_GPS import ck2cti


class dialog_view_mech(object):


	def set_summary(self):
		self.w.txt_n_e.setText(': ' + str(self.soln.n_elements))
		self.w.txt_n_sp.setText(': ' + str(self.soln.n_species))
		self.w.txt_n_rxn.setText(': ' + str(self.soln.n_reactions))


	def set_lists(self):
		for e in self.soln.element_names:
			self.w.cb_e.addItem(e)
		for sp in self.soln.species_names:
			self.w.cb_sp.addItem(sp)
		for rxn in self.soln.reaction_equations():
			self.w.cb_rxn.addItem(rxn)

	def act_ok(self):
		self.w.accept()



	# init ============================
	def __init__(self, parent, data_name=None, btn=None):

		ui_name = 'view_mech.ui'
		self.parent = parent
		self.data_name = data_name

		# load ui and set connection ====================

		self.w = uic.loadUi(os.path.join(parent.dir_ui, ui_name))
		self.w.btn_ok.clicked.connect(self.act_ok)

		# set initial values =============================

		#dir_desk = os.path.join(self.parent.project['dir_public'],data_name)
		#dir_desk_mech = os.path.join(dir_desk,'mech')
		dir_desk = self.parent.project['mech'][data_name]['desk']
		path_cti = os.path.join(dir_desk,'mech','chem.cti')
		if os.path.exists(path_cti) == False:
			msg = 'no chem.cti file\n\n'+path_cti
			QMessageBox.information(QWidget(),'',msg)
			return None

		if data_name not in self.parent.soln.keys():
			self.parent.soln[data_name] = ct.Solution(path_cti)
			self.parent.soln_in[data_name] = ct.Solution(path_cti)

		self.soln = self.parent.soln[data_name]
		self.w.txt_name.setText(': '+ data_name)
		self.set_summary()
		self.set_lists()
		if btn is not None:
			btn.setEnabled(True)
			btn.setText('view')

		# exec and return =============================

		self.w.exec_()
