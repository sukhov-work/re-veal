// graph.js: the graph view of the job (STUDIO.md §3, the Graph row): the stages as nodes laid out in layers left to
// right by the flow's order, an optional stage (readers, probe, measure) in a row under its parent; each node a flat
// tile with its thumbnail, name, state chip, input ports (the files its latest record read) and output ports (the
// files it wrote); a line from a producer's output port to a consumer's input port wherever a file one record wrote was
// read by another (job_view's graph). Selecting a node selects the stage, so the panel beneath and the inspector show
// it as the strip does. A node carries "rerun from here", which asks for a yes in the node before it runs (critique
// A2, P2 5), and "show"; "add" lists the optional stages the registry allows after the selected node. No dragging, no
// hand-drawn lines.
'use strict';
S.graphAdded={};S.gConfirm=null;
const G_MIN=176,G_MAX=240,G_COL=56,G_ROW=36,G_PAD=16,G_PORTS=6;
// the flow's graph data: the stages whose node can show its first picture, and what a rerun from the graph costs, in
// the confirmation's words
function gHosts(){return (flowUI().graph||{}).hosts||[];}
function gCost(name){return ((flowUI().graph||{}).cost||{})[name];}
// The node width that shows whole columns at rest: every column when they fit, else as many as fit, widened so the
// next column starts past the scroller's edge and no node is cut there (the detector's edge-flush-cards at 1280).
function graphWidth(avail,cols){if(!avail)return G_MIN;const fit=k=>(avail-2*G_PAD-(k-1)*G_COL)/k;let n=cols;while(n>1&&fit(n)<G_MIN)n--;return Math.floor(n<cols?fit(n):Math.min(G_MAX,fit(n)));}
function gConfirmHTML(s){return '<div class="gconfirm"><span>Rerun '+esc(s.title)+' with the inspector\'s knobs? '+esc(gCost(s.name)||'The stages after it go stale')+'.</span><span class="gyn"><button class="btn primary" data-act="yes" data-hint="control.rerun">yes, rerun</button><button class="btn ghost" data-act="no" data-hint="control.rerun">no</button></span></div>';}
function graphStages(){const v=S.view;const added=S.graphAdded[v.job.id]||[];return v.stages.filter(s=>!s.optional||s.latest||s.state!=='none'||added.includes(s.name));}
// the layout rule: the required stages in one row in the flow's order; an optional stage in its parent's column, in the
// first free row under it
function graphLayout(stages){const pos={},col={},used={};stages.filter(s=>!s.optional).forEach((s,i)=>{col[s.name]=i;pos[s.name]={col:i,row:0};});
 stages.filter(s=>s.optional).forEach(s=>{const c=col[s.parent]!=null?col[s.parent]:0;let r=1;while(used[c+':'+r])r++;used[c+':'+r]=true;pos[s.name]={col:c,row:r};});return pos;}
