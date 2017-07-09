import numpy as np
import networkx as nx
from src.core.def_yen import k_shortest_paths as yen
from def_tools import *
import os
from src.core.def_build_graph import *

__author__ = 'Xiang Gao'




def find_hubs(score, iso, alpha, gamma=None):

    if iso == None:
        iso_kept = None
        n_hub = sum([score[node] > alpha for node in score.keys()])
        hubs = keys_sorted(score, n_hub)
        
    else:
        hubs = []
        iso_kept = dict()
        # isomers as hubs
        for iso_name in iso.keys():
            total_score = 0
            members = iso[iso_name]

            #iso_alpha = alpha / len(members)

            members_available = dict()
            for sp in members:
                if sp in score.keys():# and score[sp] > iso_alpha:
                    total_score += score[sp]
                    members_available[sp] = score[sp]
                    #hubs.append(sp)

            #alpha_iso = alpha * np.exp(1/len(members)) / np.exp(1)
            #alpha_iso = alpha * (gamma + (1 - gamma) * 1/len(members))


            tops = keys_sorted(members_available)
            members_available_sorted = []
            for top in tops:
                members_available_sorted.append(top + ', ' + str(score[top]))


            members_kept = []
            if total_score > alpha:
                acc_score = 0
                for top in tops:
                    members_kept.append(top)
                    if top not in hubs:
                        hubs.append(top)
                    acc_score += score[top]
                    if acc_score > alpha * gamma:
                        break

            # single species as hubs
            for sp in score.keys():
                if (not(sp in members_kept)) and (score[sp] > alpha):
                    if sp not in hubs:
                        hubs.append(sp)
                    members_kept.append(sp)


            if bool(members_kept):
                iso_kept[iso_name] = dict()
                #iso_kept[iso_name]['alpha_iso'] = alpha_iso
                iso_kept[iso_name]['total_score'] = total_score
                iso_kept[iso_name]['all'] = members
                iso_kept[iso_name]['available'] = members_available_sorted
                iso_kept[iso_name]['kept'] = members_kept

    return hubs, iso_kept










