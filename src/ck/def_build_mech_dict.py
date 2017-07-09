import re
import json as json
import os

__author__ = 'Xiang Gao'


""" --------------------------
simple functions
---------------------------"""


def cheminp_clean(line):
    # delete all comments (starting with !) and remove all white space at the beginning and the end of the line (strip)
    return re.split('!', line)[0].strip()


def cheminp_split(line):
    # split the line by whitespace(\s) or tab(\t), + means one or multiple successive matches
    return re.split(r'\s+|\t+', line)


def cheminp_extract_rxn_name(line):
    # the last three are Arrhenius parameters, the rest is the expression of this reaction (reaction.Name)
    name = ''.join(cheminp_split(line)[:-3]).replace(' ','')

    # change <=, =>, <=> to =
    name = name.replace('<', '')
    name = name.replace('>', '')

    # remove 3rd body info like (+M), (+h2)
    L,R = name.split('=')
    par_L = find_3rd_body(L)
    par_R = find_3rd_body(R)
    if ('+' in par_L) and (par_L == par_R):
        name = name.replace('('+par_L+')','')

    #print 'extracted name "'+str(name)+'" from line "'+str(line)+'"'
    return name



def find_3rd_body(s):
    i0 = s.find('(+')
    if i0 >= 0:
        i1 = s[i0:].find(')') + i0
        if i1 >= 0:
            return s[i0+1:i1]
        else:
            raise ValueError('find "(+" but cannot find ")" in '+str(s))
    else:
        return ''


""" --------------------------
find member of a reaction
---------------------------"""


def fun_parse_rxn(name, species):
    
    lr = name.split('=')

    member = {}
    # {Species,int} to store what species involved in this reaction

    sgn = -1
    # if nsns is left hand side, i.e. nsns==lr[0], then sgn = -1, else sgn = 1
    # sgn is updated at the end of the following for loop

    for nsns in lr:
        nsns = nsns.split('+')

        for ns in nsns:

            # split ns to n and s at i
            # if ns is '2CO2', n is 2, s is 'CO2'
            # if ns is 'CH4', n is 1, s is 'CH4'

            i = next(i for i in range(len(ns)) if ns[i].isalpha())
            s =ns[i:]
            if s.lower() != 'm':
                if i > 0:
                    n = int(ns[:i])
                else:
                    n = 1

                if s in species:
                    if s in member.keys():
                        member[s] += sgn * n
                    else:
                        member[s] = sgn * n
                else:
                    raise ValueError(s+' is not a valid species')
        sgn += 2
    return member



""" --------------------------
read chem.inp
---------------------------"""


def read_cheminp(path):

    # INPUT:  path of chem.inp
    # OUTPUT: a dict contains info of element, species, and reactions

    # initialization
    mechanism = {'element': {}, 'species': {}, 'reaction': {},
                 'species_id2name': {},
                 'n_species': 0, 'n_reaction': 0, 'n_element': 0}

    id_rxn = 0
    id_sp = 0
    id_e = 0

    f = open(path, 'r')
    section = 0
    for line in f:
        if_parse = 0
        line = cheminp_clean(line)

        if line:
            # if this line is not empty after being cleaned
            # figure out which section I'm reading

            if re.search('element', line, re.IGNORECASE):
                section = 1
            elif re.search('species', line, re.IGNORECASE):
                section = 2
            elif re.search('reaction', line, re.IGNORECASE):
                section = 3
            elif re.search('end', line, re.IGNORECASE):
                if section == 3:
                    break
            else:
                if_parse = 1

        if if_parse:
            # parse the line only when this line is not empty, a section header, or END

            if section == 1:
                ee = cheminp_split(line)
                for e in ee:
                    if e not in mechanism['element'].keys():
                        id_e += 1
                        mechanism['element'][e] = {}
                        mechanism['element'][e]['id'] = id_e

            elif section == 2:
                ss = cheminp_split(line)
                for s in ss:
                    if s not in mechanism['species'].keys():
                        id_sp += 1
                        mechanism['species'][s] = {}
                        mechanism['species'][s]['id'] = id_sp
                        mechanism['species'][s]['member'] = {}
                        mechanism['species_id2name'][str(id_sp)] = s

            elif section == 3:
                if line.find('=') >= 0:
                    name = cheminp_extract_rxn_name(line)
                    member = fun_parse_rxn(name, mechanism['species'].keys())
                    id_rxn += 1

                    # it is true that int can be a dict key
                    # however, after dump&load by json, int key will be converted to str
                    # therefore I use str(id_rxn) here as the key

                    mechanism['reaction'][str(id_rxn)] = {}
                    mechanism['reaction'][str(id_rxn)]['name'] = name
                    mechanism['reaction'][str(id_rxn)]['member'] = member
                    mechanism['reaction'][str(id_rxn)]['info'] = []
                mechanism['reaction'][str(id_rxn)]['info'].append(line)
    f.close()
    mechanism['n_element'] = len(mechanism['element'].keys())
    mechanism['n_species'] = len(mechanism['species'].keys())
    mechanism['n_reaction'] = len(mechanism['reaction'].keys())

    return mechanism


""" --------------------------
build and save mech
this is for the generation of skeletal mechanism
basically it simplify and purify original chem.inp by read_cheminp
and store it as mech.json in detailed/mech folder
so we can easily pick up the species and rxn info to read a skeletal chem.inp
---------------------------"""


def build_mech(mech_folder,overwrite=False):

    if_build = True
    if overwrite is False:
        try:
            mechanism = json.load(open(os.path.join(mech_folder,'mech.json'), 'rb'))
            if_build = False
        except IOError:
            pass

    if if_build:
        print 'building mech...'
        path_cheminp = os.path.join(mech_folder,'chem.inp')
        path_thermdat = os.path.join(mech_folder,'therm.dat')
        mechanism = read_cheminp(path_cheminp)
        json.dump(mechanism, open(os.path.join(mech_folder,'mech.json'), 'w'))

    return mechanism