function graphPorts(name){const g=(S.view.graph&&S.view.graph.ports)||{};return g[name]||{in:[],out:[]};}
function graphEdges(){return (S.view.graph&&S.view.graph.edges)||[];}
// the ports a node lists: the ones a line uses first, then the rest, at most G_PORTS and a "+N more" row
function portList(ports,linked){const a=ports.filter(p=>linked.has(p.name)),b=ports.filter(p=>!linked.has(p.name));const all=a.concat(b);return {shown:all.slice(0,G_PORTS),more:all.slice(G_PORTS)};}
function firstImage(name){return graphPorts(name).out.find(p=>p.url)||null;}
function addable(sel){const v=S.view;const shown=graphStages().map(s=>s.name);return v.stages.filter(s=>s.optional&&s.parent===sel&&!shown.includes(s.name));}
function renderGraph(){const v=S.view;const host=$('#graph');if(!v||!host||S.viewMode!=='graph')return;const stages=graphStages();const pos=graphLayout(stages);const cols=Math.max(1,...Object.values(pos).map(p=>p.col+1));const gw=graphWidth(host.clientWidth,cols);
 const sig=JSON.stringify([stages.map(s=>[s.name,s.state,s.stale,s.thumb,s.latest,s.progress]),v.graph,S.stage,S.gConfirm,gw]);if(sig===S.graphSig)return;S.graphSig=sig;
 const fk=focusKey(host);const keepX=host.scrollLeft,keepY=host.scrollTop;
 const edges=graphEdges();const inL={},outL={};edges.forEach(e=>{(outL[e.from]=outL[e.from]||new Set()).add(e.file);(inL[e.to]=inL[e.to]||new Set()).add(e.file);});
 const add=addable(S.stage);const sel=stageOf(S.stage);
 $('#gbar').innerHTML='<span class="label muted">'+stages.length+' nodes · '+edges.length+' lines '+hintBtn('region.graph')+'</span><label class="label muted">add after '+esc(sel?sel.title:'—')+' <select id="gAdd" data-hint="control.graph_add"'+(add.length?'':' disabled')+'><option value="">'+(add.length?'— choose an optional stage —':'no optional stage follows this one')+'</option>'+add.map(s=>'<option value="'+esc(s.name)+'">'+esc(s.title)+'</option>').join('')+'</select></label>';
 let h='';stages.forEach(s=>{const p=pos[s.name];const ports=graphPorts(s.name);const ins=portList(ports.in,inL[s.name]||new Set()),outs=portList(ports.out,outL[s.name]||new Set());const st=s.stale?'stale':s.state;const added=s.optional&&!s.latest&&s.state==='none';
  const portRow=(q,side,linked)=>'<div class="gport '+side+(linked.has(q.name)?' linked':'')+'" data-port="'+esc(q.name)+'" title="'+esc(q.path)+'"><i></i>'+esc(q.name)+'</div>';
  const more=(m,side)=>m.length?'<div class="gport '+side+' more" data-port="+more" title="'+esc(m.map(q=>q.name).join(', '))+'"><i></i>+'+m.length+' more</div>':'';
  const img=firstImage(s.name);const canRun=s.kind==='script'&&s.name!=='page';const canShow=!!img&&gHosts().includes(s.name);
  h+='<div class="gnode'+((s.state==='failed'||s.state==='refused'||s.state==='lost')?' failed':'')+(s.state==='running'?' running':'')+(added?' added':'')+'" data-stage="'+esc(s.name)+'" data-row="'+p.row+'" data-col="'+p.col+'" data-hint="stage.'+esc(s.name)+'" tabindex="0" role="group" aria-label="'+esc(s.title+', '+st)+'" aria-current="'+(s.name===S.stage)+'" style="left:'+(G_PAD+p.col*(gw+G_COL))+'px;width:'+gw+'px">'
   +'<div class="ghead"><span class="label">'+esc(s.title)+'</span>'+hintBtn('stage.'+s.name)+(s.generated?'<span class="tick" title="generated content"></span>':'')+chip(added?'not run':st+(s.progress?' '+s.progress.i+'/'+s.progress.n:''),added?'':stateClass(st),added||s.stale?null:s.chip_key)+'</div>'
   +'<div class="gthumb'+(s.thumb?'':' empty')+'">'+(s.thumb?'<img src="'+esc(s.thumb)+'" alt="">':esc(s.title))+'</div>'
   +'<div class="gports"><div class="gin">'+ins.shown.map(q=>portRow(q,'in',inL[s.name]||new Set())).join('')+more(ins.more,'in')+'</div><div class="gout">'+outs.shown.map(q=>portRow(q,'out',outL[s.name]||new Set())).join('')+more(outs.more,'out')+'</div></div>'
   +'<div class="gacts">'+(canRun?(S.gConfirm===s.name?gConfirmHTML(s):'<button class="btn ghost" data-act="rerun" data-hint="control.rerun">rerun from here</button>'):'')+'<button class="btn ghost" data-act="show" data-hint="control.show"'+(canShow?'':' disabled')+'>show</button></div></div>';});
 host.innerHTML='<div class="gcanvas" id="gcanvas">'+h+'<svg class="gedges" id="gedges" aria-hidden="true"></svg></div>';
 placeNodes(pos,gw);drawEdges(edges);host.scrollLeft=keepX;host.scrollTop=keepY;wireGraph();
 // the focus: "no" when a confirmation opens, "rerun from here" when it is answered no, else the element it was on
 const into=(name,act)=>{const b=host.querySelector('.gnode[data-stage="'+CSS.escape(name||'')+'"] [data-act="'+act+'"]');if(b)focusQuiet(b);return !!b;};
 if(S.gFocus){const f=S.gFocus;S.gFocus=null;if(into(f.name,f.act))return;}
 restoreFocus(host,fk);}
