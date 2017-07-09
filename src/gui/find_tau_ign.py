import os, csv

# 1. put this file at the same level of the target folder
# 2. run this file

def find_tau_ign(fld):

	if bool(fld):
		folder = os.path.join(fld,'autoignition')
		tau_csv = os.path.join(fld,'tau_ign.csv')
	else:
		folder = 'autoignition'
		tau_csv = 'tau_ign.csv'

	if not os.path.exists(folder):
		print 'no such folder: '+str(folder)
		return False

	list_fat = os.listdir(folder)

	T_list = []
	phi_list = []
	atm_list = []
	tau_list = []

	for fat in list_fat:
		if fat[:3]=='phi' and os.path.isdir(os.path.join(folder,fat)):

			t_csv = os.path.join(folder,fat,'time.csv')
			if os.path.exists(t_csv):
				with open(t_csv, "rU") as f:
					reader = csv.reader(f, delimiter=',')
					for row in reader:
						last_t = row[0]

				tau_list.append(last_t)
				T_list.append(fat.split('_')[2].replace('K',''))
				phi_list.append(fat.split('_')[0].replace('phi',''))
				atm_list.append(fat.split('_')[1].replace('atm',''))
	
		
	with open(tau_csv, "w") as f:
		f.write('initial temperature (K),ignition delay (s),equivalence ratio, pressure (atm)\n')
		for ix in range(len(T_list)):
			f.write(str(T_list[ix])+','+str(tau_list[ix]) +','+str(phi_list[ix])+','+str(atm_list[ix])+'\n')
				

if __name__ == '__main__':
	fld = '/Users/xianggao/GPS data/CH4 Suo/reduction/detailed/raw/[CH4] + [air]/'
	print os.path.exists(fld)
	find_tau_ign(fld)
