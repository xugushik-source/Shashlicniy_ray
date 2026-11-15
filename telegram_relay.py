"""Development relay for a private Sites endpoint; permanent production uses webhook.
Credentials are entered hidden or supplied through process environment, never files.
"""
import getpass,json,os,time,urllib.request,urllib.error
from telegram_bot import API,TelegramError,ROOT

def main():
 print('Ready for relay credential JSON (hidden).',flush=True)
 c=json.loads(getpass.getpass(''));api=API(c['bot_token']);path=ROOT/'data/telegram-offset.txt'
 try:offset=int(path.read_text())
 except (ValueError,FileNotFoundError):offset=0
 print('Private-site Telegram relay active',flush=True)
 while True:
  try:
   for u in api('getUpdates',offset=offset,timeout=25,allowed_updates=['message','callback_query']):
    req=urllib.request.Request(c['url']+'/api/telegram/webhook',data=json.dumps(u).encode(),headers={'Content-Type':'application/json','OAI-Sites-Authorization':'Bearer '+c['service_token'],'X-Telegram-Bot-Api-Secret-Token':c['webhook_secret']})
    with urllib.request.urlopen(req,timeout=30) as r:result=json.load(r)
    if not result.get('ok'):raise ValueError('Relay rejected')
    offset=u['update_id']+1;tmp=path.with_suffix('.tmp');tmp.write_text(str(offset));tmp.replace(path)
    print('Incoming update processed by hosted worker',flush=True)
  except (TelegramError,urllib.error.URLError,ValueError):
   print('Relay retry pending',flush=True);time.sleep(3)
if __name__=='__main__':
 try:main()
 except KeyboardInterrupt:pass
