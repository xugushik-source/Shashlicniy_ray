import unittest,json
from pathlib import Path
from telegram_bot import Bot,TEXT
class BotTest(unittest.TestCase):
 def setUp(self):
  self.calls=[];self.bot=Bot(lambda method,**kw:self.calls.append((method,kw)),json.loads(Path('demo/catalog.json').read_text())['products'])
 def message(self,text):return {'update_id':1,'message':{'chat':{'id':1,'type':'private'},'from':{'id':1,'language_code':'ru'},'text':text}}
 def callback(self,data):return {'update_id':1,'callback_query':{'id':'callback','from':{'id':1},'data':data,'message':{'chat':{'id':1,'type':'private'}}}}
 def test_start_and_language(self):
  self.bot.handle(self.message('/start'));self.assertIn('Ахалкалаки',self.calls[-1][1]['text'])
  for l in TEXT:
   self.bot.handle(self.callback('lang:'+l));self.assertEqual(self.calls[-1][1]['text'],TEXT[l]['welcome'])
 def test_menu_and_prices(self):
  self.bot.handle(self.message('/menu'));self.assertTrue(self.calls[-1][1]['reply_markup']['inline_keyboard'])
  self.bot.handle(self.callback('cat:pork:0'));self.assertIn('₾',self.calls[-1][1]['text']);self.assertNotIn('RUB',self.calls[-1][1]['text'])
 def test_ignore_groups(self):
  u=self.message('/start');u['message']['chat']['type']='group';self.bot.handle(u);self.assertEqual(self.calls,[])
 def test_unknown(self):
  self.bot.handle(self.message('hello'));self.assertIn('/start',self.calls[-1][1]['text'])
 def test_malformed_callback(self):
  self.bot.handle(self.callback('cat:pork:invalid'));self.assertEqual(self.calls[-1][0],'answerCallbackQuery')
