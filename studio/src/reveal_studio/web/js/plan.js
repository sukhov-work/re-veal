// plan.js: the plan panel: the timeline as bars, the forms generated from the registry's plan schema, undo and redo,
// "% faster", the JSON tab kept in sync both ways, save as a new plan; the rulings' resolver and chips (used by the
// inspector too); the page panel's variants control (backlog T76).
'use strict';
// The editor's state lives here, not in S: the poll may rebuild the panel at any time and the editor renders from PE.
// A form edit is a path set on the loaded plan object, never a plan rebuilt from the form, so a saved copy records
// exactly the keys that were changed (an empty field removes its key; no default is ever written back).
const PE={jid:null,plan:null,from:'',base:'null',hist:[],cur:-1,sel:{k:'plan'},tab:'bars',json:null,jsonErr:'',
  name:'',words:'',faster:'',focus:null,focusNext:null,hits:[],variants:{}};
const GEN_METHODS=['rife','teleport','slide','rise'];  // their frames.json rows say "rife": the generated violet
const peClone=o=>JSON.parse(JSON.stringify(o));

// ------------------------------------------------------------------ the schema and the resolver (registry/schema.py)
function peSchema(){return S.reg.plan_schema;}
function peEntry(group,key){return peSchema().entries.find(e=>e.group===group&&e.key===key)||null;}
function peGroupTitle(g){const x=peSchema().groups.find(x=>x.group===g);return x?x.title:g;}
function stepGroups(st){if(!('to' in st))return ['hold'];const m=st.method||'rife';return [m,'transition'].concat(peSchema().chain_methods.includes(m)?['chain']:[]);}
function isObj(o){return o!==null&&typeof o==='object'&&!Array.isArray(o);}
function elGroups(listKey,el,parent){
  if(!isObj(el))return [];
  if(listKey==='timeline'&&parent.includes('plan'))return stepGroups(el);
  if(listKey==='effects'&&parent.includes('plan'))return ['effect.'+el.kind,'effect'];
  for(const g of parent){const e=peEntry(g,listKey);if(e&&e.item&&peSchema().groups.some(x=>x.group===e.item))return [e.item];}
  return [];}
function entryFor(groups,key){for(const g of groups){const e=peEntry(g,key);if(e)return e;}return null;}
function selOk(sel,el,groups){if(sel==='*')return true;const [k,v]=sel.split('=');if(k in el)return String(el[k])===v;const e=entryFor(groups,k);return !!e&&e.default!==null&&String(e.default)===v;}
// Every place a pattern names in a plan as [pointer, effective value, explicit]; an absent key takes its default.
function resolvePath(plan,pattern){
  const segs=pattern.split('.').map(s=>{const m=s.match(/^([A-Za-z_][A-Za-z0-9_]*)(?:\[([^\]]+)\])?$/);return [m[1],m[2]===undefined?null:m[2]];});
  let nodes=[['',plan,['plan']]];const out=[];
  segs.forEach(([name,sel],depth)=>{const last=depth===segs.length-1;const nxt=[];
    nodes.forEach(([ptr,obj,groups])=>{
      if(!isObj(obj))return;
      if(last&&sel===null){if(name in obj)out.push([ptr+'/'+name,obj[name],true]);else{const e=entryFor(groups,name);if(e&&e.default!==null)out.push([ptr+'/'+name,e.default,false]);}return;}
      const child=obj[name];
      if(sel===null){const p=entryFor(groups,name);if(isObj(child)&&p&&p.item)nxt.push([ptr+'/'+name,child,[p.item]]);return;}
      if(!Array.isArray(child))return;
      child.forEach((el,i)=>{const eg=elGroups(name,el,groups);if(isObj(el)&&eg.length&&selOk(sel,el,eg))nxt.push([ptr+'/'+name+'/'+i,el,eg]);});});
    nodes=nxt;});
  return out;}
// ------------------------------------------------------------------ the rulings (registry/rulings.py): warnings, never refusals
function ruledVal(r,v){if(isObj(r)){if(typeof v!=='number')return false;if('min' in r)return v>=r.min;if('above' in r)return v>r.above;return false;}if(typeof r==='boolean'||typeof v==='boolean')return r===v;return JSON.stringify(r)===JSON.stringify(v);}
function isStageKnob(k){return (S.reg.stage_order||[]).includes(k.split('.')[0].split('[')[0]);}
function planHits(plan){const out=[];(S.reg.rulings||[]).forEach(r=>{if(isStageKnob(r.knob))return;resolvePath(plan,r.knob).forEach(([p,v,ex])=>{if(ruledVal(r.value,v))out.push({knob:r.knob,since:r.since,why:r.why,source:r.source,path:p,value:v,absent:!ex});});});return out;}
function ruledChip(w){return '<span class="chip bad ruled" data-hint="chip.ruled_out">ruled out '+esc(w.since)+': '+esc(w.why)+(w.absent?' (the code\'s default, the key is absent)':'')+'</span>';}
// The inspector's knob rows: a stage knob's ruled value, and for the render's plan the ruled values the plan holds.
function rulingChips(stage,key,val){
  if(!S.reg||!S.reg.rulings||!S.view)return '';
  if(stage==='render'&&key==='plan'){const p=(S.view.plans||[]).concat(S.view.frozen_plans||[]).find(p=>p.ref===val);const ws=(p&&p.warnings)||[];return ws.length?'<div class="rulings">'+ws.map(w=>'<span class="data muted">'+esc(w.path)+'</span> '+ruledChip(w)).join('<br>')+'</div>':'';}
  const ws=S.reg.rulings.filter(r=>r.knob===stage+'.'+key&&ruledVal(r.value,val));
  return ws.length?'<div class="rulings">'+ws.map(r=>ruledChip(r)).join('')+'</div>':'';}
// The 202 body's warnings, as a tail for the "started" message.
function runWarnings(ws){return ws&&ws.length?' · '+ws.length+' ruled value'+(ws.length>1?'s':'')+': '+ws.map(w=>w.path+' = '+JSON.stringify(w.value)+' (ruled out '+w.since+')').join('; ')+'; the record keeps the warning':'';}

