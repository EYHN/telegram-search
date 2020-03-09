from telethon import TelegramClient, events, Button
import socks
import asyncio
import html
import os
from datetime import datetime
from config import config_redis_host, config_redis_port, config_elastic_url
from config import config_api_id, config_api_hash, config_bot_token
from config import config_admin_id, config_chat_id

REDIS_HOST = "REDIS_HOST" in os.environ and os.environ["REDIS_HOST"] or config_redis_host
REDIS_PORT = "REDIS_PORT" in os.environ and os.environ["REDIS_PORT"] or config_redis_port
ELASTIC_URL = "ELASTIC_URL" in os.environ and os.environ["ELASTIC_URL"] or config_elastic_url
API_ID = "API_ID" in os.environ and os.environ["API_ID"] or config_api_id
API_HASH = "API_HASH" in os.environ and os.environ["API_HASH"] or config_api_hash
BOT_TOKEN = "BOT_TOKEN" in os.environ and os.environ["BOT_TOKEN"] or config_bot_token
CHAT_ID = "CHAT_ID" in os.environ and os.environ["CHAT_ID"] or config_chat_id
ADMIN_ID = "ADMIN_ID" in os.environ and os.environ["ADMIN_ID"] or config_admin_id


from elasticsearch import Elasticsearch
es = Elasticsearch([ELASTIC_URL])

import redis
db = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# https://docs.telethon.dev/en/latest/basic/signing-in.html
api_id = str(API_ID)
api_hash = API_HASH
bot_token = BOT_TOKEN

#proxy = (socks.SOCKS5, '127.0.0.1', 1086)
proxy = None

chat_id = int(CHAT_ID)
admin_id = int(ADMIN_ID)



help_message = '''
这里是telegram中文搜索bot，请点击我的头像，打开和我的对话框，直接发送您想搜索的内容。搜索支持Lucene 语法。示例如下：
1. 如果您想搜索黄金，则发送
哇哈哈

2. 如果您想搜索黄金以及购买两个关键词，则发送：
+哇哈哈 +购买 

3. 如果您想搜索某用户说过的关于黄金的话，则发送：
+哇哈哈 +name:noone

4. 如果您想搜索某天出现的关于黄金的记录，则发送：
+哇哈哈 +date:2020-3-8

5. 如果您想搜索某个时间段内出现的关于黄金的记录，则发送:
+哇哈哈 +date:[2020-3-1 TO 2020-3-8]

6. 上述方式可以组合，例如：
+哇哈哈 +date:[2020-3-1 TO 2020-3-8] +name:noone

'''

welcome_message = '''
这里是telegram的中文搜索bot，请点击我的头像，打开和我的对话框，直接发送您想搜索的内容。
'''


share_id = chat_id < 0 and chat_id * -1 - 1000000000000 or chat_id

elastic_index = "chat" + str(chat_id)

mapping = {
  "properties":{
    "content": {
      "type": "text",
      "analyzer": "ik_max_word",
      "search_analyzer": "ik_smart"
    },
    "url": {
      "type": "text"
    },
    "date": {
      "type": "date",
      "format": "yyyy-MM-dd HH:mm:ss||yyyy-MM-dd||epoch_millis"
    },
    "name": {
      "type": "text",
      "analyzer": "ik_max_word",
      "search_analyzer": "ik_smart"
    },
    "username":{
        "type": "keyword"
    }
  }
}

def ensureElasticIndex(index, mapping):
  if not es.indices.exists(index=elastic_index):
      es.indices.create(index=elastic_index)
      es.indices.put_mapping(index=elastic_index, body=mapping)

def deleteElasticIndex(index):
  if es.indices.exists(index=elastic_index):
      es.indices.delete(index=elastic_index)

def search(q, from_, size=10):
  ensureElasticIndex(index=elastic_index, mapping=mapping)
  return es.search(index=elastic_index, q=q, df="content", sort="date:desc", size=10, from_=from_, body={
    "highlight" : {
      "pre_tags" : ["<b>"],
      "post_tags" : ["</b>"],
      "fields" : {
          "content" : {
            "fragment_size" : 15,
            "number_of_fragments" : 3,
            "fragmenter": "span"
        }
      }
    }
  })

