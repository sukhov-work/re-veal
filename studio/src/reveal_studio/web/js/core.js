// core.js: S, api, esc, the format helpers, chips, the hints popover, the focus across a rebuild, setMsg and the poll
// scheduler.
'use strict';
const $=s=>document.querySelector(s);
const esc=s=>String(s==null?'':s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const S={reg:null,jobs:[],jid:null,view:null,stage:null,cand:null,render:null,frame:0,playing:null,knobs:{},msg:null,mode:'fit',timer:null,planText:'',planFrom:'',editorDirty:false};
// FLOW_UI: what the page draws per flow, registered by each flow's scripts at load (the loop's by rail.js, panels.js,
// plan.js, viewer.js, inspector.js and graph.js; pair.js and director.js for theirs). An entry: {panels: {stage: fn
// returning the panel's HTML}, wire: fn after a panel is drawn, sources: fn giving the viewer's pictures, candRow: fn
// drawing a render's row, plots: fn drawing the axis plots, measures: fn giving the inspector's measures for a render,
// newJob: fn opening the flow's new-job form, inputsWord: the inputs' word in the head, hosts: the stages whose panel
// holds the viewer, graph: {hosts: the stages whose node can show a picture, cost: {stage: the rerun's cost}}}.
const FLOW_UI={};
function flowEntry(f){return FLOW_UI[f]||(FLOW_UI[f]={panels:{}});}
function flowUI(){return (S.view&&FLOW_UI[S.view.job.flow])||{panels:{}};}
function fmtS(s){return s==null?'—':(s<60?s.toFixed(1)+' s':Math.floor(s/60)+' min '+Math.round(s%60)+' s');}
function fmtAge(s){return s>=3600?Math.floor(s/3600)+' h '+Math.floor(s%3600/60)+' min':s>=60?Math.floor(s/60)+' min':s+' s';}
function stateClass(st){return ({done:'ok',saved:'ok',graded:'ok',answered:'ok',running:'run',cancelling:'run',waiting:'run',failed:'bad',refused:'bad',lost:'bad',cancelled:'bad',ungraded:'info','ungraded by his word':'info',stale:'info'})[st]||'';}
// The "?" opens its hint on hover or click; it is not a Tab stop, since every control carries its own key and its
// keyboard focus opens the same hint (critique A2, P2 11).
function hintBtn(key){return '<button class="hint" data-hint="'+esc(key)+'" tabindex="-1" aria-label="about '+esc(key)+'">?</button>';}
// A chip's hint key: the key a value chip names (a frame tag, a method, a frame number), else "chip." and the text's
// state word: a parenthesis and a progress fraction dropped, and a leading state word kept alone ("draft 480",
// "stale after registration", "round 1 graded", "waiting 3 min", "generated t 0.5"); Fable review F2.
const CHIP_WORDS=['stale','draft','round','waiting','running','generated'];
function chipKey(text){const t=String(text).replace(/ \(.*$/,'').replace(/ \d+\/\d+.*$/,'').trim();const w=t.split(' ')[0];return 'chip.'+(CHIP_WORDS.includes(w)?w:t);}
function chip(text,cls,key){const k=key||chipKey(text);const has=S.reg&&S.reg.hints[k];return '<span class="chip '+(cls||'')+'"'+(has?' data-hint="'+esc(k)+'"':'')+'>'+esc(text)+'</span>';}
async function api(path,body,method){let r;try{r=await fetch(path,body?{method:method||'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});}catch(e){throw new Error('the studio server at 127.0.0.1:'+location.port+' does not answer: start it again with reveal-studio serve');}
 const t=await r.text();let j;try{j=JSON.parse(t)}catch(e){j={error:t.slice(0,200)}}if(!r.ok){const e=new Error(j.error||('HTTP '+r.status));e.extra=j;throw e;}return j;}
// Whether a text field, a select or a checkbox inside el holds the focus: the poll then leaves el as it is.
function typing(el){const a=document.activeElement;return !!(el&&a&&el.contains(a)&&a.matches('input,textarea,select'));}
// The focus across a rebuild by innerHTML (Fable review F3): the focused element's identity inside root (its id, else
// its tag, first class and data attributes, and its place among the matches), and its restore on the rebuilt element.
const FOCUS_SKIP=['data-v','data-src'];
function focusKey(root){const a=document.activeElement;if(!root||!a||a===document.body||!root.contains(a))return null;
 if(a.id)return {sel:'#'+CSS.escape(a.id),i:0};
 const sel=a.tagName.toLowerCase()+(a.classList.length?'.'+CSS.escape(a.classList[0]):'')+[...a.attributes].filter(x=>x.name.startsWith('data-')&&!FOCUS_SKIP.includes(x.name)).map(x=>'['+x.name+'="'+CSS.escape(x.value)+'"]').join('');
 return {sel,i:Math.max(0,[...root.querySelectorAll(sel)].indexOf(a))};}
function restoreFocus(root,k){if(!k||!root)return false;const all=root.querySelectorAll(k.sel);const el=all[k.i]||all[0];if(!el)return false;focusQuiet(el);return true;}
// A focus the page puts back after a rebuild opens no hint: a hint follows the owner's own moves (Tab, the arrows).
let quietFocus=false;
function focusQuiet(el){if(!el||document.activeElement===el)return;quietFocus=true;try{el.focus({preventScroll:true});}finally{quietFocus=false;}}
function setMsg(text,cls){S.msg={text,cls};const m=$('#msg');if(m){m.className='msg '+(cls||'');m.textContent=text;m.style.display=text?'':'none';}}
// hints: one popover, from the registry's table
const pop=$('#pop');
// a stage knob's row: the JSON a "?" carries, else the knob of the stage the key names (a knob's own field)
function knobOf(btn,key){const d=btn.dataset.knob;if(d&&d.charAt(0)==='{')return JSON.parse(d);const m=/^knob\.([^.]+)\.(.+)$/.exec(key||'');if(!m||!S.view)return null;const s=S.view.stages.find(x=>x.name===m[1]);return (s&&s.knobs.find(k=>k.key===m[2]))||null;}
function showHint(btn){const key=btn.dataset.hint;const h=(S.reg&&S.reg.hints[key])||null;const stageKnob=knobOf(btn,key);let html='';
 if(stageKnob){html='<div class="k">'+esc(stageKnob.key)+(stageKnob.flag?' <span class="muted">('+esc(stageKnob.flag)+')</span>':'')+'</div>'+esc(stageKnob.what)+'<div class="meta">default <code>'+esc(JSON.stringify(stageKnob.default))+'</code> · range '+(stageKnob.range?'<code>'+esc(JSON.stringify(stageKnob.range))+'</code>':'none stated by the script')+' · type '+esc(stageKnob.type)+'</div>';}
 else if(h){html='<div class="k">'+esc(key)+'</div>'+esc(h.what);const meta=[];if(h.default!==undefined)meta.push('default <code>'+esc(JSON.stringify(h.default))+'</code>');if(h.range)meta.push('range <code>'+esc(JSON.stringify(h.range))+'</code>');if(h.stage)meta.push('read by the '+esc(h.stage)+' stage');if(h.source)meta.push('from '+esc(h.source));if(meta.length)html+='<div class="meta">'+meta.join(' · ')+'</div>';}
 else html='<div class="k">'+esc(key)+'</div><span class="muted">no hint recorded for this key (a gap: add it to the hints table in registry/hints.py)</span>';
 pop.innerHTML=html;pop.style.display='block';const r=btn.getBoundingClientRect();let x=r.left,y=r.bottom+6;if(x+430>innerWidth)x=innerWidth-430;if(y+pop.offsetHeight>innerHeight)y=r.top-pop.offsetHeight-6;pop.style.left=x+'px';pop.style.top=y+'px';}
function hideHint(){pop.style.display='none';}
// A "?", a chip or a label opens its hint at once on hover; a control opens it after 600 ms of hover, or at once on
// keyboard focus; a key other than Tab hides it, so a scrubber or a field in use is not covered.
let hoverT=0;
document.addEventListener('mouseover',e=>{const b=e.target.closest('.hint,[data-hint]');clearTimeout(hoverT);if(!b)return;if(b.matches('.hint,.chip')||!b.matches('button,input,select,textarea,a,[tabindex]'))showHint(b);else hoverT=setTimeout(()=>showHint(b),600);});
document.addEventListener('mouseout',e=>{if(e.target.closest('.hint,[data-hint]')){clearTimeout(hoverT);hideHint();}});
document.addEventListener('focusin',e=>{if(quietFocus)return;const b=e.target.closest('.hint,[data-hint]');if(b&&b.matches(':focus-visible'))showHint(b);});
document.addEventListener('focusout',e=>{if(e.target.closest('.hint,[data-hint]'))hideHint();});
document.addEventListener('keydown',e=>{if(e.key!=='Tab'&&e.key!=='Shift')hideHint();},true);
document.addEventListener('click',e=>{const b=e.target.closest('.hint');if(b){e.preventDefault();showHint(b);}});
function schedulePoll(id,ms){clearTimeout(S.timer);S.timer=setTimeout(async()=>{if(S.jid!==id)return;try{await openJob(id,true);await loadJobs();}catch(e){const t=$('#tasks');if(t)t.innerHTML='<li class="kv">'+chip('server unreachable, retrying','bad','chip.server unreachable')+'</li>';schedulePoll(id,5000);}},ms);}
