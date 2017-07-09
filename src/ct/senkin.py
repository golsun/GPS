import cantera as ct
import numpy as np
import matplotlib.pyplot as plt
from def_ct_tools import *
import copy
import os
import time






def senkin(soln, atm, T0, X0, if_half=True, dir_raw=None, if_fine=False):

	print 'if_half = '+str(if_half)

	#if soln.n_species > 100:
	#    verbose=True
	#else:
	#    verbose=False

	dT_ign = 400

   # if_half=True

	verbose=True

	cpu0 = time.time()

	print '>'*30
	print 'senkin for ['+ X0 + '] at '+ str(atm)+'atm' + ' and '+str(T0)+'K'
	print '<'*30
	
	p = ct.one_atm * atm

	"""
	find the ignition process

	:param mech:    mechanism
	:param p:       pressure (Pa)
	:param T0:      temperature (K) of the inlet flow
	:param T:       initial temperature (K) of the reactor
	:param tau:     residence time (s) of the reactor

	:return reactor:

	"""

	if if_half:
		max_dT = 40
	else:
		max_dT = 100

	if if_fine:
		n_loop = 2
	else:
		n_loop = 1

	i_loop = 0


	# @@@@@@@@@@@@@@@@@@@@@@@@@@
	# loop until grid resolution found
	while i_loop < n_loop:
		i_loop += 1
		print '-'*5
		print 'i_loop = '+str(i_loop)

		soln.TPX = T0, p, X0
		reactor = ct.IdealGasConstPressureReactor(soln)
		network = ct.ReactorNet([reactor])

		if i_loop == 2:
			dt = 1.0*tau_ign/20
			max_dT /= 4.0
		else:
			dt = 0.1
		t = 0

		if verbose:
			print 'dt0 = '+str(dt)
		T_prev = T0

		ii_add = []
		#TT = []
		raw = None
		raw_all = None

		# @@@@@@@@@@@@@@@@@@@@@@@@@@
		# loop until ignited/equil reached
		while True:
			t_prev = t

			# @@@@@@@@@@@@@@@@@@@@@@@@@@
			# loop until find the proper time step
			while True:
				if i_loop == 2:
					dt = min(dt, 1.0*tau_ign/20)
				t += dt
				t = float(str(t))

				if verbose:
					print 'now, '+str(t)

				# find T at tried t ------------
				# corresponding data stored in raw_all[i_add]

				new_sim = True
				if raw_all is not None:
					if (t in raw_all['axis0']):
						new_sim = False
						if verbose:
							print 'calculated before, loaded !!!!!!'
						i_add = raw_all['axis0'].index(t)
						T = raw_all['temperature'][i_add]

				if new_sim:
					network.advance(t)
					if verbose:
						print 'advanced, T = '+str(soln.T)
					raw_all = soln2raw(t, 'time', soln, raw_all)
					i_add = len(raw_all['axis0'])-1
					T = soln.T

				# decide if tried t is proper -------
				
				dT = abs(T - T_prev)
				if dT > max_dT or (if_half and T-T0>404):
					# if dT is too large, this t is not okay, decrease time step and start over
					t = t_prev
					dt /= 2.0
					soln.TPX = T0, p, X0
					reactor = ct.IdealGasConstPressureReactor(soln)
					network = ct.ReactorNet([reactor])
				
				else:
					# if dT is too small, this t is okay, we increase time step for next t
					if (soln.T - T0 < 400 and dT < 10):
						dt *= 2.0
					if (soln.T - T0 >= 400 and dT < 50):
						dt *= 5.0
					break

			ii_add.append(i_add)
			T_prev = T

			if if_half:
				if soln.T - T0 > dT_ign:
					print 'ignited'
					tau_ign = t
					break
			else:
				if soln.T - T0 > 1000 and dT < 1:
					print 'equilibrium reached'
					break




	raw = slice_raw(raw_all, ii_add)
	print 'n_points = ' + str(len(raw['axis0'])) + '/' + str(len(raw_all['axis0']))
	print 'CPU time = '+str(time.time() - cpu0)


	if dir_raw is not None:

		path_raw = os.path.join(dir_raw,'raw.npz')
		raw = save_raw_npz(raw, path_raw)
		save_raw_csv(raw, soln, dir_raw)


	return raw


def test_senkin():

	#from src.inp.inp_TRF import dir_public, fuel_dict
	#soln = ct.Solution(os.path.join(dir_public,'detailed','mech','chem.cti'))
	soln = ct.Solution('gri30.xml')

	atm = 1
	T0 = 1000.0
	phi = 1

	X0 = 'CH4:1, O2:2, N2:7.52'
	dir_raw = 'test'
	raw = senkin(soln, atm, T0, X0, if_half=True, if_fine=False, dir_raw=dir_raw)
	#raw = save_raw(raw, None)

	tt = raw['axis0']
	TT = raw['temperature']
	qq = raw['heat_release_rate']
	#print str(len(tt)) + ' points'
	#print raw['net_reaction_rate'].shape

	plt.plot(qq, TT, marker='o')
	#plt.savefig(os.path.join(dir_raw,'ign_fine.jpg'))
	plt.show()

	#print tt[-1]

	#return raw


if __name__=="__main__":
	test_senkin()
	#raw = load_raw('raw.npz')
	#plt.plot(raw['axis0'],raw['temperature'])
	#plt.show()