def renderRespondText(result, from_):
  total = result['hits']['total']['value']
  respond = '搜素到%d个结果：\n' % (total)
  for i in range(len(result['hits']['hits'])):
    hit = result['hits']['hits'][i]
    content = 'highlight' in hit and hit['highlight']['content'][0] or hit['_source']['content'][0:15]
    date = datetime.fromtimestamp(int(hit['_source']['date'] )/ 1000)
    date = date.strftime('%Y-%m-%d') 
    respond += '%d. <a href="%s">%s</a>\n name: <a href="https://t.me/%s">%s</a>\n date: %s\n\r' % (from_ + i + 1, hit['_source']['url'], content, hit['_source']['username'],hit['_source']['name'], date)
  respond += '耗时%.3f秒。' % (result['took'] / 1000)
  return respond

def renderRespondButton(result, from_):
  total = result['hits']['total']['value']
  return [
    [
      Button.inline('上一页⬅️', str(max(from_ - 10, 0))),
      Button.inline('➡️下一页', str(min(from_ + 10, total // 10 * 10))),
    ]
  ]

@events.register(events.NewMessage)
async def ClientMessageHandler(event):
  if event.chat_id == chat_id and event.raw_text and len(event.raw_text.strip()) >= 0:
    first_name = ''
    last_name = ''
    username = ''
    try:
      first_name = event.sender.first_name
      last_name = event.sender.last_name
      username = event.sender.username
    except:
      pass
    es.index(index=elastic_index, body={"content": html.escape(event.raw_text).replace('\n',' '), 
                                        "date": int(event.date.timestamp()*1000), 
                                        "url": "https://t.me/c/%s/%s" % (share_id, event.id),
                                        "name": (" ".join([first_name, last_name])).strip(),
                                        "username": username
                                        }, id=event.id)

@events.register(events.CallbackQuery)
async def BotCallbackHandler(event):
  if event.data:
    from_i = int(event.data)
    q = db.get('msg-' + str(event.message_id) + '-q')
    if q:
      result = search(q, from_i)
      respond = renderRespondText(result, from_i)
      buttons = renderRespondButton(result, from_i)
      msg = await event.edit(respond, parse_mode='html', buttons=buttons)

  await event.answer()

async def downloadHistory():
  deleteElasticIndex(index=elastic_index)
  ensureElasticIndex(index=elastic_index, mapping=mapping)
  async for message in client.iter_messages(chat_id, reverse=True):
    print('elastic index:', elastic_index)
    if message.chat_id == chat_id and message.raw_text and len(message.raw_text.strip()) >= 0:
      print('start to index the message!')
      print(message.raw_text)
      first_name = ''
      last_name = ''
      username = ''
      try:
        if message.sender.first_name:
          first_name = message.sender.first_name
        if message.sender.last_name:
          last_name = message.sender.last_name
        if message.sender.username:
          username = message.sender.username
      except:
        pass

      try:
        es.index(
          index=elastic_index,
          body={"content": html.escape(message.raw_text).replace('\n',' '), 
              "date": int(message.date.timestamp() * 1000), 
              "url": "https://t.me/c/%s/%s" % (share_id, message.id),
              "name": " ".join([first_name, last_name]).strip(),
              "username": username
              },
          id=message.id
        )
      except:
        pass

@events.register(events.NewMessage)
async def BotMessageHandler(event):
  print('event from_id:', event.from_id)
  if event.raw_text.startswith('/start'):
    await event.respond(welcome_message, parse_mode='markdown')

  elif event.raw_text.startswith('/help'):
    await event.respond(help_message, parse_mode='markdown')

  elif event.raw_text.startswith('/download_history') and event.from_id == admin_id:
    # 下载所有历史记录
    await event.respond('开始下载历史记录', parse_mode='markdown')
    await downloadHistory()
    await event.respond('下载完成', parse_mode='markdown')
  elif event.chat_id != chat_id:
    from_i = 0
    q = event.raw_text
    result = search(q, from_i)
    respond = renderRespondText(result, from_i)
    buttons = renderRespondButton(result, from_i)
    msg = await event.respond(respond, parse_mode='html', buttons=buttons)

    db.set('msg-' + str(msg.id) + '-q', q)

loop = asyncio.get_event_loop()

client = TelegramClient('session/client', api_id, api_hash, connection_retries=None, proxy=proxy, loop=loop)
client.add_event_handler(ClientMessageHandler)
client.start()

bot = TelegramClient('session/bot', api_id, api_hash, connection_retries=None, proxy=proxy, loop=loop)
bot.add_event_handler(BotMessageHandler)
bot.add_event_handler(BotCallbackHandler)
bot.start(bot_token=bot_token)

try:
  loop.run_forever()
except KeyboardInterrupt:
  pass
