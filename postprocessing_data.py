__author__ = 'vinay_vijayan'

class PostProcessingData(object):

    def get_pairings(self, dict_weights, dict_binary):
        dict_output = {}

        for each_tuple in dict_weights:
            if each_tuple[0] not in dict_output:
                dict_output[each_tuple[0]] = {}
            weight = dict_weights[each_tuple].x
            binary = dict_binary[each_tuple].x
            if int(binary) == 1 and weight >= 0.0000001:
                dict_output[each_tuple[0]][each_tuple[1]] = weight

        return dict_output
