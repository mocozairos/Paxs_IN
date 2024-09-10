import pandas as pd
import mysql.connector
import decimal
import streamlit as st

def bd_phoenix(vw_name):
    # Parametros de Login AWS
    config = {
    'user': 'user_automation_jpa',
    'password': 'luck_jpa_2024',
    'host': 'comeia.cixat7j68g0n.us-east-1.rds.amazonaws.com',
    'database': 'test_phoenix_joao_pessoa'
    }
    # Conexão as Views
    conexao = mysql.connector.connect(**config)
    cursor = conexao.cursor()

    request_name = f'SELECT * FROM {vw_name}'

    # Script MySql para requests
    cursor.execute(
        request_name
    )
    # Coloca o request em uma variavel
    resultado = cursor.fetchall()
    # Busca apenas o cabecalhos do Banco
    cabecalho = [desc[0] for desc in cursor.description]

    # Fecha a conexão
    cursor.close()
    conexao.close()

    # Coloca em um dataframe e muda o tipo de decimal para float
    df = pd.DataFrame(resultado, columns=cabecalho)
    df = df.applymap(lambda x: float(x) if isinstance(x, decimal.Decimal) else x)
    return df

if 'mapa_router' not in st.session_state:

    st.session_state.mapa_router = bd_phoenix('vw_router')

if 'mapa_sales_ranking' not in st.session_state:

    st.session_state.mapa_sales_ranking = bd_phoenix('vw_sales_ranking')

st.title('Ranking Vendedores')

st.divider()

row0 = st.columns(2)

with row0[0]:

    modo = st.selectbox('Tipo de Ranking', ['Passeios vs Vendedores', 'Vendedores vs Passeios'], index=None)

with row0[1]:

    container_dados = st.container()

    atualizar_dados = container_dados.button('Carregar Dados do Phoenix', use_container_width=True)

if atualizar_dados:

    st.session_state.mapa_router = bd_phoenix('vw_router')

    st.session_state.mapa_sales_ranking = bd_phoenix('vw_sales_ranking')

row1 = st.columns(2)

with row1[0]:

    periodo = st.date_input('Período', value=[] ,format='DD/MM/YYYY')

if len(periodo)>1 and modo=='Vendedores vs Passeios':

    data_inicial = periodo[0]

    data_final = periodo[1]

    df_router_filtrado = st.session_state.mapa_router[(st.session_state.mapa_router['Data Execucao'] >= data_inicial) & 
                                                      (st.session_state.mapa_router['Data Execucao'] <= data_final) & 
                                                      (st.session_state.mapa_router['Tipo de Servico'] == 'TOUR')].reset_index(drop=True)
    
    df_sales_filtrado = st.session_state.mapa_sales_ranking[(st.session_state.mapa_sales_ranking['Data de Execucao'] >= data_inicial) & 
                                                            (st.session_state.mapa_sales_ranking['Data de Execucao'] <= data_final) & 
                                                            (st.session_state.mapa_sales_ranking['Tipo de Servico'] == 'TOUR')].reset_index(drop=True)

    df_vendedores = pd.merge(df_router_filtrado, df_sales_filtrado[['Codigo da Reserva', '1 Vendedor', 'Data de Execucao', 'Servico']], how='left', 
                             left_on=['Reserva', 'Data Execucao', 'Servico'], 
                             right_on=['Codigo da Reserva', 'Data de Execucao', 'Servico'])
    
    lista_servicos = df_vendedores['Servico'].unique().tolist()

    with row1[1]:

        st.write('Passeios')

        container = st.container(height=200, border=True)

        servico = container.radio('', sorted(lista_servicos), index=None)

    st.divider()

    row2 = st.columns(1)

    container_2 = st.container(border=True)

    if servico:

        df_mapa_filtrado_servico = df_vendedores[df_vendedores['Servico']==servico].reset_index(drop=True)

        df_mapa_filtrado_servico['Total ADT | CHD'] = df_mapa_filtrado_servico['Total ADT'] + df_mapa_filtrado_servico['Total CHD']

        df_ranking = df_mapa_filtrado_servico.groupby('1 Vendedor').agg({'Total ADT | CHD': 'sum'})\
            .sort_values(by='Total ADT | CHD', ascending=False).reset_index()

        container_2.dataframe(df_ranking, hide_index=True, use_container_width=True)

elif len(periodo)>1 and modo=='Passeios vs Vendedores':

    data_inicial = periodo[0]

    data_final = periodo[1]

    df_router_filtrado = st.session_state.mapa_router[(st.session_state.mapa_router['Data Execucao'] >= data_inicial) & 
                                                      (st.session_state.mapa_router['Data Execucao'] <= data_final) & 
                                                      (st.session_state.mapa_router['Tipo de Servico'] == 'TOUR')].reset_index(drop=True)
    
    df_sales_filtrado = st.session_state.mapa_sales_ranking[(st.session_state.mapa_sales_ranking['Data de Execucao'] >= data_inicial) & 
                                                            (st.session_state.mapa_sales_ranking['Data de Execucao'] <= data_final) & 
                                                            (st.session_state.mapa_sales_ranking['Tipo de Servico'] == 'TOUR')].reset_index(drop=True)

    df_vendedores = pd.merge(df_router_filtrado, df_sales_filtrado[['Codigo da Reserva', '1 Vendedor', 'Data de Execucao', 'Servico']], how='left', 
                             left_on=['Reserva', 'Data Execucao', 'Servico'], 
                             right_on=['Codigo da Reserva', 'Data de Execucao', 'Servico']) 
    
    df_vendedores = df_vendedores[~pd.isna(df_vendedores['1 Vendedor'])].reset_index(drop=True)
    
    lista_vendedores = df_vendedores['1 Vendedor'].unique().tolist()

    with row1[1]:

        st.write('Vendedores')

        container = st.container(height=200, border=True)

        vendedor = container.radio('', sorted(lista_vendedores), index=None)

    st.divider()

    row2 = st.columns(1)

    container_2 = st.container(border=True)

    if vendedor:

        df_mapa_filtrado_vendedor = df_vendedores[df_vendedores['1 Vendedor']==vendedor].reset_index(drop=True)

        df_mapa_filtrado_vendedor['Total ADT | CHD'] = df_mapa_filtrado_vendedor['Total ADT'] + df_mapa_filtrado_vendedor['Total CHD']

        df_ranking = df_mapa_filtrado_vendedor.groupby('Servico').agg({'Total ADT | CHD': 'sum'})\
            .sort_values(by='Total ADT | CHD', ascending=False).reset_index()

        container_2.dataframe(df_ranking, hide_index=True, use_container_width=True)

