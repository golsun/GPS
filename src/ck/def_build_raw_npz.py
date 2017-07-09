import re
import numpy as np

__author__ = 'Xiang Gao'

# ---------------------------------------
# note
#
# 1. id of species and rxn (which we care) starts from 1, same value as in Chemkin,
#    while id of time (which we don't care) starts from 0
#    e.g., you can get mole fraction of a species whose id is 3 at the initial state by raw['mole_fraction'][0,3]
#
# 2. although raw is saved using numpy.savez as a npz file, this funciton returned as a dict-like obj
#    which means you can get mole_fraction by raw['mole_fraction']
# ----------------------------------------


""" --------------------------
simple functions
---------------------------"""


def csv_clean(label):
    return re.sub(r'Soln#\d+_','',label)


def csv_extract_rxn_id(label):
    return int(re.search("GasRxn#(\d+)_",label).groups()[0])


def csv_extract_sp_name(label):
    label = label.replace(';',',')
    return re.search("fraction_(.*)_()",label).groups()[0]


""" --------------------------------
parse a single CKSoln
-----------------------------------"""


def parse_CKSoln(csv_name, mechanism, raw, section):


    # firstly, read labels ------------------------------------------------

    # (partiall) fill raw by info parsed from csv_name

    # csv can divide into four parts
    # section == 0, contains info of x,t,T,P,V
    # section == 1, contains mole fraction
    # section == 2, contains reaction rates
    # section == 3, contains hdot, which will NOT be read

    with open(csv_name, 'r') as f:
        labels = f.readline().split(',')

        n_sp = mechanism['n_species']
        n_rxn = mechanism['n_reaction']

        # as in Chemkin, id starts from 1, size+1 here to be consistent
        j_rxn_net = np.zeros([n_rxn+1,1],dtype=int)-1
        j_rxn_fw = np.zeros([n_rxn+1,1],dtype=int)-1
        j_rxn_rv = np.zeros([n_rxn+1,1],dtype=int)-1
        j_mf = np.zeros([n_sp+1,1],dtype=int)-1
        j_x = -1
        j_P = -1
        j_T = -1
        j_V = -1
        sp_id0 = -1
        rxn_id0 = -1

        col_num = 0
        for label in labels:
            label = csv_clean(label)

            if section == 0:
                if 'Distance_(' in label:
                    j_x = col_num
                    raw['axis0_type'] = 'distance'
                elif 'Time_(' in label:
                    j_x = col_num
                    raw['axis0_type'] = 'time'
                elif 'Temperature_(' in label:
                    j_T = col_num
                elif 'Volume_(' in label:
                    j_V = col_num
                elif 'Pressure_(' in label:
                    j_P = col_num

            if section == 0 or section == 1:

                if 'Mole_fraction_' in label:
                    section = 1
                    sp_id = mechanism['species'][csv_extract_sp_name(label)]['id']
                    j_mf[sp_id] = col_num
                    if sp_id0 < 0: sp_id0 = sp_id

            if section == 1 or section == 2:

                if 'Net_rxn_rate_' in label:
                    section = 2
                    rxn_id = csv_extract_rxn_id(label)
                    j_rxn_net[rxn_id] = col_num
                    if rxn_id0 < 0 : rxn_id0 = rxn_id
                elif 'Forward_rxn_rate_' in label:
                    j_rxn_fw[csv_extract_rxn_id(label)] = col_num
                elif 'Reverse_rxn_rate_' in label:
                    j_rxn_rv[csv_extract_rxn_id(label)] = col_num

            if section == 2:
                if ('Hdot' in label) and ('GasRxn' in label):
                    section = 3
                    break

            col_num += 1

    # then, read numbers ------------------------------------------------

    numbers = np.matrix(np.loadtxt(csv_name, delimiter=',', skiprows=1, dtype=float))
    nx = numbers.shape[0]

    if raw['mole_fraction'] is None:
        raw['mole_fraction'] = np.matrix(np.ndarray([nx,n_sp+1]))
        raw['net_reaction_rate'] = np.matrix(np.ndarray([nx,n_rxn+1]))
        raw['forward_reaction_rate'] = np.matrix(np.ndarray([nx,n_rxn+1]))
        raw['reverse_reaction_rate'] = np.matrix(np.ndarray([nx,n_rxn+1]))

    if j_T >= 0:
        raw['temperature'] = numbers[:,j_T]
    if j_x >= 0:
        raw['axis0'] = numbers[:,j_x]
    if j_P >= 0:
        raw['pressure'] = numbers[:,j_P]
    if j_V >= 0:
        raw['volume'] = numbers[:,j_V]


        # universal gas constant, J/mole-K
        R = 8.3144598
        pV = np.multiply(raw['pressure'] * 101325, raw['volume'] * pow(1.0 / 100, 3))
        # by pV = nRT, we have n = pV/RT
        raw['mole'] = np.divide(pV, raw['temperature'] * R)

    if sp_id0 > 0:
        for sp_id in range(sp_id0, n_sp+1):
            if j_mf[sp_id] >= 0:
                # if you slice a n-dim array (ndarray in numpy), you got a ndarray
                # you need to convert it to int before used as a index
                raw['mole_fraction'][:,sp_id] = numbers[:, int(j_mf[sp_id])]
    if rxn_id0 > 0:
        for rxn_id in range(rxn_id0, n_rxn+1):
            if j_rxn_net[rxn_id] >= 0:
                raw['net_reaction_rate'][:, rxn_id] = numbers[:, int(j_rxn_net[rxn_id])]
            if j_rxn_fw[rxn_id] >= 0:
                raw['forward_reaction_rate'][:, rxn_id] = numbers[:, int(j_rxn_fw[rxn_id])]
            if j_rxn_rv[rxn_id] >= 0:
                raw['reverse_reaction_rate'][:, rxn_id] = numbers[:, int(j_rxn_rv[rxn_id])]

    return raw, section


