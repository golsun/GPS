import cantera as ct
import numpy as np
from src.ct.def_ct_tools import * 
from src.ct.senkin import senkin
import time

def PFA_algo(soln, RR, crit, seeds, path_save=None, overwrite=False):

	#if soln.n_species > 200:
	#	verbose = True
	#else:
	

	if path_save is None:
		overwrite = True

	rxn = soln.reaction
	sp = soln.species
	n_sp = soln.n_species
	n_rxn = soln.n_reactions

	if_compute = True
	if overwrite is False:
		try:
			PFA_file = np.load(open(path_save, 'rb'))
			rmat = PFA_file['rmat']
			if_compute = False
		except IOError:
			#print 'no such file ---- '+ path_save
			pass

	verbose = if_compute

	if if_compute:
		cpu0 = time.time()

		if verbose:
			print 'calculating P, C flux ... '

		P = [0]*n_sp
		C = [0]*n_sp
		Pmat = np.zeros([n_sp,n_sp])
		Cmat = np.zeros([n_sp,n_sp])

		rPmat1 = np.zeros([n_sp,n_sp])
		rCmat1 = np.zeros([n_sp,n_sp])
		rPmat2 = np.zeros([n_sp,n_sp])
		rCmat2 = np.zeros([n_sp,n_sp])
		rmat = np.zeros([n_sp,n_sp])


		for i_rxn in range(n_rxn):
			#print 'rxn'+str(i_rxn)+' RR = '+str(RR[i_rxn])

			s_mu = dict()

			for s in rxn(i_rxn).reactants.keys():
				if s not in s_mu.keys():
					s_mu[s] = 0
				s_mu[s] -= rxn(i_rxn).reactants[s]
			
			for s in rxn(i_rxn).products.keys():
				if s not in s_mu.keys():
					s_mu[s] = 0
				s_mu[s] += rxn(i_rxn).products[s]

			#print s_mu

			for s in s_mu.keys():
				#print s
				sp_id = soln.species_index(s)
				#print 'P[sp_id] = '+str(P[sp_id])
				P[sp_id] += max( 1.0 * s_mu[s] * RR[i_rxn], 0)
				C[sp_id] += max(-1.0 * s_mu[s] * RR[i_rxn], 0)

			for A in s_mu.keys():
				id_A = soln.species_index(A)
				for B in s_mu.keys():
					id_B = soln.species_index(B)
					if B != A:
						#print str(id_A)+' not '+str(id_B)
						Pmat[id_A,id_B] += float(max( 1.0 * s_mu[A] * RR[i_rxn], 0))
						Cmat[id_A,id_B] += float(max(-1.0 * s_mu[A] * RR[i_rxn], 0))
						#print 'Pmat('+str(id_A)+','+str(id_B)+') = '+str(s_mu[A] * RR[i_rxn])+','+str(Pmat[id_A,id_B])


		if verbose:
			print 'calculating 1st-gen coefficients ... '

		for id_A in range(n_sp):
			for id_B in range(n_sp):
				norm =  max(P[id_A], C[id_A])
				if norm>0 and id_B != id_A:
					rPmat1[id_A, id_B] = Pmat[id_A, id_B] / norm
					rCmat1[id_A, id_B] = Cmat[id_A, id_B] / norm

		if verbose:
			print 'calculating 2st-gen coefficients ... (the correct way!!!)'

		for id_A in range(n_sp):
			for id_B in range(n_sp):
				rPmat2[id_A, id_B] = float(np.dot(rPmat1[id_A, :], rPmat1[:, id_B]))
				rCmat2[id_A, id_B] = float(np.dot(rCmat1[id_A, :], rCmat1[:, id_B]))

				#raise ValueError(str(rPmat2[id_A, id_B]) + ' vs ' + str(rPmat2_slow))


		if verbose:
			print 'calculating total-gen coefficients ... '

		for id_A in range(n_sp):
			for id_B in range(n_sp):
				rmat[id_A, id_B] = rPmat1[id_A, id_B] + rCmat1[id_A, id_B] + \
					rPmat2[id_A, id_B] +rCmat2[id_A, id_B]	

		if verbose:
			print 'CPU time for coefficients = ' + str(time.time()-cpu0)

		np.savez(path_save,\
			P=P, C=C, Pmat=Pmat, Cmat=Cmat, rPmat1=rPmat1, \
			rCmat1=rCmat1, rPmat2=rPmat2, rCmat2=rCmat2, rmat=rmat)

	
	if verbose:
		print 'iterating ... '
	cpu0 = time.time()

	species_kept = seeds
	n_kept = len(species_kept)
	n_round = 0
	
	if verbose:
		print species_kept
	while True:
		n_round += 1
		if verbose:
			print 'round '+str(n_round)
		for id_B in range(n_sp):
			B = sp(id_B).name
			for A in species_kept:
				id_A = soln.species_index(A)
				if (rmat[id_A, id_B] > crit) and (B not in species_kept):
					species_kept.append(B)
					if verbose:
						print 'added '+B+' from '+A

		if len(species_kept) == n_kept:
			break
		else:
			n_kept = len(species_kept)

	
	if verbose:
		print 'CPU time for picking up species = ' + str(time.time()-cpu0)
	return species_kept







def test_PFA():

	soln = 'gri30.xml'
	soln = ct.Solution(soln)
	fuel_dict = {'CH4':1.0}
	crit = 0.1
	phi = 1.0
	X0 = Xstr(soln, fuel_dict, phi)
	path_save = 'senkin.npz'

	raw = load_raw(path_save)
	#raw = senkin(soln, 5, 1000, X0, 'True')
	#raw = save_raw(raw, path_save)
	RR = []
	for i in range(soln.n_reactions):
		RR.append(float(raw['net_reaction_rate'][10,i]))
	#print RR

	species_kept = PFA(soln, RR, crit, fuel_dict)
	print len(species_kept)

if __name__ == '__main__':
	test_PFA()