// rows take the height of their tallest node; the lines are drawn from the ports' measured places
function placeNodes(pos,gw){const nodes=[...document.querySelectorAll('#gcanvas .gnode')];const rowH={};nodes.forEach(n=>{const r=+n.dataset.row;rowH[r]=Math.max(rowH[r]||0,n.offsetHeight);});
 const rowY={};let y=G_PAD;Object.keys(rowH).map(Number).sort((a,b)=>a-b).forEach(r=>{rowY[r]=y;y+=rowH[r]+G_ROW;});
 nodes.forEach(n=>{n.style.top=rowY[+n.dataset.row]+'px';});const cols=Math.max(1,...Object.values(pos).map(p=>p.col+1));
 const cv=$('#gcanvas');cv.style.width=(G_PAD*2+cols*gw+(cols-1)*G_COL)+'px';cv.style.height=(y-G_ROW+G_PAD)+'px';}
function portPoint(stage,side,file){const cv=$('#gcanvas');const n=cv.querySelector('.gnode[data-stage="'+stage+'"]');if(!n)return null;const base=cv.getBoundingClientRect();const nb=n.getBoundingClientRect();
 const q=n.querySelector('.gport.'+side+'[data-port="'+CSS.escape(file)+'"]')||n.querySelector('.gport.'+side+'.more')||n.querySelector('.ghead');const qb=q.getBoundingClientRect();
 return {x:(side==='out'?nb.right:nb.left)-base.left,y:qb.top+qb.height/2-base.top};}
function drawEdges(edges){const svg=$('#gedges'),cv=$('#gcanvas');
 const box=st=>{const n=cv.querySelector('.gnode[data-stage="'+st+'"]');return n?{top:n.offsetTop,bottom:n.offsetTop+n.offsetHeight,row:+n.dataset.row,col:+n.dataset.col}:null;};
 const rowBottom=r=>Math.max(0,...[...cv.querySelectorAll('.gnode[data-row="'+r+'"]')].map(n=>n.offsetTop+n.offsetHeight));let skip=0,low=0;
 svg.innerHTML=edges.map(e=>{const a=portPoint(e.from,'out',e.file),b=portPoint(e.to,'in',e.file);if(!a||!b)return '';const sel=e.from===S.stage||e.to===S.stage;let d;const pa=box(e.from),pb=box(e.to);
  if(b.x>a.x+40&&pa&&pb&&pa.row===pb.row&&pb.col-pa.col>1){
   // a line that skips a column runs through the gap under the row, so it never passes behind a node (critique A2, P2 9)
   const y=rowBottom(pa.row)+10+6*(skip++);low=Math.max(low,y);d='M'+a.x.toFixed(1)+' '+a.y.toFixed(1)+' H'+(a.x+22).toFixed(1)+' V'+y.toFixed(1)+' H'+(b.x-22).toFixed(1)+' V'+b.y.toFixed(1)+' H'+b.x.toFixed(1);}
  else if(b.x>a.x+40){const dx=Math.max(48,(b.x-a.x)/2);d='M'+a.x.toFixed(1)+' '+a.y.toFixed(1)+' C'+(a.x+dx).toFixed(1)+' '+a.y.toFixed(1)+' '+(b.x-dx).toFixed(1)+' '+b.y.toFixed(1)+' '+b.x.toFixed(1)+' '+b.y.toFixed(1);}
  else{// a node in a row under its parent: out to the right, through the gap between the rows, in from the left
   const pa=box(e.from),pb=box(e.to);const ym=pa&&pb?(pb.top>pa.bottom?(pa.bottom+pb.top)/2:(pb.bottom+pa.top)/2):(a.y+b.y)/2;d='M'+a.x.toFixed(1)+' '+a.y.toFixed(1)+' H'+(a.x+14).toFixed(1)+' V'+ym.toFixed(1)+' H'+(b.x-14).toFixed(1)+' V'+b.y.toFixed(1)+' H'+b.x.toFixed(1);}
  const sock=pt=>'<rect x="'+(pt.x-4).toFixed(1)+'" y="'+(pt.y-3).toFixed(1)+'" width="8" height="6" rx="1" class="'+(sel?'sel':'')+'"/>';
  return '<path class="'+(sel?'sel':'')+'" d="'+d+'"><title>'+esc(e.file+': '+e.from+' → '+e.to)+'</title></path>'+sock(a)+sock(b);}).join('');
 if(low+G_PAD>cv.offsetHeight)cv.style.height=(low+G_PAD)+'px';svg.setAttribute('width',cv.offsetWidth);svg.setAttribute('height',cv.offsetHeight);}
