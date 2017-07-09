import zipfile, os, sys
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import cantera as ct
import matplotlib.pyplot as plt


def makedirs(fld):
	if not os.path.exists(fld):
		os.makedirs(fld)



def get_sheets(filename):

	file = zipfile.ZipFile(filename, "r")
	# ref: http://stackoverflow.com/questions/38208137/processing-large-xlsx-file-in-python

	names = []
	for name in file.namelist():
		if name == 'xl/workbook.xml':
			data = BeautifulSoup(file.read(name), 'html.parser')
			sheets = data.find_all('sheet')
			for sheet in sheets:
				names.append(sheet.get('name'))
	return names


def xls2sheets(filename, preview=False):

	# if preview, return atm0, T0, u0
	# else, save each sheet as a csv

	if not preview:
		fld = os.path.join(filename.replace('.xlsx',''), 'sheets')
		makedirs(fld)

	atm0 = None
	T0 = None
	u0 = None
	sheets = get_sheets(filename)
	for sheet in sheets:
		if 'soln' in sheet:
			
			df = None
			if atm0 is None:
				df = pd.read_excel(filename,sheetname=sheet)
				for k in df.ix[0].keys():
					v = float(df.ix[0][k])
					if 'pressure' in k.lower():
						atm0 = np.round(v*1000)/1000
					elif 'temperature' in k.lower():
						T0 = v
					elif 'axial_velocity' in k.lower():
						u0 = v
			if preview:
				return	atm0, T0, u0		
			
			else:
				csv_path = os.path.join(fld, sheet+'.csv')
				if not os.path.exists(csv_path):
					print 'saving '+str(sheet)
					if df is None:
						df = pd.read_excel(filename,sheetname=sheet)
					df.to_csv(csv_path)
				else:
					print 'skipped '+str(sheet)

	return	atm0, T0, u0	



def unify(s):
	s = s.replace('Mole_fraction_','Mole fraction ')
	s = s.replace('Net_rxn_rate_GasRxn#','Net rxn rate GasRxn#')
	i = s.find('Soln')
	if i>0:
		s = s[:i].strip('_')
	return s.strip()


def csv2raw(path, x_type, raw={}, MF={}, NRR={}, ROP={}):

	data = np.genfromtxt(path, delimiter=',', skip_header=1)
	with open(path) as f:
		lines = f.readlines()
	ss = lines[0].split(',')

	for i_s in range(len(ss)):
		s = unify(ss[i_s])
		n = list(data[:,i_s])
		if x_type == s.split('_')[0].lower():
			raw['axis0'] = n
		elif 'Pressure' in s:
			raw['pressure'] = n
		elif 'Temperature' in s:
			raw['temperature'] = n
		elif 'Volume' in s.lower():
			raw['volume'] = n
		elif 'Axial velocity' in s:
			raw['speed'] = n
		elif 'Mole fraction' in s:
			k = s.replace('Mole fraction ','')
			MF[k] = n
		elif 'Net rxn rate GasRxn#' in s:
			k = s.replace('Net rxn rate GasRxn#','')
			NRR[k] = n
		elif 'ROP GasRxn#' in s:
			sp = s.split(' ')[0]
			if sp not in ROP.keys():
				ROP[sp] = dict()
			rxn = s.replace(sp+' '+'ROP GasRxn#','').split('_')[0]
			ROP[sp][rxn] = n

	return raw, MF, NRR, ROP







def sheets2raw(filename, x_type, soln):

	sp_list = soln.species_names
	n_rxn = soln.n_reactions

	x_type = x_type.lower()

	fld_sheets = os.path.join(filename.replace('.xlsx',''), 'sheets')
	dir_csv = os.path.join(filename.replace('.xlsx',''))
	makedirs(dir_csv)

	raw = dict()
	raw['axis0'] = []
	raw['axis0_type'] = x_type	# 'distance', or 'time', etc
	raw['pressure'] = []
	raw['temperature'] = []
	raw['volume'] = []
	raw['mole_fraction'] = []
	raw['net_reaction_rate'] = []
	raw['speed'] = []

	MF = dict()
	NRR = dict()

	for sheet in os.listdir(fld_sheets):
		print 'reading '+sheet
		if sheet.endswith('.csv'):
			path = os.path.join(fld_sheets,sheet)
			raw, MF, NRR, trash = csv2raw(raw, x_type, MF, NRR)


	if len(raw['volume'])==0:
		raw['volume'] = [1.0]*len(raw['axis0'])

	raw['mole'] = []
	R = 8314
	for i in range(len(raw['axis0'])):
		# pV = n R T
		raw['mole'].append(raw['pressure'][i] * ct.one_atm * raw['volume'][i] / R / raw['temperature'][i])


	for i in range(len(raw['axis0'])):
		mf = []
		for sp in sp_list:
			if sp not in MF.keys():
				mf.append(0)
			else:
				mf.append(MF[sp][i])
		raw['mole_fraction'].append(mf)

		nrr = []
		# note in Chemkin, rxn_id starts from 1, not 0
		for k in range(1, n_rxn+1):
			k = str(k)
			if k not in NRR.keys():
				nrr.append(0)
			else:
				nrr.append(NRR[k][i])
		raw['net_reaction_rate'].append(nrr)

	return raw
			



def compress_raw(raw):
	x = raw['axis0']
	T = raw['temperature']
	n = len(x)

	i_ign = n-1
	for i in range(n):
		if T[i] >= T[0] + 400:
			i_ign = i
			break
	dx = 1.0*x[i_ign]/10

	ii = [0]
	for i in range(1, n):
		if x[i]-x[ii[-1]] >= dx or T[i]-T[ii[-1]]>50:
			ii.append(i)


	raw_c = dict()
	for k in raw.keys():
		if k in ['net_reaction_rate','mole_fraction']:
			M = [np.matrix(raw[k])[i,:].tolist()[0] for i in ii]
			raw_c[k] = np.matrix(M)
		elif k == 'axis0_type':
			raw_c[k] = str(raw[k])
		else:
			try:
				raw_c[k] = [raw[k][i] for i in ii]
			except IndexError:
				print 'got IndexError for '+str(k)
				raw_c[k] = raw[k]
				pass
	return raw_c



	"""
	print 'before compression: '+str(n)+' points'
	print 'after compression: '+str(len(ii))+' points'

	plt.plot(x, T, marker='.')
	plt.plot([x[i] for i in ii], [T[i] for i in ii], marker='o', fillstyle='none')
	plt.show()
	"""


if __name__ == '__main__':
	#print xls2sheets('N2_hi_soln1.xlsx', True)

	print unify('Mole_fraction_H2_Soln#1_()')
