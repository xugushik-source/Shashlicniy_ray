// Practical store settings, not clinical dietary recommendations or alcohol norms.
export const FEAST_RULES={version:'2026-11-15-multi-target',hotAdult:250,hotChild:125,saladAdult:125,saladChild:75,vegetableAdult:60,vegetableChild:40,breadAdult:60,breadChild:40,sauceAdult:20,sauceChild:10,starterAdult:40,starterChild:20,softDrinkAdultMl:250,softDrinkChildMl:250,ranking:'absolute_contribution_within_feasible_table',requireConfirmedCosts:true,budgetNearRatio:0.95,maxBudgetStates:1000};
export function buildFeast(catalog,p,rules=FEAST_RULES){
 const fail=c=>{throw Error(c)},int=(n,a,b)=>Number.isInteger(n)&&n>=a&&n<=b;
 if(!int(p.adults,1,100)||!int(p.children??0,0,100)||!Array.isArray(p.categories)||!p.categories.length)fail('INVALID_NUMBER');
 if(p.budget!==undefined&&!int(p.budget,1,10000000))fail('INVALID_BUDGET');
 const adults=p.adults,children=p.children??0,guests=adults+children,budget=p.budget??Infinity;
 const selected=new Set(p.categories),prefs={salads:p.salads!==false,bread:p.bread!==false,sauces:p.sauces!==false,vegetables:p.vegetables!==false,starters:p.starters!==false,water:p.water!==false,softDrinks:p.softDrinks===true};
 const alcoholTypes=['wine','vodka','beer','chacha','cognac'];
 const legacy=p.alcohol??'none';if(!['none',...alcoholTypes].includes(legacy))fail('INVALID_ALCOHOL');
 const choices=p.alcoholSelections===undefined?(legacy==='none'?[]:[{type:legacy,quantity:p.alcoholBottles??1}]):p.alcoholSelections;
 if(!Array.isArray(choices)||choices.length>5||new Set(choices.map(x=>x?.type)).size!==choices.length||choices.some(x=>!x||!alcoholTypes.includes(x.type)||!int(x.quantity,1,12)||(x.productId!==undefined&&typeof x.productId!=='string')))fail('INVALID_ALCOHOL');
 if(p.budgetMode!==undefined&&!['target','cap'].includes(p.budgetMode))fail('INVALID_BUDGET');
 const targetBudget=Number.isFinite(budget)&&p.budgetMode!=='cap';
 const available=catalog.filter(x=>x.pricing_status!=='pending'&&!x.details?.identity_pending&&x.active!==0&&x.stock>0&&x.price>0),known=x=>!x.details?.weight_unknown&&x.grams>0;
 const name=x=>x.names.ru.toLowerCase(),isLula=x=>/люля/.test(name(x)),plainHot=x=>/шашлык|люля|мякоть|шея|шейка|корейка|цыпл|дорадо|форель|лосось|семга|сёмга|баранина|семечки|филе/.test(name(x))&&!/лаваше|шаверм|хинкал|ассорти|суп|харчо|салат|жульен|сердеч|печень|наггет/.test(name(x))&&['pork','lamb','beef','poultry','fish','tandoor','lula'].includes(x.category);
 const hot=available.filter(x=>known(x)&&plainHot(x)&&((isLula(x)&&selected.has('lula'))||selected.has(x.category))).sort((a,b)=>a.price/a.grams-b.price/b.grams||a.id.localeCompare(b.id));
 if(!hot.length)fail(available.some(x=>plainHot(x)&&!known(x))?'PORTION_UNCONFIRMED':'NO_SUITABLE_PRODUCTS');
 const hotTarget=adults*rules.hotAdult+children*rules.hotChild;
 const groupDefinitions=[
  {key:'salads',enabled:prefs.salads,target:adults*rules.saladAdult+children*rules.saladChild,products:available.filter(x=>known(x)&&x.category==='salads').sort((a,b)=>(/грузинск/.test(name(b))?1:0)-(/грузинск/.test(name(a))?1:0)||a.price/a.grams-b.price/b.grams)},
  {key:'vegetables',enabled:prefs.vegetables,target:adults*rules.vegetableAdult+children*rules.vegetableChild,products:available.filter(x=>known(x)&&x.category==='vegetables'&&!/картоф/.test(name(x))).sort((a,b)=>(/микс|овощной шашлык/.test(name(b))?1:0)-(/микс|овощной шашлык/.test(name(a))?1:0)||a.price-b.price)},
  {key:'bread',enabled:prefs.bread,target:adults*rules.breadAdult+children*rules.breadChild,products:available.filter(x=>known(x)&&x.category==='bread').sort((a,b)=>a.price/a.grams-b.price/b.grams)},
  {key:'sauces',enabled:prefs.sauces,target:adults*rules.sauceAdult+children*rules.sauceChild,products:available.filter(x=>known(x)&&x.category==='sauces'&&/сацебели|ткемали|чесноч|наршараб|шашлыч|тартар|тар-тар/.test(name(x))).sort((a,b)=>a.price-b.price||a.id.localeCompare(b.id))},
  {key:'starters',enabled:prefs.starters,target:adults*rules.starterAdult+children*rules.starterChild,products:available.filter(x=>known(x)&&/пхали|солень|рулетики из баклажанов|сыр сулугуни|сырное ассорти/.test(name(x))).sort((a,b)=>a.price/a.grams-b.price/b.grams)}
 ];
 const drinks=available.filter(x=>x.category==='drinks');
 const volume=x=>{if(x.details?.volume_ml>0)return x.details.volume_ml;const n=name(x);const ml=n.match(/(\d+)\s*мл/);if(ml)return +ml[1];const l=n.match(/(\d+(?:[.,]\d+)?)\s*(?:литр|л\b)/);if(l)return Math.round(+l[1].replace(',','.')*1000);return 0};
 const waters=drinks.filter(x=>/вода/.test(name(x))).sort((a,b)=>(/б\/газа|негаз/.test(name(b))?1:0)-(/б\/газа|негаз/.test(name(a))?1:0)||a.price-b.price);
 const soft=drinks.filter(x=>/компот|морс|лимонад|тархун|дюшес/.test(name(x))&&volume(x)>0).sort((a,b)=>a.price/volume(a)-b.price/volume(b));
 const alcoholType=x=>x.details?.alcohol_type||alcoholTypes.find(type=>({wine:/вино|саперави|ркацители/,vodka:/водка/,beer:/пиво/,chacha:/чача/,cognac:/коньяк|бренди/})[type].test(name(x)));
 const lookup=new Map(available.map(x=>[x.id,x]));
 const alcoholOptions=new Map(choices.map(c=>{if(c.productId&&(!lookup.has(c.productId)||lookup.get(c.productId).category!=='alcohol'||alcoholType(lookup.get(c.productId))!==c.type))fail('INVALID_ALCOHOL');return [c.type,available.filter(x=>x.category==='alcohol'&&alcoholType(x)===c.type&&x.stock>=c.quantity&&(!c.productId||x.id===c.productId)).sort((a,b)=>a.price-b.price||a.id.localeCompare(b.id))]}));
 const rowFor=(product,quantity,group)=>({id:product.id,quantity,group,names:product.names,price:product.price,grams:known(product)?product.grams:null,volume_ml:volume(product)||null,image:product.details?.image||null,...(group==='alcohol'?{alcohol_type:alcoholType(product)}:{})});
 function make(first,second){
  const rows=[],warnings=[];
  function add(product,quantity,group){if(!product||quantity<1)return;const old=rows.find(x=>x.id===product.id);if(old){old.quantity+=quantity;return}rows.push(rowFor(product,quantity,group))}
  let left=hotTarget;const variants=[...new Map([first,second].filter(Boolean).map(x=>[x.id,x])).values()];
  // Balance kinds, not just cheapest grams. One round distributes portions across guests.
  let index=0;while((left>0||index<Math.ceil(adults+children*0.5))&&index<200){const product=variants[index%variants.length];add(product,1,'hot');left-=product.grams;index++}
  const targets={hot:hotTarget};
  for(const g of groupDefinitions){if(!g.enabled)continue;targets[g.key]=g.target;if(!g.products.length){warnings.push('missing_'+g.key);continue}if(g.key==='sauces'){
    const hotNames=variants.map(name).join(' ');const preferred=[];
    for(const pattern of [...(/рыб|форел|семг|лосос|дорадо|сибас/.test(hotNames)?[/наршараб/,/тартар|тар-тар/]:[]),...(/свин/.test(hotNames)?[/сацебели|шашлыч/]:[]),...(/кур|индей/.test(hotNames)?[/чесноч/]:[]),...(/баран|ягнен/.test(hotNames)?[/ткемали/]:[])]){const found=g.products.find(x=>pattern.test(name(x)));if(found&&!preferred.some(x=>x.id===found.id))preferred.push(found)}
    if(!preferred.length)preferred.push(g.products[0]);let covered=0,i=0;while(covered<g.target&&i<100){const x=preferred[i%preferred.length];add(x,1,g.key);covered+=x.grams;i++}
   }else{const product=g.products[0];add(product,Math.ceil(g.target/product.grams),g.key)}}
  if(prefs.water){const w=waters[0];if(w){const ml=volume(w);const quantity=ml?Math.ceil(guests*500/ml):Math.ceil(guests/2);add(w,quantity,'water');if(!ml)warnings.push('water_volume_unknown')}else warnings.push('missing_water')}
  if(prefs.softDrinks){const d=soft[0];if(d)add(d,Math.ceil((adults*rules.softDrinkAdultMl+children*rules.softDrinkChildMl)/volume(d)),'softDrinks');else warnings.push('missing_softDrinks')}
  for(const choice of choices){const drink=alcoholOptions.get(choice.type)[0];if(drink)add(drink,choice.quantity,'alcohol');else warnings.push('missing_'+choice.type)}
  let total=rows.reduce((a,l)=>a+l.price*l.quantity,0);
  // Preserve a complete core table. Offer optional items separately when budget is tight.
  const optional=[];
  for(const group of ['starters','vegetables','softDrinks']){if(total<=budget)break;const removed=rows.filter(x=>x.group===group);for(const row of removed){optional.push(row);total-=row.price*row.quantity;rows.splice(rows.indexOf(row),1);warnings.push('budget_excluded_'+group)}}
  const tooLarge=rows.some(l=>{const product=available.find(x=>x.id===l.id);return l.quantity>Math.min(100,product.stock)});
  const variety=variants.length;const animalVariety=new Set(variants.map(x=>{const n=name(x);return /баран|ягнен/.test(n)?'lamb':/свин|свиная|шея/.test(n)?'pork':/кур|индей|цыпл/.test(n)?'poultry':/говя|теля/.test(n)?'beef':x.category})).size;
  const profitKnown=rows.every(l=>{const x=available.find(p=>p.id===l.id);return x.cost_confirmed===true&&Number.isInteger(x.cost_minor)&&x.cost_minor>=0});
  const contribution=profitKnown?rows.reduce((sum,l)=>sum+(l.price-available.find(x=>x.id===l.id).cost_minor)*l.quantity,0):null;
  return {rows,total,warnings,optional,targets,tooLarge,variety,animalVariety,profitKnown,contribution,bone:variants.filter(x=>/семечки|р[её]бр|кости|н\/к|крыл/.test(name(x))).length,hotGrams:rows.filter(x=>x.group==='hot').reduce((a,x)=>a+x.grams*x.quantity,0)};
 }
 // Upgrade existing slots, never add unrequested alcohol or multiply bottles to spend money.
 function fitBudget(plan){
  if(!targetBudget||plan.total>budget)return plan;
  const slots=plan.rows.map(line=>{
   let options=[line];
   if(line.group==='alcohol')options=alcoholOptions.get(line.alcohol_type).map(x=>rowFor(x,line.quantity,'alcohol'));
   else if(['salads','vegetables','starters','bread'].includes(line.group)&&plan.rows.filter(x=>x.group===line.group).length===1){const def=groupDefinitions.find(x=>x.key===line.group);options=def.products.filter(x=>!x.details?.bundle&&x.grams<=Math.max(350,def.target*2)).map(x=>rowFor(x,Math.ceil(def.target/x.grams),line.group));options.push(line)}
   else if(line.group==='softDrinks')options=soft.map(x=>rowFor(x,Math.ceil((adults*rules.softDrinkAdultMl+children*rules.softDrinkChildMl)/volume(x)),line.group));
   if(['starters','vegetables','softDrinks'].includes(line.group))options.push({...line,quantity:0});
   return [...new Map(options.filter(l=>l.quantity<=Math.min(100,lookup.get(l.id).stock)).map(l=>[l.id+'|'+l.quantity,l])).values()];
  });
  const suffix=Array(slots.length+1).fill(0);for(let i=slots.length-1;i>=0;i--)suffix[i]=suffix[i+1]+Math.min(...slots[i].map(l=>l.price*l.quantity));
  const costsKnown=slots.every(options=>options.every(l=>{const x=lookup.get(l.id);return x.cost_confirmed===true&&Number.isInteger(x.cost_minor)&&x.cost_minor>=0}));
  let states=new Map([[0,{rows:[],profit:0}]]);
  for(let i=0;i<slots.length;i++){const next=new Map();for(const [spent,state] of states)for(const line of slots[i]){const sum=spent+line.price*line.quantity;if(sum+suffix[i+1]>budget)continue;const profit=costsKnown?state.profit+(line.price-lookup.get(line.id).cost_minor)*line.quantity:0;const old=next.get(sum);if(!old||profit>old.profit)next.set(sum,{rows:[...state.rows,line],profit})}states=next.size>(rules.maxBudgetStates??1000)?new Map([...next].sort((a,b)=>b[0]-a[0]).slice(0,rules.maxBudgetStates??1000)):next;if(!states.size)return plan}
  const options=[...states].map(([total,state])=>({total,...state}));
  options.sort((a,b)=>{const nearA=a.total>=budget*(rules.budgetNearRatio??0.95),nearB=b.total>=budget*(rules.budgetNearRatio??0.95);return Number(nearB)-Number(nearA)||(nearA&&nearB&&costsKnown?b.profit-a.profit:0)||b.total-a.total});
  const best=options[0],merged=new Map();for(const row of best.rows){if(!row.quantity)continue;const old=merged.get(row.id);if(old)old.quantity+=row.quantity;else merged.set(row.id,{...row})}
  const rows=[...merged.values()];if(rows.some(l=>l.quantity>Math.min(100,lookup.get(l.id).stock)))return plan;
  const removed=best.rows.filter(l=>!l.quantity).map(l=>plan.rows.find(x=>x.id===l.id));
  return {...plan,rows,total:best.total,optional:[...plan.optional,...removed],warnings:[...plan.warnings,...removed.map(l=>'budget_excluded_'+l.group)],profitKnown:costsKnown,contribution:costsKnown?best.profit:null};
 }
 const pairs=[];const lula=hot.filter(isLula).slice(0,8),shashlik=hot.filter(x=>!isLula(x)).slice(0,12);
 if(lula.length&&shashlik.length)for(const a of lula)for(const b of shashlik)pairs.push([a,b]);
 else{for(let i=0;i<Math.min(hot.length,12);i++)for(let j=i+1;j<Math.min(hot.length,12);j++)pairs.push([hot[i],hot[j]]);if(!pairs.length)pairs.push([hot[0]])}
 const plans=pairs.map(x=>make(...x)).filter(x=>!x.tooLarge);if(!plans.length)fail('INSUFFICIENT_STOCK');
 let candidates=plans;
 const baseQuality=(a,b)=>b.variety-a.variety||a.optional.length-b.optional.length||b.animalVariety-a.animalVariety||a.bone-b.bone;
 if(targetBudget){const ordered=[...plans].sort((a,b)=>baseQuality(a,b)||b.total-a.total);const feasible=ordered.filter(x=>x.total<=budget);if(feasible.length)candidates=feasible.map(fitBudget)}
 const affordable=candidates.filter(x=>x.total<=budget);
 const allCostsKnown=candidates.every(x=>x.profitKnown);
 const ranking=(a,b)=>{if(targetBudget){const nearA=a.total>=budget*(rules.budgetNearRatio??0.95),nearB=b.total>=budget*(rules.budgetNearRatio??0.95);return b.variety-a.variety||Number(nearB)-Number(nearA)||(nearA&&nearB&&allCostsKnown?b.contribution-a.contribution:0)||b.total-a.total||baseQuality(a,b)}return baseQuality(a,b)||(allCostsKnown?b.contribution-a.contribution:0)||Math.abs(a.hotGrams-hotTarget)-Math.abs(b.hotGrams-hotTarget)||a.total-b.total};
 const result=(affordable.length?affordable:candidates).sort(affordable.length?ranking:(a,b)=>a.total-b.total)[0];
 const items=result.rows.map(l=>({id:l.id,quantity:l.quantity}));
 const hotRows=result.rows.filter(l=>l.group==='hot');const meatWeightsConfirmed=hotRows.every(l=>{const x=available.find(p=>p.id===l.id);return Number.isInteger(x.details?.cooked_meat_g)&&x.details.cooked_meat_g>=0&&x.details.cooked_meat_g<=x.grams});
 const meatGrams=meatWeightsConfirmed?hotRows.reduce((sum,l)=>sum+available.find(p=>p.id===l.id).details.cooked_meat_g*l.quantity,0):null;
 const food=result.rows.filter(l=>!['water','softDrinks','alcohol'].includes(l.group));
 return {items,lines:result.rows,total:result.total,grams:food.reduce((a,l)=>a+(l.grams||0)*l.quantity,0),hot_grams:result.hotGrams,meat_grams:meatGrams,weight_basis:'complete_dish',budget_mode:targetBudget?'target':'cap',alcohol_selections:choices.map(c=>({...c})),guests,adults,children,budget:p.budget??null,budget_ok:result.total<=budget,remaining:p.budget===undefined?null:p.budget-result.total,required_grams:hotTarget,targets:result.targets,warnings:[...new Set(result.warnings)],optional:result.optional,rules_version:rules.version};
}
