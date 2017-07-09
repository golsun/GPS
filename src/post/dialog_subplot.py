
import sys
import os
import cantera as ct
import json
import time
import copy

from PyQt4 import uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

from def_painter import *
from src.core.def_tools import keys_sorted, cond2dir, para2dir_GPS
from src.core.def_GPSA import *
from src.ct.def_ct_tools import load_raw
from src.gui.def_dialog import *







""" >>>>>>>>>>>>>------------------------------------------------
1.1.0 dialog_ign_db
     called by: dialog_plot_builder
                                  




      dP            dP            dP                                  
      88            88            88                                  
.d888b88 .d8888b. d8888P .d8888b. 88d888b. .d8888b. .d8888b. .d8888b. 
88'  `88 88'  `88   88   88'  `88 88'  `88 88'  `88 Y8ooooo. 88ooood8 
88.  .88 88.  .88   88   88.  .88 88.  .88 88.  .88       88 88.  ... 
`88888P8 `88888P8   dP   `88888P8 88Y8888' `88888P8 `88888P' `88888P' 



"""


class dialog_plot_db(base_dialog):

	def set_items(self):

		self.w_cbs['items'] = []
		db_name = self.data['db_name']
		if bool(db_name) and db_name in self.parent.project['database'].keys():
			self.w.gb_key.setEnabled(True)
			db = self.parent.project['database'][db_name]
			self.w.txt_reactor.setText(db['reactor'])
			self.data['reactor'] = db['reactor']

			for key in self.w_cbs['key']:
				items = []
				for item in db[key]:
					items.append(str(item))
				if len(items) > 1: items.append('varying')
				self.w_cbs['items'].append(items)
				if self.init_fnished:
					self.data[key] = items[0]

		else:
			self.w.gb_key.setEnabled(False)
			self.w_cbs['items'] = [list()] * len(self.w_cbs['obj'])

		self.set_cb()


	def act_save(self):
		for reader in self.readers:
			if reader() == False:
				return None

		n_varying = 0
		for key in self.w_cbs['key']:
			if self.data[key] == 'varying':
				n_varying += 1

		subkey = self.extra['subkey']
		if ('ign_evolve' in subkey) or ('psr_state' in subkey) or ('premix_evolve' in subkey):
			n_min = 0
			n_max = 1
		elif 'ign_state' in subkey:
			n_min = 1
			n_max = 2
		elif 'GPedge' in subkey:
			n_min = 0
			n_max = 0

		if n_varying < n_min:
			msg = 'current plot needs at least ' + str(n_min) + \
				' items to be varying'
			QMessageBox.information(QWidget(),'',msg)
			return None

		if n_varying > n_max:
			msg = 'for current plot at most ' + str(n_max) + \
				' items can be varying'
			QMessageBox.information(QWidget(),'',msg)
			return None


		self.w.accept() 



	def act_db(self):
		if self.init_fnished:
			db_name = str(self.w.cb_db.currentText())
			self.data['db_name'] = db_name
			self.set_items()


	def init_data_default(self):
		self.data = dict()
		self.data['db_name'] = ''
		self.data['reactor'] = ''
		self.data['fuel'] = ''
		self.data['oxid'] = ''
		self.data['T0'] = ''
		self.data['atm'] = ''


	def init(self):
		self.init_fnished = False
		self.ui_name = 'plot_db.ui'
		self.init_ui()
		if self.extra['db'] == None:
			self.init_data_default()
		else:
			self.data = copy.copy(self.extra['db'])

		# set connection ====================

		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)
		self.w.cb_db.currentIndexChanged.connect(self.act_db)

		# set obj IO ==============================

		self.w_cbs = dict()
		self.w_cbs['obj'] = [self.w.cb_fuel, self.w.cb_oxid, self.w.cb_T0, self.w.cb_atm]
		self.w_cbs['key'] = ['fuel','oxid', 'T0','atm']
		self.w_cbs['name'] = ['fuel','oxidizer','initial/inlet T','pressure']


		# set ui obj ==============================

		self.set_items()
		self.set_cb()
		
		self.w.cb_db.clear()
		self.w.cb_db.addItem('')
		index = 0
		current_index = index
		for db_name in self.parent.project['database'].keys():
			print 'checking db_name '+str(db_name)
			self.w.cb_db.addItem(db_name)
			index += 1
			if db_name == self.data['db_name']:
				current_index = index

		self.w.cb_db.setCurrentIndex(current_index)
		self.init_fnished = True

		# exec ==============================

		self.readers = [self.read_cb]
		if self.w.exec_() == QDialog.Rejected:
			self.data = None























