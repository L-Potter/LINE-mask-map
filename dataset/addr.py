import requests
import json
import twd97
from requests.exceptions import RequestException,ReadTimeout,ConnectionError,SSLError
import urllib3
import time
from selenium import webdriver
import csv
from ESDB import logfunc, es_search, es_update, es_count, es
import subprocess

# InsecureRequestWarning: Unverified HTTPS request is being made.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
url="https://map.tgos.tw/TGOSCloud/Generic/Project/GHTGOSViewer_Map.ashx?pagekey=mtjd5vY3d54b5kdpdDJSEpwgUt8JOTDB"

class Session_Expired_Error(Exception):
    pass

def Get_SessionID():
    chrome_options = webdriver.ChromeOptions()

    #https://peter.sh/experiments/chromium-command-line-switches/
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-gpu-sandbox")
    chrome_options.add_argument("--disable-accelerated-2d-canvas")
    #init webdriver
    browser = webdriver.Chrome(options=chrome_options)
    browser.get('https://map.tgos.tw/TGOSCloud/Web/Map/TGOSViewer_Map.aspx?addr=%E6%A1%83%E5%9C%92%E5%B8%82%E9%BE%9C%E5%B1%B1%E5%8D%80%E6%96%87%E5%8C%96%E4%B8%80%E8%B7%AF250%E8%99%9F')
    
    # Get CTK 
    CTK = browser.get_cookie('CTK')
    CTK=CTK['value']
    print(f'CTK:{CTK}')
    
    # Get SessionID
    NET_SessionId = browser.get_cookie('ASP.NET_SessionId')
    NET_SessionId=NET_SessionId['value']
    print(f'NET_SessionId:{NET_SessionId}')
    
    browser.delete_all_cookies()
    browser.quit()
    return NET_SessionId,CTK


def request_addr(address,seesion_id,CTK):
    headers = {
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Host":"map.tgos.tw",
        "Origin":"https://map.tgos.tw",
        "Referer":"https://map.tgos.tw/TGOSCloud/Web/Map/TGOSViewer_Map.aspx?addr=%E6%96%87%E5%8C%96%E4%B8%80%E8%B7%AF240%E8%99",
        "Sec-Fetch-Dest":"empty",
        "Sec-Fetch-Mode":"cors",
        "Sec-Fetch-Site":"same-origin",
        "User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
        "X-Requested-With":"XMLHttpRequest"
    }
    cookies = {
        "ASP.NET_SessionId":f"{seesion_id}",
        "CTK":f"{CTK}",
        "G_ENABLED_IDPS":"google"
    }
    data = {
        "method":"querymoiaddr",
        "address": f"{address}",
        "useoddeven": "false",
        "sid": f"{seesion_id}"
    }
    try:
        resp = requests.post(url,headers = headers, cookies=cookies,data=data, verify=False, timeout=30)
    except (ReadTimeout,ConnectionError,SSLError):
        resp = requests.post(url,headers = headers, cookies=cookies,data=data, verify=False, timeout=30)
    data = resp.content.decode('utf-8')
    #print(resp.status_code)
    #print(data) #str
    if(data=="超過 Session 的最大呼叫次數."):
        raise Session_Expired_Error
    data1= data.split("X\":")[1]
    data2= data1.split(",\r\n      \"Y\":")
    _X= float(data2[0])
    data3= data2[1].split("\r\n")
    _Y = float(data3[0])
    #data_json=json.loads(data)
    Ans = twd97.towgs84(_X, _Y) #tuple
    Latitude=Ans[0]
    longitude=Ans[1] #經度
    return Latitude,longitude


class DATA_Error(Exception):
    pass

class ES_Error(Exception):
    pass

def create_or_update_doc(form):
    try:
        if not form["adult_num"] or not form["child_num"] or not form["code"]: #adult_num
            raise DATA_Error
    except KeyError:
        raise DATA_Error
    res = es_search(body={
        "query": {
            "bool": {
                "must": {"match_phrase": {"code": form["code"]}}
            }
        }
    })
    if not res:
        raise ES_Error
    if len(res['hits']['hits']) == 0:
        # Create data
        # print(form)
        es.index(index="mask_data", body=form)
    else:
        res = es_update(_id=res["hits"]["hits"][0]["_id"],
                        body={"doc": {"adult_num": form["adult_num"],
                                      "child_num": form["child_num"],
                                      "datetime": form["datetime"]
                                    }
                              }
                        )
        if not res:
            raise ES_Error

def detect_new_data():
    tmp_csv,new_data,already_data=([] for i in range(3))  #醫事機構代碼	醫事機構名稱	醫事機構地址	醫事機構電話	成人口罩剩餘數	兒童口罩剩餘數	來源資料時間
    with open('maskdata.csv', newline='') as csv_in_file:
        has_header = csv.Sniffer().has_header(csv_in_file.read(1024))
        csv_in_file.seek(0)  # Rewind.
        rows = csv.reader(csv_in_file)
        if has_header:
            next(rows)
        for row in rows:
            tmp_csv.append(row)#list         
    for i in tmp_csv:
        res = es_search(body={
            "query": {
                "bool": {
                    "must": {"match_phrase": {"code": i[0]}}
                }
            }
        })
        if not res:
            continue
        if len(res['hits']['hits']) == 0:
            new_data.append(i)
        else:
            already_data.append(i)
    return new_data,already_data

if __name__ == "__main__":

    while(True):
        exe_code = subprocess.run(["curl","-o","maskdata.csv","https://data.nhi.gov.tw/resource/mask/maskdata.csv"])
        try:
            subprocess.CompletedProcess.check_returncode(exe_code)
        except subprocess.CalledProcessError:
            logfunc("wget error")
            time.sleep(3600)
            continue
        

        session_id,CTK=Get_SessionID()
        try: 
            new_data,already_data=detect_new_data()
        except UnicodeDecodeError:
            continue
        logfunc("new data:",len(new_data))
        logfunc("already data:",len(already_data))
        for i in new_data:
            #print(f'data:{i}')
            try:       
                lat,lon=request_addr(i[2],session_id,CTK)
            except Session_Expired_Error:
                session_id,CTK=Get_SessionID()
            except IndexError:
                lat=0.0
                lon=0.0
            #print(f"lat:{lat}",sep=" ")
            #print(f"lon:{lon}")
            #addr
            # i.append(lat)
            #i.append(lon)
            data={
                "name":i[1],
                "code":i[0],
                "address":i[2],
                "phone":i[3],
                "adult_num":i[4],
                "child_num":i[5],
                "datetime":i[6],
                "location":{
                    "lon": lon,
                    "lat": lat
                }
            }
            try:
                create_or_update_doc(data)
            except (DATA_Error,ES_Error):
                logfunc("'wrong new data':", data)

        for i in already_data:
            data={
                "code":i[0],
                "adult_num":i[4],
                "child_num":i[5],
                "datetime":i[6]
            }
            try:
                create_or_update_doc(data)
            except (DATA_Error,ES_Error):
                logfunc("'wrong data':", data)
        time.sleep(180)


    # with open('output.csv','w',newline='') as csv_out_file:
    #     writer=csv.writer(csv_out_file)
    #     for i in tmp_csv:
    #         writer.writerow(i)

    