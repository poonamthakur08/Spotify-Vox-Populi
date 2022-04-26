from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
from pymongo import MongoClient

options = webdriver.ChromeOptions()
options.add_argument("--remote-debugging-port=9222")
options.add_argument("--disable-blink-features=AutomationControlled")
options.headless = True
navegador = webdriver.Chrome('/datadrive/scrape/chromedriver', options=options)

def get_data(date):
    #navegador = webdriver.Chrome()
    cod = []
    navegador.get('https://spotifycharts.com/regional/global/daily/latest')
    DATA_CHART = date
    tmp = date.split('/')
    DATE_STANDARD = tmp[2]+'-'+tmp[0]+'-'+tmp[1]
    df = pd.read_csv('/datadrive/make_plots/maps_loc.csv')

    for I in range(1,74):
        lista_urls = navegador.find_element(By.XPATH, f'//*[@id="content"]/div/div/div/span/div[2]/div/div/div/div[1]/ul/li[{I}]').get_attribute('data-value')
        if 'global' ==lista_urls:
            three_code = "-"
            country = "Global"
        else:
            if country == 'Viet Name':
                country = 'Vietnam'
            three_code = df[df['Alpha-2 code']==' "'+lista_urls.upper()+'"']['Alpha-3 code'].values[0].split('"')[1]
            country = df[df['Alpha-2 code']==' "'+lista_urls.upper()+'"']['Country'].values[0]
        cod.append((lista_urls,country,three_code))
    data = []
    for lista_urls,country,three_code in cod:
        navegador.get(f"https://spotifycharts.com/regional/{lista_urls}/daily/{DATE_STANDARD}")
        for J in range(1,201):
            try:
                music_name = navegador.find_element(By.XPATH,f'//*[@id="content"]/div/div/div/span/table/tbody/tr[{J}]/td[4]/strong').text
                artist = navegador.find_element(By.XPATH,f'//*[@id="content"]/div/div/div/span/table/tbody/tr[{J}]/td[4]/span').text.replace("by ","")
                streams = navegador.find_element(By.XPATH,f'//*[@id="content"]/div/div/div/span/table/tbody/tr[{J}]/td[5]').text
                position = navegador.find_element(By.XPATH,f'//*[@id="content"]/div/div/div/span/table/tbody/tr[{J}]/td[2]').text
                link = navegador.find_element(By.XPATH,f'//*[@id="content"]/div/div/div/span/table/tbody/tr[{J}]/td[1]/a').get_attribute('href')
                link_img = navegador.find_element(By.XPATH,f'//*[@id="content"]/div/div/div/span/table/tbody/tr[{J}]/td[1]/a/img').get_attribute('src')


                streams = int(streams.replace(",", ""))

                one ={'Date': DATA_CHART,
                'Track URL': link,
                'Track Image': link_img,
                'Position': int(position),
                'Track Name': music_name, 
                'Artist': artist, 
                'Streams': streams,
                'Country': country,
                'Country-3': three_code
                 }
                data.append(one)
            except:
                break
        print(lista_urls,'and',date,'is done')
    
    #navegador.close()

    client = MongoClient("mongodb://localhost:27017/")
    db = client["test"]
    collection = db["top_spotify"]

    x = collection.insert_many(data)
    return date+" is done!"
    
for i in range(10,15):
    print(get_data('04/{}/2022'.format(i)))