""" >>>>>>>>>>>>>------------------------------------------------



               dP          
               88          
.d8888b. .d888b88 dP   .dP 
88'  `88 88'  `88 88   d8' 
88.  .88 88.  .88 88 .88'  
`88888P8 `88888P8 8888P'   
                           
                           



"""

class dialog_adv(base_dialog):

	def init(self):

		self.ui_name = 'subplot_adv.ui'
		self.init_ui()

		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)

		extra = self.extra
		self.ls_list = ['-','--','-.',':','none']

		# =============================

		self.data = copy.copy(extra)

		# =============================

		self.w_txts = dict()
		self.w_txts['obj'] = [self.w.txt_marker, self.w.txt_ls, self.w.txt_color, self.w.txt_wordx, self.w.txt_ytick, self.w.txt_ylim]
		self.w_txts['key'] = ['marker','ls','color','word_loc','ytick','ylim']
		self.w_txts['name'] = ['marker', 'line style', 'color', 'label location', 'ticks', 'limits']
		self.w_txts['vali'] = [self.is_any, self.is_ls, self.is_any, self.is_float, self.is_float, self.is_float]
		self.w_txts['empty'] = [False, False, False, False, True, True]
		self.w_txts['len'] = [None, None, None, 1, None, 2]


		items = ['mech','2nd var','feature']
		items_lg_loc = ['upper left','upper right','center left','center right','lower left','lower right','center']
		self.w_cbs = dict()
		self.w_cbs['obj'] = [self.w.cb_marker_by, self.w.cb_ls_by, self.w.cb_color_by, self.w.cb_scale, self.w.cb_lg_loc]
		self.w_cbs['key'] = ['marker_by','ls_by','color_by','scale','lg_loc']
		self.w_cbs['name'] = ['marker varying by','line style varying by','color varying by','scale','legend location']
		self.w_cbs['items'] = [items, items, items,['linear','log'],items_lg_loc]


		self.w_cks = dict()
		self.w_cks['obj'] = [self.w.gb_word, self.w.ck_word_mech, self.w.ck_word_2nd, self.w.ck_word_feature, \
			self.w.gb_lg, self.w.ck_lg_mech, self.w.ck_lg_sec, self.w.ck_lg_feature]
		self.w_cks['key'] = ['word_show','word_mech','word_2nd','word_feature',\
			'lg_show','lg_mech','lg_sec','lg_feature']
		self.w_cks['name'] = self.w_cks['key']


		# =============================

		self.set_txt()
		self.set_cb()
		self.set_ck()
		self.w.txt_feature.setText(self.data['feature_name'])

		# =============================

		self.readers = [self.read_txt, self.read_cb, self.read_ck]
		if self.w.exec_() == QDialog.Rejected:
			self.data = None



def act_adv(dialog):

	subset = dialog_adv(parent=dialog.parent, extra=dialog.data).data
	if subset != None:
		dialog.data = subset




def init_data_default():

	data = dict()

	data['scale'] = 'linear'

	data['ls'] = ['-','--','-.',':','none','-','--','-.']
	data['ls_by'] = 'feature'
	data['color'] = ['r','b','k','g','b','k','g','r']
	data['color_by'] = '2nd var'
	data['marker'] = ['None','o','v','s','*','>','<']
	data['marker_by'] = 'mech'

	data['word_show'] = True
	data['word_mech'] = False
	data['word_2nd'] = True
	data['word_feature'] = False
	data['word_loc'] = [50.0]

	data['lg_show'] = True
	#data['lg_marker'] = True
	#data['lg_ls'] = True
	#data['lg_color'] = False
	data['lg_mech'] = False
	data['lg_sec'] = False
	data['lg_feature'] = True
	data['lg_loc'] = 'upper left'

	data['ytick'] = []
	data['ylim'] = []

	return data

















""" >>>>>>>>>>>>>------------------------------------------------
1.1.1 dialog_plot_single
     called by: dialog_plot_builder



         oo                   dP          
                              88          
.d8888b. dP 88d888b. .d8888b. 88 .d8888b. 
Y8ooooo. 88 88'  `88 88'  `88 88 88ooood8 
      88 88 88    88 88.  .88 88 88.  ... 
`88888P' dP dP    dP `8888P88 dP `88888P' 
                          .88             
                      d8888P              

                                                 
"""


