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
# scheduler = BlockingScheduler()
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
    config = configparser.ConfigParser()
    config.read('config.ini')
    if event.message.type != "text":
        return

    if event.message.text == 'GroupID?':
        Group_ID = TextMessage(text=event.source.group_id)
        line_bot_api.reply_message(event.reply_token, Group_ID)
        print ('Reply Group ID =>' + event.source.group_id)
        return

    if event.message.text == "柴柴說話":
        config['setting']['talk'] = True
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="我可以說話囉，歡迎來跟我互動 ^_^ "))
        return

    if event.message.text == "柴柴閉嘴":
        config['setting']['talk'] = False
        # working_status = False
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text="好的，我乖乖閉嘴 > <，如果想要我繼續說話，請跟我說 「柴柴說話」 > <"))
        return

    if event.message.text.upper().startswith('CALL', 0, 4):
        result = findYT(event.message.text.split(" ")[1])
        YT_link = 'https://www.youtube.com/watch?v=' + result
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage(text=YT_link))
        return

    now_hour = datetime.datetime.now().hour
    if now_hour == 8 or now_hour == 11:
        line_bot_api.push_message(
            group_id,
            TextSendMessage(text="掰掰~~"))
        config['setting']['say_hi'] = True

    if now_hour == 7 or now_hour == 10:
        print(group_id)
        print(config.getboolean('setting', 'say_hi'))
        if config.getboolean('setting', 'say_hi'):
            line_bot_api.push_message(
                group_id,
                TextSendMessage(text="信柴柴，發大財！＼(●´ϖ`●)／"))
            config['setting']['say_hi'] = False

        if config.getboolean('setting', 'talk') and event.message.text.startswith('柴柴',0, 4):
            chatgpt.add_msg(f"HUMAN:{event.message.text}?\n")
            reply_msg = chatgpt.get_response().replace("AI:", "", 1)
            chatgpt.add_msg(f"AI:{reply_msg}\n")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=reply_msg))


if __name__ == "__main__":
    app.run()

