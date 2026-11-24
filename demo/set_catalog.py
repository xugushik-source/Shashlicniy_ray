"""Source-backed set composition. Missing amounts remain None, never one by default."""
import math
from copy import deepcopy
LABELS={
'pork':('Шашлык из свиной мякоти','ღორის რბილობის მწვადი','Խոզի փափկամսի խորոված','Pork shashlik'),
'neck':('Свиная шея','ღორის კისერი','Խոզի վիզ','Pork neck'),
'chicken':('Шашлык из куриной мякоти','ქათმის რბილობის მწვადი','Հավի փափկամսի խորոված','Chicken shashlik'),
'ribs':('Свиные рёбра','ღორის ნეკნები','Խոզի կողեր','Pork ribs'),
'lula_pork':('Люля-кебаб из свинины','ღორის ქაბაბი','Խոզի լյուլյա քյաբաբ','Pork lula kebab'),
'lula_chicken':('Люля-кебаб из курицы','ქათმის ქაბაბი','Հավի լյուլյա քյաբաբ','Chicken lula kebab'),
'lula_beef':('Люля-кебаб из говядины','საქონლის ქაბაბი','Տավարի լյուլյա քյաբաբ','Beef lula kebab'),
'lula_lamb':('Люля-кебаб из баранины','ცხვრის ქაბაბი','Գառան լյուլյա քյաբաբ','Lamb lula kebab'),
'potato':('Молодой картофель на углях','ახალი კარტოფილი ნაკვერჩხალზე','Մատղաշ կարտոֆիլ ածխի վրա','Grilled baby potatoes'),
'potato_plain':('Картофель на углях','კარტოფილი ნაკვერჩხალზე','Կարտոֆիլ ածխի վրա','Grilled potatoes'),
'vegetables':('Овощной микс на углях','ბოსტნეულის მიქსი ნაკვერჩხალზე','Բանջարեղենի խառնուրդ ածխի վրա','Mixed grilled vegetables'),
'bbq':('Соус шашлычный','მწვადის სოუსი','Խորովածի սոուս','Shashlik sauce'),
'garlic':('Соус чесночный','ნივრის სოუსი','Սխտորի սոուս','Garlic sauce'),
'lavash':('Лаваш армянский','სომხური ლავაში','Հայկական լավաշ','Armenian lavash'),
'onion':('Лук красный / маринованный','წითელი / მარინირებული ხახვი','Կարմիր / մարինացված սոխ','Red / pickled onion'),
'herbs':('Зелень','მწვანილი','Կանաչի','Fresh herbs'),
'lamb':('Шашлык из бараньей мякоти','ცხვრის რბილობის მწვადი','Գառան փափկամսի խորոված','Lamb shashlik'),
'lamb_riblets':('Бараньи семечки','ცხვრის პატარა ნეკნები','Գառան մանր կողիկներ','Lamb riblets'),
'lamb_ribs':('Бараньи рёбрышки','ცხვრის ნეკნები','Գառան կողեր','Lamb ribs'),
'lamb_rack':('Каре ягнёнка','ბატკნის კარე','Գառան կարե','Rack of lamb'),
'vegetable_side':('Овощной гарнир','ბოსტნეულის გარნირი','Բանջարեղենային խավարտ','Vegetable side'),
'wings':('Куриные крылья','ქათმის ფრთები','Հավի թևիկներ','Chicken wings'),
'dorado':('Дорадо на мангале','დორადო მაყალზე','Դորադո մանղալի վրա','Grilled sea bream'),
'salmon':('Сёмга на мангале','ორაგული მაყალზე','Սաղմոն մանղալի վրա','Grilled salmon'),
'trout':('Форель на мангале','კალმახი მაყალზე','Իշխան մանղալի վրա','Grilled trout'),
'seabass':('Сибас на мангале','სიბასი მაყალზე','Սիբաս մանղալի վրա','Grilled sea bass'),
'lemon':('Лимон','ლიმონი','Կիտրոն','Lemon'),
'narsharab':('Соус наршараб','ნარშარაბის სოუსი','Նարշարաբ սոուս','Narsharab sauce'),
'Tartar':('Соус тартар','ტარტარის სოუსი','Թարթառ սոուս','Tartare sauce'),
'bonelamb':('Баранина на кости','ცხვრის ხორცი ძვლით','Գառան միս ոսկորով','Bone-in lamb'),
'thigh':('Куриное бедро','ქათმის ბარკალი','Հավի ազդր','Chicken thigh'),
'turkey':('Филе индейки','ინდაურის ფილე','Հնդկահավի ֆիլե','Turkey fillet'),
'vegetable_platter':('Овощное ассорти','ბოსტნეულის ასორტი','Բանջարեղենի տեսականի','Vegetable platter'),
'pickles':('Соленья','მწნილეული','Թթուներ','Pickles'),
'khachapuri':('Хачапури по-мегрельски','მეგრული ხაჭაპური','Մեգրելական խաչապուրի','Megrelian khachapuri'),
'caucasus':('Ассорти «Кавказ»','ასორტი „კავკასია“','«Կովկաս» տեսականի','Caucasus platter'),
'courgette':('Кабачки','ყაბაყი','Դդմիկ','Courgettes'),
'aubergine':('Баклажаны','ბადრიჯანი','Սմբուկ','Aubergines'),
'pepper':('Перец','წიწაკა','Պղպեղ','Peppers'),
'zucchini':('Цукини','ცუკინი','Ցուկկինի','Zucchini'),
'mushrooms':('Шампиньоны','შამპინიონები','Շամպինիոն','Button mushrooms'),
}
LANGS=('ru','ka','hy','en')
def row(key,quantity=None,grams=None):return {'key':key,'names':dict(zip(LANGS,LABELS[key])),'quantity':quantity,'grams':grams}
def rows(*keys):return [row(k) for k in keys]
TAIL=rows('lavash','onion','herbs')
DEFINITIONS={
'Ассорти №1':{'servings':(5,7),'components':[row('pork',2),row('chicken',2),row('lula_pork',1),row('lula_chicken',1),row('lula_beef',1),row('potato',1),row('bbq',grams=100),row('garlic',grams=100)]+TAIL},
'Ассорти №2':{'servings':(7,10),'components':[row('pork',2),row('chicken',2),row('ribs',1),row('lula_pork',2),row('lula_chicken',2),row('lula_beef',2),row('potato',1),row('vegetables',1),row('bbq',grams=100),row('garlic',grams=100)]+TAIL},
'Ассорти №3':{'servings':(3,5),'components':[row('lamb',1),row('lamb_riblets',1),row('lamb_rack',1),row('lula_lamb',1),row('chicken',1),row('potato',1),row('vegetables',1),row('bbq',grams=100),row('garlic',grams=50)]+TAIL},
'Ассорти из баранины':{'servings':(2,4),'components':rows('lamb_rack','lamb_ribs','lamb','lula_lamb','vegetable_side','lavash','onion','herbs','bbq')},
'Ассорти из курицы':{'servings':(2,4),'components':[row('wings'),row('chicken',2),row('lula_chicken'),row('potato'),row('vegetables')]+TAIL+[row('bbq',grams=100),row('garlic',grams=50)]},
'Ассорти из свинины':{'servings':(2,4),'components':[row('pork',2),row('ribs',2),row('lula_pork'),row('potato'),row('vegetables')]+TAIL+[row('bbq',grams=100)],'notes':['pork_source_conflict']},
'Ассорти люля-кебабов':{'servings':(2,4),'components':rows('lula_lamb','lula_beef','lula_chicken','potato','vegetables')+TAIL+[row('bbq',grams=100),row('garlic',grams=50)]},
'Рыбное ассорти':{'servings':(2,4),'components':rows('dorado','salmon','trout','seabass','vegetables','lemon','herbs')+[row('narsharab',grams=60),row('Tartar',grams=60)]},
'Ассорти овощей №1':{'servings':(2,4),'components':rows('courgette','aubergine','pepper','zucchini','mushrooms','potato'),'notes':['side_platter']},
'Ассорти корпоративный':{'slug':'assorti_korporativnii','total_grams':9450,'estimate_servings':False,'components':[row('neck',grams=600),row('thigh',grams=600),row('bonelamb',grams=600),row('lula_lamb',grams=600),row('wings',grams=600),row('turkey',grams=600),row('potato_plain',grams=1250),row('bbq',grams=600),row('vegetable_platter',grams=1500),row('pickles',grams=1000),{**row('khachapuri',3,1500),'grams_per_piece':500,'weight_confirmation':'owner'}]},
'Ассорти праздничный':{'slug':'assorti_prazdnichnii','total_grams':6250,'estimate_servings':False,'components':[row('neck',grams=400),row('ribs',grams=400),row('lula_lamb',grams=400),row('wings',grams=400),row('lula_chicken',grams=400),row('thigh',grams=400),{**row('khachapuri',2,1000),'grams_per_piece':500,'weight_confirmation':'owner'},row('potato_plain',grams=750),row('caucasus',grams=1000),row('pickles',grams=700),row('bbq',grams=400)]},
'Ассорти от шефа':{'slug':'assorti_ot_shefa','total_grams':1500,'components':rows('neck','ribs','lula_beef','thigh','wings','lula_chicken','potato_plain')},
'Ассорти от души':{'slug':'assorti_ot_dushi','total_grams':1500,'components':rows('neck','bonelamb','lula_pork','turkey','lamb','thigh','potato_plain')},
'Ассорти шашлыков':{'slug':'assorti_shashlikov','total_grams':1300,'components':rows('neck','lamb_ribs','chicken','wings','lula_chicken','potato_plain')},
'Ассорти люля':{'slug':'assorti_lyulya','total_grams':1100,'components':rows('lula_beef','lula_lamb','lula_chicken','lula_pork','potato_plain')},
}
def apply_sets(products):
 for p in products:
  spec=DEFINITIONS.get(p['names']['ru'])
  if not spec:continue
  d=p['details'];grams=spec.get('total_grams')
  if grams:p['grams']=grams;d['weight_unknown']=False
  guests=spec.get('servings')
  basis='source' if guests else 'unknown'
  if not guests and not d['weight_unknown'] and spec.get('estimate_servings',True):
   # Editorial adult full-platter estimate, not a promise of meat-only grams.
   guests=(max(1,math.floor(p['grams']/500)),max(1,math.floor(p['grams']/350)));basis='estimate'
  previous=d.get('bundle',{})
  d['bundle']={'components':deepcopy(spec['components']),'servings':{'min':guests[0],'max':guests[1],'basis':basis} if guests else {'min':None,'max':None,'basis':basis},'notes':spec.get('notes',[]),'checked_at':'2026-11-15','weight_basis':'complete_set','estimate_full_dish_g_per_adult':[350,500] if basis=='estimate' else None}
  for key in ('pricing_status','missing_prices','costing_approved','revision'):
   if key in previous:d['bundle'][key]=previous[key]
  if spec.get('slug'):
   d['source_page']='https://shashlik-mashlik.com/menu/shashlik/nabory/'+spec['slug']
   # Preserve source wording separately. UI uses the structured, translated composition.
   d['description']['ru']=', '.join(x['names']['ru']+(f" ({x['quantity']} шт.)" if x['quantity'] else '')+(f" ({x['grams']} г)" if x['grams'] else '') for x in spec['components'])
 return products