class dialog_plot_single(base_dialog):


	def act_adv_helper(self): act_adv(self)

	def init_data_default(self):
		self.data = init_data_default()

		if self.extra['current_subplot'] == 'T-t relation':
			self.data['type'] = self.key + '_T'	
			self.data['feature_name'] = 'temperature'
		elif self.extra['current_subplot'] == 'heat release':
			self.data['type'] = self.key + '_Qdot'	
			self.data['feature_name'] = 'heat release'
		elif self.extra['current_subplot'] == 'T-x relation':
			self.data['type'] = self.key + '_T'	
			self.data['feature_name'] = 'temperature'
		elif self.extra['current_subplot'] == 'ignition delay':
			self.data['type'] = self.key + '_tau-ign'
			self.data['feature_name'] = 'ignition delay'
		elif self.extra['current_subplot'] == 'PSR temperature':
			self.data['type'] = self.key + '_psr-T'
			self.data['feature_name'] = 'PSR temperature'
			


		self.data['name'] = self.new_name(self.data['type'], self.occupied)
		self.data['phi'] = ''
		self.data['norm'] = False


	def init(self):
		self.ui_name = 'subplot_single.ui'
		self.key = self.extra['subkey']
		self.init_ui()
		self.occupied = self.init_occupied()
		self.init_data()

		# set connection ====================

		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)
		self.w.btn_adv.clicked.connect(self.act_adv_helper)

		# set obj IO ==============================

		self.w_cbs = dict()
		self.w_cbs['obj'] = [self.w.cb_phi]
		self.w_cbs['key'] = ['phi']
		self.w_cbs['name'] = ['equiv. ratio']
		db = self.parent.project['database'][self.extra['db']['db_name']]
		self.w_cbs['items'] = [[str(v) for v in db['phi']]]

		# set ui obj ==============================

		self.set_name()
		self.set_cb()

		# exec ==============================

		self.readers = [self.read_name, self.read_cb]
		if self.w.exec_() == QDialog.Rejected:
			self.data = None















""" >>>>>>>>>>>>>------------------------------------------------
1.1.2 dialog_plot_sp
     called by: dialog_plot_builder
                  



                                    oo                   
                                                         
.d8888b. 88d888b. .d8888b. .d8888b. dP .d8888b. .d8888b. 
Y8ooooo. 88'  `88 88ooood8 88'  `"" 88 88ooood8 Y8ooooo. 
      88 88.  .88 88.  ... 88.  ... 88 88.  ...       88 
`88888P' 88Y888P' `88888P' `88888P' dP `88888P' `88888P' 
         88                                              
         dP                                              


                               
"""


class dialog_plot_sp(base_dialog):


	def act_add_sp(self):
		self.read_txt(pop_msg=False)
		sp = self.w.cb_sp.currentText()
		if sp not in self.data['sp']:
			self.data['sp'].append(sp)
			self.set_txt()


	def act_adv_helper(self): act_adv(self)



	def init_data_default(self):
		self.data = init_data_default()
		self.data['sp'] = []
		self.data['type'] = self.key + '_sp'
		self.data['name'] = self.new_name(self.data['type'], self.occupied)
		self.data['phi'] = ''
		#self.data['norm'] = False
		self.data['task'] = 'mole fraction'
		self.data['feature_name'] = 'species'

		
	
	def init(self):
		self.ui_name = 'subplot_sp.ui'
		self.key = self.extra['subkey']
		self.init_ui()
		self.occupied = self.init_occupied()
		self.init_data()

		self.sp_list = self.parent.soln['detailed'].species_names		

		# set connection ====================

		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)
		self.w.btn_add_sp.clicked.connect(self.act_add_sp)
		self.w.btn_adv.clicked.connect(self.act_adv_helper)

		# set obj IO ==============================


		self.w_txts = dict()
		self.w_txts['obj'] = [self.w.txt_sp]
		self.w_txts['key'] = ['sp']
		self.w_txts['name'] = ['species list']
		self.w_txts['vali'] = [self.is_sp]
		self.w_txts['empty'] = [False]
		self.w_txts['len'] = [None]


		self.w_cbs = dict()
		self.w_cbs['obj'] = [self.w.cb_phi, self.w.cb_task]
		self.w_cbs['key'] = ['phi','task']
		self.w_cbs['name'] = ['equiv. ratio','task']
		db = self.parent.project['database'][self.extra['db']['db_name']]
		self.w_cbs['items'] = [
			[str(v) for v in db['phi']],
			['mole fraction','net ROP']
			]

		# set ui obj ==============================

		self.set_name()
		self.set_txt()
		self.set_cb()

		for sp in self.sp_list:
			self.w.cb_sp.addItem(sp)


		# exec ==============================

		self.readers = [self.read_name, self.read_txt, self.read_cb]
		if self.w.exec_() == QDialog.Rejected:
			self.data = None


























