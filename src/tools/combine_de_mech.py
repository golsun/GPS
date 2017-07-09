from add_root_path import *
from src.ck.def_build_mech_dict import *
from src.ck.def_cheminp import *
import json
import numpy as np


def alias_a_rxn(rxn_dict):
	sorted_member = sorted(rxn_dict['member'].keys())
	s = ''
	sign = None
	for k in sorted_member:
		mu0 = rxn_dict['member'][k]
		if sign is None:
			sign = np.sign(mu0)
		mu = sign * mu0
		s += '{'+str(mu)+'}' + k

	return s


def combine_de_mech(fld_list, fld_combined):

	if not os.path.exists(fld_combined):
		os.makedirs(fld_combined)

	mech_combined = None
	therm_lines = []
	for source, fld in fld_list:
		with open(os.path.join(fld,'therm.dat'),'r') as f:
			therm_lines += f.readlines()

		mech_new = build_mech(fld)
		if mech_combined is None:
			mech_combined = mech_new
			del mech_combined['species_id2name']
			mech_combined['rxn_alias'] = []
			for rxn in mech_combined['reaction']:
				alias = alias_a_rxn(mech_combined['reaction'][rxn])
				mech_combined['rxn_alias'].append(alias)
				mech_combined['reaction'][rxn]['source'] = source
				mech_combined['reaction'][rxn]['alias'] = alias
				mech_combined['reaction'][rxn]['info'].append('! source = '+source+', alias = '+alias)
		else:
			for sp in mech_new['species'].keys():
				if sp not in mech_combined['species'].keys():
					mech_combined['n_species'] += 1
					mech_combined['species'][sp] = {'member':{}, 'id':mech_combined['n_species']}

			for rxn in mech_new['reaction'].keys():
				rxn_dict = mech_new['reaction'][rxn]
				alias = alias_a_rxn(rxn_dict)
				if alias not in mech_combined['rxn_alias']:
					mech_combined['n_reaction'] += 1
					mech_combined['rxn_alias'].append(alias)


					rxn_dict['source'] = source
					rxn_dict['alias'] = alias
					rxn_dict['info'].append('! source = '+source+', alias = '+alias)
					mech_combined['reaction'][mech_combined['n_reaction']] = rxn_dict

	
	with open(os.path.join(fld_combined,'therm.dat'),'w') as f:
		f.writelines(therm_lines)



	json.dump(mech_combined, open(os.path.join(fld_combined, 'mech.json'),'w'))

	notes = ['! this is a combination of the following mech']+\
		['!     '+tup[0] for tup in fld_list]+\
		['! by Xiang Gao, Georgia Tech']
	skeletal(fld_combined, fld_combined, mech_combined['species'].keys(), notes=notes)








if __name__ == '__main__':
	fld_prj = os.path.join(root_path,'prj','prj_mix','prj_mix_dec+tol+hep')
	fld_list = [
		('Chaos dec+tol 121', os.path.join(fld_prj,'mech Chaos dec+tol 121')),
		('LLNL hep 160', os.path.join(fld_prj,'mech LLNL hep 160')),
		]
	fld_combined = os.path.join(fld_prj,'combined')

	combine_de_mech(fld_list, fld_combined)