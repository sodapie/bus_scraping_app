
import pandas as pd
import numpy as np
import seaborn as sns
import requests
from bs4 import BeautifulSoup
import re
import japanize_matplotlib
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import time
import aiohttp
import asyncio
import streamlit as st
import io

def scrape(from_where, to_where, data_list):
    base_url = f'https://www.bushikaku.net/search/{from_where}_{to_where}/'

    # 今日から一か月分の日付を取得
    data_get_date = datetime.today().strftime('%Y%m%d')

    eventdates = []
    data_get_dates = []
    starting_points = []
    starting_point_details = []
    starting_point_times = []
    destinations = []
    destination_details = []
    destination_times = []
    prices = []
    bus_cos = []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    for date in date_list:
        date_str = date.strftime("%Y%m%d")
        page_num = 1
        # 次のページがある限り処理を続行する
        while True:
            if page_num == 1:
                eachday_url = f'{base_url}{date_str}/'
            else:
                eachday_url = f'{base_url}{date_str}/page-{page_num}/'

            response = requests.get(eachday_url, headers=headers)
            if response.status_code != 200: # サイトにアクセスできない場合に処理を終了
                break

            soup = BeautifulSoup(response.content, 'html.parser')
            chunks = soup.find_all('li', class_=['SearchCardDirect_search-card__PPng1'])

            if not chunks:
                break # サイトの要素が空の時に処理を終了

            for chunk in chunks:
                # event_dateをappend
                eventdates.append(date_str)

                # data_get_dateをappend
                data_get_dates.append(data_get_date)

                # starting_pointをappend
                starting_points.append(from_where)

                # destinationをappend
                destinations.append(to_where)

                # starting_point_detail, starting_point_timeをappend
                st_element = chunk.find('div', class_='SearchCardDirect_platform-box-item-geton--target__2R6oE')
                if st_element:
                    span_tag_place = st_element.find('span', class_='SearchCardDirect_platform-box-name__tKD_I')
                    span_tag_time = st_element.find('span', class_='SearchCardDirect_platform-box-time__o58nc')
                    if span_tag_place:
                        starting_point_detail = span_tag_place.get_text(strip=True)
                        starting_point_details.append(starting_point_detail)
                    else:
                        starting_point_details.append(None)
                    if span_tag_time:
                        starting_point_time = span_tag_time.get_text(strip=True)
                        starting_point_times.append(starting_point_time)
                else:
                    starting_point_details.append(None)
                    starting_point_times.append(None)

                # destination_detail, destination_timeをappend
                dd_element = chunk.find('div', class_='SearchCardDirect_platform-box-item-getout--target__hmfCI')
                if dd_element:
                    span_tag_place = dd_element.find('span', class_='SearchCardDirect_platform-box-name__tKD_I')
                    span_tag_time = dd_element.find('span', class_='SearchCardDirect_platform-box-time__o58nc')
                    if span_tag_place:
                        destination_detail = span_tag_place.get_text(strip=True)
                        destination_details.append(destination_detail)
                    else:
                        destination_details.append(None)
                    if span_tag_time:
                        destination_time = span_tag_time.get_text(strip=True)
                        destination_times.append(destination_time)
                    else:
                        destination_times.append(None)
                else:
                    destination_details.append(None)
                    destination_times.append(None)

                # priceをappend
                td_element = chunk.find('td', class_='SearchCardStructure_structure-table-planamount-td__OgHr9')
                if td_element:
                    a_tag = td_element.find('a')
                    if a_tag:
                        # <span>タグ内の価格情報を取得
                        span_tag = a_tag.find('span', class_='SearchCardStructure_structure-table-planamount-text__NXUJI')
                        if span_tag:
                            price_text = span_tag.get_text(strip=True)
                            if '〜' in price_text:  # '〜'が含まれている場合
                                price = price_text.split('〜')[0]  # 最初の価格のみを抽出（5200~7000の時に、5200のみを抽出）
                            else:
                                price = ''.join(re.findall(r'\d+', price_text))
                            prices.append(price.replace(',', '').replace('円', ''))  # カンマや「円」を取り除きappend
                        else:
                            prices.append(None)
                    else:
                        prices.append(None)
                else:
                    prices.append(None)

                # bus_coをappend
                li_elements = chunk.find_all('li', class_='SearchCardDirect_company-list-item__BWgqU')
                if len(li_elements) > 1:
                    # 2つ目の要素を選択（予約サイトではなく、バス会社の方）
                    li_element = li_elements[1]
                    # ラベル部分を削除
                    span_label = li_element.find('span', class_='SearchCardDirect_company-list-item-label__TqCuP')
                    if span_label:
                        span_label.decompose()
                    
                    # 残りのテキストを取得してバス会社名とする
                    bus_co = li_element.get_text(strip=True)
                    bus_cos.append(bus_co)
                else:
                    bus_cos.append(None)

            # 次のページがあるか確認しなければ終了
            next_page_element = soup.find('a', text='次へ')
            if next_page_element and 'href' in next_page_element.attrs:
                page_num += 1
            else:
                break

        time.sleep(0.1)
    
    # 取得したデータをdfに変換
    df = pd.DataFrame({
        'eventdates': eventdates,
        'data_get_dates' : data_get_dates,
        'from_where': starting_points,
        'from_where_details' : starting_point_details,
        'from_where_times' : starting_point_times,
        'to_where': destinations,
        'to_where_details' : destination_details,
        'to_where_times' : destination_times,
        'prices': prices,
        'bus_cos': bus_cos
    })

    # 細かい型の調整
    df['prices'] = pd.to_numeric(df['prices'], errors='coerce').fillna(0).astype(int)

    return df

