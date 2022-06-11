FROM python:3.8.0-slim-buster

RUN pip3 install requests -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install requests_async -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install youtube-dl -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip3 install sanic -i https://pypi.tuna.tsinghua.edu.cn/simple

#工作目录
WORKDIR /code
#复制代码
COPY . .
#暴露端口
EXPOSE 5000
#暴露目录
VOLUME ["/app"]

RUN chmod 777 /code/docker-entrypoint.sh

#运行项目
CMD ["/code/docker-entrypoint.sh"]