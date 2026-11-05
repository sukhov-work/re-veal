// strip.js: the job: openJob (the poll's re-render rules), the stage strip with its stale chips (a branch stage, the
// probe or a measure, as a short tile in a second row under its parent), and the switch between the strip and the graph.
'use strict';
S.viewMode=(()=>{try{return localStorage.getItem('studio_view')==='graph'?'graph':'strip';}catch(e){return 'strip';}})();
// the job
async function openJob(id,keep){if(!keep){S.jid=id;S.stage='render';S.cand=null;S.render=null;S.frame=0;S.msg=null;S.sig=null;S.vw={};S.shown=null;stopPlay();}
 try{localStorage.setItem('studio_job',id)}catch(e){}
 S.view=await api('/api/jobs/'+encodeURIComponent(id));const v=S.view;$('#title').textContent=v.job.seq+' · '+v.job.flow;$('#subtitle').textContent=v.job.id+(v.job.adopted?' · adopted from '+v.job.root:'')+' · '+v.job.inputs.length+' stills';
 document.querySelectorAll('#jobs .job').forEach(li=>li.setAttribute('aria-current',li.dataset.id===id));
 if(!v.stages.find(s=>s.name===S.stage))S.stage='render';renderStrip();renderGraph();
 // a poll re-renders the panel and the inspector only when their data changed and nothing in them has the focus (typed text is never wiped);
 // the render's viewer also follows the measure stage, whose runs it plots
 // (the render's measures reach the inspector through loadRender's syncInspector, after the render is fetched: T97)
 const st=stageOf(S.stage);const also=(S.stage==='render'||S.stage==='measure')?stageOf('measure'):null;const sig=JSON.stringify([st,also,v.candidates.length,v.requests.length,v.rounds.length,v.plans.length,v.page.md5]);
 if(!keep||(sig!==S.sig&&!typing($('#panel'))))renderPanel();
 if(!keep||(sig!==S.sig&&!typing($('#inspector'))))renderInspector();
 S.sig=sig;
 const busy=v.stages.some(s=>s.state==='running');schedulePoll(id,busy?1000:5000);}
function selectStage(name){S.stage=name;S.msg=null;S.focusLater=null;S.gConfirm=null;renderStrip();renderGraph();renderPanel();renderInspector();}
function stripTile(s,row,col){const st=s.stale?'stale':s.state;const cls=['stage',s.branch?'branch':'',(s.state==='failed'||s.state==='refused'||s.state==='lost')?'failed':'',s.state==='running'?'running':''].join(' ');
 const prog=s.progress?' '+s.progress.i+'/'+s.progress.n+' '+esc(s.progress.phase||''):(s.unchanged_from?' (unchanged)':'');
 return '<div class="'+cls+'" role="tab" tabindex="0" style="grid-row:'+row+';grid-column:'+col+'" data-row="'+row+'" data-col="'+col+'" data-stage="'+esc(s.name)+'" data-hint="stage.'+esc(s.name)+'" aria-selected="'+(s.name===S.stage)+'">'+(s.generated?'<span class="tick" title="generated content"></span>':'')+(s.branch?'':'<div class="thumb'+(s.thumb?'':' empty')+'">'+(s.thumb?'<img src="'+esc(s.thumb)+'" alt="">':esc(s.title))+'</div>')+'<div class="nm"><span class="label">'+esc(s.title)+(s.optional?' <span class="muted">(optional)</span>':'')+'</span>'+hintBtn('stage.'+s.name)+'</div><div class="dt" title="'+esc(s.detail)+'">'+esc(s.detail||'')+'</div><div class="ft"><span class="data muted">'+(s.wall_s!=null?esc(fmtS(s.wall_s)):(s.state==='running'&&s.progress?'':'—'))+'</span>'+chip(st+prog,stateClass(st))+'</div></div>';}
function renderStrip(){const v=S.view;const ssig=JSON.stringify(v.stages.map(s=>[s.name,s.state,s.stale,s.detail,s.wall_s,s.progress,s.thumb,s.generated,s.unchanged_from,s.branch,s.parent]))+'|'+S.stage;if(ssig===S.stripSig)return;S.stripSig=ssig;const focusedTile=document.activeElement&&document.activeElement.closest('.stage')?document.activeElement.dataset.stage:null;
 const main=v.stages.filter(s=>!s.branch),col={},rows={};main.forEach((s,i)=>{col[s.name]=i+1;});
 const strip=$('#strip');strip.style.gridTemplateColumns='repeat('+main.length+',minmax(0,1fr))';
 strip.innerHTML=main.map(s=>stripTile(s,1,col[s.name])).join('')+v.stages.filter(s=>s.branch).map(s=>{const c=col[s.parent]||1;rows[c]=(rows[c]||1)+1;return stripTile(s,rows[c],c);}).join('');
 const tiles=[...strip.querySelectorAll('.stage')];
 // a key on a tile, or on the "?" inside it, stays the strip's: the arrows never step the scrubber (critique A2, minor 9)
 tiles.forEach(b=>{b.onclick=e=>{if(e.target.closest('.hint'))return;selectStage(b.dataset.stage);};b.onkeydown=e=>{e.stopPropagation();if(e.target.closest('.hint'))return;let t=null;const r=+b.dataset.row,c=+b.dataset.col;
  if(e.key==='ArrowRight'||e.key==='ArrowLeft'){const same=tiles.filter(x=>+x.dataset.row===r).sort((p,q)=>+p.dataset.col-+q.dataset.col);t=same[same.indexOf(b)+(e.key==='ArrowRight'?1:-1)];}
  if(e.key==='ArrowDown'||e.key==='ArrowUp')t=tiles.find(x=>+x.dataset.col===c&&+x.dataset.row===r+(e.key==='ArrowDown'?1:-1));
  if(t){t.focus();e.preventDefault();}
  if(e.key==='Enter'||e.key===' '){b.click();e.preventDefault();}};});
 if(focusedTile){const b=strip.querySelector('.stage[data-stage="'+focusedTile+'"]');if(b)focusQuiet(b);}}
function stageHint(name){const s=S.view.stages.find(x=>x.name===name);if(s&&S.reg)S.reg.hints['stage.'+name]={what:s.what,stage:name,source:s.backend||'the studio'};}
function stageOf(name){return S.view.stages.find(s=>s.name===name);}
// the strip or the graph: the same stages, the same selection; the panel beneath and the inspector follow either
function setViewMode(m){S.viewMode=m;try{localStorage.setItem('studio_view',m)}catch(e){}applyViewMode();}
function applyViewMode(){const g=S.viewMode==='graph';$('#stripwrap').hidden=g;$('#graphwrap').hidden=!g;$('#viewStrip').setAttribute('aria-pressed',String(!g));$('#viewGraph').setAttribute('aria-pressed',String(g));if(g&&S.view){S.graphSig=null;renderGraph();}}
$('#viewStrip').onclick=()=>setViewMode('strip');$('#viewGraph').onclick=()=>setViewMode('graph');applyViewMode();
