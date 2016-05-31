__author__ = 'vinay_vijayan'

from preprocessing_data import PreProcessingData
from get_matchings import GetMatchings
from postprocessing_data import PostProcessingData

from gurobipy import tuplelist

if __name__ == '__main__':
    test_object_preprocessing = PreProcessingData()
    test_dict_old_codes, test_dict_new_codes = test_object_preprocessing.get_multidicts()

    test_object_getmatchings = GetMatchings(test_dict_old_codes, test_dict_new_codes)

    arcs_old, weights_old = test_dict_old_codes
    arcs_old = tuplelist(arcs_old)
    test_dict_number_matchings = {}
    set_arcs_old = set([each_tuple[0] for each_tuple in arcs_old])
    for each_old_node in set_arcs_old:
        test_dict_number_matchings[each_old_node] = 4

    test_object_getmatchings.update_number_matchings_constraints(test_dict_number_matchings)
    dict_weights, dict_binary, obj_value = test_object_getmatchings.get_matchings()
    print('objective value: ', obj_value)

    test_object_postprocessing = PostProcessingData()
    dict_mappings = test_object_postprocessing.get_pairings(dict_weights, dict_binary)