""" --------------------------------
decide which CKSoln to parse
-----------------------------------"""


def read_CKSoln(csv_folder, mechanism, initial_condition=None):

    raw = {
           'axis0':None, 'axis0_type':None,     # the primary axis for plot, usually time or distance
           'pressure':None, 'temperature':None, 'volume':None,
            'mole_fraction':None, 'net_reaction_rate':None, 'forward_reaction_rate':None,
           }

    csv_name0 = csv_folder + 'CKSoln_solution_no_1'
    try:
        csv_name = csv_name0 + '.csv'
        raw, section = parse_CKSoln(csv_name, mechanism, raw, 0)
    except IOError:

        print 'no',csv_name
        i_sub = 1
        section = 0
        while section < 3:
            csv_name = csv_name0+'_'+str(i_sub)+'.csv'
            raw, section = parse_CKSoln(csv_name, mechanism, raw, section)
            i_sub += 1

    return raw


""" --------------------------------
build rawdata from various source
-----------------------------------"""


def build_raw(case_folder, mechanism, source='cksoln', overwrite=False):

    # output: numpy matrix


    #print overwrite
    path_raw = case_folder + 'raw.npz'
    if_build = True
    if overwrite is False:
        try:
            raw_file = np.load(open(path_raw, 'rb'))
            raw = dict()
            for key in raw_file.keys():
                raw[key] = np.matrix(raw_file[key])
            raw['axis0_type'] = str(raw_file['axis0_type'])
            return raw
        except IOError:
            pass

    print 'building raw...'
    if source.lower() == 'cksoln':
        raw = read_CKSoln(case_folder, mechanism)
    np.savez(path_raw,
             axis0=raw['axis0'], axis0_type=raw['axis0_type'],
             pressure=raw['pressure'], temperature=raw['temperature'], volume=raw['volume'],
             mole_fraction=raw['mole_fraction'], mole=raw['mole'],
             net_reaction_rate=raw['net_reaction_rate'],
             forward_reaction_rate=raw['forward_reaction_rate'],
             reverse_reaction_rate=raw['reverse_reaction_rate'])
    #raw = np.load(open(path_raw, 'rb'))

    return raw
