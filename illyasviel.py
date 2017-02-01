# -*- coding: utf-8 -*-

# webhook address
# -> https://[YOUR WEBSITE]/whook/[YOUR TOKEN]
# setWebhook address
# -> https://api.telegram.org/bot[YOUR TOKEN]/setWebhook?url=https://[YOUR WEBSITE]/whook/[YOUR TOKEN]/hook

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

bot_token = '[YOUR TOKEN]'
# Tornado define
define("port", default=8022, help="run on the given port", type=int)

# Telegram Bot API URL
url = 'https://api.telegram.org/bot%s/' % bot_token
# Local URL for ImageEventHandler
bot_url = 'https://[YOUR WEBSITE]/whook/%s/' % bot_token

def illyasviel_answerInlineQuery(update: dict, queryResult: dict):
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
        # append dict into list
        for mode in range(0,2):
            tempDict = {}
            tempDict['type'] = "photo"
            tempDict['id'] = uuid.uuid4().hex
            # set size to avoid display blank picture in timeline
            if mode == 0:
                tempDict['photo_width'] = 473
                tempDict['photo_height'] = 512
            else:
                tempDict['photo_width'] = 512
                tempDict['photo_height'] = 300
            tempDict['photo_url'] = bot_url + "img?thumb=0&mode=%s&msg=%s" % (mode, queryInput)
            tempDict['thumb_url'] = bot_url + "img?thumb=1&mode=%s&msg=%s" % (mode, queryInput)
            tempDict['title'] = str(mode)
            queryResult.append(tempDict)
        # callback API
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
        # set image info
        # path prefix
        filename = "/tmp/"
        pos = 256
        font_size = 40
        font_color = (0,0,0)
        if mode == "0":
            filename += "file_50820.png" #chino
            pos = 420
            font_size = 60
        else:
            filename += "tomcat.jpg" # tom newspaper
            pos = 160
        img = Image.open(filename)
        draw = ImageDraw.Draw(img)
        # draw text
        font_path = "/tmp/apple.ttf"
        font = ImageFont.truetype(font_path, font_size)
        imgW, imgH = img.size
        textW, textH = draw.textsize(message,font=font)
        draw.text(((imgW-textW)/2,pos),message,font_color,font=font)
        # generate thumbnail
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