class dialog_GP_alias(base_dialog):

	def act_save(self):

		alias = str(self.w.txt_alias.text())
		if bool(alias) == False:
			msg = 'alias is empty!'
			QMessageBox.information(QWidget(),'',msg)
			return None

		if (alias in self.occupied) and (alias != self.old_alias):
			msg = 'alias "' + alias + '" already occupied or not allowed, \nplease rename'
			QMessageBox.information(QWidget(),'',msg)
			return None

		self.data['alias'] = alias
		self.w.accept()



	def init(self):

		self.ui_name = 'GP_alias.ui'
		self.key = 'GP_' + self.extra['traced']
		self.init_ui()

		print 'self.key = '+str(self.key)

		self.occupied = []
		for GP_name in self.parent.project[self.key].keys():
			GP = self.parent.project[self.key][GP_name]
			alias = GP['alias']
			self.occupied.append(alias)
			if GP_name == self.old_name:
				self.old_alias = alias
				self.data = copy.copy(GP)

		# set connection ====================

		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)

		# set ui obj ==============================

		self.w.txt_name.setText(self.data['name'])
		self.w.txt_alias.setText(self.data['alias'])

		# exec ==============================

		if self.w.exec_() == QDialog.Rejected:
			self.data = None





def find_GP_order(dir_raw, traced, parent, sample, method='D_GP'):


	path_raw = os.path.join(dir_raw,'raw.npz')
	raw = load_raw(path_raw)

	if sample['by'] != 'max':
		i_plot = find_i_plot(sample['at'], raw, sample_by=sample['by'])

	GP_traced = parent.project['GP_'+traced]
	list_GP_name = []
	list_GP_source = []
	list_GP_target = []
	list_GP_cc = []
	list_GP_nan = []

	any_available = False
	for GP_name in GP_traced.keys():
		GP_dir = GP_traced[GP_name]
		GP_alias = GP_dir['alias']
		member = GP_dir['member']
		cc = load_GPSA(dir_raw, GP_dir, method)
		if cc is None:
			c = 0
			list_GP_nan.append(True)
		else:
			any_available = True
			if sample['by'] == 'max':
				c = max(cc)
			else:
				c = cc[i_plot]
			list_GP_nan.append(False)

		list_GP_name.append(GP_name)
		list_GP_source.append(member[0])
		list_GP_target.append(member[-1])

		list_GP_cc.append(c)

	try:
		# sort by source first, then target, then cc
		ind = np.lexsort((list_GP_cc, list_GP_target, list_GP_source))
	except ValueError:
		print list_GP_cc
		print list_GP_target
		print list_GP_source
		import sys
		sys.exit()
	#print 'lexsort OK'

	if not any_available:
		msg = 'no '+traced+'-GPSA data is available for\n\n'+str(dir_raw)+\
			'\n\ntry different dataset or run GPSA first'
		QMessageBox.information(QWidget(),'',msg)




	list_GP_name_sorted = [list_GP_name[i] for i in ind]
	list_GP_nan_sorted = [list_GP_nan[i] for i in ind]

	if bool(dir_raw):
		if max(list_GP_cc)>0:
			norm = max(list_GP_cc)
		else:
			norm = 1.0			
		list_GP_cc_norm_sorted = [list_GP_cc[i]/norm for i in ind]
	else:
		list_GP_cc_norm_sorted = list_GP_cc

	return list_GP_name_sorted, list_GP_cc_norm_sorted, list_GP_nan_sorted






""" >>>>>>>>>>>>>------------------------------------------------
1.1.3 dialog_plot_GP
     called by: dialog_plot_builder
                     




         dP          dP                dP                        dP   dP       
         88          88                88                        88   88       
.d8888b. 88 .d8888b. 88d888b. .d8888b. 88    88d888b. .d8888b. d8888P 88d888b. 
88'  `88 88 88'  `88 88'  `88 88'  `88 88    88'  `88 88'  `88   88   88'  `88 
88.  .88 88 88.  .88 88.  .88 88.  .88 88    88.  .88 88.  .88   88   88    88 
`8888P88 dP `88888P' 88Y8888' `88888P8 dP    88Y888P' `88888P8   dP   dP    dP 
     .88                                     88                                
 d8888P                                      dP                                

                            
"""


