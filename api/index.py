from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from api.chatgpt import ChatGPT
from apscheduler.schedulers.blocking import BlockingScheduler
import requests, json, os, datetime, configparser

line_bot_api = LineBotApi(os.getenv("LINE_CHANNEL_ACCESS_TOKEN"))
line_handler = WebhookHandler(os.getenv("LINE_CHANNEL_SECRET"))
working_status = os.getenv("DEFALUT_TALKING", default="true").lower() == "true"
yt_id = os.getenv('YT_API_KEY', None)
user_id = os.getenv('USER_ID', None)
group_id = os.getenv('GROUP_ID', None)

app = Flask(__name__)
chatgpt = ChatGPT()

def findYT(keyword):
    r = requests.get('https://www.googleapis.com/youtube/v3/search?part=snippet&q='+keyword+'&maxResults=1&order=relevance&key='+yt_id)
    data = json.loads(r.text)
    return data['items'][0]['id']['videoId']


# domain root
@app.route('/')
def home():
    return 'Hello, World!'

@app.route("/webhook", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        line_handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


@line_handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    config = configparser.ConfigParser()
    # print(os.path.join(BASE_DIR, 'config.ini'))
    config.read(os.path.join(BASE_DIR, 'config.ini'))
    if event.message.type != "text":
        return

    if event.message.text == 'ID?' or event.message.text == 'id?':
        User_ID = TextMessage(text=event.source.user_id)
        line_bot_api.reply_message(event.reply_token, User_ID)
        print('Reply User ID =>' + event.source.user_id)
    elif event.message.text == 'GroupID?':
        Group_ID = TextMessage(text=event.source.group_id)
        line_bot_api.reply_message(event.reply_token, Group_ID)
        print('Reply Group ID =>' + event.source.group_id)
        return

    if event.message.text == "柴柴說話":
        config.set('settings', 'talk', 'True')
        print(config.getboolean('settings', 'talk'))
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我可以說話囉，歡迎來跟我互動 ^_^ "))
        return

    if event.message.text == "柴柴閉嘴":
        config.set('settings', 'talk', 'False')
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「柴柴說話」 > <"))
        return

    if event.message.text.upper().startswith('CALL', 0, 4):
        result = findYT(' ',join(event.message.text.split()[1:])
        print(result)
        YT_link = 'https://www.youtube.com/watch?v=' + result
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=YT_link))
        return

    if event.message.text.startswith('柴柴',0, 4):
        chatgpt.add_msg(f"HUMAN:{event.message.text}?\n")
        reply_msg = chatgpt.get_response().replace("AI:", "", 1)
        chatgpt.add_msg(f"AI:{reply_msg}\n")
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=reply_msg))


if __name__ == "__main__":
    app.run()

