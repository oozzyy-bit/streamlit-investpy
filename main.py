import investpy as inp
from datetime import datetime, timedelta 
import streamlit as st
from googletrans import Translator
import plotly.figure_factory as ff
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup


st.set_page_config(
    page_title='BİST İnceleme', 
    page_icon=None, 
    layout='wide', 
    initial_sidebar_state='auto'
)

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

@st.cache()
def get_company_logo_url(symbol):
        try:
            base_url='https://www.kap.org.tr'
            page=requests.get(f'{base_url}/tr/bist-sirketler').content
            soup = BeautifulSoup(page, 'html.parser')
            element=soup.find(lambda tag:tag.name=="a" and symbol in tag.text)
            page2=requests.get(base_url+element['href']).content
            soup2 = BeautifulSoup(page2, 'html.parser')
            logo_url = base_url+soup2.find("img", {"class": "comp-logo"})['src']
            return logo_url 
        except:
            return 'https://www.designfreelogoonline.com/wp-content/uploads/2014/12/00240-Design-Free-3D-Company-Logo-Templates-03.png'


def main():
    companies = get_companies()
    title = st.title('BİST Veri İnceleme')
    st.sidebar.title("Seçenekler")

    def label(symbol):
        a = companies.loc[symbol]
        return symbol + ' - ' + a['Kısa İsim']

    if st.sidebar.checkbox('Şirket Veri Seti'):
        st.dataframe(companies)
    st.sidebar.subheader('Şirket Seçimi')
    asset = st.sidebar.selectbox('Aşağıdaki listeden istediğiniz şirketi seçebilirsiniz.',
                                 companies.index.sort_values(), index=3,
                                 format_func=label)
    

    header_col1, header_col2,header_col3 = st.beta_columns(3) 

    header_col1.image(
            get_company_logo_url(asset),
            width=100, # Manually Adjust the width of the image as per requirement
        )

    subheader=header_col1.markdown(companies.loc[asset]['Şirket'])                         
    
    company_info=get_company_info(asset)
    arr_len=len(company_info.loc[asset])

    header_col2.table(company_info.loc[asset][arr_len//2:])
    header_col3.table(company_info.loc[asset][:arr_len//2])    

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
    data.columns=['Açılış', 'Yüksek', 'Düşük','Kapanış', 'Hacim','Para Birimi']

    section = st.sidebar.slider('Geriye Dönük Veri Sayısı', 
                                min_value=30,
                                max_value=min([2000, data.shape[0]]),
                                value=500,  
                                step=10)

    

    st.sidebar.subheader('Grafik Seçimi')
    graph_types=(
        'Çizgi Grafiği',
        'Alan Grafiği',
        'Mum Grafiği'
    )
    selected_graph_type = st.sidebar.selectbox(
        'Aşağıdaki listeden grafik çeşidini seçebilirsiniz.',
        graph_types
    )

    if selected_graph_type == 'Alan Grafiği':
        st.subheader('Grafik Veri Seçimi')
        option = st.selectbox(
            'Grafikte Kullanılacak Veri',
            data.columns[:-1],
            index=3
        )

        data2 = data[-section:][option].to_frame(option)

        st.subheader(f'{asset} {option} {selected_graph_type}')
        st.area_chart(data2)

    elif selected_graph_type == 'Çizgi Grafiği':
        st.subheader('Grafik Veri Seçimi')
        option = st.selectbox(
            'Grafikte Kullanılacak Veri',
            data.columns[:-1],
            index=3
        )

        data2 = data[-section:][option].to_frame(option)

        st.subheader(f'{asset} {option} {selected_graph_type}')

        using_pred_model = st.sidebar.checkbox('Analiz Modeli')
        if using_pred_model:
            pred_model_list=[
                'Yürüyen Ortalama',
                'Yürüyen Standart Sapma',
                'Lineer Regresyon'
            ]
            pred_model = st.selectbox(
                'Analiz Modeli Seçimi',
                pred_model_list
            )
            
            if pred_model=='Lineer Regresyon':

                lin_reg_col1, lin_reg_col2 = st.beta_columns(2)

                lin_reg_degree= lin_reg_col1.slider('Lineer Regresyon Derecesi', min_value=0, max_value=20,
                                value=5,  step=1)
                pred_days=lin_reg_col2.slider('Tahmin Edilecek Gün Sayısı', min_value=1, max_value=90,
                                value=30,  step=1)
                xaxis = range(len(data2.index))
                coefficients = np.polyfit(xaxis,data2[option],lin_reg_degree)
                f = np.poly1d(coefficients)
                #y_pred=[f(x) for x in xaxis]
                #data2['Lineer Regresyon']=y_pred

                y_pred={'lin_reg':[f(x) for x in range(len(xaxis)+pred_days)]}
                new_x=data2.index.to_list()+[data2.index.to_list()[-1]+timedelta(days=i) for i in range(1,pred_days+1)]
                new_df = pd.DataFrame(y_pred, index = new_x) 

                data2=pd.concat([data2, new_df], axis=1)

                main_chart=st.line_chart(data2)


            elif pred_model=='Yürüyen Ortalama':

                sma_1_col1, sma_1_col2 = st.beta_columns(2)
               
                sma = sma_1_col1.checkbox('1. Yürüyen Ortalama',True)
                if sma:
                    period= sma_1_col2.slider('1. Yürüyen Ortalama Periyodu', min_value=5, max_value=500,
                                        value=20,  step=1)
                    data[f'1. Yürüyen Ortalama {period}'] = data[option].rolling(period ).mean()
                    data2[f'1. Yürüyen Ortalama {period}'] = data[f'1. Yürüyen Ortalama {period}'].reindex(data2.index)

                sma_2_col1, sma_2_col2 = st.beta_columns(2)
                sma2 = sma_2_col1.checkbox('2. Yürüyen Ortalama')
                if sma2:
                    period2= sma_2_col2.slider('2. Yürüyen Ortalama Periyodu', min_value=5, max_value=500,
                                        value=100,  step=1)
                    data[f'2. Yürüyen Ortalama {period2}'] = data[option].rolling(period2).mean()
                    data2[f'2. Yürüyen Ortalama {period2}'] = data[f'2. Yürüyen Ortalama {period2}'].reindex(data2.index)

                main_chart=st.line_chart(data2)

            elif pred_model=='Yürüyen Standart Sapma':

                stdev_1_col1, stdev_1_col2 = st.beta_columns(2)
               
                stdev1 = stdev_1_col1.checkbox('1. Yürüyen Standart Sapma',True)

                go_stdev_main=go.Scatter(
                    name= asset,
                    x=data2[option].index,
                    y=data2[option],
                    mode='lines',
                    line=dict(color='rgb(31, 119, 180)')
                )
                
                if stdev1:
                    period= stdev_1_col2.slider('1. Yürüyen Standart Sapma Periyodu', min_value=7, max_value=90,
                                        value=7,  step=1)

                    data[f'1. Yürüyen Standart Sapma Üst - {period}'] = data[option] + data[option].rolling(period).std()*2 
                    data[f'1. Yürüyen Standart Sapma Alt - {period}'] = data[option] - data[option].rolling(period).std()*2
                    data2[f'1. Yürüyen Standart Sapma Üst - {period}'] = data[f'1. Yürüyen Standart Sapma Üst - {period}'].reindex(data2.index)
                    data2[f'1. Yürüyen Standart Sapma Alt - {period}'] = data[f'1. Yürüyen Standart Sapma Alt - {period}'].reindex(data2.index)


                    go_stdev_1_upper=go.Scatter(
                        name='1. Üst Sınır',
                        x=data2[option].index,
                        y=data2[f'1. Yürüyen Standart Sapma Üst - {period}'],
                        mode='lines',
                        marker=dict(color="#633"),
                        line=dict(width=0),
                        showlegend=False
                    )

                    go_stdev_1_lower=go.Scatter(
                        name='1. Alt Sınır',
                        x=data2[option].index,
                        y=data2[f'1. Yürüyen Standart Sapma Alt - {period}'],
                        marker=dict(color="#633"),
                        line=dict(width=0),
                        mode='lines',
                        fillcolor='rgba(90, 40, 40, 0.3)',
                        fill='tonexty',
                        showlegend=False
                    )

                stdev_2_col1, stdev_2_col2 = st.beta_columns(2)
               
                stdev2 = stdev_2_col1.checkbox('2. Yürüyen Standart Sapma',False)

                if stdev2:
                    period2= stdev_2_col2.slider('2. Yürüyen Standart Sapma Periyodu', min_value=7, max_value=90,
                                        value=28,  step=1)

                    data[f'1. Yürüyen Standart Sapma Üst - {period2}'] = data[option] + data[option].rolling(period2).std()*2 
                    data[f'1. Yürüyen Standart Sapma Alt - {period2}'] = data[option] - data[option].rolling(period2).std()*2
                    data2[f'1. Yürüyen Standart Sapma Üst - {period2}'] = data[f'1. Yürüyen Standart Sapma Üst - {period2}'].reindex(data2.index)
                    data2[f'1. Yürüyen Standart Sapma Alt - {period2}'] = data[f'1. Yürüyen Standart Sapma Alt - {period2}'].reindex(data2.index)


                    go_stdev_2_upper=go.Scatter(
                        name='2. Üst Sınır',
                        x=data2[option].index,
                        y=data2[f'1. Yürüyen Standart Sapma Üst - {period2}'],
                        mode='lines',
                        marker=dict(color="#a88"),
                        line=dict(width=0),
                        showlegend=False
                    )

                    go_stdev_2_lower=go.Scatter(
                        name='2. Alt Sınır',
                        x=data2[option].index,
                        y=data2[f'1. Yürüyen Standart Sapma Alt - {period2}'],
                        marker=dict(color="#a88"),
                        line=dict(width=0),
                        mode='lines',
                        fillcolor='rgba(170, 100, 100, 0.15)',
                        fill='tonexty',
                        showlegend=False
                    )

                stdev_data=[go_stdev_main]

                try:
                    stdev_data.append(go_stdev_1_upper)
                    stdev_data.append(go_stdev_1_lower)
                except:
                    pass

                try:
                    stdev_data.append(go_stdev_2_upper)
                    stdev_data.append(go_stdev_2_lower)
                except:
                    pass
                    
                stdev_fig = go.Figure(stdev_data)
                stdev_fig.update_layout(
                    hovermode="x"
                )
                conf={'scrollZoom': True}
                st.plotly_chart(stdev_fig, use_container_width=True,scroll_zoom= True,config=conf)
        else:
            main_chart=st.line_chart(data2)

                

                


        


    elif selected_graph_type == 'Mum Grafiği':

        st.subheader(f'{asset} {selected_graph_type}')

        candlestick_data=data[-section:]

        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=candlestick_data.index,
                    open=candlestick_data['Açılış'],
                    high=candlestick_data['Yüksek'],
                    low=candlestick_data['Düşük'],
                    close=candlestick_data['Kapanış']
                )
            ]
        )
        fig.update_layout(
            hovermode="x",
            yaxis_title='Ortalama Değer (TL)',
            title=f'{asset} Yürüyen Standart Sapma Grafiği',
        )
        conf={'scrollZoom': True}
        st.plotly_chart(fig, use_container_width=True,scroll_zoom= True,config=conf)


        
    elif selected_graph_type=='Mum Grafiği':
        pass
        

    if st.sidebar.checkbox('İstatistik Bilgiler'):
        st.subheader(f'{asset} İstatistik Bilgileri')
        st.table(data2.describe())

    if st.sidebar.checkbox('Geçmiş Veriler'):
        st.subheader(f'{asset} Geçmiş Verileri')
        st.write(data2)


if __name__ == '__main__':
    main()