class dialog_plot_GP(base_dialog):


	def set_enable(self):
		if bool(self.w.cb_phi.currentText()) and bool(self.w.cb_traced.currentText()):
			self.w.gb_GP.setEnabled(True)
		else:
			self.w.gb_GP.setEnabled(False)


		self.w.cb_fofat.clear()
		if bool(self.w.cb_phi.currentText()):
			db_name = self.extra['db']['db_name']
			db = self.parent.project['database'][db_name]
			cond = dict()
			cond['phi'] = [str(self.w.cb_phi.currentText())]
			keys = ['fuel','oxid','T0','atm']
			reactor = self.extra['db']['reactor']

			for key in keys:
				if self.extra['db'][key] == 'varying':
					cond[key] = db[key]
				else:
					cond[key] = [self.extra['db'][key]]


			self.fofat = []
			for fuel in cond['fuel']:
				for oxid in cond['oxid']:
					for phi_str in cond['phi']:
						phi = float(phi_str)
						for T0_str in cond['T0']:
							T0 = float(T0_str)
							for atm_str in cond['atm']:
								atm = float(atm_str)
								subdir_raw = cond2dir('', fuel, oxid, phi, atm, T0, reactor, self.parent.n_digit)
								subdir_raw = subdir_raw.replace('raw','').strip('\/')

								self.w.cb_fofat.addItem(subdir_raw)
								self.fofat.append(subdir_raw)

		#self.w.cb_GPS.clear()
		traced = str(self.w.cb_traced.currentText())
		if bool(traced):
			self.set_table_GP()


	def set_table_GP(self, key=None):

		dir_desk = self.parent.project['mech']['detailed']['desk']

		traced = str(self.w.cb_traced.currentText())
		if bool(traced) == False:
			return None
		GP_traced = 'GP_' + traced
		self.data['traced'] = traced
		print 'updated self.data'

		fofat = str(self.w.cb_fofat.currentText())
		if bool(fofat):
			dir_raw = os.path.join(dir_desk,'raw',fofat)
		else:
			return None

		sample = dict()
		if self.w.rbtn_max.isChecked():
			sample['by'] = 'max'
		elif self.w.rbtn_sample.isChecked():
			sample['by'] = self.w.cb_sample_by.currentText()
			try:
				sample_at =  self.w.txt_sample_at.text()
				sample['at'] = float(sample_at)
			except ValueError:
				msg = 'cannot convert '+str(sample_at)+' to a number'				
				QMessageBox.information(QWidget(),'',msg)
				return None
		else:
			return None


		method = str(self.w.cb_method.currentText())
		if not bool(method):
			method = 'D_GP'
		
		list_GP_name, list_GP_cc_norm, list_GP_nan = find_GP_order(
			dir_raw, traced, self.parent, sample, method)

		#list_GP_name = list_GP_name
		#list_GP_cc_norm = list_GP_cc_norm

		model = QStandardItemModel()
		n_row = 0
		for index in range(len(list_GP_name)):
			GP_name = list_GP_name[index]
			alias = self.parent.project[GP_traced][GP_name]['alias']
			

			Qitem = QStandardItem(alias)
			Qitem.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)

			if GP_name in self.data[GP_traced]:
				Qitem.setData(QVariant(Qt.Checked), Qt.CheckStateRole)
			else:					
				Qitem.setData(QVariant(Qt.Unchecked), Qt.CheckStateRole)
			model.setItem(n_row,0, Qitem)

			if not list_GP_nan[index]:
				n_bar = int(list_GP_cc_norm[index] * 50)
				Qitem = QStandardItem('|' * n_bar)
			else:
				Qitem = QStandardItem('NA')

			model.setItem(n_row,1, Qitem)

			n_row += 1


		self.w.table_GP.setModel(model)
		self.w.table_GP.setColumnWidth(0, 440-25)
		self.w.table_GP.setColumnWidth(1, 180)

		for i_row in range(n_row):
			self.w.table_GP.setRowHeight(i_row,20)




	def read_table_GP(self, key=None, pop_msg=True):
		model = self.w.table_GP.model()
		if model == None:
			return None

		traced = str(self.w.cb_traced.currentText())
		if bool(traced) == False:
			return False
		GP_traced = 'GP_' + traced
		self.data[GP_traced] = []

		for j in range(model.rowCount()):
			alias = str(model.item(j,0).text())

			GP_name = None
			for GP_name_i in self.parent.project[GP_traced].keys():
				if self.parent.project[GP_traced][GP_name_i]['alias'] == alias:
					GP_name = GP_name_i
					break

			if GP_name != None:
				if model.item(j,0).checkState():
					self.data[GP_traced].append(GP_name)
			else:
				print 'cannot find GP whose alias is ' + alias

		if bool(self.data[GP_traced]) == False:
			if pop_msg:
				msg = 'no global pathways selected'
				QMessageBox.information(QWidget(),'',msg)

	

	def act_rename_GP(self):

		traced = str(self.w.cb_traced.currentText())
		if bool(traced) == False:
			return None
		GP_traced = 'GP_' + traced		
		alias = self.read_item(self.w.table_GP)

		if alias == None:
			return None

		GP_name = None
		for GP_name_i in self.parent.project[GP_traced].keys():
			if self.parent.project[GP_traced][GP_name_i]['alias'] == alias:
				GP_name = GP_name_i
				break

		if GP_name == None:
			print 'cannot find GP whose alias is ' + alias
			return None

		self.read_table_GP(pop_msg=False)
		GP_new = dialog_GP_alias(parent=self.parent, data_name=GP_name, extra=self.data).data
		if GP_new is not None:
			self.parent.project[GP_traced][GP_name] = GP_new
			self.set_table_GP()



	def act_adv_helper(self): act_adv(self)




	def init_data_default(self):

		self.data = init_data_default()
		self.data['type'] = self.key + '_GP'
		self.data['name'] = self.new_name(self.data['type'], self.occupied)
		self.data['phi'] = ''
		self.data['traced'] = ''
		self.data['method'] = ''
		self.data['feature_name'] = 'global pathway'

		for e in self.parent.soln['detailed'].element_names:
			key = 'GP_' + e
			self.data[key] = []
			if key not in self.parent.project.keys():
				self.parent.project[key] = dict()


		
	
	def init(self):
		
		self.ui_name = 'subplot_GP.ui'
		self.key = self.extra['subkey']
		self.init_ui()
		self.occupied = self.init_occupied()
		self.init_data()

		# set connection ====================

		self.w.btn_adv.clicked.connect(self.act_adv_helper)
		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)
		self.w.btn_sort.clicked.connect(self.set_table_GP)

		self.w.btn_rename.clicked.connect(self.act_rename_GP)
		self.w.table_GP.doubleClicked.connect(self.act_rename_GP)

		self.w.cb_phi.currentIndexChanged.connect(self.set_enable)
		self.w.cb_traced.currentIndexChanged.connect(self.set_enable)



		# set obj IO ==============================

		self.w_cbs = dict()
		self.w_cbs['obj'] = [self.w.cb_method, self.w.cb_phi, self.w.cb_traced]
		self.w_cbs['key'] = ['method', 'phi', 'traced']
		self.w_cbs['name'] = ['GP feature', 'equiv. ratio', 'traced element']

		db = self.parent.project['database'][self.extra['db']['db_name']]

		self.w_cbs['items'] = [
			['D_GP','R_GP production','R_GP consumption','normR_GP production', 'normR_GP consumption'],#'oldD_GP','oldR_GP production','oldR_GP consumption'],
			[str(v) for v in db['phi']],
			self.parent.soln['detailed'].element_names,
			]


		# set ui obj ==============================

		self.set_name()
		self.set_cb()
		self.set_enable()


		for item in ['T (K)', 'T rised (K)','t passed (s)','normalized t']:
			self.w.cb_sample_by.addItem(item)

		# exec ==============================

		self.readers = [self.read_name, self.read_table_GP, self.read_cb]
		if self.w.exec_() == QDialog.Rejected:
			self.data = None

