// ------------------------------------------------------------------ pointers, diff, history
function ptrParts(p){return p.split('/').slice(1).map(x=>/^\d+$/.test(x)?+x:x);}
function getAt(o,p){return ptrParts(p).reduce((a,k)=>a==null?undefined:a[k],o);}
function setAt(o,p,v){const ks=ptrParts(p);let a=o;ks.slice(0,-1).forEach((k,i)=>{if(a[k]==null||typeof a[k]!=='object')a[k]=typeof ks[i+1]==='number'?[]:{};a=a[k];});a[ks[ks.length-1]]=v;}
function delAt(o,p){const ks=ptrParts(p);const a=getAt(o,'/'+ks.slice(0,-1).join('/'));const k=ks[ks.length-1];if(Array.isArray(a)&&typeof k==='number')a.splice(k,1);else if(isObj(a))delete a[k];}
// The changed leaves as jobs/plans.py's plan_diff counts them (the provenance block skipped).
function planDiff(a,b,out){out=out||[];if(isObj(a)&&isObj(b)){new Set(Object.keys(a).concat(Object.keys(b))).forEach(k=>{if(k==='provenance')return;if(!(k in a)||!(k in b))out.push(k);else planDiff(a[k],b[k],out);});}else if(Array.isArray(a)&&Array.isArray(b)){for(let i=0;i<Math.max(a.length,b.length);i++){if(i>=a.length||i>=b.length)out.push(i);else planDiff(a[i],b[i],out);}}else if(JSON.stringify(a)!==JSON.stringify(b))out.push(1);return out;}
function peCommit(next){const j=JSON.stringify(next);if(j===PE.hist[PE.cur])return false;PE.hist=PE.hist.slice(0,PE.cur+1);PE.hist.push(j);if(PE.hist.length>300)PE.hist.shift();PE.cur=PE.hist.length-1;PE.plan=next;PE.json=null;PE.jsonErr='';peSoon();return true;}
// A field commits on `change`, which a mouse press elsewhere fires before its click: the rebuild waits for the
// pointer to come up, so the click lands on the element the owner pressed and its own handler renders.
let peDown=false,pePending=false;
document.addEventListener('pointerdown',()=>{peDown=true;},true);
document.addEventListener('pointerup',()=>{peDown=false;if(pePending)setTimeout(()=>{if(pePending)peRender();},0);},true);
function peSoon(){pePending=true;if(!peDown)setTimeout(()=>{if(pePending)peRender();},0);}
// an undo or a redo clears the message: it described the step just undone (critique A2, minor 6)
function peUndo(){if(PE.cur<=0)return;PE.cur--;PE.plan=JSON.parse(PE.hist[PE.cur]);PE.json=null;PE.jsonErr='';peFixSel();setMsg('');peRender();}
function peRedo(){if(PE.cur>=PE.hist.length-1)return;PE.cur++;PE.plan=JSON.parse(PE.hist[PE.cur]);PE.json=null;PE.jsonErr='';peFixSel();setMsg('');peRender();}
function peFixSel(){const s=PE.sel,p=PE.plan;if(s.k==='step'&&!(p.timeline||[])[s.i])PE.sel={k:'plan'};if(s.k==='fx'&&!(p.effects||[])[s.i])PE.sel={k:'plan'};}

// ------------------------------------------------------------------ the timeline's arithmetic
function stepFrames(st,before){if(!('to' in st))return {n:st.hold!==undefined?st.hold:1,est:false};const m=st.method||'rife';
  if(m==='cut')return {n:0,est:false};
  if(m==='rewind'){const s=st.stride||3,f=st.from||0;return {n:Math.max(0,Math.ceil((before-f-s)/s)),est:true};}
  if(m==='slices')return {n:st.n||0,est:true};
  return {n:st.n||0,est:false};}
function peTimeline(plan){let cur=null,f=0,est=false;return (plan.timeline||[]).map((st,i)=>{const r=stepFrames(st,f);const from=cur;if('to' in st)cur=st.to;else cur=st.key;const row={i,st,from,to:cur,start:f,n:r.n,est:r.est};f+=r.n;est=est||r.est;row.total=f;row.anyEst=est;return row;});}

// ------------------------------------------------------------------ the panel
function panelPlan(){
  const v=S.view;if(PE.jid!==v.job.id){Object.assign(PE,{jid:v.job.id,plan:null,from:'',base:'null',hist:[],cur:-1,sel:{k:'plan'},tab:'bars',json:null,jsonErr:'',name:'',words:''});}
  const ae=document.activeElement;const inside=!!(ae&&ae.closest&&ae.closest('#pe'));
  const k=inside?peKey(ae):null;if(k){PE.focus=k;queueMicrotask(peAfter);}  // after renderPanel's innerHTML
  pePending=false;
  return '<p class="muted">'+esc(stageOf('plan').what)+' '+hintBtn('control.save_plan')+'</p><div id="pe">'+peHTML()+'</div>';}
// Rebuilds the editor only; the focus returns to the element of the same data-pf (an action may name the next one),
// and is never pulled into the editor from a control outside it.
function peRender(){const box=$('#pe');pePending=false;if(!box)return;const ae=document.activeElement;const inside=!!(ae&&box.contains(ae));
  if(PE.focusNext){PE.focus=PE.focusNext;PE.focusNext=null;}else if(inside)PE.focus=peKey(ae);else if(ae&&ae!==document.body)PE.focus=null;
  box.innerHTML=peHTML();peAfter();}
