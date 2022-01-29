import os
import json
import requests
import pandas as pd

from iterator_objects import generation_type, state_abbrieviations
class Extract_Elec_Generation_Data():
    '''
    From eia.gov/opendata, this object extracts all electricity generation sources for all 50 states, plus DC.

    Depends on file `iterator_objects` to bring in:
        * generation_type -> api code for each fuel type
        * state_abbreviations -> two letter abbreviations of all 50 states plus DC

    To retrieve data for all 50 states (plus DC), use the `run_extractor` method.

    All values under the fuel methods are in thousand megawatt hours.

    Methods:
        * run_extractor -> runs extractor for all two letter abbreviations for all 50 states.
            - Returns a DataFrame object for all 50 states plus DC's electric generation data.

        * get_eia_response_data -> sends api calls to eia for all fuel types for whatever state abbreviation is fed in
            - Returns a DataFrame object for each state's data.

        * rearrange_state_df_columns -> takes each state dataframe and rearranges the column order
    '''
    def __init__(self):
        self.EIA_API_KEY = os.getenv('EIA_API_KEY')

    def run_extractor(self, state_abbrieviations=state_abbrieviations):
        us_df_list = []

        for state_abbr in state_abbrieviations:
            state_df = self.get_eia_response_data(state_abbr=state_abbr)
            us_df_list.append(state_df)

        us_generation_df = pd.concat(us_df_list)

        return us_generation_df

    def get_eia_response_data(self, state_abbr, generation_type=generation_type):
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
        column_order = ['state', 'year', 'all_fuels', 'coal', 'natural_gas', 'other_gas', 'petro_liquids', 'petro_coke',
                        'nuclear', 'hydro_electric', 'hydro_electric_storage', 'all_solar','wind', 'utility_scale_solar', 
                        'utility_scale_photovoltaic', 'small_scale_photovoltaic', 'other_renewables', 'utility_scale_thermal', 'geothermal', 
                        'other_biomass', 'wood_fuels', 'other']

        return state_df[column_order]


if __name__ == '__main__':
    extractor = Extract_Elec_Generation_Data()

    print("extracting data from EIA...")
    print("I'd go grab a quick coffee, this will take 2 to 3 minutes...")
    extractor.run_extractor().to_csv('us_electric_generation_2001_20.csv')
    print("data extracted!")