class dialog_plot_node(base_dialog):


	""" >>>>>>>>>>>>>------------------------------------------------
	1.1.4 dialog_plot_GP_rxn
	     called by: dialog_plot_builder

	                        dP          
	                        88          
	88d888b. .d8888b. .d888b88 .d8888b. 
	88'  `88 88'  `88 88'  `88 88ooood8 
	88    88 88.  .88 88.  .88 88.  ... 
	dP    dP `88888P' `88888P8 `88888P' 
                                    

	"""

	def act_adv_helper(self): act_adv(self)

	def init_data_default(self):

		self.data = init_data_default()
		self.data['type'] = self.key + '_node'
		self.data['name'] = self.new_name(self.data['type'], self.occupied)
		self.data['phi'] = ''
		self.data['traced'] = ''
		self.data['node'] = ''
		self.data['n_edge'] = [4]
		self.data['feature_name'] = 'node edges'
		self.data['method'] = 'node edge flux (mole/cm3-s)'


	def init(self):

		self.ui_name = 'subplot_node.ui'
		self.key = self.extra['subkey']
		self.init_ui()
		self.occupied = self.init_occupied()
		self.init_data()

		# set connection ====================

		self.w.btn_adv.clicked.connect(self.act_adv_helper)
		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)

		# set obj IO ==============================

		self.w_txts = dict()
		self.w_txts['obj'] = [self.w.txt_nedge]
		self.w_txts['key'] = ['n_edge']
		self.w_txts['name'] = ['max. edge #']
		self.w_txts['vali'] = [self.is_pos_int]
		self.w_txts['empty'] = [False]
		self.w_txts['len'] = [1]


		self.w_cbs = dict()
		self.w_cbs['obj'] = [self.w.cb_phi, self.w.cb_traced, self.w.cb_node]
		self.w_cbs['key'] = ['phi', 'traced', 'node']
		self.w_cbs['name'] = ['equiv. ratio', 'traced element', 'node']

		
		db = self.parent.project['database'][self.extra['db']['db_name']]

		self.w_cbs['items'] = [
			[str(v) for v in db['phi']],
			self.parent.soln['detailed'].element_names,
			self.parent.soln['detailed'].species_names,
			]

		# set ui obj ==============================

		self.set_name()
		self.set_cb()
		self.set_txt()
		

		# exec ==============================

		self.readers = [self.read_name, self.read_cb, self.read_txt]
		if self.w.exec_() == QDialog.Rejected:
			self.data = None























