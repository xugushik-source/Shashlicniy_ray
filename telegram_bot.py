"""Local long-polling demo bot. Token stays in process memory/environment.
Replies only to incoming private messages and callbacks. Does not take real orders.
"""
import json,os,time,sys,getpass,urllib.request,urllib.error,fcntl
from pathlib import Path
ROOT=Path(__file__).parent
TEXT={
'ru':{'welcome':'Шашлычный рай · Ахалкалаки\nДемо-бот: меню и цены для просмотра. Реальные заказы здесь пока не принимаются.\nВыберите действие:','menu':'Меню','contact':'Контакты и доставка','language':'Язык','choose':'Выберите раздел','back':'Назад','next':'Далее','demo':'Демонстрационные цены в лари, не утверждённый прайс.','contact_text':'Ахалкалаки\n+995 591 244 075\nНаличные при получении или ручной перевод. Доставка и время согласовываются по телефону. Демо-бот не подтверждает оплату и не отправляет заказы.','empty':'Позиции ещё не добавлены.','unknown':'Используйте /start, /menu или /contact.','error':'Не удалось загрузить раздел. Повторите /start.'},
'ka':{'welcome':'მწვადის სამოთხე · ახალქალაქი\nდემო ბოტი: მენიუ და ფასები სანახავად. რეალური შეკვეთები აქ ჯერ არ მიიღება.\nაირჩიეთ მოქმედება:','menu':'მენიუ','contact':'კონტაქტი და მიტანა','language':'ენა','choose':'აირჩიეთ განყოფილება','back':'უკან','next':'შემდეგი','demo':'სადემონსტრაციო ფასები ლარში, დაუმტკიცებელი პრეისკურანტი.','contact_text':'ახალქალაქი\n+995 591 244 075\nნაღდი ანგარიშსწორება მიღებისას ან ხელით გადარიცხვა. მიტანა და დრო ტელეფონით შეთანხმდება. დემო ბოტი გადახდას არ ადასტურებს და შეკვეთებს არ აგზავნის.','empty':'პროდუქტები ჯერ არ არის.','unknown':'გამოიყენეთ /start, /menu ან /contact.','error':'ვერ ჩაიტვირთა. გაიმეორეთ /start.'},
'hy':{'welcome':'Խորովածի դրախտ · Ախալքալաք\nԴեմո բոտ՝ ճաշացանկն ու գները դիտելու համար։ Իրական պատվերներ այստեղ դեռ չեն ընդունվում։\nԸնտրեք գործողությունը․','menu':'Ճաշացանկ','contact':'Կապ և առաքում','language':'Լեզու','choose':'Ընտրեք բաժինը','back':'Հետ','next':'Հաջորդը','demo':'Դեմո գներ լարիով, չհաստատված գնացուցակ։','contact_text':'Ախալքալաք\n+995 591 244 075\nԿանխիկ՝ ստանալիս, կամ ձեռքով փոխանցում։ Առաքումն ու ժամը համաձայնեցվում են հեռախոսով։ Դեմո բոտը վճարում չի հաստատում և պատվեր չի ուղարկում։','empty':'Ապրանքներ դեռ չկան։','unknown':'Օգտագործեք /start, /menu կամ /contact։','error':'Չհաջողվեց բեռնել։ Կրկնեք /start։'},
'en':{'welcome':'Shashlik Paradise · Akhalkalaki\nDemo bot: browse dishes and prices. Real orders are not accepted here yet.\nChoose an action:','menu':'Menu','contact':'Contact and delivery','language':'Language','choose':'Choose a category','back':'Back','next':'Next','demo':'Demo prices in GEL, not an approved price list.','contact_text':'Akhalkalaki\n+995 591 244 075\nCash on delivery or manual transfer. Delivery and times are agreed by phone. The demo bot does not verify payments or send orders.','empty':'No products yet.','unknown':'Use /start, /menu or /contact.','error':'Could not load the section. Try /start again.'}}
CATS={
'pork':['Свинина','ღორის ხორცი','Խոզի միս','Pork'],'lamb':['Баранина','ცხვრის ხორცი','Գառան միս','Lamb'],'beef':['Говядина','საქონლის ხორცი','Տավարի միս','Beef'],'poultry':['Птица','ფრინველი','Թռչնամիս','Poultry'],'fish':['Рыба','თევზი','Ձուկ','Fish'],'tandoor':['Тандыр','თონე','Թոնիր','Tandoor'],'lula':['Люля-кебаб','ქაბაბი','Քյաբաբ','Lula kebab'],'vegetables':['Овощи','ბოსტნეული','Բանջարեղեն','Vegetables'],'salads':['Салаты','სალათები','Աղցաններ','Salads'],'pickles':['Соленья','მწნილეული','Թթու','Pickles'],'cheese':['Сыры','ყველი','Պանիր','Cheese'],'herbs':['Зелень','მწვანილი','Կանաչի','Herbs'],'sides':['Гарниры','გარნირი','Խավարտ','Sides'],'bread':['Хлеб','პური','Հաց','Bread'],'sauces':['Соусы','სოუსები','Սոուսներ','Sauces'],'drinks':['Напитки','სასმელები','Ըմպելիքներ','Drinks'],'desserts':['Десерты','დესერტები','Աղանդեր','Desserts'],'supplies':['Сервировка','სერვირება','Սպասք','Tableware'],'combo':['Наборы','ნაკრებები','Հավաքածուներ','Platters'],'snacks':['Закуски','წასახემსებელი','Նախուտեստներ','Starters'],'alcohol':['Алкоголь','ალკოჰოლი','Ալկոհոլ','Alcohol']}
class TelegramError(Exception):
 def __init__(self,code):self.code=code;super().__init__('Telegram API error '+str(code))
