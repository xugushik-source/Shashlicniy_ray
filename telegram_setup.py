"""Verify a new bot's identity using a process secret; never prints the token.
No messages are sent and no webhook is registered by this command.
"""
import json,os,sys,urllib.request,urllib.error

def main():
 token=os.environ.get('TELEGRAM_BOT_TOKEN','')
 if not token:
  print('TELEGRAM_BOT_TOKEN is not configured. Create a new bot with https://t.me/BotFather and store the token in the process environment.');return 1
 try:
  with urllib.request.urlopen(urllib.request.Request('https://api.telegram.org/bot'+token+'/getMe',data=b''),timeout=15) as r:result=json.load(r)
  if not result.get('ok'):print('Telegram rejected verification.');return 1
  bot=result['result'];print(json.dumps({'verified':True,'username':bot.get('username'),'name':bot.get('first_name'),'webhook_configured_by_this_command':False},ensure_ascii=False));return 0
 except (urllib.error.URLError,ValueError,KeyError):
  print('Telegram verification failed. Check network and the configured secret.');return 1
if __name__=='__main__':sys.exit(main())
