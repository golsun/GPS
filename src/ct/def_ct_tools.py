
import cantera as ct
import numpy as np
import matplotlib.pyplot as plt
import os


def estimate_tau0(T0, atm):

	T0_fit = np.array([600,1000])
	tau0_fit = np.array([5,0.1])
	x = 1000.0/T0_fit
	y = 1.0*np.log10(tau0_fit)
	coeff_low = np.polyfit(x,y,1)

	T0_fit = np.array([1000,1600])
	tau0_fit = np.array([0.1,1e-4])
	x = 1000.0/T0_fit
	y = 1.0*np.log10(tau0_fit)
	coeff_high = np.polyfit(x,y,1)

	atm_fit = 1.0*np.array([1, 10, 20])
	mtp_fit = 1.0*np.array([1, 0.1, 0.02])
	x = np.sqrt(atm_fit)
	y = np.log10(mtp_fit)
	coeff_p = np.polyfit(x,y,1)

	if T0 < 1000:
		tau_1atm = (10 ** np.polyval(coeff_low, 1000.0/T0))
	else:
		tau_1atm = (10 ** np.polyval(coeff_high, 1000.0/T0))

	mtp = 10 ** np.polyval(coeff_p, np.sqrt(atm))

	tau = tau_1atm * mtp
	#print 'tau = '+str(tau)
	tau_level = 10 ** (np.floor(np.log10(tau)))
	#print 'tau_level = '+str(tau_level)
	tau_rounded = tau_level * np.round(tau/tau_level * 1.0)/1.0
	#print 'tau_rounded = '+str(tau_rounded)
	#print tau_level
	#print str(tau_rounded)

	#print tau_rounded
	tau_rounded = max(1e-2, tau_rounded)
	return float(str(tau_rounded))


def test_est_tau0():

	atm_list = [20]# [1,10,20]
	T0_list = [900]#[600, 800, 1000, 1200, 1400, 1600]
	marker = ['o','x','+']
	for i_atm in range(len(atm_list)):
		atm = atm_list[i_atm]
		tau = []
		for T0 in T0_list:
			tau.append(estimate_tau0(T0, atm))
		#plt.semilogy(1000.0/np.array(T0_list), tau, label=str(atm)+'atm', marker=marker[i_atm],fillstyle='none')
		print tau

	plt.legend(loc='lower right')
	plt.savefig('est_tau.jpg')



""" --------------------------------- """

def Xstr(gas, fuel_dict, phi, oxid_dict):


	mech = gas#ct.Solution(mech_file)
	element = mech.element_names
	species = mech.species
	reaction = mech.reaction

	C_fuel = 0
	H_fuel = 0
	O_fuel = 0
	O_oxid = 0

	Xstr = ''
	for fuel_sp in fuel_dict.keys():
		val = fuel_dict[fuel_sp]
		Xstr += (fuel_sp + ':' + str(1.0*val*phi) + ', ')
		atoms = species(fuel_sp).composition
		if 'C' in atoms.keys():
			C_fuel = C_fuel + atoms['C'] * val
		if 'c' in atoms.keys():
			C_fuel = C_fuel + atoms['c'] * val
		if 'H' in atoms.keys():
			H_fuel = H_fuel + atoms['H'] * val
		if 'h' in atoms.keys():
			H_fuel = H_fuel + atoms['h'] * val
		if 'O' in atoms.keys():
			O_fuel = O_fuel + atoms['O'] * val
		if 'o' in atoms.keys():
			O_fuel = O_fuel + atoms['o'] * val


	for oxid_sp in oxid_dict.keys():
		val = oxid_dict[oxid_sp]
		atoms = species(oxid_sp).composition
		if 'O' in atoms.keys():
			O_oxid = O_oxid + atoms['O'] * val
		if 'o' in atoms.keys():
			O_oxid = O_oxid + atoms['o'] * val


	O_stoic = C_fuel * 2.0 + H_fuel / 2.0 - O_fuel
	n_oxid = O_stoic / O_oxid

	for oxid_sp in oxid_dict.keys():
		val = oxid_dict[oxid_sp]
		Xstr += (oxid_sp + ':' + str(n_oxid*val) + ', ')

	Xstr = Xstr[:-2]
	return Xstr



def test_Xstr():
	mech = 'gri30.xml'
	fuel_dict = {'CH4':1.0}
	phi = 2.0
	print Xstr(mech, fuel_dict, phi)

""" --------------------------------- """


def load_raw(path_raw):
    raw_file = np.load(open(path_raw, 'rb'))
    raw = dict()
    for key in raw_file.keys():
        if key in ['mole_fraction','net_reaction_rate']:
            raw[key] = np.matrix(raw_file[key])
        else:
            raw[key] = raw_file[key]
    return raw
    