function wireGraph(){const nodes=[...document.querySelectorAll('#gcanvas .gnode')];
 // "rerun from here" asks first: the node shows what the rerun costs, with "no" focused; "yes" runs it
 const answer=(name,yes)=>{S.gConfirm=null;if(yes){graphRerun(name);return;}S.gFocus={name,act:'rerun'};S.graphSig=null;renderGraph();};
 nodes.forEach(n=>{n.onclick=e=>{if(e.target.closest('.hint'))return;const act=e.target.closest('[data-act]');const name=n.dataset.stage;const a=act?act.dataset.act:null;
   if(a==='rerun'){selectStage(name);S.gConfirm=name;S.gFocus={name,act:'no'};S.graphSig=null;renderGraph();return;}
   if(a==='yes'||a==='no'){answer(name,a==='yes');return;}
   if(a==='show'){const img=firstImage(name);selectStage(name);if(img)showInViewer(img.url,name+': '+img.name);return;}if(name!==S.stage)selectStage(name);};
  n.onkeydown=e=>{if(e.key==='Escape'&&S.gConfirm===n.dataset.stage){e.preventDefault();e.stopPropagation();answer(n.dataset.stage,false);return;}if(e.target!==n)return;if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown',' ','Enter'].includes(e.key))e.stopPropagation();const r=+n.dataset.row,c=+n.dataset.col;let t=null;
   if(e.key==='ArrowRight'||e.key==='ArrowLeft'){const same=nodes.filter(x=>+x.dataset.row===r).sort((p,q)=>+p.dataset.col-+q.dataset.col);t=same[same.indexOf(n)+(e.key==='ArrowRight'?1:-1)];}
   if(e.key==='ArrowDown'||e.key==='ArrowUp'){const d=e.key==='ArrowDown'?1:-1;t=nodes.find(x=>+x.dataset.col===c&&+x.dataset.row===r+d)||(d<0?nodes.filter(x=>+x.dataset.row===r-1).sort((p,q)=>Math.abs(+p.dataset.col-c)-Math.abs(+q.dataset.col-c))[0]:null);}
   if(t){e.preventDefault();e.stopPropagation();t.focus();}
   if(e.key==='Enter'||e.key===' '){e.preventDefault();e.stopPropagation();if(n.dataset.stage!==S.stage)selectStage(n.dataset.stage);}};});
 const ad=$('#gAdd');if(ad)ad.onchange=()=>{const name=ad.value;if(!name)return;const id=S.view.job.id;(S.graphAdded[id]=S.graphAdded[id]||[]).push(name);selectStage(name);};}
// the knobs: the flow's own when it names them (the director's resolve and render send the plan panel's, which its
// inspector shows: critique B, P1 (a)), else the inspector's fields over the last run's knobs
async function graphRerun(name){const v=S.view,s=stageOf(name);const own=flowUI().runKnobs;let knobs=own?own(name):null;
 if(!knobs){const K=knobState(v,s);knobs={};s.knobs.forEach(k=>{knobs[k.key]=K[k.key]!==undefined?K[k.key]:knobBase(s,k);});}
 selectStage(name);try{const r=await api('/api/jobs/'+encodeURIComponent(v.job.id)+'/stages/'+encodeURIComponent(name)+'/run',{knobs});setMsg('started '+r.record+' from the graph with the inspector\'s knobs','ok');await openJob(v.job.id,true);loadJobs();}catch(e){setMsg(e.message,'bad');}}
window.addEventListener('resize',()=>{if(S.viewMode==='graph'&&$('#gcanvas'))renderGraph();});
flowEntry('loop').graph={hosts:['registration','readers','probe','render'],cost:{registration:'The prep moves aside and the stages after it go stale',readers:'The readers folder is replaced',probe:'The probe folder is replaced',render:'A new render under the name the inspector holds',measure:'A new measure folder under the render'}};
