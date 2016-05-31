__author__ = 'vinay_vijayan'

from gurobipy import *
import time

class GetMatchings(object):

    def __init__(self, multidict_old_nodes, multidict_new_nodes):
        self.arcs_old, self.weights_old = multidict_old_nodes
        self.arcs_old = tuplelist(self.arcs_old)

        self.arcs_new, self.weights_new = multidict_new_nodes
        self.arcs_new = tuplelist(self.arcs_new)

        self.set_old_nodes = set([each_tuple[0] for each_tuple in self.arcs_old])
        self.set_new_nodes = set([each_tuple[0] for each_tuple in self.arcs_new])

        self.m = Model('crosswalk')
        self.m.setParam('OutputFlag', False)

        self.weights = {}
        self.binary = {}

        for each_old_node in self.set_old_nodes:
            for each_new_node in self.set_new_nodes:
                self.weights[each_old_node, each_new_node] = self.m.addVar(lb=0, ub=1, name='weight_%s_%s'
                                                                                  % (each_old_node, each_new_node))
                self.binary[each_old_node, each_new_node] = self.m.addVar(vtype=GRB.BINARY, name='binary_%s_%s'
                                                                          % (each_old_node, each_new_node))
        self.m.update()

        for each_old_node in self.set_old_nodes:
            self.m.addConstr(quicksum([self.weights[each_old_node, each_new_node] for each_new_node
                                       in self.set_new_nodes]) == 1, 'sum_of weights_constraint_%s' % (each_old_node))

            self.m.addQConstr(quicksum([self.binary[each_old_node, each_new_node] *
                                       self.weights[each_old_node, each_new_node] for each_new_node in
                                       self.set_new_nodes]) == 1, 'force_1_0_constraint_%s' % (each_old_node))

    def update_number_matchings_constraints(self, dict_number_matchings):

        for each_old_node in dict_number_matchings:
            self.m.addConstr(quicksum([self.binary[each_old_node, each_new_node] for each_new_node in self.set_new_nodes])
                             == dict_number_matchings[each_old_node], 'edge_limit_constraint_%s' % (each_old_node))

    def multiply_weights_new(self, new_node, old_node):
        dict_output_new = {}

        for new_node, activity_code_new in self.arcs_new.select(new_node, '*'):
            dict_output_new[activity_code_new] = self.weights_new[new_node, activity_code_new]

        weight_binary_product = self.weights[old_node, new_node] * self.binary[old_node, new_node]

        for each_key in dict_output_new:
            dict_output_new[each_key] *= weight_binary_product

        return dict_output_new

    def multiply_weights_old(self, old_node):
        dict_output_old = {}

        for old_node, activity_code_old in self.arcs_old.select(old_node, '*'):
            dict_output_old[activity_code_old] = self.weights_old[old_node, activity_code_old]

        return dict_output_old

    def cumulate_weighted_acs(self, list_dicts):
        dict_output = {}

        for each_dict in list_dicts:
            for each_key in each_dict:
                if each_key in dict_output:
                    dict_output[each_key] += each_dict[each_key]
                else:
                    dict_output[each_key] = each_dict[each_key]

        return dict_output

    def difference_weighted_arcs(self, dict_old, dict_new):
        set_acs_old = set(dict_old.keys())
        set_acs_new = set(dict_new.keys())

        set_old_intersection_new = set_acs_old & set_acs_new
        set_old_exclusive = set_acs_old - (set_acs_old & set_acs_new)
        set_new_exclusive = set_acs_new - (set_acs_old & set_acs_new)

        dict_output = {}
        for activity_code in set_old_exclusive:
            dict_output[activity_code] = dict_old[activity_code]

        for activity_code in set_new_exclusive:
            dict_output[activity_code] = dict_new[activity_code]

        for activity_code in set_old_intersection_new:
            actual_var = dict_new[activity_code] - dict_old[activity_code]
            auxilary_var = self.m.addVar(name='aux_%s' % (activity_code))
            self.m.update()
            self.m.addConstr(actual_var <= auxilary_var)
            self.m.addConstr(actual_var >= -1 * auxilary_var)
            dict_output[activity_code] = auxilary_var

        return dict_output


    def get_matchings(self):
        list_differnced_weights = []

        list_dicts_multiplied_weights_old = []
        list_dicts_multiplied_weights_new = []
        for old_node in self.set_old_nodes:
            dict_multiplied_weights_old = self.multiply_weights_old(old_node)
            list_dicts_multiplied_weights_old.append(dict_multiplied_weights_old)

            for new_node in self.set_new_nodes:
                dict_multiplied_weights_new = self.multiply_weights_new(new_node, old_node)
                list_dicts_multiplied_weights_new.append(dict_multiplied_weights_new)

        dict_multiplied_weights_old = self.cumulate_weighted_acs(list_dicts_multiplied_weights_old)
        dict_multiplied_weights_new = self.cumulate_weighted_acs(list_dicts_multiplied_weights_new)
        dict_differenced_weights = self.difference_weighted_arcs(dict_multiplied_weights_old,
                                                                 dict_multiplied_weights_new)
        list_differnced_weights += dict_differenced_weights.values()

        self.m.setObjective(quicksum(list_differnced_weights), GRB.MINIMIZE)
        print time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + ' Optimization Started '
        self.m.optimize()
        print time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime()) + ' Optimization Ended '

        return self.weights, self.binary, self.m.objVal

    def print_variables(self):
        for v in self.m.getVars():
            print v.varName, v.x
        print 'Obj:', self.m.objVal




if __name__ == '__main__':
    test_old_dict = multidict({ ('AB_old', '31181.01'): 0.25,
                                ('AB_old', '31182.01'): 0.50,
                                ('AB_old', '31181.02'): 0.25 })

    test_new_dict = multidict({ ('AA_new', '31181.01'): 1,

                                ('AB_new', '31182.01'): 0.50,
                                ('AB_new', '31181.02'): 0.50, })

    # test_old_dict = multidict({ ('AB_old', '31181.02'): 0.33,
    #                             ('AB_old', '31182.02'): 0.17,
    #                             ('AB_old', '31181.01'): 0.33,
    #                             ('AB_old', '31182.01'): 0.17 })
    #
    # test_new_dict = multidict({ ('AA_new', '31120.07'): 0.34,
    #                             ('AA_new', '31120.06'): 0.37,
    #                             ('AA_new', '31120.08'): 0.29,
    #
    #                             # ('AB_new', '31120.08'): 0.29,
    #                             # ('AB_new', '31110.03'): 0.16,
    #                             # ('AB_new', '31182.03'): 0.20,
    #                             # ('AB_new', '31191.05'): 0.19,
    #                             # ('AB_new', '31181.01'): 0.16,
    #
    #                             ('AB_new', '31181.02'): 0.33,
    #                             ('AB_new', '31182.02'): 0.17,
    #                             ('AB_new', '31181.01'): 0.33,
    #                             ('AB_new', '31182.01'): 0.17,
    #
    #                             ('AC_new', '31140.02'): 0.50,
    #                             ('AC_new', '31130.03'): 0.50,
    #
    #                             ('AD_new', '31181.02'): 0.40,
    #                             ('AD_new', '31182.02'): 0.39,
    #                             ('AD_new', '31181.01'): 0.21 })

    test_dict_number_matchings = {'AB_old': 2}

    test_object = GetMatchings(test_old_dict, test_new_dict)
    test_object.update_number_matchings_constraints(test_dict_number_matchings)
    test_object.get_matchings()
    test_object.print_variables()