def save_raw_npz(raw0, path_raw):

	raw = dict()
	for key in raw0.keys():
		if key in ['net_reaction_rate','mole_fraction','mass_fraction']:
			raw[key] = np.matrix(raw0[key])
		else:
			raw[key] = raw0[key]

	if path_raw is not None:
		np.savez(path_raw, **raw)


		"""

		if raw['axis0_type'] == 'distance':
			np.savez(path_raw,
				axis0=raw['axis0'], axis0_type=str(raw['axis0_type']),
				pressure=raw['pressure'], temperature=raw['temperature'], volume=raw['volume'],
				mole_fraction=raw['mole_fraction'],speed=raw['speed'],
				mole=raw['mole'],
				net_reaction_rate=raw['net_reaction_rate'])

		elif raw['axis0_type'] == 'time':
			np.savez(path_raw,
				axis0=raw['axis0'], axis0_type=str(raw['axis0_type']),
				pressure=raw['pressure'], temperature=raw['temperature'], volume=raw['volume'],
				mole_fraction=raw['mole_fraction'], mole=raw['mole'],
				net_reaction_rate=raw['net_reaction_rate'])
		else:
			np.savez(path_raw,
				axis0=raw['axis0'], axis0_type=str(raw['axis0_type']),
				pressure=raw['pressure'], temperature=raw['temperature'], 
				mole_fraction=raw['mole_fraction']
				net_reaction_rate=raw['net_reaction_rate'])
				"""


	return raw


def save_raw_csv(raw, soln, dir_csv):
	np.savetxt(os.path.join(dir_csv,str(raw['axis0_type'])+'.csv'), raw['axis0'])
	np.savetxt(os.path.join(dir_csv,'pressure.csv'), raw['pressure'])
	np.savetxt(os.path.join(dir_csv,'temperature.csv'), raw['temperature'])
	np.savetxt(os.path.join(dir_csv,'mole_fraction.csv'), raw['mole_fraction'], delimiter=',')
	np.savetxt(os.path.join(dir_csv,'net_reaction_rate.csv'), raw['net_reaction_rate'], delimiter=',')
	if 'speed' in raw.keys():
		np.savetxt(os.path.join(dir_csv,'speed.csv'), raw['speed'], delimiter=',')

	f = open(os.path.join(dir_csv,'species_list.csv'),'w')
	for sp in soln.species_names:
		f.write(sp+'\n')
	f.close()

	f = open(os.path.join(dir_csv,'reaction_list.csv'),'w')
	for rxn in soln.reaction_equations():
		f.write(rxn+'\n')
	f.close()





def slice_raw(raw_all, ii):
	
	tt = [raw_all['axis0'][i] for i in ii]
	TT = [raw_all['temperature'][i] for i in ii]
	pp = [raw_all['pressure'][i] for i in ii]
	vv = [raw_all['volume'][i] for i in ii]
	mm = [raw_all['mole'][i] for i in ii]
	mf = [raw_all['mole_fraction'][i] for i in ii]
	rr = [raw_all['net_reaction_rate'][i] for i in ii]
	qq = [raw_all['heat_release_rate'][i] for i in ii]

	if 'speed' in raw_all.keys():
		uu = [raw_all['speed'][i] for i in ii]

	jj = np.argsort(tt)
	raw = dict()
	raw['axis0_type'] = str(raw_all['axis0_type'])
	raw['axis0'] = [tt[j] for j in jj]
	raw['temperature'] = [TT[j] for j in jj]
	raw['pressure'] = [pp[j] for j in jj]
	raw['volume'] = [vv[j] for j in jj]
	raw['mole_fraction'] = [mf[j] for j in jj]
	raw['net_reaction_rate'] = [rr[j] for j in jj]
	raw['heat_release_rate'] = [qq[j] for j in jj]
	raw['mole'] = [mm[j] for j in jj]

	if 'speed' in raw_all.keys():
		raw['speed'] = [uu[j] for j in jj]


	return raw


def soln2raw(xx, x_type, soln, raw):

	if raw is None:

		raw = dict()
		raw['axis0'] = []
		raw['axis0_type'] = str(x_type)
		raw['pressure'] = []
		raw['temperature'] = []
		raw['volume'] = []
		raw['mole_fraction'] = []
		raw['net_reaction_rate'] = []
		raw['mole'] = []
		raw['heat_release_rate'] = []

	raw['axis0'].append(xx)
	raw['pressure'].append(soln.P)
	raw['temperature'].append(soln.T)

	S,V = soln.SV 
	raw['volume'].append(V)

	V_mole = soln.volume_mole
	mole = V / V_mole * 1e3
	raw['mole'].append(mole)

	mf = soln.concentrations / sum(soln.concentrations)
	raw['mole_fraction'].append(mf)
	#print sum(mf)

	raw['net_reaction_rate'].append(soln.net_rates_of_progress * 1e3)	# original unit is kmole/m3-s
	raw['heat_release_rate'].append(-sum(soln.delta_enthalpy * soln.net_rates_of_progress))	# J/m3-s

	return raw

if __name__ == '__main__':
	#test_Xstr()
	test_est_tau0()
