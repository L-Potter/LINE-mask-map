# elasticsearch.exceptions.TransportError: TransportError(503,'search_phase_execution_exception')
# equests.exceptions.ConnectionError: HTTPSConnectionPool(host='/v2/bot/message/reply', port=443): Max retries exceeded with url api.line.me

from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage,AudioMessage, TextSendMessage,LocationMessage,LocationSendMessage,FlexSendMessage
)

from ESDB import logfunc, es_search
import requests
import time
from pydub import AudioSegment
import tempfile
import os
from speech_recognition import olami_cloud_speech_reconition

def get_nearly_drugstore(lat,lon,fr=0,sz=10):
    body = {
        "from": fr,
        "size": sz, 
        "sort" : [
            {
                "_geo_distance" : {
                    "location" : {
                            "lat" : lat,
                            "lon" : lon
                        },
                    "order" : "asc",
                    "unit" : "km",
                    "mode" : "min",
                    "distance_type" : "arc",
                    "ignore_unmapped": True
                }
            }
        ],
        "query" : {
            "bool" : {
                "must" : {
                    "match_all" : {}
                }
            }
        }
    }
    return es_search(body=body)




app = Flask(__name__)

line_bot_api = LineBotApi('R+6qAADfXRVsKuVHCiP8Z4FUIie15fOH7vt9jFL2pLaPlhB8JBaimO37YrxqC+k+wN0nknlbz3Zu2wqxk4hchUBeVKbTp011pKKJ1jKy4K6uapj4wVvDXhxLcXmfWleLIysBq+Bl7EWiBpzOkI1v4gdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('c4c5245f608da6d30c2d843b79017a5a')


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

def flex_message_single_card(store_name,num_adult,num_chlid,phone,address): #all string so need to convert to str
    data = {
            "type": "bubble",
            "size": "micro",
            
            "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                "type": "text",
                "text": store_name,
                "weight": "bold",
                "size": "sm"
                },
                {
                "type": "box",
                "layout": "baseline",
                "contents": [
                    {
                    "type": "text",
                    "text": "成人口罩數量",
                    "size": "sm",
                    "color": "#8c8c8c",
                    "margin": "md",
                    "flex": 0
                    },
                    {
                    "type": "text",
                    "text": f": {num_adult}",
                    "align": "center"
                    }
                ]
                },
                {
                "type": "box",
                "layout": "baseline",
                "contents": [
                    {
                    "type": "text",
                    "text": "兒童口罩數量",
                    "size": "sm",
                    "color": "#8c8c8c",
                    "margin": "md",
                    "flex": 0
                    },
                    {
                    "type": "text",
                    "text": f": {num_chlid}",
                    "align": "center"
                    }
                ]
                },
                {
                "type": "button",
                "action": {
                    "type": "uri",
                    "label": "導航",
                    "uri": f"https://www.google.com/maps/dir/?api=1&destination={address}"
                },
                "position": "relative",
                "margin": "sm",
                "height": "md",
                "style": "link",
                "offsetTop": "-10px"
                },
                {
                "type": "button",
                "action": {
                    "type": "uri",  #if url "message": "invalid uri scheme"
                    "label": "聯絡商家",
                    "uri": f"tel:{phone}",
                },
                "position": "relative",
                "offsetEnd": "0px",
                "offsetTop": "-30px"
                },
                {
                "type": "button",
                "action": {
                    "type": "uri",
                    "label": "商家資訊",
                    "uri": f"https://www.google.com/maps/search/?api=1&query={store_name}"
                },
                "position": "absolute",
                "offsetTop": "150px",
                "offsetStart": "32px"
                }
            ],
            "spacing": "sm",
            "paddingAll": "13px"
            }
        }
    return data

###test_data
# _test_data=[]
# data1=["大愛藥局","金門縣金城鎮東門里民族路１６號","(082)312266","106","90"]
# data2=["安康藥局","花蓮縣吉安鄉中山路三段３８４號","(03)8513951","0","765"]
# _test_data.append(data1)
# _test_data.append(data2)