// A focusable element's key: its data-pf, or for a hint button its hint key and its place among the same key's buttons.
function peKey(el){if(!el||!el.dataset)return null;if(el.dataset.pf)return el.dataset.pf;if(el.matches('.hint')){const same=[...document.querySelectorAll('#pe .hint')].filter(x=>x.dataset.hint===el.dataset.hint);return 'hint:'+same.indexOf(el)+':'+el.dataset.hint;}return null;}
function peFind(k){if(k.startsWith('hint:')){const m=k.match(/^hint:(\d+):(.*)$/);const same=[...document.querySelectorAll('#pe .hint')].filter(x=>x.dataset.hint===m[2]);return same[+m[1]]||null;}return document.querySelector('#pe [data-pf="'+CSS.escape(k)+'"]');}
function peAfter(){if(!PE.focus)return;const el=peFind(PE.focus);if(el)focusQuiet(el);}
function peHTML(){
  const v=S.view;const opts=v.plans.map(p=>'<option value="'+esc(p.ref)+'"'+(PE.from===p.ref?' selected':'')+'>'+esc(p.ref)+(p.title?' · '+esc(p.title.slice(0,60)):'')+'</option>').join('')+v.frozen_plans.map(p=>'<option value="'+esc(p.ref)+'"'+(PE.from===p.ref?' selected':'')+'>'+esc(p.ref)+(p.seq?' · '+esc(p.seq):'')+'</option>').join('');
  let h='<div class="pe-top"><label class="label muted" for="peFrom">start from</label><select id="peFrom" data-pf="from" data-name="pe:from" data-hint="control.plan_load"><option value="">— empty plan —</option>'+opts+'</select><button class="btn" data-pa="load" data-pf="btn:load" data-hint="control.plan_load">load</button>'+hintBtn('control.plan_load');
  if(PE.plan){const n=planDiff(JSON.parse(PE.base),PE.plan).length;const tl=peTimeline(PE.plan);const last=tl[tl.length-1];
    h+='<div class="seg" role="group" aria-label="editor view"><button data-pa="tab" data-tab="bars" data-pf="tab:bars" data-hint="control.plan_json" aria-pressed="'+(PE.tab==='bars')+'">bars</button><button data-pa="tab" data-tab="json" data-pf="tab:json" data-hint="control.plan_json" aria-pressed="'+(PE.tab==='json')+'">JSON</button></div>'+hintBtn('control.plan_json');
    h+='<button class="btn" data-pa="undo" data-pf="btn:undo" data-hint="control.plan_undo"'+(PE.cur>0?'':' disabled')+' aria-keyshortcuts="Meta+Z Control+Z">undo</button>'+hintBtn('control.plan_undo')+'<button class="btn" data-pa="redo" data-pf="btn:redo" data-hint="control.plan_redo"'+(PE.cur<PE.hist.length-1?'':' disabled')+' aria-keyshortcuts="Shift+Meta+Z Shift+Control+Z">redo</button>'+hintBtn('control.plan_redo');
    h+='<span class="pe-count" data-hint="control.plan_changes"><span class="data">'+n+'</span> change'+(n===1?'':'s')+' from <span class="data">'+esc(PE.from||'the empty plan')+'</span></span>';
    h+='<span class="pe-faster"><input id="peFaster" data-pf="faster" data-name="pe:faster" data-hint="control.plan_faster" inputmode="decimal" value="'+esc(PE.faster)+'" aria-label="percent faster"><span class="unit">% faster</span><button class="btn" data-pa="faster" data-pf="btn:faster" data-hint="control.plan_faster">apply</button>'+hintBtn('control.plan_faster')+'</span>';
    h+='<span class="pe-total data">'+(last?(last.anyEst?'≈':'')+last.total+'<span class="unit">f</span> · '+(last.total/25).toFixed(2)+'<span class="unit">s at 25 fps</span>':'0<span class="unit">f</span>')+'</span>';}
  h+='</div>';
  if(!PE.plan)return h+'<div class="empty">Load a plan to edit it as bars and forms; "— empty plan —" starts from a plan with no steps.</div>';
  PE.hits=planHits(PE.plan);
  if(PE.json!==null&&PE.jsonErr&&PE.tab==='bars')h+='<div class="msg bad">The JSON tab holds text that does not parse ('+esc(PE.jsonErr)+'): the bars show the last valid plan. <button class="btn ghost" data-pa="tab" data-tab="json" data-pf="btn:fixjson" data-hint="control.plan_json">fix it</button><button class="btn ghost" data-pa="json-discard" data-hint="control.plan_json" data-pf="btn:discard">discard the text</button></div>';
  if(PE.hits.length)h+='<div class="pe-hits"><span class="label">'+PE.hits.length+' ruled value'+(PE.hits.length>1?'s':'')+'</span> '+PE.hits.map(w=>{const m=w.path.match(/^\/(timeline|effects)\/(\d+)/);return '<button class="btn ghost data" data-hint="chip.ruled_out" data-pa="sel" data-k="'+(m&&m[1]==='effects'?'fx':(m?'step':'plan'))+'" data-i="'+(m?m[2]:'')+'" data-pf="hit:'+esc(w.path)+'">'+esc(w.path)+' = '+esc(JSON.stringify(w.value))+'</button>';}).join(' ')+'</div>';
  h+=PE.tab==='json'?peJsonTab():peBarsTab();
  h+='<div class="pe-save"><input id="peName" data-pf="name" data-name="pe:name" data-hint="control.save_plan" placeholder="name (letters, digits, - _)" value="'+esc(PE.name)+'" aria-label="the new plan\'s name"><input id="peWords" data-pf="words" data-name="pe:words" data-hint="control.save_plan" placeholder="your words (why)" value="'+esc(PE.words)+'" aria-label="your words"><button class="btn primary" data-pa="save" data-pf="btn:save" data-hint="control.save_plan">save as a new plan</button>'+hintBtn('control.save_plan')+'</div>';
  return h;}
function peJsonTab(){
  const text=PE.json!==null?PE.json:JSON.stringify(PE.plan,null,1);
  return '<textarea id="peJson" data-pf="json" data-hint="control.plan_json" spellcheck="false" aria-label="the plan as JSON">'+esc(text)+'</textarea><div class="pe-jerr'+(PE.jsonErr?' bad':'')+'" id="peJsonErr">'+(PE.jsonErr?'JSON: '+esc(PE.jsonErr)+'. The bars keep the last valid plan until the text parses.':'The text enters the history when the field loses the focus.')+'</div>'+(PE.jsonErr?'<button class="btn ghost" data-pa="json-discard" data-hint="control.plan_json" data-pf="btn:discard">discard the text</button>':'')+
    '<p class="muted pe-keys">The bars tab shows each key\'s sentence, default and units beside its field. Methods: '+S.reg.methods.map(m=>'<code>'+esc(m)+'</code>').join(' ')+'; eases: '+S.reg.eases.map(m=>'<code>'+esc(m)+'</code>').join(' ')+'.</p>';}

// ------------------------------------------------------------------ the bars
function barLabel(r){const st=r.st;if(!('to' in st))return 'hold · '+r.n+' f';const m=st.method||'rife';
  if(m==='cut')return 'cut';
  const e=st.ease||(m==='sheets'?'linear':'smooth');
  return m+(m==='snap'||m==='rewind'?'':' · '+e)+(st.through?' · through '+st.through.join(', '):'')+(m==='sheets'&&st.sheets?' · '+st.sheets.length+' sheets':'')+' · '+(r.est?'≈':'')+r.n+' f';}
