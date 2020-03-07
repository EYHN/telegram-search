# Telegram Search Bot

这个bot从Bot：[@awesomeopensource_search_bot](http://t.me/awesomeopensource_search_bot)fork而来。

这里是为 [@awesomeopensource](https://t.me/awesomeopensource) 打造的搜索 Bot，直接发送你要搜索的内容即可。搜索支持 Lucene 语法。

同时可以为群组、频道、个人提供聊天记录搜索服务。

## 特性

* 中文分词引擎
* 可按日期搜索
* Telegram Bot 前端
* 可拓展的定制化搜索引擎

## 原理

使用 Telegram Client Api 获取频道内所有信息，并持续监听新信息。

将所有信息归档进 Elasticsearch 搜索引擎，用户可以在 Bot 前端执行搜索。

## 如何搭建

1. **前提条件**

    申请 Telegram MTProto API ID： https://my.telegram.org/app

    申请 Telegram Bot ID：[@BotFather](https://t.me/BotFather)

    准备一个 Telegram 账号

    安装 Python3：https://www.python.org/downloads/

2. **登陆**

    clone 下这个项目 

    安装依赖： `pip install -r requirements.txt`

    修改 main.py 中的配置或使用环境变量
    
    * API_ID：Telegram MTProto API ID
    * API_HASH：Telegram MTProto API ID
    * BOT_TOKEN：从 BotFather 获取的 bot token
    * CHAT_ID：你要搜索的 chat 的 ID，可以使用 [@getidsbot](https://t.me/getidsbot) 获取。
    * ADMIN_ID：管理员的 ID，可以使用 [@getidsbot](https://t.me/getidsbot) 获取。

    生成 session 文件，运行 `python main.py` 提示输入手机号和验证码即可，在目录下会生成 session 文件夹。

3. **部署**

    把 session 文件夹和源码部署到服务器。

    修改 docker-compose.yml 中的环境变量

    使用 docker-compose 部署：`docker-compose up -d`
    
    启动程序`python3 main.py`

## 继续开发

