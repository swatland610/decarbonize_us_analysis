import os
import json
from typing import final
from httpx import request
import requests

import pandas as pd

from iterator_objects import generation_type, state_abbrieviations

class Extract_Elec_Generation_Data():
    '''
    '''
    def __init__(self):
        self.EIA_API_KEY = os.getenv('EIA_API_KEY')
        return self.get_eia_data_all_states()


    def get_eia_data_all_states(self, state_abbrieviations=state_abbrieviations):
        '''
        '''
        us_df_list = []

        for state_abbr in state_abbrieviations:
            state_df = self.get_eia_response_data(state_abbr=state_abbr)
            us_df_list.append(state_df)

        us_generation_df = pd.concat(us_df_list)

        return us_generation_df

    def get_eia_response_data(self, state_abbr, generation_type=generation_type):
        '''
        '''
        df_list = []

        for metric in generation_type:
            col_label = metric[0]
            metric_code = metric[1]

            adjusted_metric_code = metric_code.replace('XX', state_abbr)

            url = "http://api.eia.gov/series/?api_key="+self.EIA_API_KEY+"&series_id="+adjusted_metric_code
            response = requests.get(url)

            try:
                json_data = json.loads(response.text)['series'][0]['data']

            except KeyError:
                # this means that there's no data found for whatever the generation type is
                # we will set dummy data to continue through the loop
                json_data = [[year, 0] for year in range(2001,2021)] # this relates to the year column
                
            finally:
                df = pd.DataFrame(json_data, columns=[['year', col_label]])
                df['state'] = state_abbr
                df_list.append(df)


        state_df = pd.concat(df_list, axis=1)
        # remove duplicate columns created through concat
        state_df = state_df.loc[:, ~state_df.columns.duplicated()]\
                           .fillna(0)

        state_df = self.rearrange_state_df_columns(state_df)

        return state_df

    def rearrange_state_df_columns(self, state_df):
        column_order = ['state', 'year', 'all_fuels', 'all_solar', 'coal', 'natural_gas', 'other_gas', 'petro_liquids', 'petro_coke',
                        'nuclear', 'hydro_electric', 'hydro_electric_storage', 'all_solar', 'wind', 'utility_scale_solar', 
                        'utility_scale_photovoltaic', 'small_scale_photovoltaic', 'other_renewables', 'utility_scale_thermal', 'geothermal', 
                        'other_biomass', 'other']

        return state_df[column_order]