class API:
 def __init__(self,token):self.token=token
 def __call__(self,method,**params):
  req=urllib.request.Request('https://api.telegram.org/bot'+self.token+'/'+method,data=json.dumps(params).encode(),headers={'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(req,timeout=40) as r:d=json.load(r)
  except urllib.error.HTTPError as e:raise TelegramError(e.code) from None
  except (urllib.error.URLError,ValueError,TimeoutError):raise TelegramError('network') from None
  if not d.get('ok'):raise TelegramError(d.get('error_code','unknown'))
  return d.get('result')
class Bot:
 def __init__(self,api,products):self.api=api;self.products=products;self.languages={}
 def button(self,text,data):return {'text':text,'callback_data':data}
 def home(self,lang):
  t=TEXT[lang];return [[self.button(t['menu'],'menu')],[self.button(t['contact'],'contact'),self.button(t['language'],'language')]]
 def send(self,chat,text,buttons):self.api('sendMessage',chat_id=chat,text=text,reply_markup={'inline_keyboard':buttons})
 def handle(self,u):
  callback=u.get('callback_query');m=callback.get('message',{}) if callback else u.get('message',{});chat=m.get('chat',{})
  if chat.get('type')!='private':return
  uid=(callback.get('from',{}) if callback else m.get('from',{})).get('id')
  raw=(callback.get('from',{}) if callback else m.get('from',{})).get('language_code','ru').split('-')[0]
  lang=self.languages.get(uid,raw if raw in TEXT else 'ru');t=TEXT[lang]
  if callback:
   self.api('answerCallbackQuery',callback_query_id=callback['id']);action=callback.get('data','')
  else:action=m.get('text','').split(' ')[0].split('@')[0].removeprefix('/')
  cid=chat['id']
  if action.startswith('lang:'):
   choice=action[5:]
   if choice in TEXT:self.languages[uid]=choice;lang=choice;t=TEXT[lang];action='start'
  if action in ('start','help'):self.send(cid,t['welcome'],self.home(lang))
  elif action=='language':self.send(cid,'RU · KA · HY · EN',[[self.button('Русский','lang:ru'),self.button('ქართული','lang:ka')],[self.button('Հայերեն','lang:hy'),self.button('English','lang:en')]])
  elif action=='contact':self.send(cid,t['contact_text'],self.home(lang))
  elif action=='menu':
   present={p['category'] for p in self.products};idx=['ru','ka','hy','en'].index(lang)
   buttons=[self.button(names[idx],'cat:'+cat+':0') for cat,names in CATS.items() if cat in present]
   self.send(cid,t['choose'],[buttons[i:i+2] for i in range(0,len(buttons),2)]+[[self.button(t['back'],'start')]])
  elif action.startswith('cat:'):
   parts=action.split(':')
   if len(parts)!=3 or parts[1] not in CATS or not parts[2].isdigit():return
   cat=parts[1];page=min(int(parts[2]),100);items=[p for p in self.products if p['category']==cat];shown=items[page*6:page*6+6]
   lines=[t['demo'],'']+[p['names'][lang]+' — '+str(p['price']//100)+' ₾' for p in shown]
   buttons=[]
   if page:buttons.append(self.button(t['back'],'cat:'+cat+':'+str(page-1)))
   if (page+1)*6<len(items):buttons.append(self.button(t['next'],'cat:'+cat+':'+str(page+1)))
   self.send(cid,'\n'.join(lines) if shown else t['empty'],([buttons] if buttons else [])+[[self.button(t['menu'],'menu')]])
  else:self.send(cid,t['unknown'],self.home(lang))
def main():
 data=ROOT/'data';data.mkdir(exist_ok=True,mode=0o700)
 lock=(data/'telegram-poll.lock').open('w')
 try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
 except BlockingIOError:print('Another local bot process is running.',flush=True);return 1
 token=os.environ.get('TELEGRAM_BOT_TOKEN','') or getpass.getpass('Telegram token (hidden): ')
 if not token:print('Missing token',flush=True);return 1
 api=API(token)
 try:
  me=api('getMe');hook=api('getWebhookInfo')
  if me.get('username','').lower()!='shashlichnyrayakhalkalakibot':print('Bot identity does not match expected username.',flush=True);return 1
  if hook.get('url'):print('Bot has an existing webhook; no changes made.',flush=True);return 1
  api('setMyCommands',commands=[{'command':'start','description':'Start / Начать'},{'command':'menu','description':'Menu / Меню'},{'command':'contact','description':'Contact / Контакты'},{'command':'language','description':'RU / KA / HY / EN'}])
 except TelegramError as e:print('Startup failed: '+str(e),flush=True);return 1
 print('CONNECTED @'+me['username']+'; long polling active',flush=True)
 bot=Bot(api,json.loads((ROOT/'demo/catalog.json').read_text())['products']);offsetfile=data/'telegram-offset.txt'
 try:offset=int(offsetfile.read_text())
 except (FileNotFoundError,ValueError):offset=0
 while True:
  try:
   updates=api('getUpdates',offset=offset,timeout=25,allowed_updates=['message','callback_query'])
   for u in updates:
    try:bot.handle(u)
    except TelegramError as e:
     if e.code not in (400,403):raise
    offset=u['update_id']+1;temp=offsetfile.with_suffix('.tmp');temp.write_text(str(offset));temp.replace(offsetfile)
   if updates:print('Processed '+str(len(updates))+' incoming update(s)',flush=True)
  except TelegramError as e:
   print('Polling status: '+str(e),flush=True)
   if e.code in (401,409):return 1
   time.sleep(3)
if __name__=='__main__':
 try:sys.exit(main())
 except KeyboardInterrupt:pass