function peBarsTab(){
  const tl=peTimeline(PE.plan);const fx=PE.plan.effects||[];const sel=PE.sel;
  const hitSteps=new Set(PE.hits.map(w=>(w.path.match(/^\/timeline\/(\d+)/)||[])[1]).filter(x=>x!==undefined).map(Number));
  let bars=tl.map(r=>{const st=r.st;const m='to' in st?(st.method||'rife'):null;const cls=['pe-bar',m?'tr':'hold',m==='cut'?'cut':'',GEN_METHODS.includes(m)?'gen':'',hitSteps.has(r.i)?'ruled':''].join(' ');
    const on=sel.k==='step'&&sel.i===r.i;const label=barLabel(r);const ends=m?('k'+(r.from==null?'?':r.from)+' → k'+r.to):('k'+st.key);
    const tabi=(on||(sel.k!=='step'&&r.i===0))?'0':'-1';
    if(m==='cut')return '<button class="'+cls+'" data-pa="sel" data-k="step" data-i="'+r.i+'" data-pf="bar:'+r.i+'" data-hint="region.plan_bars" tabindex="'+tabi+'" role="tab" aria-selected="'+on+'" aria-label="step '+r.i+': cut '+esc(ends)+'" title="step '+r.i+': cut '+esc(ends)+'"></button>';
    return '<button class="'+cls+'" style="flex-grow:'+Math.max(1,r.n)+'" data-pa="sel" data-k="step" data-i="'+r.i+'" data-pf="bar:'+r.i+'" data-hint="region.plan_bars" tabindex="'+tabi+'" role="tab" aria-selected="'+on+'" aria-label="step '+r.i+': '+esc(label)+', '+esc(ends)+'" title="step '+r.i+' · frames '+r.start+'–'+(r.start+r.n-1)+' · '+esc(label)+'">'+
      '<span class="pe-end l data">'+(m?'k'+(r.from==null?'?':r.from):'k'+st.key)+'</span><span class="pe-lb">'+esc(label)+(hitSteps.has(r.i)?' · ruled':'')+'</span>'+(m?'<span class="pe-end r data">k'+r.to+'</span>':'')+'</button>';}).join('');
  if(!tl.length)bars='<span class="muted">no steps: add a hold</span>';
  let h='<div class="pe-main"><div class="pe-left">';
  h+='<div class="pe-acts"><button class="btn" data-pa="add-hold" data-pf="btn:add-hold" data-hint="control.plan_add_hold">add a hold after</button>'+hintBtn('control.plan_add_hold')+'<button class="btn" data-pa="add-tr" data-pf="btn:add-tr" data-hint="control.plan_add_transition">add a transition after</button>'+hintBtn('control.plan_add_transition')+'<button class="btn" data-pa="move" data-d="-1" data-pf="btn:left" data-hint="control.plan_move"'+(sel.k==='step'&&sel.i>0?'':' disabled')+'>move left</button><button class="btn" data-pa="move" data-d="1" data-pf="btn:right" data-hint="control.plan_move"'+(sel.k==='step'&&sel.i<tl.length-1?'':' disabled')+'>move right</button>'+hintBtn('control.plan_move')+'<button class="btn" data-pa="remove" data-pf="btn:remove" data-hint="control.plan_remove"'+(sel.k==='step'||sel.k==='fx'?'':' disabled')+'>remove</button>'+hintBtn('control.plan_remove')+'<button class="btn" data-pa="sel" data-k="plan" data-hint="region.plan_form" data-pf="btn:plan" aria-pressed="'+(sel.k==='plan')+'">plan keys</button></div>';
  h+='<div class="label muted pe-rowlbl">timeline '+hintBtn('region.plan_bars')+'</div><div class="pe-bars" role="tablist" aria-label="the timeline, one bar per step">'+bars+'</div>';
  h+='<div class="label muted pe-rowlbl">effects over the loop '+hintBtn('region.plan_effects')+'</div><div class="pe-fxs" role="tablist" aria-label="the effects over the loop">'+(fx.length?fx.map((e,i)=>{const on=sel.k==='fx'&&sel.i===i;const ruled=PE.hits.some(w=>w.path.startsWith('/effects/'+i+'/'));return '<button class="pe-fx'+(ruled?' ruled':'')+'" data-pa="sel" data-k="fx" data-i="'+i+'" data-pf="fx:'+i+'" data-hint="region.plan_effects" role="tab" tabindex="'+(on||(sel.k!=='fx'&&i===0)?'0':'-1')+'" aria-selected="'+on+'">'+esc(fxLabel(e))+'</button>';}).join(''):'<span class="muted">no effects</span>')+'</div>';
  h+='<div class="pe-acts"><select id="peFxKind" data-pf="fxkind" data-name="pe:fxkind" data-hint="control.plan_add_effect" aria-label="effect kind">'+S.reg.effects.map(k=>'<option>'+esc(k)+'</option>').join('')+'</select><button class="btn" data-pa="add-fx" data-pf="btn:add-fx" data-hint="control.plan_add_effect">add an effect</button>'+hintBtn('control.plan_add_effect')+'</div>';
  h+='</div><div class="pe-form">'+peForm()+'</div></div>';
  return h;}
function fxLabel(e){const k=e.kind;const nums=Object.keys(e).filter(x=>x!=='kind'&&typeof e[x]==='number').slice(0,3).map(x=>x+' '+e[x]);return k+(nums.length?' · '+nums.join(' · '):'')+' · over the loop';}

// ------------------------------------------------------------------ the forms
function peForm(){const s=PE.sel,p=PE.plan;
  if(s.k==='step'){const st=p.timeline[s.i];const groups=stepGroups(st);const r=peTimeline(p)[s.i];
    return '<h3>step '+s.i+' · '+esc('to' in st?'a transition k'+(r.from==null?'?':r.from)+' → k'+st.to:'a hold on k'+st.key)+hintBtn('region.plan_form')+'</h3>'+peFields(st,'/timeline/'+s.i,groups);}
  if(s.k==='fx'){const e=p.effects[s.i];return '<h3>effect '+s.i+' · '+esc(e.kind||'?')+hintBtn('region.plan_form')+'</h3>'+peFields(e,'/effects/'+s.i,['effect.'+e.kind,'effect']);}
  return '<h3>the plan'+hintBtn('region.plan_form')+'</h3>'+peFields(p,'',['plan']);}
