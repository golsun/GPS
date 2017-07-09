
import sys, copy
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




def fun_cleanck(dir_desk_mech):

	# ========= chem.inp ====================

	p0 = os.path.join(dir_desk_mech,'chem0.inp')
	f0 = open(p0,'r')
	f = open(os.path.join(dir_desk_mech,'chem.inp'),'w')

	for ln0 in f0:
		ln = ln0
		if 'TROE' in ln.upper() or 'LOW' in ln.upper():
			#print 'TROE or LOW found'
			ln = ln.replace(',',' ')

		ln = ln.replace(',',';')
		f.write(ln)

	f.close()
	f0.close()
	os.remove(p0)


	# ========= chem.inp ====================

	p0 = os.path.join(dir_desk_mech,'therm0.dat')
	f0 = open(p0,'r')
	f = open(os.path.join(dir_desk_mech,'therm.dat'),'w')

	prev_status = None
	reg_len = 80
	for ln0 in f0:

		ln = ln0.rstrip()

		if bool(ln):

			if ln[0] == '!':
				status = 0
			elif len(ln)>70 and ln[-1] in ['1','2','3','4']:
				status = int(ln[-1])
				if len(ln) < reg_len:
					ln = ln[:-2] + ' '*(reg_len - len(ln)) + ln[-2:]
				elif len(ln) > reg_len:
					ln = ln[:-2 - (len(ln)-reg_len)] + ln[-2:]
			else:
				if prev_status == 3:
					ln = ln + ' '*(reg_len-len(ln)-1) + '4'
					status = 4
				else:
					status = None


		ln = ln.replace(',',';')
		f.write(ln+'\n')
		prev_status = status

	f.close()
	f0.close()
	os.remove(p0)








