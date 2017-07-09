import sys
import os
import cantera as ct
import json
import time
import copy

from PyQt4 import uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

from src.core.def_tools import keys_sorted




# w_txts:  obj, key, name, vali, empty, len
# w_lists: obj, key, name
# w_cbs:   obj, key, name, items
# sub:     obj, key, name, dialog, viewer, reader, single


class common(object):

	def read_name(self, name0=None, save=True, occupied0=None):

		if name0 == None:
			name = str(self.w.txt_name.text())
		else:
			name = name0

		if occupied0 == None:
			occupied = self.occupied
		else:
			occupied = occupied0

		# ==============================================	

		if bool(name) == False:
			msg = 'name is empty!'
			QMessageBox.information(QWidget(),'',msg)
			return False

		if save and (name == self.old_name):
			pass

		elif (name.lower().strip().strip('[]') in occupied):
			msg = 'name "' + name + '" already occupied or not allowed, \nplease rename'
			QMessageBox.information(QWidget(),'',msg)
			return False

		for c in self.parent.chr_not_allowed:
			if c in name:
				msg = 'name can not include the following characters:\n' +\
					str(self.parent.chr_not_allowed).replace(chr(39),'').strip('[]')
				QMessageBox.information(QWidget(),'',msg)
				return False

		if save:
			self.data['name'] = name
		return True



	def init_occupied(self, key=None):
		if key == None:
			key = self.key
		occupied = self.parent.project[key].keys() + \
			['default','current','detailed','none','true','false','new','no filter']
		return [o.lower().strip().strip('[]') for o in occupied]




	def new_name(self, name0, occupied):
		copy_id = 0
		while True:
			name = name0 + '_' + str(copy_id)
			if name.lower().strip().strip('[]') not in occupied:
				return name
			else:
				copy_id += 1


	def act_cancel(self):
		self.w.reject()




	def read_item(self, obj):
		try:
			j = obj.currentIndex().row()
		except AttributeError:
			return str(obj.currentText())

		if j<0:
			return None
		try:
			return str(obj.model().item(j).text())	
		finally:
			return str(obj.model().item(j,0).text())	


	def is_any(self, s): return s,''


	def is_pos_float(self, s):
		try:
			n = float(s)
		except ValueError:
			return None,''

		if n<=0:
			return None,''
		else:
			return n,''

	def is_float(self, s):
		try:
			n = float(s)
		except ValueError:
			return None,''
		return n,''


	def is_sp(self, s):
		if s in self.sp_list + ['radical']:
			return s,''
		else:
			return None, 'should be a species name'


	def is_ls(self, s):
		if s in self.ls_list:
			return s,''
		else:
			return None, 'should in '+str(self.ls_list)


	
	def is_0to1(self, s):
		try:
			n = float(s)
		except ValueError:
			return None,''

		if n<=0 or n>=1:
			return None,'allowed range is (0.0, 1.0)'
		else:
			return n,''


	def is_pos_int(self, s):
		try:
			n = float(s)
		except ValueError:
			return None,''

		if n<=0 or int(n) != n:
			return None,'should be positive integer'
		else:
			return n,''










