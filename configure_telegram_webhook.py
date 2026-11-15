"""Explicit transition from private dev relay to permanent public webhook.
No token is stored. Refuses to configure while endpoint requires sign-in.
"""
import getpass,json,urllib.request,urllib.error,sys
from telegram_bot import API,TelegramError

def main():
 print('Ready for webhook configuration JSON (hidden).',flush=True)
 c=json.loads(getpass.getpass(''));base=c['url'].rstrip('/')
 try:
  with urllib.request.urlopen(urllib.request.Request(base+'/api/settings',headers={'User-Agent':'Mozilla/5.0'}),timeout=20) as r:s=json.load(r)
  if not s.get('pilot'):raise ValueError()
 except (urllib.error.URLError,ValueError):
  print('Public order API is not accessible. Webhook unchanged.',flush=True);return 1
 api=API(c['bot_token'])
 if api('getMe').get('username')!='ShashlichnyRayAkhalkalakiBot':
  print('Unexpected bot identity. Webhook unchanged.',flush=True);return 1
 api('setWebhook',url=base+'/api/telegram/webhook',secret_token=c['webhook_secret'],allowed_updates=['message','callback_query'],drop_pending_updates=False)
 info=api('getWebhookInfo');print(json.dumps({'webhook_url':info.get('url'),'pending_updates':info.get('pending_update_count'),'last_error_message':info.get('last_error_message')}),flush=True);return 0
if __name__=='__main__':
 try:sys.exit(main())
 except TelegramError as e:print(str(e));sys.exit(1)