class dialog_mech(common):

	""" >>>>>>>>>>>>>------------------------------------------------
	0.2. dialog_mech
	     called by: window_main
	"""



	# read ============================


	def read_path(self):
		txt_list = [self.w.txt_desk, self.w.txt_chem, self.w.txt_therm]
		key_list = ['desk','chem', 'therm']
		para_list = ['folder', 'gas-phase kinetic file', 'thermodynamics data file']

		for i_txt in range(len(txt_list)):
			txt = txt_list[i_txt]
			key = key_list[i_txt]
			para = para_list[i_txt]
			ss = str(txt.text())

			if bool(ss):
				self.data[key] = ss
			else:
				msg = para + ' not provided'
				QMessageBox.information(QWidget(),'',msg)
				return False

		return True



	# acts ============================


	def act_ns(self):
		dir_desk = str(self.w.txt_desk.text())
		path_ns = os.path.join(dir_desk,'mech','ns.txt')

		if os.path.exists(path_ns):
			f = open(path_ns,'r')
			n_sp = f.read()
			self.w.txt_ns.setText(n_sp)
			f.close()
		else:
			self.w.txt_ns.setText('...')



	def act_desk(self):
		dir_public = str(self.parent.w.txt_dir.text())
		dir_desk = str(QFileDialog.getExistingDirectory(self.w, '', dir_public))
		if bool(dir_desk):
			if dir_desk[-5:] == '/mech':
				dir_desk = dir_desk[:-5]
			self.w.txt_desk.setText(dir_desk)
			self.act_ns()

			if bool(str(self.w.txt_therm.text())) == False:
				therm_str = os.path.join(dir_desk,'mech','therm.dat')
				if os.path.exists(therm_str):
					self.w.txt_therm.setText(therm_str)

			if bool(str(self.w.txt_chem.text())) == False:
				chem_str = os.path.join(dir_desk,'mech','chem.inp')
				if os.path.exists(chem_str):
					self.w.txt_chem.setText(chem_str)



	def act_path_chem(self):
		therm_str = str(self.w.txt_therm.text())
		dir_desk = str(self.w.txt_desk.text())
		if bool(self.data['chem']):
			path_ini = self.data['chem']
		elif bool(therm_str):
			path_ini = os.path.dirname(therm_str)
		elif bool(dir_desk):
			path_ini = dir_desk
		else:
			path_ini = self.parent.project['dir_public']

		path_chem = str(QFileDialog.getOpenFileName(self.w, 'Open File', path_ini))
		if bool(path_chem):
			self.w.txt_chem.setText(path_chem)


	def act_path_therm(self):
		chem_str = str(self.w.txt_chem.text())
		dir_desk = str(self.w.txt_desk.text())
		if bool(self.data['therm']):
			path_ini = self.data['therm']
		elif bool(chem_str):
			path_ini = os.path.dirname(chem_str)
		elif bool(dir_desk):
			path_ini = dir_desk
		else:
			path_ini = self.parent.project['dir_public']

		path_therm = str(QFileDialog.getOpenFileName(self.w, 'Open File', path_ini))
		if bool(path_therm):
			self.w.txt_therm.setText(path_therm)

	def act_cancel(self):
		self.w.reject()


	def act_save(self):

		if self.read_name() and self.read_path():

			dir_desk = self.data['desk']
			path_cti = os.path.join(dir_desk,'mech','chem.cti')

			if  self.data['chem'] != self.data_ini['chem'] or \
				self.data['therm'] != self.data_ini['therm'] or \
				self.data['desk'] != self.data_ini['desk'] or \
				(not os.path.exists(path_cti)):

				if self.act_set() == False:
					return None

			data_name = self.old_name

			if data_name in self.parent.soln.keys():
				try:
					del self.parent.soln[data_name]
					del self.parent.soln_in[data_name]
				except KeyError:
					pass

			if self.soln !=None:
				self.parent.soln[self.data['name']] = self.soln
				self.parent.soln_in[self.data['name']] = self.soln_in

			self.w.accept()




	def act_set(self):

		if self.read_path():
			dir_desk = self.data['desk']
			path_cti = os.path.join(dir_desk,'mech','chem.cti')
			if not os.path.exists(path_cti):

				dir_desk = self.data['desk']
				dir_desk_mech = os.path.join(dir_desk,'mech')
				path_cti = os.path.join(dir_desk_mech,'chem.cti')

				if not os.path.exists(dir_desk_mech):
					os.makedirs(dir_desk_mech)

				shutil.copy(self.data['chem'],os.path.join(dir_desk_mech,'chem0.inp'))
				shutil.copy(self.data['therm'],os.path.join(dir_desk_mech,'therm0.dat'))

				fun_cleanck(dir_desk_mech)

				self.w.btn_save.setEnabled(False)
				self.w.btn_save.setText('setting...')
				self.parent.app.processEvents()

				if ck2cti(dir_desk_mech):
					self.no_set = False
					self.soln = ct.Solution(path_cti)
					self.soln_in = ct.Solution(path_cti)

					n_sp = self.soln.n_species
					f = open(os.path.join(dir_desk_mech,'ns.txt'),'w')
					f.write(str(n_sp))
					f.close()

					self.act_ns()

					self.w.btn_save.setEnabled(True)
					self.w.btn_save.setText('save')
					self.parent.app.processEvents()	
					return True

		else:
			return False





	# init ============================



	def __init__(self, parent, data_name=None):

		ui_name = 'mech.ui'
		self.parent = parent
		self.key = 'mech'
		self.old_name = data_name
		self.occupied = self.init_occupied() + ['PFA','GPS','detailed']

		# load ui and set connection ====================

		self.w = uic.loadUi(os.path.join(parent.dir_ui, ui_name))
		self.w.btn_desk.clicked.connect(self.act_desk)
		self.w.btn_path_chem.clicked.connect(self.act_path_chem)
		self.w.btn_path_therm.clicked.connect(self.act_path_therm)
		self.w.btn_cancel.clicked.connect(self.act_cancel)
		self.w.btn_save.clicked.connect(self.act_save)

		

		# set initial values =============================
		
		if data_name is None:
			self.data = dict()
			self.data['desk'] = ''
			self.data['chem'] = ''
			self.data['therm'] = ''
			self.data['name'] = self.new_name('skeletal', self.occupied)
			self.data['checked'] = True
			self.soln = None
			self.soln_in = None

		else:
			self.data = copy.copy(self.parent.project['mech'][data_name])
			if data_name in self.parent.soln.keys():
				self.soln = self.parent.soln[data_name]
				self.soln_in = None#copy.deepcopy(self.soln)#self.parent.soln_in[data_name]
			else:
				self.soln = None
				self.soln_in = None


		self.data_ini = copy.copy(self.data)
		self.no_set = True

		self.w.txt_name.setText(self.data['name'])
		self.w.txt_desk.setText(self.data['desk'])
		self.w.txt_chem.setText(self.data['chem'])
		self.w.txt_therm.setText(self.data['therm'])
		self.act_ns()

		if data_name == 'detailed':
			self.w.txt_name.setReadOnly(True)
			dir_de = os.path.join(self.parent.project['dir_public'],'detailed')
			self.w.txt_desk.setText(dir_de)
			self.w.btn_desk.setEnabled(False)


		# exec and return =============================

		if self.w.exec_() == QDialog.Rejected:
			self.data = None


