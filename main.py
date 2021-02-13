import investpy as inp
import yfinance as yf

from datetime import datetime, timedelta 
from dateutil.relativedelta import relativedelta
import pandas as pd
import streamlit as st
from googletrans import Translator

@st.cache
def get_companies():
    companies=inp.get_stocks(country='turkey')
    companies.columns=['Ülke','Kısa İsim','Şirket','ISIN','Para Birimi','Sembol']
    companies=companies.set_index('Sembol')
    return companies

@st.cache()
def get_comp_data(symbol):
    end_date=datetime.now()
    start_date=end_date-timedelta(days=2000)
    
    df = inp.get_stock_historical_data(
        stock=symbol, 
        country='turkey', 
        from_date=start_date.strftime('%d/%m/%Y'), 
        to_date=end_date.strftime('%d/%m/%Y'), 
        as_json=False, 
        order='ascending'
    )
    return df

@st.cache()
def get_company_summary(symbol):

    summary_text=inp.get_stock_company_profile(stock=symbol,country='turkey')['desc']
    return summary_text

@st.cache()
def get_company_info(symbol):
    summary_text=inp.get_stock_information(stock=symbol,country='turkey').set_index('Stock Symbol')
    return summary_text

@st.cache()
def translate_text(txt):
    translator = Translator(service_urls=['translate.googleapis.com'])
    x=translator.translate(txt,src='en', dest='tr')
    return x.text

def main():
    companies = get_companies()
    title = st.title('BİST İnceleme')
    st.sidebar.title("Seçenekler")
    subheader=st.subheader('')

    def label(symbol):
        a = companies.loc[symbol]
        return symbol + ' - ' + a['Kısa İsim']

    if st.sidebar.checkbox('Şirket Veri Seti'):
        st.dataframe(companies)
    st.sidebar.subheader('Şirket Seçimi')
    asset = st.sidebar.selectbox('Aşağıdaki listeden incelemek istediğiniz şirketi seçin',
                                 companies.index.sort_values(), index=3,
                                 format_func=label)
    subheader.title(companies.loc[asset]['Kısa İsim'])


    col1, col2 = st.beta_columns(2)
    company_info=get_company_info(asset)
    arr_len=len(company_info.loc[asset])

    col1.table(company_info.loc[asset][arr_len//2:])
    col2.table(company_info.loc[asset][:arr_len//2])    

    if st.sidebar.checkbox('Şirket Amaç ve Konusu', False):      

        en_summary_text=get_company_summary(asset)
        tr_summary_text=translate_text(en_summary_text)

        show_summary_text=en_summary_text

        if st.checkbox('Bilgileri Türkçeye Çevir',False):
            show_summary_text=tr_summary_text
        
        summary_text=st.markdown(show_summary_text)


        
        
        
    
    

    data0 = get_comp_data(asset)
    data = data0.copy().dropna()
    data.index.name = None

    section = st.sidebar.slider('Geriye Dönük Veri Sayısı', 
                                min_value=30,
                                max_value=min([2000, data.shape[0]]),
                                value=500,  
                                step=10)
    data2 = data[-section:]['Close'].to_frame('Close')

    sma = st.sidebar.checkbox('1. Yürüyen Ortalama')

    if sma:
        period= st.sidebar.slider('1. Yürüyen Ortalama Periyodu', min_value=5, max_value=500,
                             value=20,  step=1)
        data[f'1. Yürüyen Ortalama {period}'] = data['Close'].rolling(period ).mean()
        data2[f'1. Yürüyen Ortalama {period}'] = data[f'1. Yürüyen Ortalama {period}'].reindex(data2.index)

    sma2 = st.sidebar.checkbox('2. Yürüyen Ortalama')
    if sma2:
        period2= st.sidebar.slider('2. Yürüyen Ortalama Periyodu', min_value=5, max_value=500,
                             value=100,  step=1)
        data[f'2. Yürüyen Ortalama {period2}'] = data['Close'].rolling(period2).mean()
        data2[f'2. Yürüyen Ortalama {period2}'] = data[f'2. Yürüyen Ortalama {period2}'].reindex(data2.index)

    st.subheader('Chart')
    st.line_chart(data2)

    if st.sidebar.checkbox('İstatistik Bilgiler'):
        st.subheader(f'{asset} İstatistik Bilgileri')
        st.table(data2.describe())

    if st.sidebar.checkbox('Geçmiş Veriler'):
        st.subheader(f'{asset} Geçmiş Verileri')
        st.write(data2)


if __name__ == '__main__':
    main()