class dialog_plot_Rrop(base_dialog):


	""" >>>>>>>>>>>>>------------------------------------------------
	1.1.4 dialog_plot_GP_rxn
	     called by: dialog_plot_builder

	                        dP oo                   dP 
	                        88                      88 
	88d888b. .d8888b. .d888b88 dP .d8888b. .d8888b. 88 
	88'  `88 88'  `88 88'  `88 88 88'  `"" 88'  `88 88 
	88       88.  .88 88.  .88 88 88.  ... 88.  .88 88 
	dP       `88888P8 `88888P8 dP `88888P' `88888P8 dP 
                                                   
	"""

	def act_adv_helper(self): act_adv(self)


	def init_data_default(self):

		self.data = init_data_default()
		self.data['type'] = self.key + '_Rrop'
		self.data['name'] = self.new_name(self.data['type'], self.occupied)
		self.data['phi'] = ''
		self.data['role'] = 'production'
		self.data['n_rxn'] = [4]
		self.data['feature_name'] = 'radical rop'
		self.data['sample_with'] = 'max'
		self.data['sample_by'] = 'T rised (K)'
		self.data['sample_at'] = [200]


	def init(self):

		self.ui_name = 'subplot_radical.ui'
		self.key = self.extra['subkey']
		self.init_ui()
		self.occupied = self.init_occupied()
		self.init_data()

		# set connection ====================

		self.w.btn_adv.clicked.connect(self.act_adv_helper)
		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)

		# set obj IO ==============================

		self.w_txts = dict()
		self.w_txts['obj'] = [self.w.txt_n_rxn, self.w.txt_sample_at]
		self.w_txts['key'] = ['n_rxn','sample_at']
		self.w_txts['name'] = ['max. reaction #','sample at']
		self.w_txts['vali'] = [self.is_pos_int, self.is_float]
		self.w_txts['empty'] = [False, True]
		self.w_txts['len'] = [1, 1]


		self.w_cbs = dict()
		self.w_cbs['obj'] = [self.w.cb_phi, self.w.cb_role, self.w.cb_sample_by]
		self.w_cbs['key'] = ['phi', 'role','sample_by']
		self.w_cbs['name'] = ['equiv. ratio', 'role','sample by']

		
		db = self.parent.project['database'][self.extra['db']['db_name']]

		self.w_cbs['items'] = [
			[str(v) for v in db['phi']],
			['production','consumption'],
			['T (K)','T rised (K)','t passed (t)','norm t passed']
			]


		self.w_rbtns = dict()
		self.w_rbtns['obj'] = [[self.w.rbtn_sample, self.w.rbtn_max]]
		self.w_rbtns['key'] = ['sample_with']
		self.w_rbtns['val'] = [['sample','max']]




		# set ui obj ==============================

		self.set_name()
		self.set_cb()
		self.set_txt()
		self.set_rbtn()
		

		# exec ==============================

		self.readers = [self.read_name, self.read_cb, self.read_txt, self.read_rbtn]
		if self.w.exec_() == QDialog.Rejected:
			self.data = None


























