from __future__ import unicode_literals

import argparse
import base64
import logging
import os
import threading

import requests_async as  requests
import youtube_dl
# 日志相关
from sanic import Blueprint
from sanic import Sanic
from sanic import response

app = Sanic(__name__)
blueprint = Blueprint('service')
proxies = {'http': 'http://127.0.0.1:7080',
           'https': 'http://127.0.0.1:7080'}

##初始化log
logger = logging.getLogger()
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s: - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')
# 使用StreamHandler输出到屏幕
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.setLevel(logging.INFO)

STREAM_MAP = {}
LIVE_MAP = {}


def extractStreamUrl(youtube_url):
    # 定义某些下载参数
    ydl_opts = {
        # outtmpl 格式化下载后的文件名，避免默认文件名太长无法保存
        'outtmpl': '%(id)s%(ext)s',
        # 'proxy': 'socks5://127.0.0.1:7080',
        'format': 'best',

    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(youtube_url, download=False, process=False)
        return info['formats'][-1]['url']


def processUrl(urlprefix, content):
    ss = content.split("\n")
    r = ""
    for line in ss:
        if line.startswith("#"):
            r = r + line + "\r\n"
        elif line.startswith("http"):
            r = r + urlprefix + base64.urlsafe_b64encode(line.encode(encoding="utf-8")).decode() + "\r\n"
    return r


close = False


def updateM3u8():
    logger.info("更新StreamURL")
    for k in STREAM_MAP.keys():
        if close:
            return
        url = "https://www.youtube.com/watch?v=" + k
        logger.info("更新URL=" + url)
        for x in range(0, 3):
            try:
                stream_url = extractStreamUrl(url)
                if '.m3u8' in stream_url:
                    STREAM_MAP[k] = stream_url
                    break
            except:
                pass
    threading.Timer(60 * 10, updateM3u8).start()


def initURL():

    with open("./youtube_channel.txt") as lines:
        for line in lines:
            ss = line.strip().split(",")
            if len(ss) != 2:
                continue
            if ss[1].find("https://www.youtube.com/watch?v=")<0:
                continue
            LIVE_MAP[ss[0]] = ss[1].strip().replace("https://www.youtube.com/watch?v=","")
    if len(LIVE_MAP.keys()) == 0:
        logger.info("必须要有直播定义在youtube_channel.txt中")
        os._exit(0)




    for x, v in LIVE_MAP.items():
        STREAM_MAP[v] = None


# 代理ts文件
@app.get('/live.ts', stream=True)
async def service(request):
    k = request.args['k'][0]
    ku = base64.urlsafe_b64decode(k.encode(encoding='utf-8')).decode()
    r = await requests.get(ku, stream=True)

    async def write_generator(response):
        async for chunk in r.iter_content(chunk_size=10 * 1024):
            if len(chunk) > 0:  # Skip empty bytes to avoid ending http chunking early
                await response.write(chunk)

    return response.stream(
        write_generator,
        content_type=r.headers['Content-Type']
    )


# 返回频道列表
@app.get('/ytb.m3u')
async def m3u(request):
    urlprefx = await getBaseUrl(request) + "/ytb/"
    content = "#EXTM3U\r\n"
    for k, v in LIVE_MAP.items():
        content = content + "#EXTINF:-1," + k + "\r\n" + urlprefx + v + "\r\n"
    return response.text(body=content, headers={
        'Content-type': "application/vnd.apple.mpegurl",
        'Content-Length': str(len(content))
    }, status=200)


# 将ts文件以代理列表的形式返回
@app.get('/ytb/<id:str>')
async def service(request, id):
    if id not in STREAM_MAP:
        return response.text("not found", status=404)

    url = "https://www.youtube.com/watch?v=" + id

    if id in STREAM_MAP and STREAM_MAP[id] is not None:
        stream_url = STREAM_MAP[id]
    else:
        stream_url = extractStreamUrl(url)
        if '.m3u8' not in stream_url:
            return response.text("not found", status=404)
        STREAM_MAP[id] = stream_url
    r = await requests.get(stream_url)
    if r.status_code != 200:
        return response.text("error", status=r.status_code)

    text = r.text

    urlprefx = await getBaseUrl(request) + "/live.ts?k="
    m3u8Body = processUrl(urlprefx, text)

    return response.text(body=m3u8Body, headers={
        'Content-type': "text/plain; charset=utf-8",
        'Content-Length': str(len(m3u8Body))
    }, status=200)


async def getBaseUrl(request):
    baseUrl = request.headers.get("baseUrl")
    if baseUrl is None or baseUrl == "":
        return request.scheme + "://" + request.host
    else:
        return baseUrl


@app.listener("after_server_stop")
async def closeListener(app, loop):
    global close
    close = True
    os._exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='A proxy server to get real url of live providers.')
    parser.add_argument('-p', '--port', type=int, required=False, default=5000, help='Binding port of HTTP server.')
    args = parser.parse_args()

    initURL()

    thread = threading.Thread(target=updateM3u8)
    thread.setDaemon(True)
    thread.start()

    port = int(args.port)
    logging.info('Serving HTTP on %s port %d...', "0.0.0.0", args.port)

    app.blueprint(blueprint)
    app.run(host="0.0.0.0", port=port, debug=False, access_log=False)
    logging.info('Server stopped.')