// The entries of an element's groups in display order: the transition's keys (a method's override in their place),
// the chain's, then the method's own; a group's own keys for the others.
function peEntriesOf(groups){const all=peSchema().entries;const own=g=>all.filter(e=>e.group===g);
  if(groups[0]==='hold'||groups[0]==='plan'||groups.length===1)return own(groups[0]);
  if(groups[1]==='effect')return own('effect').concat(own(groups[0]));
  const m=groups[0];const over={};own(m).forEach(e=>over[e.key]=e);
  const out=own('transition').map(e=>over[e.key]||e);
  if(groups.includes('chain'))out.push(...own('chain'));
  own(m).forEach(e=>{if(!out.includes(e))out.push(e);});return out;}
// The chain's weights, soft and knot_margin show only on a step with `through` (or when the step sets them).
function peFields(obj,ptr,groups){const o=obj||{};const es=peEntriesOf(groups).filter(e=>e.group!=='chain'||e.key==='through'||'through' in o||e.key in o);const known=new Set(es.map(e=>e.key));
  if(groups[0]==='plan'){['timeline','effects','provenance'].forEach(k=>known.add(k));}
  let h=es.map(e=>peRow(e,obj,ptr)).join('');
  const other=Object.keys(obj||{}).filter(k=>!known.has(k));
  if(other.length)h+='<div class="label muted pe-sub">other keys: loop_seq.py reads them, the schema does not list them</div>'+other.map(k=>peOtherRow(k,obj[k],ptr+'/'+k)).join('');
  return h;}
function peHitsAt(p){return PE.hits.filter(w=>w.path===p).map(ruledChip).join('');}
function peDef(e,has){if(e.default===null)return e.required?(has?'required':'<span class="chip bad" data-hint="chip.required">required</span>'):'absent: none';return 'default <span class="data">'+esc(JSON.stringify(e.default))+'</span>'+(e.default_from?' · '+esc(e.default_from):'');}
function peRow(e,obj,ptr){const p=ptr+'/'+e.key;const has=isObj(obj)&&(e.key in obj);const val=has?obj[e.key]:undefined;
  if(e.type==='list'&&e.item&&e.item.includes('.'))return peItems(e,val,p);
  if(e.type==='object'&&e.item)return '<div class="pe-sub label">'+esc(e.key)+' '+hintBtn(e.hint)+' <span class="muted">'+peDef(e,has)+'</span></div>'+peSchema().entries.filter(x=>x.group===e.item).map(x=>peRow(x,isObj(val)?val:{},p)).join('');
  const missing=e.required&&!has;
  return '<div class="pe-row'+(missing?' missing':'')+'"><div class="pe-k"><span class="key data">'+esc(e.key)+'</span>'+hintBtn(e.hint)+'</div><div class="pe-v">'+peInput(e,val,has,p)+(e.units?'<span class="unit">'+esc(e.units)+'</span>':'')+(has&&!e.required?'<button class="btn ghost" data-pa="clear" data-hint="control.plan_clear" data-ptr="'+esc(p)+'" data-pf="clr:'+esc(p)+'" aria-label="clear '+esc(e.key)+'">clear</button>':'')+'</div><div class="pe-d">'+peDef(e,has)+(missing?' · the render fails without it':'')+'</div>'+peHitsAt(p)+'<div class="pe-err" data-err="'+esc(p)+'"></div></div>';}
function peAttrs(e,p,extra){return ' data-pf="f:'+esc(p)+(extra||'')+'" data-name="f:'+esc(p)+(extra||'')+'" data-ptr="'+esc(p)+'" data-path="'+esc(e.path)+'" data-type="'+esc(e.type)+'" data-hint="'+esc(e.hint)+'"';}
function peInput(e,val,has,p){const t=e.type;const lab=' aria-label="'+esc(e.key)+'"';
  if(t==='bool')return '<input type="checkbox" class="pe-in"'+peAttrs(e,p)+lab+((has?val:e.default)===true?' checked':'')+'>';
  if(e.choices){const cur=has?val:undefined;const opts=e.choices.slice();if(has&&!opts.some(c=>JSON.stringify(c)===JSON.stringify(cur)))opts.push(cur);
    return '<select class="pe-in"'+peAttrs(e,p)+lab+'><option value=""'+(has?'':' selected')+'>'+(e.default!==null?'— '+esc(String(e.default))+' (default)':'— absent')+'</option>'+opts.map(c=>'<option value="'+esc(JSON.stringify(c))+'"'+(has&&JSON.stringify(c)===JSON.stringify(cur)?' selected':'')+'>'+esc(String(c))+'</option>').join('')+'</select>';}
  if(t==='box'||t==='point'){const n=t==='box'?4:2;const roles=e.roles||[];const arr=Array.isArray(val)?val:[];const def=Array.isArray(e.default)?e.default:[];
    return '<span class="pe-nums">'+Array.from({length:n},(_,i)=>'<label class="pe-role"><span class="label muted">'+esc(roles[i]||String(i))+'</span><input class="pe-in pe-num" inputmode="decimal"'+peAttrs(e,p,'#'+i)+' data-idx="'+i+'" value="'+esc(has&&arr[i]!==undefined?String(arr[i]):'')+'" data-v="'+esc(has&&arr[i]!==undefined?String(arr[i]):'')+'" placeholder="'+esc(def[i]!==undefined?String(def[i]):'')+'" aria-label="'+esc(e.key+' '+(roles[i]||i))+'"></label>').join('')+'</span>';}
  if(t==='object'){const s=has?JSON.stringify(val):'';return '<textarea class="pe-in pe-obj"'+peAttrs(e,p)+lab+' rows="2" spellcheck="false" data-v="'+esc(s)+'" placeholder="'+esc(e.default!==null?JSON.stringify(e.default):'')+'">'+esc(s)+'</textarea>';}
  const s=!has?'':(t==='list'?(Array.isArray(val)?val.join(', '):JSON.stringify(val)):(typeof val==='string'?val:JSON.stringify(val)));
  const ph=e.default===null?'':(Array.isArray(e.default)?e.default.join(', '):String(e.default));
  return '<input class="pe-in'+(t==='str'?' pe-text':'')+'"'+peAttrs(e,p)+lab+(t==='int'||t==='float'||t==='list'?' inputmode="decimal"':'')+' value="'+esc(s)+'" data-v="'+esc(s)+'" placeholder="'+esc(ph)+'">';}