class dialog_plot_GPrxn(base_dialog):


	""" >>>>>>>>>>>>>------------------------------------------------
	1.1.4 dialog_plot_GP_rxn
	     called by: dialog_plot_builder





	 .88888.   888888ba                             
	d8'   `88  88    `8b                            
	88        a88aaaa8P' 88d888b. dP.  .dP 88d888b. 
	88   YP88  88        88'  `88  `8bd8'  88'  `88 
	Y8.   .88  88        88        .d88b.  88    88 
	 `88888'   dP        dP       dP'  `dP dP    dP 
	                                                
	                           

	"""

	def read_cbGP(self):
		alias = str(self.w.cb_GP.currentText())
		e = str(self.w.cb_traced.currentText())
		if bool(e) == False:
			return False

		if bool(alias) == False:
			msg = 'no global pathway selected'
			QMessageBox.information(QWidget(),'',msg)
			return False

		else:
			for GP_name in self.parent.project['GP_'+e].keys():
				GP = self.parent.project['GP_'+e][GP_name]
				if GP['alias'] == alias:
					self.data['GP'] = GP_name
					return True

			msg = 'cannot find GP whose alias is '+alias
			QMessageBox.information(QWidget(),'',msg)
			return False


	def act_traced(self):
		e = str(self.w.cb_traced.currentText())
		current_alias = ''
		if bool(e):
			items = []
			for GP_name in self.parent.project['GP_'+e].keys():
				GP = self.parent.project['GP_'+e][GP_name]
				items.append(GP['alias'])
				if GP_name == self.data['GP']:
					current_alias = GP['alias']

		else:
			items = []
		
		self.w.cb_GP.clear()
		index = 0
		current_index = 0
		self.w.cb_GP.addItem('')
		for item in items:
			self.w.cb_GP.addItem(item)
			index += 1
			if current_alias == item:
				current_index = index

		self.w.cb_GP.setCurrentIndex(current_index)


	def act_adv_helper(self): act_adv(self)

	def init_data_default(self):

		self.data = init_data_default()
		self.data['type'] = self.key + '_GPrxn'
		self.data['name'] = self.new_name(self.data['type'], self.occupied)
		self.data['phi'] = ''
		self.data['traced'] = ''
		self.data['GP'] = ''
		self.data['nrxn'] = [4]
		self.data['feature_name'] = 'reactions associated to GP'
		self.data['method'] = '' 	# will be determined in def_painter.py/find_yy
		self.data['role'] = 'production'


	def init(self):

		self.ui_name = 'subplot_GP_rxn.ui'
		self.key = self.extra['subkey']
		self.init_ui()
		self.occupied = self.init_occupied()
		self.init_data()

		# set connection ====================

		self.w.btn_adv.clicked.connect(self.act_adv_helper)
		self.w.btn_save.clicked.connect(self.act_save)
		self.w.btn_cancel.clicked.connect(self.act_cancel)
		self.w.cb_traced.currentIndexChanged.connect(self.act_traced)

		# set obj IO ==============================

		self.w_txts = dict()
		self.w_txts['obj'] = [self.w.txt_nrxn]
		self.w_txts['key'] = ['nrxn']
		self.w_txts['name'] = ['max. rxn #']
		self.w_txts['vali'] = [self.is_pos_int]
		self.w_txts['empty'] = [False]
		self.w_txts['len'] = [1]


		self.w_cbs = dict()
		self.w_cbs['obj'] = [self.w.cb_phi, self.w.cb_traced, self.w.cb_role]
		self.w_cbs['key'] = ['phi', 'traced', 'role']
		self.w_cbs['name'] = ['equiv. ratio','traced element', 'role']
		
		db = self.parent.project['database'][self.extra['db']['db_name']]
		self.w_cbs['items'] = [
			[str(v) for v in db['phi']],
			self.parent.soln['detailed'].element_names,
			['production','consumption']
			]

		# set ui obj ==============================

		self.set_name()
		self.set_cb()
		self.set_txt()
		self.act_traced()

		

		# exec ==============================

		self.readers = [self.read_name, self.read_cb, self.read_txt, self.read_cbGP]
		if self.w.exec_() == QDialog.Rejected:
			self.data = None