def GPS_algo(soln, flux_graph, source, target, path_save=None, \
    K=1, alpha=0.1, beta=0.5, normal='max', iso=None, overwrite=False, \
    raw='unknown',notes=None, gamma=None):

    reaction = soln.reaction

    """
    """

    """ --------------------------------
    check if results already exist
    if so, load and return
    -------------------------------- """

    if path_save is not None:
        if overwrite is False:
            try:
                GPS_results = json.load(open(path_save, 'r'))
                return GPS_results
            except IOError:
                pass

    """ --------------------------------
    if not, then compute, save, and return
    -------------------------------- """

    print 'performing GPS, source = '+str(source)+', target = '+str(target)

    arrow = ' --> '
    global_path = {}
    hub_GP = {}

    # ----------------------------------------------------------
    # score = max(in_deg, out_deg)

    in_deg = flux_graph.in_degree(weight='flux')
    out_deg = flux_graph.out_degree(weight='flux')

    if normal is 'source':
        norm_deg = out_deg[source]
    elif normal is 'max':
        norm_deg = max([max(out_deg.values()), max(in_deg.values())])

    score = {node: max(in_deg[node], out_deg[node]) / norm_deg for node in in_deg.keys()}

    # ----------------------------------------------------------
    # hubs = species whose score is above crit_score

    hubs, iso_kept = find_hubs(score, iso, alpha, gamma)
    n_hub = len(hubs)

    species_kept = dict()
    for hub in hubs:
        species_kept[hub] = dict()        
        species_kept[hub]['by_alpha'] = True
        species_kept[hub]['by_K'] = []
        species_kept[hub]['by_beta'] = []

    if target is not None:


        for hub in hubs:
            if hub not in hub_GP.keys():
                hub_GP[hub] = {}
                hub_GP[hub]['score'] = score[hub]
                hub_GP[hub]['global_path'] = []

            # ----------------------------------------------------------
            # a global path(way), GP, is the pathway, p0, from source to hub, plus the pathway, p1, from hub to target
            # however, we should further ensure there's no cycle in GP

            pp0 = []
            if K > 1:
                dd0, pp0 = yen(flux_graph, source, hub, k=K, weight='1/flux')
                dd1, pp1 = yen(flux_graph, hub, target, k=K, weight='1/flux')
            else:
                try:
                    p0 = nx.shortest_path(flux_graph, source, hub, weight='1/flux')
                    p1 = nx.shortest_path(flux_graph, hub, target, weight='1/flux')
                    pp0 = [p0]
                    pp1 = [p1]
                except nx.NetworkXNoPath:
                    print 'no path found for: '+str(source)+' --> '+str(hub)+' --> '+str(target)
                    pass

            if bool(pp0):
                k = 0
                for p0 in pp0:

                    k += 1
                    for p1 in pp1:

                        # although what returned from shortest path is ensured to not contain any cycle
                        # cycle may appear when you concatenate p0 and p1

                        no_cycle = True
                        p1 = p1[1:]
                        for s in p1:
                            if s in p0:
                                no_cycle = False
                                break

                        if no_cycle:
                            p = p0 + p1
                            GP = arrow.join(p)
                            hub_GP[hub]['global_path'].append(GP)

                            if GP not in global_path.keys():
                                global_path[GP] = {}
                                global_path[GP]['member'] = p

        # ---------------------------------     
        st_list = []
        for GP in global_path.keys():
            for sp in global_path[GP]['member']:
                if sp not in species_kept.keys():
                    species_kept[sp] = {}
                    species_kept[sp]['by_alpha'] = False
                    species_kept[sp]['by_K'] = []
                    species_kept[sp]['by_beta'] = []

                species_kept[sp]['by_K'].append(GP)

            if beta == 0:
                continue

            for isp in range(len(global_path[GP]['member']) - 1):
                s = global_path[GP]['member'][isp]
                t = global_path[GP]['member'][isp + 1]
                st = s + arrow + t
                if st not in st_list:
                    #print '-'*10
                    #print st
                    st_list.append(st)
                    rxn_beta = flux_graph[s][t]['member']
                    sum_beta = sum(rxn_beta.values())
                    rxn_top = keys_sorted(rxn_beta)
                    total_beta = 0.0
                    for rxn in rxn_top:
                        #print reaction(int(rxn)).equation + ': ' + str(int(rxn_beta[rxn]/sum_beta*100)) +'%'
                        st_rxn = st + ', ' + reaction(int(rxn)).equation

                        for sp in (reaction(int(rxn)).products.keys() + reaction(int(rxn)).reactants.keys()):
                            if sp not in species_kept.keys():
                                species_kept[sp] = {}
                                species_kept[sp]['by_alpha'] = False
                                species_kept[sp]['by_K'] = []
                                species_kept[sp]['by_beta'] = []   

                            if st_rxn not in species_kept[sp]['by_beta']:
                                species_kept[sp]['by_beta'].append(st_rxn)

                        total_beta += rxn_beta[rxn]/sum_beta
                        if total_beta >= beta:
                            break


    GPS_results = dict()

    GPS_results['parameter'] = {}
    GPS_results['parameter']['K'] = K
    GPS_results['parameter']['alpha'] = alpha
    GPS_results['parameter']['beta'] = beta
    GPS_results['parameter']['gamma'] = gamma
    GPS_results['parameter']['source'] = source
    GPS_results['parameter']['target'] = target
    GPS_results['parameter']['raw'] = raw
    GPS_results['parameter']['notes'] = notes

    GPS_results['isomer'] = iso_kept
    GPS_results['global_path'] = global_path
    GPS_results['hubs'] = hub_GP
    GPS_results['species'] = species_kept

    GPS_results['summary'] = {}
    GPS_results['summary']['n_hub'] = n_hub
    GPS_results['summary']['n_species_kept'] = len(species_kept.keys())
    GPS_results['summary']['n_global_path'] = len(global_path.keys())

    if path_save is not None:
        json.dump(GPS_results, open(path_save, 'w'))
    return GPS_results