function peOtherRow(k,v,p){const s=JSON.stringify(v);return '<div class="pe-row"><div class="pe-k"><span class="key data">'+esc(k)+'</span></div><div class="pe-v"><input class="pe-in pe-text" data-pf="f:'+esc(p)+'" data-name="f:'+esc(p)+'" data-ptr="'+esc(p)+'" data-type="json" data-hint="region.plan_form" value="'+esc(s)+'" data-v="'+esc(s)+'" aria-label="'+esc(k)+' as JSON"><button class="btn ghost" data-pa="clear" data-hint="control.plan_clear" data-ptr="'+esc(p)+'" data-pf="clr:'+esc(p)+'">clear</button></div><div class="pe-d">JSON value</div>'+peHitsAt(p)+'<div class="pe-err" data-err="'+esc(p)+'"></div></div>';}
// a group's noun without its article for counts and item heads ("1 local box", "local box 0"; critique A2, minor 5)
function peNoun(g){return peGroupTitle(g).replace(/^(a|an|the) /,'');}
function pePlural(n){return /(s|x|sh|ch)$/.test(n)?n+'es':n+'s';}
function peItems(e,val,p){const items=Array.isArray(val)?val:[];const g=e.item;
  let h='<div class="pe-sub label">'+esc(e.key)+' '+hintBtn(e.hint)+' <span class="muted">'+items.length+' '+esc(items.length===1?peNoun(g):pePlural(peNoun(g)))+'</span>'+(e.required&&!items.length?' <span class="chip bad" data-hint="chip.required">required</span>':'')+'</div>';
  h+=items.map((it,i)=>'<div class="pe-item"><div class="pe-ihead"><span class="label">'+esc(peNoun(g))+' '+i+'</span><button class="btn ghost" data-pa="del-item" data-hint="control.plan_remove" data-ptr="'+esc(p+'/'+i)+'" data-pf="del:'+esc(p+'/'+i)+'">remove</button></div>'+peFields(it,p+'/'+i,[g])+'</div>').join('');
  return h+'<button class="btn" data-pa="add-item" data-ptr="'+esc(p)+'" data-pf="add:'+esc(p)+'" data-hint="control.plan_add_item">add '+esc(peGroupTitle(g))+'</button>'+hintBtn('control.plan_add_item');}

// ------------------------------------------------------------------ reading a field back
function peNum(s,t){if(t==='int')return /^-?\d+$/.test(s)?parseInt(s,10):NaN;const x=Number(s);return s!==''&&isFinite(x)?x:NaN;}
function peErr(el,text){const box=document.querySelector('#pe [data-err="'+CSS.escape(el.dataset.ptr)+'"]');el.classList.toggle('bad',!!text);if(box)box.textContent=text||'';}
function peRead(el){const t=el.dataset.type,s=(el.value||'').trim();const e=el.dataset.path?peSchema().entries.find(x=>x.path===el.dataset.path):null;
  if(t==='bool')return {v:el.checked};
  if(el.tagName==='SELECT')return s===''?{del:true}:{v:JSON.parse(s)};
  if(t==='box'||t==='point'){const all=[...document.querySelectorAll('#pe [data-ptr="'+CSS.escape(el.dataset.ptr)+'"].pe-num')];const raw=all.map(x=>x.value.trim());
    if(raw.every(x=>x===''))return {del:true};const nums=raw.map(x=>peNum(x,'float'));if(nums.some(isNaN))return {err:'takes '+all.length+' numbers ('+(e&&e.roles?e.roles.join(' '):'')+')'};return {v:nums};}
  if(s==='')return {del:true};
  if(t==='int'||t==='float'){const x=peNum(s,t);return isNaN(x)?{err:'takes '+(t==='int'?'a whole number':'a number')}:{v:x};}
  if(t==='list'){const parts=s.split(',').map(x=>x.trim()).filter(x=>x!=='');const it=e?e.item:'str';const vals=parts.map(x=>it==='str'?x:peNum(x,it==='int'?'int':'float'));return vals.some(x=>typeof x==='number'&&isNaN(x))?{err:'takes '+(it==='int'?'whole numbers':'numbers')+' separated by commas'}:{v:vals};}
  if(t==='object'||t==='json'){try{const x=JSON.parse(s);if(t==='object'&&!isObj(x))return {err:'takes a JSON object'};return {v:x};}catch(err){return {err:'JSON: '+err.message};}}
  return {v:s};}
function peField(el){const r=peRead(el);if(r.err){peErr(el,r.err);return;}peErr(el,'');const next=peClone(PE.plan);const p=el.dataset.ptr;
  if(r.del){if(getAt(next,p)===undefined)return;delAt(next,p);}else setAt(next,p,r.v);
  peCommit(next);}  // the rebuild runs after the browser moves the focus (Tab), so it restores the focus there

// ------------------------------------------------------------------ the actions
async function peLoad(){const v=S.view;const ref=$('#peFrom').value;let p;
  if(!ref)p={seq:v.job.seq,timeline:[]};
  else{const [kind,name]=ref.split(':');try{p=await api(kind==='job'?'/api/jobs/'+encodeURIComponent(v.job.id)+'/plans/'+encodeURIComponent(name):'/api/plans/frozen/'+encodeURIComponent(name));}catch(e){setMsg(e.message,'bad');return;}if(!PE.name)PE.name=name+'_v2';}
  delete p.provenance;PE.from=ref;PE.plan=p;PE.base=JSON.stringify(p);PE.hist=[PE.base];PE.cur=0;PE.sel={k:'plan'};PE.json=null;PE.jsonErr='';
  setMsg(ref?'loaded '+ref+' without its provenance block; the change count starts here':'an empty plan: add a hold','ok');peRender();}
