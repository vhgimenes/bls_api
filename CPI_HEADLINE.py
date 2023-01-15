# -*- coding: utf-8 -*-
"""
Created on Mon Jul 12 15:24:32 2021

Script responsável pela coleta da abertura de CPI (headline) na API do BLS e publicação na planilha designada abaixo.
Se atentar para o limite de queries da API: 25 series id por query e 25 queries por dia.

@author: victor.gimenes
"""
# Importando bibliotecas necessárias
import json
from datetime import datetime 
import requests 
import pandas as pd
import xlwings as xw
import datetime as dt
from dateutil.relativedelta import relativedelta # Necessita instalação (fora do anaconda package)

# Função Auxiliar
def get_cpi_from_bls(series_dict,dates):
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
    
    # API key in config.py which contains: bls_key = 'key' # Usada na VC 4bafaf10f5014a479f9cc9927fcb50d5  1c94050653d54c7889219c1b3a298563
    key = '?registrationkey={}'.format('1c94050653d54c7889219c1b3a298563')
    
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

# Função principal
def main():
    print("Inicilizando Rotina Headline CPI em: " + str(datetime.now().replace(microsecond=0)))
    print("")
    
    import time
    # Setando os inputs da função principal
    # Iniciando conexão com a planilha que possui a 
    wb = xw.Book("CPI_HEADLINE.xlsm")
    report = wb.sheets("REPORT")
    cadastro = wb.sheets("CADASTRO")
    banco = wb.sheets("BANCO")

    # Pegando da aba Cadastro os series_ids das séries e seus respectivos nomes (os colocados na tabela)
    series_id = pd.DataFrame(cadastro["A2"].expand().value, columns = cadastro["A1"].expand("right").value)
    series = list(series_id["Series_ID"])
    names = list(series_id["Series_Nickname"])
    # Transformando as informações desejadas em dict para serem inputadas na get_cpi_from_bls 
    series_dict = dict(zip(series, names))

    # Setando o ano incial e final para a coleta dos dados
    today = datetime.today()
    end = str((today - relativedelta(months=1)).date().year) # o ano incial deverá coincidir com a data de divulgação do índice (ou seja, o mês anteior ao de publicação)
    start = str(((today - relativedelta(months=4)).date()).year) # o ano incial será o coincidente com a data de 4 meses atrás - como segurança
    dates = (start, end)

    # Extraindo dados da API (Primeira query contendo 25 series_ids - que também servirá como teste para atualizção)
    df = get_cpi_from_bls(series_dict,dates)

    # Extraindo a data que a data de interesse para coleta dos índices (localizada na aba REPORT)
    # Essa data também será usada para validação tanto dos dados extraidos, como também da planilha
    check_date = report["C14"].value
    
    # Primeiro check para vermos se os dados de CPI já foram atualizados na API
    if check_date in list(df.index):
        #Se cairmos aqui é porque conseguimos puxar os índices de interesse
        print("Dados de CPI foram atualizados na API!")
        print("")
        # Segundo check para vermos se a base de dados já foi atulizada
        if banco["A1"].end("down").value != check_date:
            print("")
            print("Atualizando dados de CPI na planilha...")
            # Fazendo um request adicional (API limita em 25 Series_ids por query com limite de 25 queries por dia)
            series_dict = {'CUSR0000SARS':'Recreation services'}
            df1 = get_cpi_from_bls(series_dict,dates)
    
            # unino as duas queries
            df2 = pd.concat([df,df1],axis=1,join='inner')
    
            # Calculando a variação mensal do indicador
            df_mom = df2.pct_change().reset_index()
    
            # Ultimos ajustes para publicação na planilha
            df_mom = pd.melt(df_mom, id_vars=["index"], 
                              var_name="Date", value_name="Value")
            df_mom.columns = ["Data","Index","Value"]
            df_mom = df_mom[df_mom['Value'].notna()]
            df_mom['Value'] = df_mom['Value']*100
            df_mom.sort_values(by=["Data"], inplace=True)
    
            # Publicando os indicadores na aba BANCO
            df_mom = df_mom[df_mom['Data'] == check_date]
            banco["A1"].end("down").offset(1,0).options(header=False,index=False).value = df_mom
            wb.save()
            print("Dados foram publicados na planilha com sucesso!")
            print("")
            print("Terminada Rotina Headline CPI em: " + str(datetime.now().replace(microsecond=0)))
            return
            # main()
        else:
            print("Dados de CPI já foram atualizados na planilha!")
            print("")
            print("Terminada Rotina Headline CPI em: " + str(datetime.now().replace(microsecond=0)))
            return 
    else:
        print("Dados de CPI ainda NÃO foram atualizados na API!")
        print("")
        print("Em 10 segundos tentaremos mais uma vez")
        print("")
        time.sleep(10)
        main()

if __name__ == "__main__":
    main()





