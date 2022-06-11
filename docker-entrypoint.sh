#!/bin/bash

pyfile=/app/ytb_proxy.py
if [ ! -f "$pyfile" ]; then
        echo '首次启动,初始化文件'
        cp /code/* /app/
fi

##启动服务
python /app/ytb_proxy.py -p 5000