function peStillAfter(i){const tl=peTimeline(PE.plan);return i>=0&&tl[i]?tl[i].to:(tl.length?tl[0].to:0);}
function peInsert(st){const next=peClone(PE.plan);next.timeline=next.timeline||[];const i=PE.sel.k==='step'?PE.sel.i+1:next.timeline.length;next.timeline.splice(i,0,st);PE.sel={k:'step',i};PE.focusNext='bar:'+i;peCommit(next);}
function peAddHold(){const i=PE.sel.k==='step'?PE.sel.i:(PE.plan.timeline||[]).length-1;peInsert({key:peStillAfter(i)});}
function peAddTr(){const tl=PE.plan.timeline||[];const i=PE.sel.k==='step'?PE.sel.i:tl.length-1;const nxt=tl[i+1];const to=nxt?('to' in nxt?nxt.to:nxt.key):(tl.length?peStillAfter(0):0);peInsert({to:to});}
function peMove(d){const s=PE.sel;if(s.k!=='step')return;const j=s.i+d;const next=peClone(PE.plan);if(j<0||j>=next.timeline.length)return;const [st]=next.timeline.splice(s.i,1);next.timeline.splice(j,0,st);PE.sel={k:'step',i:j};PE.focusNext='btn:'+(d<0?'left':'right');peCommit(next);}
function peRemove(){const s=PE.sel;const next=peClone(PE.plan);if(s.k==='step')next.timeline.splice(s.i,1);else if(s.k==='fx')next.effects.splice(s.i,1);else return;if(s.k==='fx'&&!next.effects.length)delete next.effects;PE.sel={k:'plan'};peCommit(next);}
function peAddFx(){const k=$('#peFxKind').value;const next=peClone(PE.plan);next.effects=next.effects||[];next.effects.push({kind:k});PE.sel={k:'fx',i:next.effects.length-1};PE.focusNext='fx:'+PE.sel.i;peCommit(next);}
function peFaster(){const raw=String(PE.faster).trim();if(raw===''){setMsg('type a percentage first: 20 makes the loop 20 % faster, −50 makes it 50 % slower','bad');return;}
  const p=Number(raw.replace('−','-'));if(!isFinite(p)||p>=100){setMsg('the percentage is a number below 100: 20 makes the loop 20 % faster, −50 makes it 50 % slower','bad');return;}
  const f=(100-p)/100,next=peClone(PE.plan),kept=[],sched=[];let changed=0;
  (next.timeline||[]).forEach((st,i)=>{if(!('to' in st)){const h=st.hold!==undefined?st.hold:1;const nh=Math.max(1,Math.round(h*f));if(nh!==h){st.hold=nh;changed++;}return;}
    const m=st.method||'rife';if(m==='cut'||m==='rewind'||m==='slices'){if(m!=='cut')kept.push(i);return;}
    if(typeof st.n==='number'&&st.n>0){const nn=Math.max(1,Math.round(st.n*f));if(nn!==st.n){st.n=nn;changed++;}}
    if(m==='sheets'&&(st.sheets||[]).some(s=>'lag' in s||'dur' in s))sched.push(i);});
  if(!changed){setMsg('no frame count changed at '+p+' %','bad');return;}
  peCommit(next);setMsg(changed+' frame counts × '+f.toFixed(2)+' (one undo step)'+(kept.length?'; steps '+kept.join(', ')+' keep their counts (a rewind or a slices schedule)':'')+(sched.length?'; the sheets of steps '+sched.join(', ')+' keep their lag and dur':''),'ok');}
function peFlushJson(){if(PE.json===null)return true;try{const p=JSON.parse(PE.json);if(!isObj(p))throw new Error('the plan is a JSON object');PE.jsonErr='';const keep=PE.tab;if(JSON.stringify(p)!==PE.hist[PE.cur])peCommit(p);PE.json=null;PE.tab=keep;return true;}catch(e){PE.jsonErr=e.message;return false;}}
async function peSave(){const v=S.view;if(!peFlushJson()){peRender();setMsg('the JSON text does not parse ('+PE.jsonErr+'): fix it or discard it before saving','bad');return;}
  try{const r=await api('/api/jobs/'+encodeURIComponent(v.job.id)+'/plans',{name:PE.name.trim(),plan:PE.plan,from:PE.from||undefined,words:PE.words});
    setMsg('saved '+r.path+': '+r.changes.length+' change'+(r.changes.length===1?'':'s')+' from '+(PE.from||'nothing')+(r.changes.length?' ('+r.changes.slice(0,6).map(c=>c.path).join(', ')+(r.changes.length>6?', …':'')+')':''),'ok');
    const rs=stageOf('render');if(rs)knobState(v,rs).plan=r.ref;await openJob(v.job.id,true);}catch(e){setMsg(e.message,'bad');}}

// ------------------------------------------------------------------ the page's variants (backlog T76; panels.js's panelPage calls these)
function variantsState(full){const jid=S.view.job.id;const names=full.map(c=>c.name);const st=PE.variants[jid]||(PE.variants[jid]={order:names.slice(),off:{}});
  st.order=st.order.filter(n=>names.includes(n)).concat(names.filter(n=>!st.order.includes(n)));return st;}
function pageListed(full){const st=variantsState(full);const by={};full.forEach(c=>by[c.name]=c);return st.order.filter(n=>!st.off[n]).map(n=>by[n]);}
// What POST /page sends: [] when every full render is listed in name order (no flag), else the listed names in order.
function pageVariants(){const full=S.view.candidates.filter(c=>c.kind==='full');const listed=pageListed(full).map(c=>c.name);const all=full.map(c=>c.name);return listed.length===all.length&&listed.every((n,i)=>n===all[i])?[]:listed;}
function variantsControl(full){const st=variantsState(full);const by={};full.forEach(c=>by[c.name]=c);const vs=pageVariants();
  const rows=st.order.map((n,i)=>{const c=by[n];const vchip=c.unjudged?chip('unjudged','info'):chip(c.verdict.verdict,c.verdict.verdict==='NOT READY'?'bad':'ok');
    return '<tr'+(st.off[n]?' class="off"':'')+'><td><input type="checkbox" data-hint="control.page_variants" data-pv="'+esc(n)+'" data-name="pv:'+esc(n)+'"'+(st.off[n]?'':' checked')+' aria-label="include '+esc(n)+'"></td><td class="data">'+esc(n)+'</td><td>'+vchip+'</td><td class="data muted">'+esc((c.md5_mp4||'').slice(0,8))+'</td><td><button class="btn ghost" data-pa="var" data-hint="control.page_variants" data-d="-1" data-n="'+esc(n)+'"'+(i===0?' disabled':'')+' aria-label="move '+esc(n)+' up">up</button><button class="btn ghost" data-pa="var" data-hint="control.page_variants" data-d="1" data-n="'+esc(n)+'"'+(i===st.order.length-1?' disabled':'')+' aria-label="move '+esc(n)+' down">down</button></td></tr>';}).join('');
  const listed=pageListed(full);
  return '<table class="pe-var"><tr><th>include '+hintBtn('control.page_variants')+'</th><th>candidate</th><th>verdict</th><th>md5</th><th>order</th></tr>'+rows+'</table><p class="muted">'+(vs.length?'The page lists '+listed.length+' of '+full.length+' full renders in this order: '+esc(vs.join(', '))+' (passes --variants '+esc(vs.join(','))+').':'Every full render in name order ('+full.length+'), no flag.')+'</p>';}

