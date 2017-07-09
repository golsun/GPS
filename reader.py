import pandas as pd
import os
import cantera as ct
import numpy as np
from src.ct.def_ct_tools import load_raw
import matplotlib.pyplot as plt
from DNS_plot import find_fld_prj, makedirs


def find_sp_str(soln, fraction, crit=1e-20):
	ss = []
	for sp_id in xrange(soln.n_species):
		if fraction[sp_id] > crit:
			ss.append(soln.species_names[sp_id]+':'+str(fraction[sp_id]))
	return ','.join(ss)



def chemkin_to_raw(path_csv, path_npz, soln):
	""" convert Chemkin output file (.csv) to raw file (.npz) """
	df = pd.read_csv(path_csv, delimiter=',')

	basics = {
		"Distance (cm)": ("axis0", 0.01),
		"Net_heat_production_from_gas-phase_reactions (erg/cm3-sec)": ("heat_release_rate", 0.1),
		"Pressure (atm)": ("pressure", ct.one_atm),
		"Temperature (K)": ("temperature", 1.0),
		"Mixture_fraction ()": ("mixture fraction", 1.0),
		}

	n_pnt = len(df.index)

	raw = dict()
	raw["mole_fraction"] = np.zeros((n_pnt, soln.n_species))

	for k in df.columns:
		if k in basics:
			new_k, multi = basics[k]
			raw[new_k] = (df[k]*multi).tolist()

		elif "Mole_fraction_" in k:
			sp = k.split(' ')[0].replace("Mole_fraction_","")
			i_sp = soln.species_index(sp)
			for i in range(n_pnt):
				raw["mole_fraction"][i, i_sp] = df[k][i]

	raw["net_reaction_rate"] = []
	for i_pnt in range(n_pnt):
		X = find_sp_str(soln, [raw['mole_fraction'][i_pnt, i] for i in xrange(soln.n_species)])
		T = raw['temperature'][i_pnt]
		P = raw['pressure'][i_pnt]
		soln.TPX = T, P, X
		raw['net_reaction_rate'].append(soln.net_rates_of_progress * 1e3)

	np.savez(path_npz, **raw)



def plot_raw():

	fld_prj = find_fld_prj(mech)
	d = "0.142"
	case = "U69_d"+d+"cm"
	fld_raw = os.path.join(fld_prj, "detailed", 
		"raw", "[syngas] + [air]", "DNS", "phi1.0_1.0atm_500.0K", case)
	path_npz = os.path.join(fld_raw, "raw.npz")
	raw = load_raw(path_npz)

	#plt.plot(raw["axis0"], raw["temperature"])
	plt.plot(raw["axis0"], raw["mole_fraction"][:, 0])
	plt.show()


def convert_OppDiff():

	fld_prj = find_fld_prj(mech)
	cti = os.path.join(fld_prj,'detailed','mech','chem.cti')
	soln = ct.Solution(cti)
	#print soln.species_names
	#raise ValueError



	for d in ["0.1", "0.142", "0.9"]:
		case = "U69_d"+d+"cm"
		path_csv = os.path.join(fld_prj, "OppDiff", case+".csv")
		fld_raw = os.path.join(fld_prj, "detailed", 
			"raw", "[syngas] + [air]", "DNS", "phi1.0_1.0atm_500.0K", "OppDiff_"+case)
		makedirs(fld_raw)
		path_npz = os.path.join(fld_raw, "raw.npz")

		print 'converting '+case
		chemkin_to_raw(path_csv, path_npz, soln)


if __name__ == '__main__':

	mech = 'GRI'
	#plot_raw()
	convert_OppDiff()


