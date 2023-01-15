"""
Author: Victor Gimenes
Date: 12/07/2021
Módulo responsável por armazenar as funções de coleta de dados na API do BLS.
"""

# Importando bibliotecas necessárias
import json
from datetime import datetime 
import requests 
import pandas as pd
import xlwings as xw
import datetime as dt
from dateutil.relativedelta import relativedelta # Necessita instalação (fora do anaconda package)

# Função Principal
def get_bls_key():
    return 'enter your key here!"

# Função Prinipal
def get_series(series_dict,dates):
    """
    Função responsável por fazer a coleta dos indices de CPI da API da BLS.

    Parameters
    ----------
    series_dict : Dictionary
        Dict contendo series_ids como keys e os nomes (como quiser) dos respectivos series_ids.
    dates : Tuple
        Tuple contendo o ano de íncio e ano final que irá ser requisitado na API - para todos os series_ids passados.

    Returns
    -------
    df : Dataframe
        Dataframe contendo os dados solicitados.

    """
    today = dt.datetime.now().replace(microsecond=0)
    print("Iniciando extração de CPI-U US em: "+str(today))
    
    # The url for BLS API v2
    url = 'https://api.bls.gov/publicAPI/v2/timeseries/data/'
    key = '?registrationkey={}'.format(get_bls_key())
    
    # Specify json as content type to return
    headers = {'Content-type': 'application/json'}
    
    # Submit the list of series as data
    data = json.dumps({
        "seriesid": list(series_dict.keys()),
        "startyear": dates[0],
        "endyear": dates[1]})
    
    # Post request for the data
    p = requests.post(
        '{}{}'.format(url, key),
        headers=headers,
        data=data, verify=False).json()['Results']['series']
    # Date index from first series
    date_list = [f"{i['year']}-{i['period'][1:]}-01" for i in p[0]['data']]
    
    # Empty dataframe to fill with values
    df = pd.DataFrame()
    
    # Build a pandas series from the API results, p
    for s in p:
        df[series_dict[s['seriesID']]] = pd.Series(
            index = pd.to_datetime(date_list),
            data = [i['value'] for i in s['data']]
            ).astype(float).iloc[::-1]
    return df




