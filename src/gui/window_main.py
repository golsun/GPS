# -*- coding: UTF-8 -*-


# =======================================
#
# copyright: Xiang Gao, 2016
# coded at Georgia Tech
#
# gxiang1228@gmail.com
# reference: 
# 	  Gao et al, Combustion and Flame, 2016
# 	  "A global Pathway Selection Algorithm 
#     for the Reduction of Detailed Chemical 
#     Kinetic Mechanisms"
#
# ========================================


# to do:
# cannot input capital letters
# print ck2cti process to local file
# compress app file
# avoid closeEvent

import sys
import os
import json
import time
import cantera as ct
import shutil
import copy

from PyQt4 import uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

from def_tools_gui import *
from src.core.def_tools import keys_sorted, num2str

from def_dialog import common
from dialog_GPS import dialog_GPS
from dialog_about import dialog_about
from dialog_database import dialog_database
from dialog_mech import dialog_mech
from dialog_view_mech import dialog_view_mech
from def_run import *
from dialog_comb_sk import dialog_comb_sk

from src.post.dialog_post import *
from src.post.dialog_rename import *




class window_main(common):

	""" >>>>>>>>>>>>>>>>>------------------------------------------------------------------------
	0. window_main
	"""

	""" ============================

	                    dP   
	                    88   
	.d8888b. .d8888b. d8888P 
	Y8ooooo. 88ooood8   88   
	      88 88.  ...   88   
	`88888P' `88888P'   dP   
	                         

	"""







	def set(self):

		self.set_table_db('database')
		self.set_list('GPS')
		#self.set_list('PFA')
		self.set_list('mech')
		self.set_enabled()


	def set_enabled(self):

		# if dir_public is ok
		OK_dir = (self.project['dir_public'] != None)
		self.w.menu_save.setEnabled(OK_dir)
		self.w.menu_comb_sk.setEnabled(OK_dir)
		self.w.menu_post.setEnabled(OK_dir)
		self.w.gb_sk.setEnabled(OK_dir)
		self.w.btn_set_de.setEnabled(OK_dir)
		#self.w.gb_PFA.setEnabled(OK_dir)

		# if ctSoln is ok

		OK_soln = (self.soln['detailed'] != None)
		self.w.gb_db.setEnabled(OK_soln)
		self.w.gb_GPS.setEnabled(OK_soln)
		self.w.gb_run.setEnabled(OK_soln)
		self.w.btn_view_de.setEnabled(OK_soln)

		self.app.processEvents()

		if OK_dir:
			self.w.btn_dir.setDefault(False)
			dir_desk = os.path.join(self.project['dir_public'],'detailed')
		else:
			self.w.btn_dir.setDefault(True)
			return None


		if OK_soln:
			self.w.btn_set_de.setDefault(False)
			self.init_es_default()
			#self.init_iso_default()

			self.w.cb_GPSA_traced.clear()
			for item in ['no filter']+self.soln['detailed'].element_names:
				self.w.cb_GPSA_traced.addItem(item)

			self.act_GPSA_refresh()

		else:
			self.w.btn_set_de.setDefault(True)
			return None


	def set_table_db(self, key):
		items = self.project['database']
		model = QStandardItemModel()

		n_row = 0
		sorted_items = sorted(self.project['database'].keys())
		for name in sorted_items:

			Qitem = QStandardItem(name)
			Qitem.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
			model.setItem(n_row,0, Qitem)
			keys_check = ['train','test']

			for i_key in range(len(keys_check)):

				key_check = keys_check[i_key]
				Qitem = QStandardItem(key_check)
				checked = items[name][key_check]
				Qitem.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
				if checked:
					Qitem.setData(QVariant(Qt.Checked), Qt.CheckStateRole)
				else:					
					Qitem.setData(QVariant(Qt.Unchecked), Qt.CheckStateRole)
				model.setItem(n_row,i_key+1, Qitem)

			n_row += 1

		self.w.table_db.setModel(model)
		self.w.table_db.setColumnWidth(0, 190)
		self.w.table_db.setColumnWidth(1, 75)
		self.w.table_db.setColumnWidth(2, 75)

		for i_row in range(n_row):
			self.w.table_db.setRowHeight(i_row,20)

		self.update_train_name()



	def set_list(self, key):

		i_sub = self.sub['key'].index(key)	
		obj = self.sub['obj'][i_sub]
		key = self.sub['key'][i_sub]
		model = QStandardItemModel()

		sorted_items = sorted(self.project[key].keys())
		for item_name in sorted_items:
			#print 'sorted'
			if item_name != 'detailed':
				item = self.project[key][item_name]
				Qitem = QStandardItem(item_name)
				Qitem.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)

				if item['checked']:
					Qitem.setData(QVariant(Qt.Checked), Qt.CheckStateRole)
				else:
					Qitem.setData(QVariant(Qt.Unchecked), Qt.CheckStateRole)

				model.appendRow(Qitem)

		obj.setModel(model)
		self.app.processEvents()




	def act_GPSA_refresh(self):
		items = ['no filter']
		for fuel in self.project['fuel'].keys():
			for sp in self.project['fuel'][fuel]['composition'].keys():
				if sp not in items:
					items.append(sp)

		self.w.cb_GPSA_source.clear()
		for item in items:
			self.w.cb_GPSA_source.addItem(item)





	""" ============================

		                    dP   
		                    88   
		.d8888b. .d8888b. d8888P 
		88'  `88 88ooood8   88   
		88.  .88 88.  ...   88   
		`8888P88 `88888P'   dP   
		     .88                 
		 d8888P            


	"""


	def read_list(self, key):

		i_sub = self.sub['key'].index(key)		
		model = self.sub['obj'][i_sub].model()
		checked = []

		for j in range(model.rowCount()):
			item_name = str(model.item(j).text())	
			if model.item(j).checkState():
				self.project[key][item_name]['checked'] = True
				checked.append(item_name)
			else:
				self.project[key][item_name]['checked'] = False

		return checked



	def read_table_db(self, key):
		model = self.w.table_db.model()
		trained = []
		tested = []
		for j in range(model.rowCount()):
			database_name = str(model.item(j,0).text())

			if model.item(j,1).checkState():
				trained.append(database_name)
				self.project['database'][database_name]['train'] = True
			else:
				self.project['database'][database_name]['train'] = False

			if model.item(j,2).checkState():
				tested.append(database_name)
				self.project['database'][database_name]['test'] = True
			else:
				self.project['database'][database_name]['test'] = False
				
		self.update_train_name()
		return trained, tested













	"""  ============================

		                    dP   
		                    88   
		.d8888b. .d8888b. d8888P 
		88'  `88 88'  `""   88   
		88.  .88 88.  ...   88   
		`88888P8 `88888P'   dP   

	"""






	def act_browse(self):
		self.project = self.project
		self.w = self.w
		dir_parent = self.dir_parent

		dir_public = str(QFileDialog.getExistingDirectory(self.w, '', dir_parent.replace('Contents/Resources','')))
		if bool(dir_public):


			self.w.btn_set_de.setEnabled(False)
			self.w.btn_set_de.setText('loading...')
			self.app.processEvents()

			self.project['dir_public'] = dir_public
			self.w.txt_dir.setText(dir_public)

			# project.json ----------

			path_json = os.path.join(dir_public,'project.json')
			if os.path.exists(path_json):
				self.project = json.load(open(path_json,'r'))
				self.project['version'] = self.version_info 
				self.project['dir_public'] = dir_public
				self.set()

			# detailed chem.cti ----------

			dir_desk = os.path.join(dir_public,'detailed')
			path_cti = os.path.join(dir_desk,'mech','chem.cti')

			if os.path.exists(path_cti):
				self.soln['detailed'] = ct.Solution(path_cti)
				self.soln_in['detailed'] = ct.Solution(path_cti)
				if not bool(self.project['mech']['detailed']['chem']):
					self.project['mech']['detailed']['chem'] = os.path.join(dir_desk,'mech','chem.inp')
					self.project['mech']['detailed']['therm'] = os.path.join(dir_desk,'mech','therm.dat')
			
			self.project['mech']['detailed']['desk'] = dir_desk



		self.set_enabled()		
		self.w.btn_set_de.setText('set')
		self.w.btn_set_de.setEnabled(True)
		self.app.processEvents()




	# add, edit, del =========================

	def act_add(self, key):

		i_sub = self.sub['key'].index(key)
		dialog = self.sub['dialog'][i_sub]
		set_viewer = self.sub['set_viewer'][i_sub]

		data = dialog(parent=self, data_name=None).data
		if data is not None:
			self.project[key][data['name']] = data
			set_viewer(key=key)




	def act_del(self, key):

		i_sub = self.sub['key'].index(key)
		obj = self.sub['obj'][i_sub]
		dialog = self.sub['dialog'][i_sub]
		set_viewer = self.sub['set_viewer'][i_sub]

		data_name = self.read_item(obj)
		if data_name == None:
			return None

		msg = 'are you sure to delete "'+data_name+'""?\n\n'+\
			'(you can uncheck it if you only donnot want to use it right now)'
		Qanswer = QMessageBox.question(QWidget(),'',msg, \
				QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

		if Qanswer == QMessageBox.Yes:

			if key == 'mech':
				used_by_any = []
				self_keys = []#'plot_ign','plot_fat','plot_psr','plot_sz']
				for self_key in self_keys:				
					for super_data_name in self.project[self_key].keys():
						super_data = self.project[self_key][super_data_name]
						if data_name in super_data[key]:
							used_by_any.append(super_data_name)

				if bool(used_by_any):
					msg = 'can not delete '+ data_name + \
						' because it is used by the followings: \n\n'
					for super_data_name in used_by_any:
						msg += ('    ' + super_data_name + '\n')

					msg += '\nto delete, please save the above without selecting ' + data_name
					QMessageBox.information(QWidget(),'',msg)
					return None

			del self.project[key][data_name]
			if key == 'mech':
				if data_name in self.soln.keys():
					del self.soln[data_name]
					del self.soln_in[data_name]

			set_viewer(key=key)




	def act_edit(self, key):

		i_sub = self.sub['key'].index(key)
		obj = self.sub['obj'][i_sub]
		dialog = self.sub['dialog'][i_sub]
		set_viewer = self.sub['set_viewer'][i_sub]

		data_name = self.read_item(obj)
		if data_name == None:
			return None

		data = dialog(parent=self, data_name=data_name).data	
		if data is not None:
			del self.project[key][data_name]
			self.project[key][data['name']] = data

			if key == 'mech':
				self_keys = []#'plot_ign','plot_fat','plot_psr','plot_sz']
				for self_key in self_keys:				
					for super_data_name in self.project[self_key].keys():
						super_data = self.project[self_key][super_data_name]
						if data_name in super_data[key]:
							index = super_data[key].index(data_name)
							super_data[key][index] = data['name']

			set_viewer(key=key)



	def act_edit_de(self):
		de = dialog_mech(parent=self, data_name='detailed').data
		if de is not None:
			del self.project['mech']['detailed']
			self.project['mech']['detailed'] = de
		self.set_enabled()





	def act_add_db(self): self.act_add('database')
	def act_add_GPS(self): self.act_add('GPS')
	#def act_add_PFA(self): self.act_add('PFA')
	def act_add_sk(self): self.act_add('mech')

	def act_edit_db(self): self.act_edit('database')
	def act_edit_GPS(self): self.act_edit('GPS')
	#def act_edit_PFA(self): self.act_edit('PFA')
	def act_edit_sk(self): self.act_edit('mech')

	def act_del_db(self): self.act_del('database')
	def act_del_GPS(self): self.act_del('GPS')
	#def act_del_PFA(self): self.act_del('PFA')
	def act_del_sk(self): self.act_del('mech')





	# mech view =========================


	def act_view_desk(self, data_name):

		if data_name == 'detailed':
			btn = self.w.btn_view_de
		else:
			btn = self.w.btn_view_sk

		btn.setEnabled(False)
		btn.setText('loading...')
		self.app.processEvents()
		dialog_view_mech(parent=self, data_name=data_name, btn=btn)	




	def act_view_sk(self):
		sk_name = self.read_item(self.w.list_sk)
		if sk_name != None:
			self.act_view_desk(sk_name)


	def act_view_de(self): 
		self.act_view_desk('detailed')



	# menu =========================


	def act_save_prj(self):
		self.project['dir_public'] = str(self.w.txt_dir.text())
		self.read_table_db('database')
		self.read_list('GPS')
		#self.read_list('PFA')
		#self.read_list('mech')
		self.app.processEvents()
		path_save = os.path.join(self.project['dir_public'],'project.json')
		json.dump(self.project, open(path_save,'w'))
		self.app.processEvents()


	def act_post(self):
		dialog_post(parent=self)


	def act_rename(self):
		dialog_rename(parent=self)

	def act_comb_sk(self):
		dialog_comb_sk(parent=self)




	# update =========================

	def update_train_name(self):
		train_name = ''
		for db_name in sorted(self.project['database'].keys()):
			if self.project['database'][db_name]['train']:
				train_name += (add_bracket(db_name)+' + ')
		self.train_name = train_name[:-3]


	def act_about(self):
		dialog_about(parent=self)

	
	"""  ============================

                           
                           
		88d888b. dP    dP 88d888b. 
		88'  `88 88    88 88'  `88 
		88       88.  .88 88    88 
		dP       `88888P' dP    dP 
		                           
                            

	"""








	def act_run(self):

		list_GPS = self.read_list('GPS')
		#list_PFA = self.read_list('PFA')
		list_sk = self.read_list('mech')
		list_train, list_test = self.read_table_db('database')
		
		has_task = False
		do_task = True

		progress = dialog_progress(self)



		# training ------------
		if self.w.ck_train.isChecked():
			if bool(list_train) == False:
				msg = 'no training database selected'
				QMessageBox.information(QWidget(),'',msg)
				return None

			progress.set_info('='*10 + ' calculating training database' + '='*10)
			has_task = True
			do_task = run_train(self, progress)
			progress.set_info('='*10 + ' training finished' + '='*10 + '\n'*5)

		else:
			progress.set_value('train',100)



		# GPS ------------
		
		if bool(list_GPS) and do_task and self.w.ck_GPS.isChecked():

			if bool(list_train) == False and bool(list_GPS):
				msg = 'at least one traininig database should be selected \n'+\
					'(we need it to specify GPS)'
				QMessageBox.information(QWidget(),'',msg)
				return None

			progress.set_info('='*10 + ' performing GPS' + '='*10)
			has_task = True
			do_task = run_GPS(self, progress)			
			progress.set_info('='*10 + ' GPS finished' + '='*10 + '\n'*5)

		else:
			progress.set_value('GPS',100)


		# testing ------------
		if do_task and self.w.ck_test.isChecked():
			has_task = True
			do_task = run_test(self, progress)

		else:
			progress.set_value('test',100)


		# GPSA ------------
		
		if do_task and self.w.gb_GPSA.isChecked():

			if bool(list_train) == False and bool(list_GPS):
				msg = 'at least one traininig database should be selected \n'+\
					'(we need it to specify GPS)'
				QMessageBox.information(QWidget(),'',msg)
				return None

			progress.set_info('='*10 + ' performing GPSA' + '='*10)
			has_task = True
			do_task = run_GPSA(self, progress)			
			progress.set_info('='*10 + ' GPSA finished' + '='*10 + '\n'*5)

		else:
			progress.set_value('GPS',100)



		# finished ------------

		if not has_task:
			msg = 'no task selected'
			QMessageBox.information(QWidget(),'',msg)
		else:
			if progress.stop:
				msg = 'manually stopped'
			else:
				msg = 'all tasks finished'
			QMessageBox.information(QWidget(),'',msg)

		progress.f.close()








	
	"""  ============================

                           
                           

		oo          oo   dP   
		                 88   
		dP 88d888b. dP d8888P 
		88 88'  `88 88   88   
		88 88    88 88   88   
		dP dP    dP dP   dP   
                      
                   


	"""




	# init ============================

	#def init_iso_default(self):
	#	if bool(self.project['iso']) == False:
	#		iso = dict()# default_iso(self.soln['detailed'])
	#		self.project['iso']['default'] = iso


	def init_es_default(self):

		alias_fuel = '!fuel!'
		self.alias_fuel = alias_fuel
		es_traced = ['C','c','H','h','O','o']
		es_e = dict()
		es_e['C'] = {'only_hub':False, 'source':[alias_fuel],'target':['CO2']}
		es_e['H'] = {'only_hub':False, 'source':[alias_fuel],'target':['H2O']}
		es_e['c'] = {'only_hub':False, 'source':[alias_fuel],'target':['co2']}
		es_e['h'] = {'only_hub':False, 'source':[alias_fuel],'target':['h2o']}
		es_e['!other!'] = {'only_hub':True, 'source':[],'target':[]}	

		soln = self.soln['detailed']
		if bool(self.project['es']) == False:
			element = dict()
			for e in soln.element_names:
				if e in es_e.keys():
					element[e] = copy.copy(es_e[e])
				else:
					element[e] = copy.copy(es_e['!other!'])

				if e in es_traced:
					element[e]['traced'] = True
				else:
					element[e]['traced'] = False

				element[e]['cust'] = False
				element[e]['name'] = e

			es = dict()
			es['name'] = 'default'
			es['element'] = element
			self.project['es']['default'] = es



	def init_prj_default(self):

		air_comp = {'O2':0.21,'N2':0.79}
		air = {'composition':air_comp,'name_cust':True,'name':'air'}

		self.project = dict()
		self.project['dir_public'] = None
		self.project['oxid'] = {'air':air}
		self.project['fuel'] = dict()
		self.project['database'] = dict()
		self.project['GPS'] = dict()		
		self.project['mech'] = dict()
		self.project['mech']['detailed'] = {'name':'detailed', 'chem':'', 'therm':'', 'desk':''}
		self.project['es'] = dict()
		self.project['rename'] = dict()
		self.project['version'] = self.version_info





	def __init__(self):

		self.version_info = "GPS v2.0, copyright © Xiang Gao, Prof. Wenting Sun's group @ Georgia Tech"


		# self.variables ============================

		self.dir_parent = os.getcwd()
		self.dir_ui = os.path.join(self.dir_parent,'ui')

		self.soln = dict()
		self.soln_in = dict()
		self.soln['detailed'] = None
		self.soln_in['detailed'] = None

		self.chr_not_allowed = [chr(92), '/', ':','*','?','"','<','>','|','+']
		self.ign_list = [
			'autoignition',
			'autoignition fine',
			'autoignition full',
			]
		self.psr_list = [
			'PSR extinction',
			]
		self.other_list = [
			'Premix',
			'DNS'
			]
		self.reactor_list = self.ign_list + self.psr_list + self.other_list

		self.n_digit = 4
		self.min_dT = 10


		# load ui and set connection ====================

		ui_name = 'main.ui'
		self.app = QApplication(sys.argv)
		self.w = uic.loadUi(os.path.join(self.dir_ui, ui_name))
		self.w.setFixedSize(self.w.width(), self.w.height())

		self.w.btn_dir.clicked.connect(self.act_browse)

		self.w.menu_save.triggered.connect(self.act_save_prj)
		self.w.menu_save.setShortcut('Ctrl+S')
		self.w.menu_postprocessor.triggered.connect(self.act_post)
		self.w.menu_about.triggered.connect(self.act_about)
		self.w.menu_comb_sk.triggered.connect(self.act_comb_sk)
		self.w.menu_rename.triggered.connect(self.act_rename)

		self.w.btn_add_db.clicked.connect(self.act_add_db)
		self.w.btn_edit_db.clicked.connect(self.act_edit_db)
		self.w.btn_del_db.clicked.connect(self.act_del_db)
		self.w.table_db.doubleClicked.connect(self.act_edit_db)

		self.w.btn_add_GPS.clicked.connect(self.act_add_GPS)
		self.w.btn_edit_GPS.clicked.connect(self.act_edit_GPS)
		self.w.btn_del_GPS.clicked.connect(self.act_del_GPS)
		self.w.list_GPS.doubleClicked.connect(self.act_edit_GPS)


		self.w.btn_add_sk.clicked.connect(self.act_add_sk)
		self.w.btn_edit_sk.clicked.connect(self.act_edit_sk)
		self.w.btn_del_sk.clicked.connect(self.act_del_sk)
		self.w.btn_view_sk.clicked.connect(self.act_view_sk)
		self.w.list_sk.doubleClicked.connect(self.act_edit_sk)

		self.w.btn_view_de.clicked.connect(self.act_view_de)
		self.w.btn_set_de.clicked.connect(self.act_edit_de)

		self.w.btn_GPSA_refresh.clicked.connect(self.act_GPSA_refresh)
		self.w.btn_run.clicked.connect(self.act_run)

		self.w.table_db.clicked.connect(self.update_train_name)


		# set and exec =============================

		self.sub = dict()
		self.sub['obj'] = [self.w.table_db, self.w.list_GPS, self.w.list_sk]#, self.w.list_PFA, self.w.list_sk]
		self.sub['key'] = ['database', 'GPS', 'mech']#, 'PFA', 'mech']
		self.sub['dialog'] = [dialog_database, dialog_GPS, dialog_mech]#, dialog_PFA, dialog_mech]
		self.sub['set_viewer'] = [self.set_table_db, self.set_list, self.set_list]

		self.init_prj_default()


		for item in ['no filter','with alias only']:
			self.w.cb_GPSA_alias.addItem(item)
		self.w.cb_GPSA_source.addItem('no filter')



		self.set()
		self.w.show()
		self.update_train_name()
		sys.exit(self.app.exec_())


	""" 
		end of 0. window_main
	----------------------------------------------------<<<<<<<<<<<< """


if __name__ == '__main__':
	window_main()
