const GROUP_ORDER=['grill','fish','hot','banquet','cold','salads','soups','sides','bread','sauces','combo','drinks','alcohol','desserts','supplies'];
export const CATEGORY_ORDER=['combo','pork','lamb','beef','poultry','lula','tandoor','fish','khinkali','khachapuri','vegetables','salads','snacks','pickles','cheese','herbs','sides','bread','sauces','drinks','alcohol','soups','desserts','supplies'];
export function contribution(p){return p.cost_confirmed===true&&Number.isInteger(p.cost_minor)&&p.cost_minor>=0?p.price-p.cost_minor:null}
export function tags(p){const n=(p.names?.ru||'').toLowerCase(),set=new Set([p.category,...(p.details?.pairing_tags||[])]);if(/люля/.test(n))set.add('lula');if(/карто|фри/.test(n))set.add('potato');if(/лаваш|лепеш|лепёш|хлеб/.test(n))set.add('bread');if(p.category==='sauces'){if(/чесноч/.test(n))set.add('sauce_garlic');if(/сацебели|шашлыч/.test(n))set.add('sauce_tomato');if(/ткемали/.test(n))set.add('sauce_tkemali');if(/аджик/.test(n))set.add('sauce_adjika');if(/наршараб|тартар|тар-тар/.test(n))set.add('sauce_fish')}if(/сыр|сулугуни|брынза/.test(n))set.add('cheese');if(/солень|маринов/.test(n))set.add('pickles');if(/вода/.test(n))set.add('water');if(/грузинск|овощной салат|греческ/.test(n))set.add('light_salad');if(p.category==='alcohol'){
  const beerStyle=p.details?.beer_style;
  if(/пиво|стаут|портер|пилс|пильз|эль/.test(n)||set.has('beer')||beerStyle)set.add('beer');
  // Explicit metadata wins; neither a generic lager nor every red wine is assumed light/full-bodied.
  if(beerStyle==='dark'||(!beerStyle&&/стаут|портер/.test(n)))set.add('dark_beer');
  else if(beerStyle==='light'||(!beerStyle&&/пилс|пильз|светл/.test(n)))set.add('light_beer');
  else if(beerStyle==='amber'||(!beerStyle&&/янтарн/.test(n)))set.add('amber_beer');
  if(/водка/.test(n)||set.has('vodka'))set.add('vodka');
  const wineStyle=p.details?.wine_style||( /красн/.test(n)?'red':/белое/.test(n)?'white':null);
  if(wineStyle||/вино|саперави|ркацители|цоликаури/.test(n))set.add('wine');
  if(wineStyle==='red')set.add('red_wine');if(wineStyle==='white')set.add('white_wine');
  if(wineStyle==='red'&&p.details?.wine_body==='full')set.add('rich_red_wine');
  if(wineStyle==='white'&&p.details?.wine_body==='light')set.add('light_white_wine');
 }
 if(['pork','lamb','beef','poultry','fish','lula','tandoor'].includes(p.category)&&!/салат|суп|наггет|жульен/.test(n))set.add('hot');return set}
export const PAIRING_RULES=[
 {from:'pork',to:['sauce_tomato','bread','potato','vegetables','pickles','water','amber_beer'],reason:'pairPork'},
 {from:'lamb',to:['sauce_tkemali','bread','vegetables','herbs','water','rich_red_wine'],reason:'pairLamb'},
 {from:'beef',to:['sauce_adjika','potato','vegetables','water','rich_red_wine','dark_beer'],reason:'pairBeef'},
 {from:'poultry',to:['sauce_garlic','vegetables','potato','water','light_beer'],reason:'pairPoultry'},
 {from:'fish',to:['sauce_fish','light_salad','herbs','water','light_white_wine'],reason:'pairFish'},
 {from:'lula',to:['bread','sauce_tomato','pickles','vegetables','water','amber_beer'],reason:'pairLula'},
 {from:'beer',to:['potato','cheese','pickles'],reason:'pairBeer'},
 {from:'light_beer',to:['fish','poultry','light_salad'],reason:'pairLightBeer'},
 {from:'amber_beer',to:['pork','poultry','vegetables'],reason:'pairPork'},
 {from:'dark_beer',to:['beef','lamb'],reason:'pairDarkBeer'},
 {from:'rich_red_wine',to:['beef','lamb','cheese','vegetables'],reason:'pairRedWine'},
 {from:'light_white_wine',to:['fish','poultry','light_salad','cheese'],reason:'pairWhiteWine'},
 {from:'wine',to:['cheese','vegetables'],reason:'pairWine'},
 {from:'vodka',to:['water'],reason:'pairVodka'}
];
export function rankCatalog(catalog){const completeCosts=new Map([...new Set(catalog.map(p=>p.category))].map(c=>[c,catalog.filter(p=>p.category===c).every(p=>contribution(p)!==null)]));return [...catalog].sort((a,b)=>{const order=(p)=>p.details?.catalog_group?GROUP_ORDER.indexOf(p.details.catalog_group):CATEGORY_ORDER.indexOf(p.category);const i=order(a),j=order(b);if(i!==j)return (i<0?99:i)-(j<0?99:j);const ma=contribution(a),mb=contribution(b);if(ma!==null&&mb!==null&&ma!==mb)return mb-ma;return (b.details?.display_priority||0)-(a.details?.display_priority||0)||(a.names.ru||'').localeCompare(b.names.ru||'','ru')})}
export function recommendProducts(catalog,selectedIds,{allowAlcohol=false,limit=6}={}){selectedIds=[...new Set(selectedIds.map(id=>catalog.find(p=>p.id===id||p.details?.aliases?.includes(id))?.id||id))];const selected=catalog.filter(p=>selectedIds.includes(p.id)),selectedTags=new Set(selected.flatMap(p=>[...tags(p)])),rules=PAIRING_RULES.filter(r=>selectedTags.has(r.from));const ranked=[];for(const p of catalog){if(selectedIds.includes(p.id)||p.pricing_status==='pending'||p.details?.identity_pending||p.active===0||p.stock<=0)continue;const ts=tags(p);if(ts.has('hot')&&(selectedTags.has('hot')||!selectedTags.has('alcohol')))continue;if(p.category==='alcohol'&&(!allowAlcohol||selectedTags.has('alcohol')))continue;
 const family=p.category==='sauces'?'sauces':ts.has('potato')?'potato':ts.has('water')?'water':ts.has('bread')?'bread':p.category==='alcohol'?'alcohol':ts.has('cheese')?'cheese':ts.has('light_salad')?'light_salad':p.category;
 if(selectedTags.has(family)||family==='sauces'&&selectedTags.has('sauces'))continue;
 let score=0,reason='';for(const rule of rules)for(let i=0;i<rule.to.length;i++)if(ts.has(rule.to[i])){const value=100-i*4;if(value>score){score=value;reason=rule.reason}}
 if(!score)continue;ranked.push({id:p.id,reason,score,family,margin:contribution(p)})}
 const completeScores=new Map([...new Set(ranked.map(x=>x.score))].map(score=>[score,ranked.filter(x=>x.score===score).every(x=>x.margin!==null)]));ranked.sort((a,b)=>b.score-a.score||((completeScores.get(a.score)&&a.margin!==null&&b.margin!==null)?b.margin-a.margin:0)||a.id.localeCompare(b.id));const seen=new Set(),result=[];for(const r of ranked){if(seen.has(r.family))continue;seen.add(r.family);result.push({id:r.id,reason:r.reason});if(result.length>=limit)break}return result}