st.title('バススクレイピングアプリ')

st.markdown("<hr>", unsafe_allow_html=True)

st.markdown("""
### このアプリについて

バス比較なびサイトから以下の情報を取得します：

- `eventdates`: バスの運行日
- `data_get_dates`: 今日の日付
- `from_where`: バスの出発地
- `from_where_details`: バスの出発地の詳細
- `from_where_times`: バスの出発時間
- `to_where`: バスの到着地
- `to_where_details`: バスの到着地の詳細
- `to_where_times`: バスの到着時間
- `prices`: そのバスの複数プランの中の最低価格
- `bus_cos`: そのバスの運営会社
""")

st.markdown("<hr>", unsafe_allow_html=True)

routes_display = {
    '東京-愛知': 'tokyo-aichi', '大阪-福岡': 'osaka-fukuoka', '大阪-長崎': 'osaka-nagasaki', 
    '大阪-佐賀': 'osaka-saga', '大阪-埼玉': 'osaka-saitama', '大阪-東京': 'osaka-tokyo', 
    '愛知-東京': 'aichi-tokyo', '京都-福岡': 'kyoto-fukuoka', '京都-長崎': 'kyoto-nagasaki', 
    '兵庫-埼玉': 'hyogo-saitama', '兵庫-東京': 'hyogo-tokyo', '兵庫-千葉': 'hyogo-chiba', 
    '福岡-京都': 'fukuoka-kyoto', '福岡-大阪': 'fukuoka-osaka', '長崎-京都': 'nagasaki-kyoto', 
    '長崎-大阪': 'nagasaki-osaka', '佐賀-京都': 'saga-kyoto'
}

selected_routes_display = st.multiselect('ルートを選択してください', routes_display.keys(), default=None)

all_selected = st.checkbox('全てのルートをスクレイピング')

if all_selected:
    selected_routes_display = list(routes_display.keys())

# カレンダーから開始日と終了日を選択
start_date = st.date_input('取得対象データの開始日を選択してください')
end_date = st.date_input('取得対象データの終了日を選択してください（今日から3カ月先まで）')

if start_date > end_date:
    st.error("開始日は終了日より前でなければなりません。")

st.markdown("<hr>", unsafe_allow_html=True)

# セッションステートにデータを保持
if 'scraped_data' not in st.session_state:
    st.session_state.scraped_data = None

if st.button('スクレイピング開始'):
    all_dfs = []
    with st.spinner('スクレイピング中...'):
        # 開始日から終了日までの日付のリストを作成
        date_list = pd.date_range(start=start_date, end=end_date).to_pydatetime().tolist()

        for selected_route_display in selected_routes_display:
            from_where, to_where = routes_display[selected_route_display].split('-')
            df = scrape(from_where, to_where, date_list)
            all_dfs.append(df)
        combined_df = pd.concat(all_dfs, ignore_index=True)
        st.session_state.scraped_data = combined_df
        st.write('スクレイピング完了')

start_date = st.session_state.get('start_date', datetime.today().strftime('%Y%m%d'))
end_date = st.session_state.get('end_date', datetime.today().strftime('%Y%m%d'))
today = datetime.today().strftime('%Y%m%d')

# データがセッションステートに保存されている場合は表示
if st.session_state.scraped_data is not None and not st.session_state.scraped_data.empty:
    combined_df = st.session_state.scraped_data
    st.dataframe(combined_df)
    csv = combined_df.to_csv(index=False)
    file_name = f'bus_{start_date}_{end_date}_on_{today}.csv'
    st.download_button(
        label='CSVとしてダウンロード',
        data=csv,
        file_name=file_name,
        mime='text/csv'
    )

    try:
        # 箱ひげ図のプロット
        plt.figure(figsize=(10, 6))
        # イベント名の並び順を指定
        sorted_eventdates = combined_df['eventdates'].unique()
        sns.boxplot(data=combined_df, x='eventdates', y='prices', order=sorted_eventdates)
        plt.title('日ごとのバス価格 箱ひげ図')
        plt.xticks(fontsize=8)
        
        fig1 = plt.gcf()  # 現在のFigureを取得
        st.pyplot(fig1)
        
        # Figureをバッファに保存
        buf1 = io.BytesIO()
        fig1.savefig(buf1, format="png")
        buf1.seek(0)
        
        st.download_button(
            label="グラフを保存",
            data=buf1,
            file_name=f"bus_{start_date}_{end_date}_on_{today}_boxplot.png",
            mime="image/png"
        )
        buf1.close()
    except KeyError:
        st.error('該当するデータが見つかりませんでした')

    try:
        # 箱ひげ図のプロット
        plt.figure(figsize=(10, 6))
        # イベント名の並び順を指定
        sorted_eventdates = combined_df['eventdates'].unique()
        sns.stripplot(data=combined_df, x='eventdates', y='prices', order=sorted_eventdates)
        plt.title('日ごとのバス価格 ストリッププロット')
        plt.xticks(fontsize=8)
        
        fig2 = plt.gcf()  # 現在のFigureを取得
        st.pyplot(fig2)
        
        # Figureをバッファに保存
        buf2 = io.BytesIO()
        fig2.savefig(buf2, format="png")
        buf2.seek(0)
        
        st.download_button(
            label="グラフを保存",
            data=buf2,
            file_name=f"bus_{start_date}_{end_date}_on_{today}_stripplot.png",
            mime="image/png"
        )
        buf2.close()
    except KeyError:
        st.error('該当するデータが見つかりませんでした')