@handler.default()
def default(event):
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage("請點選選單並點選地圖定位，回傳藥局是依照兩點最近距離開始排序")
    )

# from pydub import AudioSegment
# /usr/local/bin/ffmpeg
@handler.add(MessageEvent, message=AudioMessage)
def handle_audio_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    ext = 'mp3'
    try:
        with tempfile.NamedTemporaryFile(prefix=ext + '-', dir='.',delete=False) as tf:
            for chunk in message_content.iter_content():
                tf.write(chunk)
            tempfile_path = tf.name
        tmpfile = tempfile_path 
        AudioSegment.converter = '/usr/local/bin/ffmpeg'
        sound = AudioSegment.from_file_using_temporary_files(tmpfile)
        path = os.path.splitext(tmpfile)[0]+'.wav'
        os.remove(tmpfile)
        sound.export(path, format="wav")
        print(f"path:{path}")
        # with sr.AudioFile(path) as source:
        #     audio = r.record(source)
        filename = os.path.split(path)[1]
        
        print(f"filename:{filename}")
    except Exception as e:
        t = '音訊有問題'+test+str(e.args)+path
        line_bot_api.reply_message(event.reply_token,TextSendMessage(text=t))

    responsedata = olami_cloud_speech_reconition("./"+filename)
    if (responsedata == "error"):
        responsedata="資料錯誤請再傳一次資料"
    line_bot_api.reply_message(event.reply_token,TextSendMessage(text=responsedata))
    #time.sleep(60)
    #line_bot_api.push_message(event.source.user_id, TextSendMessage(text=responsedata))
    os.remove(path)
    # text = r.recognize_google(audio,language='zh-TW')
    # line_bot_api.reply_message(event.reply_token,TextSendMessage(text='你的訊息是=\n'+text))

@handler.add(MessageEvent, message=LocationMessage)
def handle_message(event):
    #app.logger.info(str(event.message.latitude)+", "+str(event.message.longitude))
    _contents={
        "type": "carousel",
        "contents": []
    }
    results = get_nearly_drugstore(lat=event.message.latitude,lon=event.message.longitude)
    #app.logger.info(f"results:\n{results}")
    store_Data=results["hits"]["hits"]
    for i in store_Data:
        data = i["_source"]
        dard_info = flex_message_single_card(data["name"],data["adult_num"],data["child_num"],data["phone"],data["address"])
        _contents["contents"].append(dard_info)
    #app.logger.info(f"_contents:\n{_contents}")
    # line_bot_api.reply_message(
    #         event.reply_token,
    #         # event.message.latitude  float
    #         #TextSendMessage(text=str(event.message.latitude)+", "+str(event.message.longitude)))
    #         # LocationSendMessage( title=event.message.title,address=event.message.address,latitude=event.message.latitude,longitude=event.message.longitude))
    #         FlexSendMessage(
    #             alt_text='藥局資料',
    #             contents=_contents
    #         )
    #     )
    try:
        line_bot_api.reply_message(
            event.reply_token,
            # event.message.latitude  float
            #TextSendMessage(text=str(event.message.latitude)+", "+str(event.message.longitude)))
            # LocationSendMessage( title=event.message.title,address=event.message.address,latitude=event.message.latitude,longitude=event.message.longitude))
            FlexSendMessage(
                alt_text='藥局資料',
                contents=_contents
            )
        )
    except requests.exceptions.ConnectionError:
        time.sleep(1)
        line_bot_api.reply_message(
            event.reply_token,
            FlexSendMessage(
                alt_text='藥局資料',
                contents=_contents
            )
        )

"""
Request body: {"events":[{"type":"message","replyToken":"...","source":{"userId":"...","type":"user"},"timestamp":1585830151427,"mode":"active","message":{"type":"location","id":"11712728183687","address":"315台灣新竹縣峨眉鄉西富興頭","latitude":24.696221,"longitude":120.985976}}],"destination":"Uad64b500543e0c0128d82cb9261d32e4"}
"""

if __name__ == "__main__":
    app.debug = True
    app.run()