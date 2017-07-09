from def_build_mech_dict import *
import os
import shutil


def rename_sp(sp_list):
	sp_list_new = []
	for s in sp_list:
		sp_list_new.append(s.replace("(","-").replace(")","-").replace(",","-"))

	return sp_list_new


def skeletal(detailed_folder, sk_folder, species_kept, notes=None):

	if not os.path.exists(sk_folder):
		os.makedirs(sk_folder)

	if detailed_folder != sk_folder:
		shutil.copyfile(os.path.join(detailed_folder,'therm.dat'), os.path.join(sk_folder,'therm.dat'))
	trandat = os.path.join(detailed_folder,'tran.dat')
	try:
		ft = open(trandat,'r')
		ft.close()
		shutil.copyfile(trandat, os.path.join(sk_folder,'tran.dat'))
	except IOError:
		pass

	sk_inp = os.path.join(sk_folder,'chem.inp')

	mech = build_mech(detailed_folder,overwrite=False)
	rxn_all = mech['reaction']

	f = open(sk_inp,'w')
	if notes is not None:
		for note in notes:
			f.write(note+'\n')
	f.write('\n')

	f.write('ELEMENTS\n')
	for e in mech['element'].keys():
		f.write(e + ' ')
	f.write('\nEND\n\n')



	f.write('SPECIES\n')
	n = 0
	for s in species_kept:
		f.write(s + ' ')
		n += 1
		if n == 5:
			f.write('\n')
			n = 0
	if n != 0:
		f.write('\n')
	f.write('END\n\n')


	f.write('REACTIONS\n')
	rxn_kept = []
	for rxn in rxn_all:
		if all(member in species_kept for member in rxn_all[rxn]['member'].keys()):
			n_ln = 0
			for info in rxn_all[rxn]['info']:
				if n_ln > 0:
					f.write('    ')


				if '/' in info and \
					('LOW' not in info.upper()) and ('TROE' not in info.upper()) \
					and ('REV' not in info.upper()):

					# this line describes three-body collision * efficiency *
					# we should remove these not included in mech

					ss = info.split('/')
					info = ''
					for i in range(len(ss)):
						s = ss[i].strip()
						if s in species_kept:
							info += (ss[i] + '/' + ss[i+1] + '/')
					

				f.write(info.strip() + '\n')
				n_ln += 1
			if n_ln > 1:
				f.write('\n')
	f.write('END\n\n')
	f.close()



def test_sk():

	detailed = 'test/gri30/'
	sk_inp = 'test/gri30/reduced'
	species_kept = ['H','HCO','CH2O','AR']
	skeletal(detailed, sk_inp, species_kept)

if __name__ == '__main__':
	test_sk()