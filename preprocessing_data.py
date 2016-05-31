__author__ = 'vinay_vijayan'

import pandas as pd
from gurobipy import multidict
import urllib
import urllib2
import json

NEW_SECTORS_FILE = 'data/list_new_sectors.csv'
OLD_SECTORS_FILE = 'data/list_old_sectors.csv'

ACTIVITY_CODER_URL = 'http://hadaly.aiddata.wm.edu/api/autocoder'

class PreProcessingData(object):

    def __init__(self):

        self.df_new_sectors = pd.read_csv(NEW_SECTORS_FILE, encoding='utf-8', sep=',')
        self.df_old_sectors = pd.read_csv(OLD_SECTORS_FILE, encoding='utf-8', sep=',')

        grouped_df_new = self.df_new_sectors.groupby('code')
        grouped_df_old = self.df_old_sectors.groupby('code')

        self.dict_old_acs = {}
        for each_old_group in grouped_df_old.groups:
            old_text_index = grouped_df_old.groups[each_old_group][0]
            old_text = self.df_old_sectors.ix[old_text_index]['text']
            old_code = self.df_old_sectors.ix[old_text_index]['code']

            list_acs_probs = self._post_request_get_response(old_text)['activity_codes']
            self.dict_old_acs[old_code] = self._normalize_probabilities(list_acs_probs)

        self.dict_new_acs = {}
        for each_new_group in grouped_df_new.groups:
            new_text_index = grouped_df_new.groups[each_new_group][0]
            new_text = self.df_new_sectors.ix[new_text_index]['text']
            new_code = self.df_new_sectors.ix[new_text_index]['code']

            list_acs_probs = self._post_request_get_response(new_text)['activity_codes']
            self.dict_new_acs[new_code] = self._normalize_probabilities(list_acs_probs)

    def get_multidicts(self):
        dict_old_codes = {}
        dict_new_codes = {}

        for each_old_code in self.dict_old_acs:
            for each_activity_code in self.dict_old_acs[each_old_code]:
                dict_old_codes[(each_old_code + '_old', each_activity_code)] = self.dict_old_acs[each_old_code][each_activity_code]

        for each_new_code in self.dict_new_acs:
            for each_activity_code in self.dict_new_acs[each_new_code]:
                dict_new_codes[(each_new_code + '_new', each_activity_code)] = self.dict_new_acs[each_new_code][each_activity_code]

        return multidict(dict_old_codes), multidict(dict_new_codes)

    def _post_request_get_response(self, text):
        value = {'input': text}
        data = urllib.urlencode(self._get_encoded_dict(value))
        req = urllib2.Request(ACTIVITY_CODER_URL, data)
        response = urllib2.urlopen(req)
        json_string = response.read()
        return json.loads(json_string)

    def _get_encoded_dict(self, in_dict):
        out_dict = {}
        for key, value in in_dict.iteritems():
            if isinstance(value, unicode):
                value = value.encode('utf8')
            elif isinstance(value, str):
                value.decode('utf8')
            out_dict[key] = value
        return out_dict

    def _normalize_probabilities(self, list_input):
        list_dummy = [each[1] for each in list_input]
        dict_output = {}
        normalization_factor = 1/sum(list_dummy)
        for each in list_input:
            dict_output[each[0]] = each[1] * normalization_factor

        return dict_output

if __name__ == '__main__':
    test_object = PreProcessingData()
    test_dict_old_codes, test_dict_new_codes = test_object.get_multidicts()
    pass