# -*- coding: utf-8 -*-

# webhook address https://[YOUR WEBSITE]/whook/[YOUR TOKEN]
# setWebhook address
# https://api.telegram.org/bot[YOUR TOKEN]/setWebhook?url=https://[YOUR WEBSITE]/whook/[YOUR TOKEN]/hook

# import for script core part
import requests
import json
from multiprocessing import Process
import uuid
import urllib.parse
# import for picture generate
from PIL import Image,ImageFont,ImageDraw
from io import BytesIO
# import for Tornado WebHook
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.gen
from tornado.options import define, options, parse_command_line
# multi-thread async
from tornado.concurrent import run_on_executor
from concurrent.futures import ThreadPoolExecutor
import config

bot_token = config.bot_token
# Tornado define
define("port", default=8022, help="run on the given port", type=int)

url = 'https://api.telegram.org/bot%s/' % bot_token
bot_url = config.bot_callback_url

def illyasviel_answerInlineQuery(update: dict, queryResult: dict):
    # print(json.dumps(queryResult))
    r = requests.post(
        url + 'answerInlineQuery',
        data = {
            'inline_query_id': update['inline_query']['id'],
            'results': json.dumps(queryResult)
        }
    )
    print(r.content)


def illyasviel_picture(update: dict) -> bool:
    if update:
        if 'inline_query' not in update:
            return False
        queryInput = update['inline_query']['query']
        if queryInput == "":
            return False
        queryInput = urllib.parse.quote_plus(queryInput)
        queryResult = []
        for mode in range(len(config.images_dict)):
            tempDict = {}
            tempDict['type'] = "photo"
            tempDict['id'] = uuid.uuid4().hex
            tempDict['photo_width'] = config.images_dict[str(mode)][0]
            tempDict['photo_height'] = config.images_dict[str(mode)][1]
            tempDict['photo_url'] = bot_url + "img?thumb=0&mode=%s&msg=%s" % (mode, queryInput)
            tempDict['thumb_url'] = bot_url + "img?thumb=1&mode=%s&msg=%s" % (mode, queryInput)
            tempDict['title'] = str(mode)
            queryResult.append(tempDict)
        illyasviel_answerInlineQuery(update, queryResult)
    return True


def illyasviel_debug(update: dict) -> bool:
    if update:
        print(update)
    return False


def illyasviel_null(update: dict) -> bool:
    if update:
        pass
    return False


# 接收来自TG的消息请求用
class MessageEventHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(10)

    @tornado.gen.coroutine
    def post(self):
        # print(self.request.body.decode(encoding='UTF-8'))
        output_string = yield self.execute_job()
        self.write(output_string)
        self.finish()

    @run_on_executor
    def execute_job(self):
        return_string = "OK"
        update = json.loads(self.request.body.decode(encoding='UTF-8'))
        jobs = []
        for function_name in [illyasviel_picture, illyasviel_debug, illyasviel_null]:
            global_job = Process(target=function_name, args=(update,))
            jobs.append(global_job)
            global_job.start()
        jobs[-1].terminate()
        return return_string


class ImageEventHandler(tornado.web.RequestHandler):
    executor = ThreadPoolExecutor(10)

    @tornado.gen.coroutine
    def get(self):
        output_data = yield self.execute_job()
        self.set_header("Content-Type", "image/jpeg")
        self.write(output_data)
        self.finish()

    @run_on_executor
    def execute_job(self):
        mode = self.get_argument("mode")
        message = self.get_argument("msg")
        thumb = self.get_argument("thumb")
        # load setting
        pos = config.images_dict[mode][2]
        font_size = config.images_dict[mode][3]
        font_color = config.images_dict[mode][4]
        filename = config.image_path + config.images_dict[mode][5]
        # gen picture
        img = Image.open(filename)
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(config.font_path, font_size)
        imgW, imgH = img.size
        textW, textH = draw.textsize(message,font=font)
        # print(textW, textH)
        draw.text(((imgW-textW)/2,pos),message,font_color,font=font)
        # thumb
        if thumb == "1":
            img.thumbnail((300,300),Image.ANTIALIAS)
        # gen file pointer
        img_io = BytesIO()
        img.save(img_io, 'JPEG', quality=100)
        img_io.seek(0)
        # return picture
        return img_io.getvalue()


if __name__ == "__main__":
    parse_command_line()
    app = tornado.web.Application(handlers=[
        (r"/hook", MessageEventHandler),
        (r"/img", ImageEventHandler)
    ])
    http_server = tornado.httpserver.HTTPServer(app)
    http_server.listen(options.port, address="127.0.0.1")
    tornado.ioloop.IOLoop.instance().start()