class base_dialog(common):


	# set =================================

	def set_name(self):
		self.w.txt_name.setText(self.data['name'])



	def set_txt(self):

		for i_txt in range(len(self.w_txts['obj'])):
			obj = self.w_txts['obj'][i_txt]
			key = self.w_txts['key'][i_txt]
			vals = [str(val) for val in self.data[key]]
			obj.setText(', '.join(vals))
		self.parent.app.processEvents()



	def set_list(self):



		for i_list in range(len(self.w_lists['obj'])):
			obj = self.w_lists['obj'][i_list]
			key = self.w_lists['key'][i_list]
			model = QStandardItemModel()

			if key not in self.data.keys():
				continue

			items_checked = self.data[key]
			items_unchecked = []
			for item in self.parent.project[key].keys():
				if item not in self.data[key]:
					items_unchecked.append(item)

			if self.sort_list:
				items = sorted(items_checked) + sorted(items_unchecked)
			else:
				items = items_checked + items_unchecked

			for item in items:
				Qitem = QStandardItem(item)
				Qitem.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled | Qt.ItemIsSelectable)

				if item in self.data[key]:
					Qitem.setData(QVariant(Qt.Checked), Qt.CheckStateRole)
				else:
					Qitem.setData(QVariant(Qt.Unchecked), Qt.CheckStateRole)

				model.appendRow(Qitem)
			obj.setModel(model)
		self.parent.app.processEvents()



	def set_cb(self, which='all'):

		# only refresh the obj specified in which
		# otherwise if you may enter deadlock if use currentIndexChanged with set_cb

		if which == 'all':
			which = range(len(self.w_cbs['obj']))

		for i_cb in which:
			obj = self.w_cbs['obj'][i_cb]
			key = self.w_cbs['key'][i_cb]
			items = [''] + self.w_cbs['items'][i_cb]
			index = 0

			obj.clear()
			current_index = 0
			for item in items:
				obj.addItem(item)
				if item == self.data[key]:
					current_index = index
				index += 1

			obj.setCurrentIndex(current_index)

			all_items = [str(obj.itemText(i)) for i in range(obj.count())]

		self.parent.app.processEvents()

			

	def set_rbtn(self):
		for i_rbtn in range(len(self.w_rbtns['obj'])):
			obj = self.w_rbtns['obj'][i_rbtn]
			key = self.w_rbtns['key'][i_rbtn]
			val = self.w_rbtns['val'][i_rbtn]
			try:
				index = val.index(self.data[key])
			except ValueError:
				print 'cannot find, '+str(self.data[key])+', in, '+str(val)+'!'*10
				index = 0

			obj[index].setChecked(True)


	def set_ck(self):
		for i_ck in range(len(self.w_cks['obj'])):
			obj = self.w_cks['obj'][i_ck]
			key = self.w_cks['key'][i_ck]
			obj.setChecked(self.data[key])


	# get =================================



	def read_txt(self, pop_msg=True):

		for i_txt in range(len(self.w_txts['obj'])):
			obj = self.w_txts['obj'][i_txt]
			key = self.w_txts['key'][i_txt]
			name = self.w_txts['name'][i_txt]
			vali = self.w_txts['vali'][i_txt]
			empty = self.w_txts['empty'][i_txt]
			length = self.w_txts['len'][i_txt]
			if 'split' in self.w_txts.keys():
				split = self.w_txts['split']
			else:
				split = True

			if split:
				ss = obj.text().split(',')
			else:
				ss = obj.text()

			vv = []
			if len(ss):
				for Qs in ss:
					s = str(Qs).strip()
					if bool(s):
						v, err_msg = vali(s)
						if v != None:
							vv.append(v)
						else:
							if pop_msg:
								msg = '"' + s + '" is not a valid input for ' + name +\
									'\n' + err_msg
								QMessageBox.information(QWidget(),'',msg)
							return False

			if not empty:
				if bool(vv) == False:
					if pop_msg:
						msg = 'no value provided for ' + name
						QMessageBox.information(QWidget(),'',msg)
					return False

				if length != None:
					if len(vv) < length:
						if pop_msg:
							msg = str(length) + ' value(s) should be provided for ' + name + \
								',\n now ' + str(len(vv)) + ' value(s) provided'
							QMessageBox.information(QWidget(),'',msg)
						return False
					if len(vv) > length and pop_msg:
						msg = 'only '+str(length) + 'values should be provided for '+ name
						QMessageBox.information(QWidget(),'',msg)
						return False

			self.data[key] = vv

		return True




	def read_list(self, pop_msg=True):

		for i_list in range(len(self.w_lists['obj'])):
			model = self.w_lists['obj'][i_list].model()
			key = self.w_lists['key'][i_list]
			name = self.w_lists['name'][i_list]
			self.data[key] = []

			for j in range(model.rowCount()):
				item = str(model.item(j).text())	
				if model.item(j).checkState():
					self.data[key].append(item)

			if bool(self.data[key]) == False:
				if pop_msg:
					msg = 'no '+ name + ' is selected/provided'
					QMessageBox.information(QWidget(),'',msg)
				return False

		return True



	def read_cb(self, pop_msg=True):

		for i_cb in range(len(self.w_cbs['obj'])):

			obj = self.w_cbs['obj'][i_cb]
			key = self.w_cbs['key'][i_cb]
			name = self.w_cbs['name'][i_cb]
			item = str(obj.currentText())

			if 'empty' not in self.w_cbs.keys():
				empty = False
			else:
				empty = self.w_cbs['empty'][i_cb]

			if empty:
				self.data[key] = item
			else:
				if bool(item):
					self.data[key] = item
				else:
					if pop_msg:
						msg = 'no ' + name + ' is selected'
						QMessageBox.information(QWidget(),'',msg)
					return False

		return True



	def read_rbtn(self):
		for i_rbtn in range(len(self.w_rbtns['obj'])):
			obj = self.w_rbtns['obj'][i_rbtn]
			key = self.w_rbtns['key'][i_rbtn]
			val = self.w_rbtns['val'][i_rbtn]
			for i in range(len(obj)):
				if obj[i].isChecked():
					self.data[key] = val[i]
					break


	def read_ck(self):
		for i_ck in range(len(self.w_cks['obj'])):
			obj = self.w_cks['obj'][i_ck]
			key = self.w_cks['key'][i_ck]
			self.data[key] = obj.isChecked()




	# act =================================


	def act_add(self, key):

		i_sub = self.sub['key'].index(key)
		dialog = self.sub['dialog'][i_sub]
		viewer = self.sub['viewer'][i_sub]
		reader = self.sub['reader'][i_sub]
		single = self.sub['single'][i_sub]
		
		reader(pop_msg=False)
		sub_data = dialog(parent=self.parent, data_name=None, extra=self.data).data

		if sub_data is not None:
			self.parent.project[key][sub_data['name']] = sub_data
			if single:
				self.data[key] = sub_data['name']
			else:
				self.data[key].append(sub_data['name'])
			viewer()




	def act_edit(self, key):

		i_sub = self.sub['key'].index(key)
		obj = self.sub['obj'][i_sub]
		dialog = self.sub['dialog'][i_sub]
		viewer = self.sub['viewer'][i_sub]
		reader = self.sub['reader'][i_sub]
		
		sub_data_name = self.read_item(obj)
		if sub_data_name == None:
			return None

		reader(pop_msg=False)
		sub_data = dialog(parent=self.parent, data_name=sub_data_name, extra=self.data).data
		if sub_data is not None:

			del self.parent.project[key][sub_data_name]
			self.parent.project[key][sub_data['name']] = sub_data

			# if renamed
			if sub_data_name != sub_data['name']:

				self_keys = [self.key]
				if key == 'mech':
					self_keys.append(['plot_ign_state','plot_ign_evolve'])

				for self_key in self_keys:				
					for data_name in self.parent.project[self_key].keys():
						data = self.parent.project[self_key][data_name]
						if sub_data_name in data[key]:
							index = data[key].index(sub_data_name)
							data[key][index] = sub_data['name']

				data = self.data
				if sub_data_name in data[key]:
					index = data[key].index(sub_data_name)
					data[key][index] = sub_data['name']

			viewer()





	def act_del(self, key):

		i_sub = self.sub['key'].index(key)
		obj = self.sub['obj'][i_sub]
		viewer = self.sub['viewer'][i_sub]
		reader = self.sub['reader'][i_sub]
		
		reader(pop_msg=False)
		sub_data_name = self.read_item(obj)
		if sub_data_name == None:
			return None

		used_by_any = []

		self_keys = [self.key]
		if key == 'mech':
			self_keys.append(['plot_ign','plot_fat','plot_psr','plot_sz'])

		for self_key in self_keys:					
			for data_name in self.parent.project[self_key].keys():
				data = self.parent.project[self_key][data_name]
				if sub_data_name in data[key]:
					if data_name == self.old_name:
						used_by_any.append('current')
					else:
						used_by_any.append(data_name)


		if bool(used_by_any) == False:
			msg = 'are you sure to delete ' + sub_data_name + '?'
			Qanswer = QMessageBox.question(QWidget(),'',msg, \
				QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

			if Qanswer == QMessageBox.Yes:
				del self.parent.project[key][sub_data_name]
				if key == 'mech':
					if sub_data_name in self.parent.soln.keys():
						del self.parent.soln[sub_data_name]
						del self.parent.soln_in[sub_data_name]

				viewer()

		else:
			msg = 'can not delete '+ sub_data_name + \
				' because it is used by the followings: \n\n'
			for data_name in used_by_any:
				msg += ('    ' + data_name + '\n')

			msg += '\nto delete, please save the above without selecting ' + sub_data_name
			QMessageBox.information(QWidget(),'',msg)





	def act_save(self):
		for reader in self.readers:
			if reader() == False:
				return None

		self.w.accept() 






	# init =================================

	def init_ui(self):
		self.w = uic.loadUi(os.path.join(self.parent.dir_ui, self.ui_name))
		self.w.setFixedSize(self.w.width(), self.w.height())	



	def init_data(self):
		if self.old_name is None:
			self.init_data_default()
		else:
			self.data = copy.copy(self.parent.project[self.key][self.old_name])



	def __init__(self, parent, data_name=None, key=None, extra=None):

		self.parent = parent
		self.extra = extra
		self.old_name = data_name
		if key is not None:
			self.key = key
		self.extra = extra
		self.sort_list = True
		self.init()		

		# exec and return =============================

		#if self.w.exec_() == QDialog.Rejected:
		#	self.data = None