// ------------------------------------------------------------------ the events: delegated from #panel, which outlives every rebuild
(function(){const panel=$('#panel');
  panel.addEventListener('click',e=>{const b=e.target.closest('[data-pa]');if(!b||b.disabled)return;const a=b.dataset.pa;
    if(a==='var'){const full=S.view.candidates.filter(c=>c.kind==='full');const st=variantsState(full);const i=st.order.indexOf(b.dataset.n),j=i+(+b.dataset.d);if(j<0||j>=st.order.length)return;[st.order[i],st.order[j]]=[st.order[j],st.order[i]];renderPanel();const nb=document.querySelector('[data-pa="var"][data-n="'+CSS.escape(b.dataset.n)+'"][data-d="'+b.dataset.d+'"]');if(nb&&!nb.disabled)focusQuiet(nb);return;}
    if(!b.closest('#pe'))return;
    if(a==='load')peLoad();else if(a==='undo')peUndo();else if(a==='redo')peRedo();else if(a==='save')peSave();else if(a==='faster')peFaster();
    else if(a==='tab'){if(PE.tab==='json'&&b.dataset.tab==='bars'&&!peFlushJson()){peRender();setMsg('the JSON text does not parse ('+PE.jsonErr+'): fix it, or discard the text to return to the last valid plan','bad');return;}PE.tab=b.dataset.tab;if(PE.tab==='json'&&!PE.jsonErr)PE.json=null;peRender();}
    else if(a==='json-discard'){PE.json=null;PE.jsonErr='';peRender();}
    else if(a==='sel'){PE.sel=b.dataset.k==='plan'?{k:'plan'}:{k:b.dataset.k,i:+b.dataset.i};PE.focusNext=b.dataset.pf;peRender();}
    else if(a==='add-hold')peAddHold();else if(a==='add-tr')peAddTr();else if(a==='move')peMove(+b.dataset.d);else if(a==='remove')peRemove();else if(a==='add-fx')peAddFx();
    else if(a==='clear'){const next=peClone(PE.plan);delAt(next,b.dataset.ptr);peCommit(next);}
    else if(a==='add-item'){const next=peClone(PE.plan);const p=b.dataset.ptr;const cur=getAt(next,p);if(Array.isArray(cur))cur.push({});else setAt(next,p,[{}]);peCommit(next);}
    else if(a==='del-item'){const next=peClone(PE.plan);delAt(next,b.dataset.ptr);peCommit(next);}});
  panel.addEventListener('change',e=>{const t=e.target;
    if(t.dataset.pv!==undefined){const full=S.view.candidates.filter(c=>c.kind==='full');variantsState(full).off[t.dataset.pv]=!t.checked;renderPanel();const nb=document.querySelector('[data-pv="'+CSS.escape(t.dataset.pv)+'"]');if(nb)focusQuiet(nb);return;}
    if(!t.closest('#pe'))return;
    if(t.id==='peJson'){PE.json=t.value;if(peFlushJson())peRender();else{const er=$('#peJsonErr');if(er){er.className='pe-jerr bad';er.textContent='JSON: '+PE.jsonErr+'. The bars keep the last valid plan until the text parses.';}}return;}
    if(t.classList.contains('pe-in'))peField(t);});
  panel.addEventListener('input',e=>{const t=e.target;if(!t.closest('#pe'))return;
    if(t.id==='peName')PE.name=t.value;else if(t.id==='peWords')PE.words=t.value;else if(t.id==='peFaster')PE.faster=t.value;
    else if(t.id==='peJson'){PE.json=t.value;try{JSON.parse(t.value);PE.jsonErr='';}catch(err){PE.jsonErr=err.message;}const er=$('#peJsonErr');if(er){er.className='pe-jerr'+(PE.jsonErr?' bad':'');er.textContent=PE.jsonErr?'JSON: '+PE.jsonErr+'. The bars keep the last valid plan until the text parses.':'The text enters the history when the field loses the focus.';}}});
  panel.addEventListener('keydown',e=>{const b=e.target.closest('.pe-bar,.pe-fx');
    if(e.target.id==='peFaster'&&e.key==='Enter'){peFaster();e.preventDefault();return;}
    // the bars keep the arrows, Home and End (boot.js would step the scrubber); Cmd-Z and the rest reach the document's
    // undo (critique A2, P2 3)
    if(!b)return;if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','End'].includes(e.key))e.stopPropagation();
    const row=[...b.parentElement.querySelectorAll('.pe-bar,.pe-fx')];const i=row.indexOf(b);let j=null;
    if(e.key==='ArrowRight'||(e.key==='ArrowDown'&&b.classList.contains('pe-fx')))j=Math.min(row.length-1,i+1);
    else if(e.key==='ArrowLeft'||(e.key==='ArrowUp'&&b.classList.contains('pe-fx')))j=Math.max(0,i-1);
    else if(e.key==='Home')j=0;else if(e.key==='End')j=row.length-1;
    else if(e.key==='ArrowDown'&&b.classList.contains('pe-bar')){const f=document.querySelector('#pe .pe-fx');if(f){f.focus();e.preventDefault();}return;}
    else if(e.key==='ArrowUp'&&b.classList.contains('pe-bar'))return;
    if(j!==null){row.forEach(x=>x.tabIndex=-1);row[j].tabIndex=0;row[j].focus();e.preventDefault();}});
  document.addEventListener('keydown',e=>{if(S.stage!=='plan'||!PE.plan||!(e.metaKey||e.ctrlKey)||e.key.toLowerCase()!=='z')return;const t=e.target;
    if(t&&t.matches&&(t.matches('textarea')||(t.matches('input')&&t.value!==(t.dataset.v||''))))return;  // a text field undoes its own typing
    e.preventDefault();if(e.shiftKey)peRedo();else peUndo();});})();
flowEntry('loop').panels.plan=panelPlan;
