config_redis_host = '127.0.0.1'
config_redis_port = 6379
config_elastic_url = 'http://127.0.0.1:9200'
config_api_id = '12345'
config_api_hash = 'abcde'
config_bot_token = '23345:56788'
config_chat_id = '123456'
config_admin_id = '123234235'

try:
    from local_config import *
except:
    pass