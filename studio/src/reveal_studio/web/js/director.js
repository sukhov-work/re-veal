// director.js: the director flow's page entries (builder D, phase B), registered in FLOW_UI.director at the end as
// core.js describes the entry: the panels of the import (the photos, the overlays, the element tables), Reveal's
// verdict, the resolve (the canvases with the anchors and the quad as SVG, the layers, the motion), the plan (the
// timeline in clip time, the concept's knob map, the renderer's --set table, the extra lines, the command), the render
// (the controls over the shared viewer), the skeptic (the loop's panel), the page and the grades in the picks shape;
// the new-job form with the pair picker; the viewer's sources, plots, measures and candidate rows of a director render.
// The plan, the concept and the set dict live per job in DIR, so the resolve, plan and render panels share them; a
// panel of this file redraws its own body (#dBody) without the shared panel's form snapshot, so a value set here is
// never replaced by the one typed before it.
'use strict';
const DIR={};
const D_KEY_RE=/^([A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)?)=(.*)$/;
const D_MIN_W=0.02;
function dSt(){const id=S.view.job.id;return DIR[id]||(DIR[id]={ref:null,cid:null,pv:null,loading:null,err:'',set:{},extra:'',sec:3,fps:30,tag:'',full:1920,rlong:1920,ov:{A:{elements:false,disparity:false},B:{elements:false,disparity:false}},op:70,both:true,matte:{A:null,B:null},gr:{},undo:[],redo:[],clearAsk:false});}
// the set dict's undo and redo (Cmd-Z, Shift-Cmd-Z), 300 steps as the loop's editor keeps (critique B, P2 8): a
// snapshot of the set dict and the extra lines before each change made by the timeline, the tables or the buttons
function dSnap(st){st.undo.push(JSON.stringify({set:st.set,extra:st.extra}));if(st.undo.length>300)st.undo.shift();st.redo=[];}
function dStep(st,back){const from=back?st.undo:st.redo,to=back?st.redo:st.undo;if(!from.length)return false;to.push(JSON.stringify({set:st.set,extra:st.extra}));const x=JSON.parse(from.pop());st.set=x.set;st.extra=x.extra;return true;}
function dEnc(s){return encodeURIComponent(s);}
function dHas(o,k){return Object.prototype.hasOwnProperty.call(o,k);}
const dClone=v=>v===undefined?undefined:JSON.parse(JSON.stringify(v));
function dGet(v,p){for(const k of p){if(v==null)return undefined;v=v[k];}return v;}
function dSetPath(v,p,x){if(!p.length)return x;v=dClone(v);if(v==null)v=typeof p[0]==='number'?[]:{};let o=v;for(let i=0;i<p.length-1;i++){if(o[p[i]]==null)o[p[i]]=typeof p[i+1]==='number'?[]:{};o=o[p[i]];}o[p[p.length-1]]=x;return v;}
function dEff(st,key,base){return dHas(st.set,key)?st.set[key]:base;}
function dSetKey(st,key,base,v){if(JSON.stringify(v)===JSON.stringify(base))delete st.set[key];else st.set[key]=v;}
// a value as Python's json.dumps writes it, so the command preview reads as the record's argv will
function pyJson(v){if(Array.isArray(v))return '['+v.map(pyJson).join(', ')+']';if(v&&typeof v==='object')return '{'+Object.keys(v).map(k=>JSON.stringify(k)+': '+pyJson(v[k])).join(', ')+'}';return JSON.stringify(v);}
function dSec(x){const n=+x;return Number.isInteger(n)?n.toFixed(1):String(n);}
function dRound(name){const m=/_r(\d+)$/.exec(name||'');return m?+m[1]:8;}
function dFrozen(){return (S.view.frozen_plans||[]).slice().sort((a,b)=>dRound(a.name)-dRound(b.name));}
function dDefaultRef(){const fp=dFrozen();return fp.length?fp[fp.length-1].ref:null;}
function dConcept(st){return st.pv?(st.pv.concepts.find(c=>c.id===st.cid)||st.pv.concepts[0]||null):null;}
function dAllSet(st){const k=dClone(st.set);(st.extra||'').split('\n').forEach(line=>{const m=D_KEY_RE.exec(line.trim());if(!m)return;try{k[m[1]]=JSON.parse(m[2]);}catch(e){k[m[1]]=m[2];}});return k;}
function dBadLines(st){return (st.extra||'').split('\n').map(x=>x.trim()).filter(x=>x&&!D_KEY_RE.test(x));}
async function dLoadPlan(st,ref){const [kind,name]=ref.split(':');const url=kind==='job'?'/api/jobs/'+dEnc(S.view.job.id)+'/director/plans/'+dEnc(name):'/api/plans/director/'+dEnc(name);const pv=await api(url);st.pv=pv;st.ref=ref;st.err='';if(!pv.concepts.find(c=>c.id===st.cid))st.cid=(pv.concepts[0]||{}).id||null;}
function dEnsurePlan(st){if(st.pv||st.loading)return;const ref=st.ref||dDefaultRef();if(!ref)return;st.loading=dLoadPlan(st,ref).then(()=>{st.loading=null;dRedraw();}).catch(e=>{st.loading=null;st.err=e.message;dRedraw();});}
// the panel's body, redrawn in place (the panel head and its message stay)
function dBody(stage,fn){return ()=>'<div id="dBody" data-stage="'+esc(stage)+'">'+fn()+'</div>';}
function dRedraw(){const b=$('#dBody');if(!b||!S.view||S.view.job.flow!=='director')return;const fn=DIR_BODIES[b.dataset.stage];if(!fn)return;const fk=focusKey(b);b.innerHTML=fn();dWire();restoreFocus(b,fk);dSyncIns();}
// the inspector's read-only knobs follow the panel's state in place, so a keystroke fetches nothing
function dSyncIns(){const n=$('#dNext'),s=S.view&&stageOf(S.stage);if(!n||!s)return;const h=dInspector(s);if(h!=null)n.outerHTML=h;}
function dPlanPick(st){const v=S.view;const opts=dFrozen().map(p=>({ref:p.ref,label:p.ref})).concat((v.plans||[]).map(p=>({ref:p.ref,label:p.ref+' (saved here)'})));
 return '<label class="label muted" for="dPlan">plan</label><select id="dPlan" data-hint="control.director_plan">'+opts.map(o=>'<option value="'+esc(o.ref)+'"'+(o.ref===(st.ref||dDefaultRef())?' selected':'')+'>'+esc(o.label)+'</option>').join('')+'</select>'
  +'<label class="label muted" for="dConcept">concept</label><select id="dConcept" data-hint="control.director_concept">'+(st.pv?st.pv.concepts.map(c=>'<option value="'+esc(c.id)+'"'+(c.id===st.cid?' selected':'')+'>'+esc(c.id)+(c.rank!=null?' · rank '+esc(c.rank):'')+'</option>').join(''):'<option>…</option>')+'</select>';}
// ---------------------------------------------------------------- import: the photos, the overlays, the element tables
function dImport(){const v=S.view,dv=v.director,st=dSt();let h='<p class="muted">'+esc(stageOf('import').what)+'</p>';
 h+='<table><tr><th>photo '+hintBtn('director.photos')+'</th><th>file</th><th>sha256</th><th class="num">bytes</th><th class="num">elements</th><th class="num">mattes</th><th>elements without a matte</th></tr>'+['A','B'].map(s=>{const p=dv.photos[s],t=dv.tables[s]||{},m=dv.mattes[s]||{};return '<tr><td><span class="label d-side '+s.toLowerCase()+'">'+s+'</span></td><td>'+esc(p.name)+'</td><td class="data">'+esc(p.sha256.slice(0,16))+'…</td><td class="num">'+esc(p.bytes)+'</td><td class="num">'+esc(t.elements!=null?t.elements:'—')+'</td><td class="num">'+esc(m.count||0)+'</td><td class="data">'+(m.missing==null?'no layer table':(m.missing.length?esc(m.missing.join(', ')):'none'))+'</td></tr>';}).join('')+'</table>';
 h+='<h3 style="margin-top:16px">Overlays '+hintBtn('control.director_overlay')+'</h3><div class="d-ovctl">'+['A','B'].map(s=>'<span class="label">'+s+'</span>'+['elements','disparity'].map(k=>'<label><input type="checkbox" class="dOv" data-side="'+s+'" data-kind="'+k+'"'+(st.ov[s][k]?' checked':'')+' data-hint="control.director_overlay"> '+k+'</label>').join('')).join('')+'<label><input type="checkbox" id="dBoth"'+(st.both?' checked':'')+' data-hint="control.director_both"> both photos together</label><label class="label muted">opacity <input type="range" id="dOp" min="0" max="100" value="'+esc(st.op)+'" data-hint="control.director_opacity" aria-label="overlay opacity"></label></div>';
 h+='<div class="d-stacks">'+['A','B'].map(s=>dStack(s)).join('')+'</div>';
 h+='<div class="d-tables">'+['A','B'].map(s=>dElements(s)).join('')+dOverlap()+'</div>';
 return h;}
function dOvUrl(side,kind){const dv=S.view.director;return dv.overlay_url+side+'/'+kind+'.png?v='+dEnc(dv.overlay_v[side]||'');}
function dStack(side){const v=S.view,dv=v.director,st=dSt(),p=dv.photos[side];const op=st.op/100;
 const base=p.readable?dOvUrl(side,'base'):(v.resolve?v.resolve.urls['canvas_'+side]:'');
 if(!base)return '<figure class="d-stack"><div class="empty">cv2 reads no '+esc(p.name.split('.').pop())+': resolve the plan to see canvas_'+side+'.png</div></figure>';
 const ov=k=>dv.photos[side].npz&&st.ov[side][k]?'<img class="ov" src="'+esc(dOvUrl(side,k))+'" alt="" style="opacity:'+op+'">':'';
 const m=st.matte[side];const mt=m!=null?'<img class="ov" src="'+esc(dOvUrl(side,'matte_'+m))+'" alt="" style="opacity:'+op+'">':'';
 return '<figure class="d-stack '+side.toLowerCase()+'"><div class="d-pic"><img src="'+esc(base)+'" alt="'+esc(side+': '+p.name)+'">'+ov('elements')+ov('disparity')+mt+'</div><figcaption>'+esc(side)+' · '+esc(p.name)+(m!=null?' · matte of element '+esc(m)+(dElementHasMatte(side,m)?'':' (no el_'+esc(m)+'.png: the hard mask, the fallback)'):'')+(p.npz?'':' · no layers.npz: no element or disparity overlay')+'</figcaption></figure>';}
function dElementHasMatte(side,id){const e=(S.view.director.elements[side]||[]).find(x=>x.id===id);return !!(e&&e.matte);}
// one Tab stop per element table (critique B, P2 9: 131 rows were 131 stops): the row last focused, else the selected
// one, else the first holds tabindex 0; up and down move the focus, Enter and Space toggle the matte
function dElTab(side,rows,sel){const t=(S.dElTab||{})[side];return rows.some(e=>e.id===t)?t:(rows.some(e=>e.id===sel)?sel:(rows[0]||{}).id);}
function dElements(side){const rows=S.view.director.elements[side]||[];const sel=dSt().matte[side];if(!rows.length)return '<div class="muted">no layer table for '+esc(side)+'</div>';const tab=dElTab(side,rows,sel);
 return '<div class="d-eltable"><h3>'+esc(side)+' · '+rows.length+' elements '+hintBtn('director.elements')+'</h3><div class="d-scroll"><table><tr><th class="num">id</th><th>label</th><th>group</th><th class="num">area</th><th class="num">depth rank</th><th class="num">disparity</th><th>matte</th></tr>'+rows.map(e=>'<tr class="d-el'+(e.id===sel?' sel':'')+'" data-side="'+side+'" data-id="'+esc(e.id)+'" tabindex="'+(e.id===tab?0:-1)+'" data-hint="control.director_element" aria-selected="'+(e.id===sel)+'" aria-label="'+esc('show the matte of '+side+' element '+e.id)+'"><td class="num">'+esc(e.id)+'</td><td>'+esc(e.label)+'</td><td>'+esc(e.group)+'</td><td class="num">'+esc(e.area_share)+'</td><td class="num">'+esc(e.depth_rank)+'</td><td class="num">'+esc(e.median_disparity)+'</td><td>'+(e.matte?'file':'<span class="muted">hard</span>')+'</td></tr>').join('')+'</table></div></div>';}
function dOverlap(){const o=S.view.director.overlap||[];return '<div class="d-eltable"><h3>Labels in both photos '+hintBtn('director.overlap')+'</h3><div class="d-scroll"><table><tr><th>label</th><th class="num">A</th><th class="num">B</th></tr>'+(o.length?o.map(x=>'<tr><td>'+esc(x.label)+'</td><td class="num">'+esc(x.A)+'</td><td class="num">'+esc(x.B)+'</td></tr>').join(''):'<tr><td colspan="3" class="muted">none</td></tr>')+'</table></div></div>';}
// ---------------------------------------------------------------- Reveal's verdict (the shared branch)
// the shared stage's run button and wording, as the pair's panel draws them (critique B, minor 6); a refusal shows
// once, in its box (minor 5)
function dVerdict(){const vd=S.view.verdict;let h='<p class="muted">'+esc(stageOf('verdict').what)+' '+hintBtn('director.verdict')+'</p>';
 h+='<div class="pair-acts"><button class="btn" id="dVerdictRun" data-hint="control.pair_verdict_run">'+(vd?'run the verdict again':'run Reveal\'s verdict')+'</button><span class="muted label">reveal.py align, the strict profile · 2 to 18 s</span></div>';
 if(!vd)return h+'<div class="empty">Optional and not run: it tells whether Reveal can align the two photos.</div>';
 h+=vd.state==='refused'?'<div class="msg bad">'+chip('refused','bad')+' '+esc(vd.reason||'')+hintBtn('verdict.refused')+'</div>':'<p>'+chip(vd.state,stateClass(vd.state))+(vd.reason?' <span class="muted">'+esc(vd.reason)+'</span>':'')+'</p>';
 if(vd.metrics)h+='<table>'+Object.entries(vd.metrics).filter(([,x])=>x==null||typeof x!=='object').map(([k,x])=>'<tr><td>'+esc(k)+'</td><td class="num">'+esc(x)+'</td></tr>').join('')+'</table>';
 return h;}
// ---------------------------------------------------------------- resolve: the canvases, the anchors, the layers
function dResolve(){const v=S.view,st=dSt(),rv=v.resolve,s=stageOf('resolve');dEnsurePlan(st);
 let h='<p class="muted">'+esc(s.what)+'</p><div class="d-row">'+dPlanPick(st)+'<label class="label muted" for="dRLong">long side</label><select id="dRLong" data-hint="control.director_resolve">'+[1920,480].map(x=>'<option'+(st.rlong===x?' selected':'')+'>'+x+'</option>').join('')+'</select><button class="btn primary" id="dResolveGo" data-hint="control.director_resolve">resolve</button>'+hintBtn('control.director_resolve')+'</div>';
 if(s.state==='running')h+='<p class="muted">'+chip('running','run')+' the scene builds; no frame loop runs</p>';
 if(!rv)return h+'<div class="empty">No resolve yet. It writes canvas_A.png, canvas_B.png and anchors.json into resolve/&lt;stamp&gt;/.</div>';
 const cam=rv.camera||{};
 h+='<p class="muted"><span class="data">'+esc(rv.record)+'</span> · '+esc(rv.plan||'')+' · concept <span class="data">'+esc(rv.concept)+'</span>'+hintBtn('anchors.concept')+' · canvas <span class="data">'+esc((rv.canvas||[]).join('×'))+'</span> px'+hintBtn('anchors.canvas')+' · camera <span class="data">'+esc(cam.kind)+'</span>'+hintBtn('resolve.camera')+' · <span class="data">'+esc(rv.frames)+'</span> frames'+hintBtn('anchors.frames')+'</p>';
 h+='<p class="muted">anchors.json: <span class="data">'+esc(rv.keys.join(', '))+'</span> '+hintBtn('anchors.info')+' <a href="'+esc(rv.urls.anchors)+'" target="_blank" data-hint="control.show">open</a> · <a href="'+esc(rv.urls.info)+'" target="_blank" data-hint="control.show">info.json</a></p>';
 h+='<div class="d-canvases">'+dCanvas('A',rv)+dCanvas('B',rv)+'</div>';
 h+='<h3 style="margin-top:16px">Layers '+hintBtn('resolve.layers')+'</h3><table><tr><th>name</th><th>kind</th><th>window</th><th>depth</th><th>resolved numbers</th></tr>'+(rv.layers.length?rv.layers.map(l=>'<tr><td>'+esc(l.name)+'</td><td>'+esc(l.by)+'</td><td class="data">'+esc(JSON.stringify(l.window))+'</td><td>'+esc(l.depth||'')+'</td><td class="data">'+esc(Object.entries(l).filter(([k])=>!['name','by','window','depth'].includes(k)).map(([k,x])=>k+' '+JSON.stringify(x)).join(' · ')||'—')+'</td></tr>').join(''):'<tr><td colspan="5" class="muted">none placed</td></tr>')+'</table>';
 const mo=rv.motion||{};
 h+='<h3 style="margin-top:16px">Motion</h3><p class="muted">model '+esc(mo.kind||'legacy')+(mo.edge!=null?' · edge '+esc(mo.edge):'')+(mo.overlap!=null?' · overlap '+esc(mo.overlap):'')+'</p><table><tr><th>adjusted '+hintBtn('resolve.adjusted')+'</th><th>held '+hintBtn('resolve.held')+'</th></tr><tr><td class="data">'+(mo.adjusted.length?esc(mo.adjusted.map(a=>a.name+' '+JSON.stringify(a.from)+' → '+JSON.stringify(a.to)).join('; ')):'none')+'</td><td class="data">'+(mo.held.length?esc(mo.held.map(a=>a.name+' '+a.end_from+' → '+a.end_to).join('; ')):'none')+'</td></tr></table>';
 h+='<p class="muted">front elements <span class="data">'+esc(rv.front_elements)+'</span>'+hintBtn('resolve.front_elements')+' · matte fallbacks <span class="data">'+(rv.matte_fallbacks.length?esc(rv.matte_fallbacks.join(', ')):'none')+'</span>'+hintBtn('resolve.matte_fallbacks')+' · guarded '+(rv.guard.length?esc(rv.guard.map(g=>g.name).join(', ')):'none')+hintBtn('info.guard')+' · unplaced '+(rv.unplaced.length?esc(rv.unplaced.map(u=>u.name+': '+u.why).join('; ')):'none')+hintBtn('info.unplaced')+'</p>';
 return h;}
function dCanvas(side,rv){const W=(rv.canvas||[1,1])[0],H=(rv.canvas||[1,1])[1];let svg='';const an=rv.anchors||{};const a=side==='A'?an.a0:an.b0;
 if(a&&a.centre)svg+='<circle cx="'+esc(a.centre[0])+'" cy="'+esc(a.centre[1])+'" r="'+esc(a.radius||8)+'" class="d-anchor '+side.toLowerCase()+'"><title>'+esc((side==='A'?'a0':'b0')+': centre '+JSON.stringify(a.centre)+', radius '+a.radius)+'</title></circle>';
 if(side==='B'&&rv.quad)svg+='<polygon points="'+esc(rv.quad.map(p=>p.join(',')).join(' '))+'" class="d-quad"><title>the container in B</title></polygon>';
 if(side==='A')rv.layers.forEach(l=>{if(l.centre)svg+='<circle cx="'+esc(l.centre[0])+'" cy="'+esc(l.centre[1])+'" r="'+esc(l.r||6)+'" class="d-layer"><title>'+esc(l.name)+'</title></circle>';});
 return '<figure class="d-canvas '+side.toLowerCase()+'"><div class="d-cv"><img src="'+esc(rv.urls['canvas_'+side])+'" alt="'+esc('canvas_'+side+'.png')+'"><svg viewBox="0 0 '+esc(W)+' '+esc(H)+'" preserveAspectRatio="none" aria-hidden="true">'+svg+'</svg></div><figcaption><span class="label d-side '+side.toLowerCase()+'">'+side+'</span> canvas_'+side+'.png'+hintBtn('resolve.canvas_'+side)+(side==='B'&&rv.quad?' · the quad'+hintBtn('resolve.quad'):'')+(an.a0||an.b0?' · the anchor'+hintBtn('anchors.anchors'):'')+'</figcaption></figure>';}
// ---------------------------------------------------------------- plan: the timeline, the knob map, the --set table
// the editing surface first (critique B, P2 7): the timeline, the concept's knobs, the command they make and the
// buttons over the set dict; then the renderer's --set keys and the extra lines; the planner's Idea and Risk folded
// last, each paragraph held to about 78 characters a line (the detector's line-length)
function dPlan(){const st=dSt();dEnsurePlan(st);let h='<p class="muted">'+esc(stageOf('plan').what)+'</p><div class="d-row">'+dPlanPick(st)+'</div>';
 if(st.err)h+='<div class="msg bad">'+esc(st.err)+'</div>';
 const c=dConcept(st);if(!c)return h+'<div class="empty">'+(st.loading?'Loading the plan…':'No director plan names this pair.')+'</div>';
 const pv=st.pv;
 h+='<p class="muted"><span class="data">'+esc(pv.path)+'</span> · sha256 <span class="data">'+esc(pv.sha256.slice(0,16))+'…</span> · relation '+esc(pv.relation||'—')+' · planner '+esc((pv.planner||{}).model||'—')+hintBtn('director.plan_identity')+'</p>';
 h+=dTimeline(st,c)+dKnobTable(st,c);
 h+='<h3 style="margin-top:16px">The next 480 draft '+hintBtn('control.director_command')+'</h3><div class="cmd" id="dCmd">'+esc(dCommand(st,true))+'</div>';
 const lr=c.last_round;
 h+='<div class="d-acts"><button class="btn" id="dLastRound" data-hint="control.director_last_round"'+(lr?'':' disabled')+'>load the last round\'s knobs</button>'+hintBtn('control.director_last_round')+(lr?'<span class="muted">'+esc(lr.from)+': <span class="data">'+esc(JSON.stringify(lr.knobs))+'</span></span>':'<span class="muted">no round render of this plan and concept</span>')
  +(st.clearAsk?'<span class="d-ask" role="group" aria-label="clear all knobs?"><span>Clear every --set key and the extra lines? Cmd-Z brings them back.</span><button class="btn" id="dClearYes" data-hint="control.director_clear">yes, clear</button><button class="btn ghost" id="dClearNo" data-hint="control.director_clear">no</button></span>':'<button class="btn ghost" id="dClear" data-hint="control.director_clear">clear all knobs</button>')+'</div>';
 h+=dSetTables(st,c);
 const bad=dBadLines(st);
 h+='<h3 style="margin-top:16px">Extra --set lines '+hintBtn('control.director_extra')+'</h3><textarea id="dExtra" data-hint="control.director_extra" rows="3" aria-label="extra --set lines, key=JSON per line" placeholder="pane_becomes_view.matte_grow=0.05">'+esc(st.extra)+'</textarea>'+(bad.length?'<div class="msg bad">not key=JSON: '+esc(bad.join('; '))+'</div>':'');
 h+='<details class="d-why"><summary class="label" data-hint="director.planner_notes">the planner\'s idea and risk for '+esc(c.id)+'</summary><p class="d-prose"><b>Idea.</b> '+esc(c.idea)+hintBtn('director.idea')+'</p><p class="d-prose muted"><b>Risk.</b> '+esc(c.risk)+hintBtn('director.risk')+'</p></details>';
 return h;}
function dBeats(c){const rows=c.beats.map(b=>({name:b.name,key:b.key,base:b.window,by:b.by,end:false,gen:!!((c.transforms.find(t=>t.name===b.name)||{}).keyframes||[]).length}));rows.push({name:'end effect · '+c.end.kind,key:'end_window',base:c.end.window,end:true,gen:false});return rows;}
function dIsSolo(st,c,n){const o=c.beats.filter(b=>b.name!==n);return o.length>0&&o.every(b=>st.set[b.name+'.skip']===true)&&!st.set[n+'.skip'];}
function dTimeline(st,c){const rows=dBeats(c);let h='<h3 style="margin-top:16px">Timeline in clip time '+hintBtn('control.director_timeline')+'</h3>';
 if(c.motion&&c.motion.kind==='continuous')h+='<p class="muted">The motion model is on: the renderer may move a beat earlier to overlap the one before; the resolve lists where.'+hintBtn('director.motion_note')+'</p>';
 h+='<div class="d-tl" id="dTl" role="group" aria-label="the beats in clip time" style="height:'+(rows.length*30+22)+'px">';
 for(let t=0;t<=10;t++)h+='<span class="d-grid" style="left:'+(t*10)+'%"></span><span class="d-tick'+(t===0?' first':(t===10?' last':''))+'" style="left:'+(t*10)+'%">'+(t/10).toFixed(1)+'</span>';
 rows.forEach((r,i)=>{const w=dEff(st,r.key,r.base);const skip=!r.end&&st.set[r.name+'.skip']===true;const ch=dHas(st.set,r.key);
  h+='<button class="d-bar'+(r.end?' end':'')+(skip?' mute':'')+(ch?' changed':'')+(r.gen?' gen':'')+((w[1]-w[0])<0.16?' narrow':'')+'" data-i="'+i+'" data-hint="control.director_timeline" aria-label="'+esc(r.name+': window '+(+w[0]).toFixed(2)+' to '+(+w[1]).toFixed(2)+'; the arrows move it, shift with the arrows its end, alt its start, page up and down by 0.1')+'" style="top:'+(i*30+2)+'px;left:'+(w[0]*100)+'%;width:'+Math.max(0.5,(w[1]-w[0])*100)+'%"><span class="d-bt"><span class="d-bl">'+esc(r.name)+'</span> <span class="data">'+(+w[0]).toFixed(2)+'–'+(+w[1]).toFixed(2)+'</span></span></button>';});
 h+='</div><div class="d-ms">'+c.beats.map(b=>'<span><span class="data">'+esc(b.name)+'</span><label><input type="checkbox" class="dMute" data-name="'+esc(b.name)+'"'+(st.set[b.name+'.skip']===true?' checked':'')+' data-hint="control.director_mute"> mute</label><label><input type="checkbox" class="dSolo" data-name="'+esc(b.name)+'"'+(dIsSolo(st,c,b.name)?' checked':'')+' data-hint="control.director_solo"> solo</label></span>').join('')+'</div>';
 return h;}
function dKnobInput(id,range,val){const isNum=Array.isArray(range)&&range.length===2&&typeof range[0]==='number'&&typeof range[1]==='number';
 if(isNum)return '<input class="dKnob" id="'+id+'" data-hint="control.director_knob" inputmode="decimal" value="'+esc(val)+'" aria-label="knob value">';
 if(Array.isArray(range)&&range.length&&range.every(x=>typeof x==='boolean'))return '<input type="checkbox" class="dKnob" id="'+id+'" data-hint="control.director_knob"'+(val?' checked':'')+' aria-label="knob value">';
 return '<input class="dKnob" id="'+id+'" data-hint="control.director_knob" value="'+esc(JSON.stringify(val))+'" aria-label="knob value as JSON">';}
function dKnobTable(st,c){if(!c.knobs.length)return '<p class="muted">The planner named no knob for this concept.</p>';
 let h='<h3 style="margin-top:16px">The concept\'s knobs, in both name forms '+hintBtn('control.director_knob')+'</h3><table class="d-knobs"><tr><th>plan knob</th><th>--set key</th><th>range</th><th class="num">plan default</th><th>value</th><th>what</th></tr>';
 c.knobs.forEach((k,i)=>{if(k.readonly){h+='<tr class="d-ro"><td class="data">'+esc(k.name)+'</td><td>'+chip('read-only','info','director.readonly')+'</td><td class="data">'+esc(JSON.stringify(k.range))+'</td><td class="num">'+esc(JSON.stringify(k.default))+'</td><td class="muted"><span class="d-what">'+esc(k.readonly)+'</span></td><td class="muted"><span class="d-what">'+esc(k.what)+'</span></td></tr>';return;}
  const cur=dGet(dEff(st,k.set_key,k.base),k.path);const val=cur===undefined?k.default:cur;const ch=dHas(st.set,k.set_key);
  h+='<tr'+(ch?' class="d-changed"':'')+'><td class="data">'+esc(k.name)+'</td><td class="data">'+esc(k.set_key)+esc(k.path.map(x=>'['+x+']').join(''))+'</td><td class="data">'+esc(JSON.stringify(k.range))+'</td><td class="num">'+esc(JSON.stringify(k.default))+'</td><td>'+dKnobInput('dK'+i,k.range,val)+'</td><td class="muted"><span class="d-what">'+esc(k.what)+'</span></td></tr>';});
 return h+'</table>';}
function dSetTables(st,c){let h='<h3 style="margin-top:16px">The renderer\'s --set keys '+hintBtn('control.director_set')+'</h3><p class="muted">A ticked key is sent as --set k=JSON. The default shown is this concept\'s; a faint row\'s condition rules it out for this container.'+hintBtn('director.condition')+'</p>';
 h+=dRows(c.globals,st,'g');
 h+='<details'+(c.container.kind==='disc'?' open':'')+'><summary class="label" data-hint="director.set_group">the sky keys, read under a disc container ('+c.sky.length+')</summary>'+dRows(c.sky,st,'s')+'</details>';
 c.transforms.forEach((t,ti)=>{h+='<details><summary class="label" data-hint="director.set_group">'+esc(t.name)+' · '+esc(t.by)+' · '+t.rows.length+' keys'+(t.keyframes.length?' '+chip('generated','gen'):'')+'</summary>'+dRows(t.rows,st,'t'+ti)+'</details>';});
 return h;}
// a boolean value is a true or false select, so its row holds one checkbox, the send box (critique B, minor 15)
function dSetInput(id,r,v){const a=' id="'+id+'" class="dSetVal" data-set="'+esc(r.set_key)+'" data-type="'+esc(r.type)+'" data-hint="'+esc(r.hint)+'" aria-label="'+esc('value of '+r.set_key)+'"';
 if(r.type==='bool')return '<select'+a+'><option value="true"'+(v?' selected':'')+'>true</option><option value="false"'+(v?'':' selected')+'>false</option></select>';
 if(r.choices&&(r.type==='str'))return '<select'+a+'>'+r.choices.concat(r.choices.includes(v)||v==null?[]:[v]).map(o=>'<option'+(o===v?' selected':'')+'>'+esc(o)+'</option>').join('')+'</select>';
 if(r.type==='int'||r.type==='float')return '<input'+a+' inputmode="decimal" value="'+esc(v==null?'':v)+'">';
 if(r.type==='str')return '<input'+a+' value="'+esc(v==null?'':v)+'">';
 return '<input'+a+' value="'+esc(v==null?'':JSON.stringify(v))+'">';}
function dRows(rows,st,pre){let h='<table class="d-set"><tr><th>send</th><th>key</th><th>default here</th><th>value</th><th>read when</th></tr>';
 rows.forEach((r,i)=>{const id='dS_'+pre+'_'+i;const on=dHas(st.set,r.set_key);let def=r.default;if(r.follows&&dHas(st.set,r.follows))def=st.set[r.follows];
  if(r.readonly){h+='<tr class="d-ro"><td></td><td class="data">'+esc(r.set_key)+hintBtn(r.hint)+'</td><td class="data">'+esc(JSON.stringify(def))+'</td><td>'+chip('read-only','info','director.readonly')+'</td><td class="muted">'+esc(r.readonly)+'</td></tr>';return;}
  const v=on?st.set[r.set_key]:def;
  h+='<tr class="'+(r.applies===false?'d-off':'')+(on?' d-changed':'')+'"><td><input type="checkbox" class="dSetOn" data-set="'+esc(r.set_key)+'" data-row="'+id+'"'+(on?' checked':'')+' data-hint="control.director_set" aria-label="'+esc('send '+r.set_key)+'"></td><td class="data">'+esc(r.set_key)+hintBtn(r.hint)+'</td><td class="data">'+esc(JSON.stringify(def))+'</td><td>'+dSetInput(id,r,v)+'</td><td class="muted d-when">'+esc(r.when)+'</td></tr>';});
 return h+'</table>';}
function dReadSet(el){const t=el.dataset.type;if(el.type==='checkbox')return el.checked;if(t==='bool')return el.value==='true';if(t==='int'||t==='float'){const n=parseFloat(el.value);return isNaN(n)?null:n;}if(t==='str')return el.value;try{return JSON.parse(el.value);}catch(e){return el.value;}}
function dQuote(a){return a.map(x=>/[\s"'<>]/.test(x)?"'"+x.replace(/'/g,"'\\''")+"'":x).join(' ');}
function dCommand(st,draft){const v=S.view,c=dConcept(st);if(!c||!st.pv)return '';const set=dAllSet(st);const jd=v.job.root.replace(/\/run$/,'');const name=st.pv.stem+'_'+c.id+(st.tag?'-'+st.tag:'');
 const a=['.venv/bin/python','scripts/research/director_render.py',st.pv.path,(draft?jd+'/drafts/':v.job.root+'/')+name+'.part','--concept',c.id,'--max-long',String(draft?480:st.full),'--seconds',dSec(st.sec),'--fps',String(st.fps)];
 Object.keys(set).sort().forEach(k=>a.push('--set',k+'='+pyJson(set[k])));
 a.push('--progress','--layers-dir',v.job.layers_dir||'','--mattes-dir',v.job.mattes_dir||'');
 return dQuote(a);}
// the resolve's command in runner/argv_director.py's order; the folder's stamp is the record's, known when it starts
function dResolveCommand(st){const v=S.view,c=dConcept(st);if(!c||!st.pv)return '';const set=dAllSet(st);const jd=v.job.root.replace(/\/run$/,'');
 const a=['.venv/bin/python','scripts/research/director_render.py',st.pv.path,jd+'/resolve/<stamp>.part','--resolve-only','--concept',c.id,'--max-long',String(st.rlong)];
 Object.keys(set).sort().forEach(k=>a.push('--set',k+'='+pyJson(set[k])));
 a.push('--layers-dir',v.job.layers_dir||'','--mattes-dir',v.job.mattes_dir||'');
 return dQuote(a);}
function dResolveKnobs(st){const c=dConcept(st);return {plan:st.ref||dDefaultRef(),concept:c?c.id:'',max_long:st.rlong,set:dAllSet(st)};}
// The inspector of the resolve and the render (critique B, P1 (a)): the knobs the panel's amber button sends, read-only,
// with the command they make and no run button of its own; the loop's inspector keeps its rows (inspector.js's hook).
function dInspector(s){if(s.name!=='resolve'&&s.name!=='render')return null;const st=dSt(),c=dConcept(st),set=dAllSet(st),keys=Object.keys(set).sort();
 const rows=[['plan',st.ref||dDefaultRef()||'none'],['concept',c?c.id:(st.loading?'loading the plan…':'the plan\'s first')]];
 if(s.name==='resolve')rows.push(['long side',st.rlong+' px']);else rows.push(['tag',st.tag||'none'],['seconds',dSec(st.sec)],['fps',String(st.fps)],['draft long side','480 px'],['full long side',st.full+' px']);
 const cmd=s.name==='resolve'?dResolveCommand(st):dCommand(st,true);
 return '<section id="dNext"><h3>Knobs the panel sends '+hintBtn('director.next_knobs')+'</h3><table class="d-next" style="width:100%">'+rows.map(([k,x])=>'<tr><td>'+esc(k)+'</td><td class="data">'+esc(x)+'</td></tr>').join('')+'</table>'
  +'<div class="label muted" style="margin-top:8px">set dict, '+keys.length+' key'+(keys.length===1?'':'s')+' '+hintBtn('control.director_set')+'</div>'+(keys.length?'<div class="data d-setro">'+keys.map(k=>esc(k)+'='+esc(pyJson(set[k]))).join('<br>')+'</div>':'<p class="muted">empty: the plan as written</p>')
  +'<div class="label muted" style="margin-top:8px">'+(s.name==='resolve'?'the next resolve':'the next 480 draft')+' '+hintBtn('control.director_command')+'</div><div class="cmd">'+esc(cmd||'the plan is loading')+'</div>'
  +'<p class="muted" style="font-size:.75rem;margin-top:8px">'+(s.name==='resolve'?'The resolve panel\'s amber button runs it; the plan panel holds the set dict.':'The render panel\'s amber button renders this draft, and render full renders at the full long side; the plan panel holds the set dict.')+'</p></section>';}
// what the graph's "rerun from here" sends for the director's resolve and render: the same knobs (graph.js's hook)
function dRunKnobs(name){const st=dSt();if(name==='resolve')return dResolveKnobs(st);if(name==='render')return dRenderKnobs(st,true);return null;}
// ---------------------------------------------------------------- render: the controls over the shared viewer
// the next render's controls sit in the viewer's side column under the renders (critique B, P2 4: above the viewer
// they took about 150 px of the frame's height, and at 1280×800 the scrubber ended below the window)
function dRenderCtl(st){const keys=Object.keys(dAllSet(st)).sort();
 return '<div class="d-nextctl"><h3 class="label">The next render</h3><div class="d-ctlgrid">'+dPlanPick(st)
  +'<label class="label muted" for="dTag">tag</label><input id="dTag" data-hint="control.director_tag" value="'+esc(st.tag)+'" placeholder="v2">'
  +'<label class="label muted" for="dSec">seconds</label><input id="dSec" data-hint="control.director_seconds" inputmode="decimal" value="'+esc(st.sec)+'">'
  +'<label class="label muted" for="dFps">fps</label><input id="dFps" data-hint="control.director_fps" inputmode="decimal" value="'+esc(st.fps)+'">'
  +'<label class="label muted" for="dFull">full long side</label><input id="dFull" data-hint="control.director_full" inputmode="decimal" value="'+esc(st.full)+'"></div>'
  +'<p class="muted d-setline">'+(keys.length?keys.length+' --set key'+(keys.length>1?'s':'')+' from the plan panel: <span class="data">'+esc(keys.join(', '))+'</span>':'No --set key: the plan as written.')+'</p>'
  +'<div class="d-acts"><button class="btn primary" id="dDraft" data-hint="control.director_draft">render a 480 draft</button><button class="btn" id="dFullGo" data-hint="control.director_full">render full</button></div>'
  +(S.render&&S.render.record_knobs&&S.render.record_knobs.plan?'<div class="d-acts"><button class="btn" id="dReRender" data-hint="control.rerun">re-render '+esc(S.render.name)+' with its record\'s knobs under the tag</button></div>':'')+'</div>';}
function dRender(){const v=S.view,st=dSt();dEnsurePlan(st);
 if(!v.candidates.length)return '<p class="muted">'+esc(stageOf('render').what)+'</p><div class="d-alone">'+dRenderCtl(st)+'</div><div class="empty">No render yet. Render a 480 draft first; the full renders are the page\'s candidates.</div>';
 return '<div id="viewerWrap"><div class="viewer"><div class="framewrap"><div class="frame" id="frameBox"></div></div><div class="vside" id="vside">'+candList()+dRenderCtl(st)+'</div></div></div>';}
// viewer.js redraws the side column after a render is fetched: the controls come back from the state, and are wired again
function dSide(){return S.stage==='render'&&S.view&&S.view.job.flow==='director'?dRenderCtl(dSt()):'';}
function dWirePick(st){const pl=$('#dPlan');if(pl)pl.onchange=async()=>{dSnap(st);st.ref=pl.value;st.pv=null;st.set={};st.cid=null;try{await dLoadPlan(st,pl.value);}catch(e){st.err=e.message;}dRedraw();};
 const cs=$('#dConcept');if(cs)cs.onchange=()=>{dSnap(st);st.cid=cs.value;st.set={};dRedraw();};}
function dWireRender(st){[['dTag','tag'],['dSec','sec'],['dFps','fps'],['dFull','full']].forEach(([id,k])=>{const el=$('#'+id);if(el)el.oninput=()=>{st[k]=el.value;dSyncIns();};});
 const dr=$('#dDraft');if(dr)dr.onclick=()=>dPost('render',dRenderKnobs(st,true),'a 480 draft',dr);
 const fg=$('#dFullGo');if(fg)fg.onclick=()=>dPost('render',dRenderKnobs(st,false),'the full render',fg);
 const rr=$('#dReRender');if(rr)rr.onclick=()=>{const k=dClone(S.render.record_knobs);k.name=st.tag;dPost('render',k,'a re-render of '+S.render.name+' under the tag '+(st.tag||'(none)'),rr);};}
function dWireSide(){if(S.stage!=='render'||!S.view||S.view.job.flow!=='director')return;const st=dSt();dWirePick(st);dWireRender(st);}
function dRenderKnobs(st,draft){const c=dConcept(st);return {plan:st.ref||dDefaultRef(),concept:c?c.id:'',name:st.tag,draft:draft?480:0,max_long:parseInt(st.full,10)||1920,seconds:parseFloat(st.sec),fps:parseInt(st.fps,10),set:dAllSet(st)};}
// a stage run from a panel button, the button inert until the request settles (critique B, P2 3)
function dPost(stage,knobs,what,btn){const v=S.view;return busy(btn,async()=>{try{const r=await api('/api/jobs/'+dEnc(v.job.id)+'/stages/'+stage+'/run',{knobs});setMsg('started '+r.record+': '+what+runWarnings(r.warnings),'ok');await openJob(v.job.id,true);loadJobs();}catch(e){setMsg(e.message,'bad');}});}
// ---------------------------------------------------------------- page and grades
function dPage(){const v=S.view;const full=v.candidates.filter(c=>c.kind==='full');const bad=full.filter(c=>c.unjudged||(c.verdict&&c.verdict.verdict==='NOT READY'));const n=v.rounds.length+1;const pg=stageOf('page');
 let h='<p class="muted">'+esc(pg.what)+' '+hintBtn('control.director_page')+'</p><div class="cols"><div class="box"><h3>Build the page</h3>'+(full.length?'<p class="muted">'+full.length+' full render'+(full.length>1?'s':'')+': <span class="data">'+esc(full.map(c=>c.name).join(', '))+'</span></p>':'<p class="muted">no full render yet</p>')+(bad.length?gateMessage(bad):'');
 const field=(id,label,val)=>'<label class="label muted" for="'+id+'" style="display:block;margin-top:6px">'+label+'</label><input id="'+id+'" data-hint="control.director_page" style="width:100%" value="'+esc(val)+'">';
 h+=field('dpTitle','title',v.job.seq+': round '+n)+field('dpKey','key',v.job.id+'_r'+n)+field('dpHead','head (an HTML file in the repo)','')+field('dpKeyframes','keyframes.json of the generated helpers','');
 h+='<div class="label muted" style="margin-top:8px">per clip: what to look at and the faults to expect (the skeptic\'s answers fill them on the page)</div>'+full.map(c=>'<div class="d-note"><span class="data">'+esc(c.name)+'</span><input class="dpLook" data-name="'+esc(c.name)+'" data-hint="control.director_page" aria-label="'+esc('look at, '+c.name)+'" placeholder="look at"><input class="dpFaults" data-name="'+esc(c.name)+'" data-hint="control.director_page" aria-label="'+esc('faults to expect, '+c.name)+'" placeholder="faults to expect"></div>').join('');
 h+='<div style="margin-top:8px"><label><input type="checkbox" id="dpOverride" data-hint="control.page_override"> override the gate (on his word)</label></div><div style="margin-top:8px"><button class="btn primary" id="dpGo" data-hint="control.director_page"'+(full.length?'':' disabled')+'>build the page</button></div></div>';
 h+='<div>'+(v.page.exists?'<h3>The page</h3><p><a href="'+esc(v.page.url)+'" target="_blank" data-hint="control.director_page">open index.html</a> <span class="data muted">md5 '+esc(v.page.md5)+'</span>'+(pg.previous?' · <a href="'+esc(pg.previous)+'" target="_blank" data-hint="control.director_page">the previous page</a>':'')+'</p><iframe class="pair-frame" src="'+esc(v.page.url)+'" title="the review page"></iframe>':'<p class="muted">no page yet</p>')+'</div></div>';
 return h;}
function dSplit(name){const i=name.lastIndexOf('_');return i<0?{stem:name,ct:''}:{stem:name.slice(0,i),ct:name.slice(i+1)};}
// The grades (critique B, P2 5; the drive's defect 6, retirement row 22): every round, newest first; a graded round
// read-only with its picks file and his words; an ungraded round's form lists the renders its page shows, pre-filled
// once from the newest picks file (the boxes, the notes and the best, never his words), as the workbench did
// (director_ui.py:1113). The picks files are fetched once per job and path.
function dPicksCache(){return S.dPicks||(S.dPicks={});}
function dPickKey(r){return S.view.job.id+'/'+r.grade.picks;}
async function dLoadPicks(){const v=S.view,rs=(v.rounds||[]).filter(r=>r.grade&&r.grade.picks),cache=dPicksCache();let fresh=false;
 for(const r of rs){const k=dPickKey(r);if(k in cache)continue;cache[k]=null;try{cache[k]=await api('/api/jobs/'+dEnc(v.job.id)+'/file/'+r.grade.picks);fresh=true;}catch(e){}}
 if(fresh&&S.view&&S.view.job.id===v.job.id&&S.stage==='grades')dRedraw();}
function dNewestPicks(){const rs=(S.view.rounds||[]).filter(r=>r.grade&&r.grade.picks).sort((a,b)=>b.n-a.n);for(const r of rs){const x=dPicksCache()[dPickKey(r)];if(x)return x;}return null;}
function dGr(st,n){const g=st.gr[n]||(st.gr[n]={clips:{},best:{},text:'',seeded:false,touched:false});
 if(!g.seeded&&!g.touched){const x=dNewestPicks();if(x){g.seeded=true;Object.entries(x.clips||{}).forEach(([nm,c])=>{const pr=c.props||{};g.clips[nm]={acceptable:!!c.acceptable,note:c.note||'',props:{one_picture:!!pr.one_picture,transforms:!!pr.transforms,not_invented:!!pr.not_invented}};});g.best=Object.assign({},x.best||{});}}
 return g;}
function dGClip(g,name){return g.clips[name]||(g.clips[name]={acceptable:false,note:'',props:{one_picture:false,transforms:false,not_invented:false}});}
function dGrades(){const v=S.view,st=dSt();let h='<p class="muted">'+esc(stageOf('grades').what)+' '+hintBtn('control.director_grade')+'</p>';
 if(!v.rounds.length)return h+'<div class="empty">No round yet: build the page first.</div>';
 dLoadPicks();
 return h+'<div class="cols">'+v.rounds.slice().reverse().map(r=>dRoundBox(st,r)).join('')+'</div>';}
function dRoundBox(st,r){const v=S.view,n=r.n;let h='<div class="box"><h3>Round '+esc(n)+' '+(r.grade?chip('graded','ok'):(r.ungraded_by_his_word?chip('ungraded by his word','info'):chip('ungraded','info')))+'</h3><p class="muted">'+esc(r.at)+' · renders <span class="data">'+esc(r.candidates.join(', '))+'</span> · page md5 <span class="data">'+esc(r.page_md5)+'</span>'+(r.override?'<br>'+esc(r.override):'')+'</p>';
 if(r.grade){const x=r.grade.picks?dPicksCache()[dPickKey(r)]:null;return h+'<div class="d-picks">'+pairPicksView(x)+'</div>'+(r.grade.text?'<blockquote class="d-words">'+esc(r.grade.text)+'</blockquote>':'')+'<p class="muted">saved '+esc(r.grade.at)+' on page md5 '+esc((r.grade.page_md5||'').slice(0,8))+'…'+(r.grade.picks?' · <a href="/api/jobs/'+esc(dEnc(v.job.id))+'/file/'+esc(r.grade.picks)+'" target="_blank" data-hint="control.director_grade">'+esc(r.grade.picks)+'</a>':'')+'</p></div>';}
 if(r.ungraded_by_his_word)return h+'<p class="muted">marked '+esc(r.ungraded_by_his_word.at)+'</p></div>';
 const g=dGr(st,n),marks=v.owner_frames||[];
 r.candidates.forEach(name=>{const c=dGClip(g,name);const fr=marks.filter(o=>o&&o.name===name&&o.kind==='full').map(o=>o.frame);
  h+='<div class="d-clip"><h3><span class="data">'+esc(name)+'</span></h3><div class="d-props">'+[['one_picture','one picture'],['transforms','content transforms'],['not_invented','nothing invented']].map(([k,l])=>'<label><input type="checkbox" class="dgProp" data-round="'+n+'" data-name="'+esc(name)+'" data-prop="'+k+'"'+(c.props[k]?' checked':'')+' data-hint="control.director_grade"> '+l+'</label>').join('')+'<label><input type="checkbox" class="dgOk" data-round="'+n+'" data-name="'+esc(name)+'"'+(c.acceptable?' checked':'')+' data-hint="control.director_grade"> acceptable as-is</label>'+(fr.length?'<span class="muted">marked frames <span class="data">'+esc(fr.join(', '))+'</span></span>':'')+'</div><textarea class="dgNote" data-round="'+n+'" data-name="'+esc(name)+'" data-hint="control.director_grade" rows="2" aria-label="'+esc('his note on '+name)+'" placeholder="what is wrong, what should happen instead, which knob">'+esc(c.note)+'</textarea></div>';});
 const stems=[...new Set(r.candidates.map(nm=>dSplit(nm).stem))];
 h+=stems.map(sm=>'<p><label class="label muted">best for <span class="data">'+esc(sm)+'</span> <select class="dgBest" data-round="'+n+'" data-stem="'+esc(sm)+'" data-hint="control.director_best"><option value="none">none</option>'+r.candidates.filter(nm=>dSplit(nm).stem===sm).map(nm=>{const ct=dSplit(nm).ct;return '<option value="'+esc(ct)+'"'+(g.best[sm]===ct?' selected':'')+'>'+esc(ct)+'</option>';}).join('')+'</select></label>'+hintBtn('control.director_best')+'</p>').join('');
 return h+'<div class="label muted">his words, verbatim</div><textarea class="dgText" data-round="'+n+'" data-hint="control.director_grade" aria-label="'+esc('his words for round '+n)+'">'+esc(g.text)+'</textarea><div style="margin-top:8px"><button class="btn primary dgSave" data-round="'+n+'" data-hint="control.director_grade">save the grade</button></div></div>';}
// the picks of round n: its own renders only, so a draft the page never showed is never graded
function dPicks(st,n){const v=S.view,r=v.rounds.find(x=>x.n===n),g=dGr(st,n),clips={},marks=v.owner_frames||[],by={};v.candidates.forEach(c=>{if(c.kind==='full')by[c.name]=c;});
 r.candidates.forEach(name=>{const c=dGClip(g,name);const fr=marks.filter(o=>o&&o.name===name&&o.kind==='full').map(o=>o.frame);const x={acceptable:!!c.acceptable,note:c.note||'',props:{one_picture:!!c.props.one_picture,transforms:!!c.props.transforms,not_invented:!!c.props.not_invented},draft:false};if(by[name]&&by[name].record)x.render=by[name].record;if(fr.length)x.frames=fr;clips[name]=x;});
 const best={};[...new Set(r.candidates.map(nm=>dSplit(nm).stem))].forEach(sm=>{best[sm]=g.best[sm]||'none';});
 return {round:n,picks:{date:new Date().toISOString(),page:(stageOf('page').latest_knobs||{}).key||(v.job.id+'_r'+n),best,clips},text:g.text};}
// ---------------------------------------------------------------- the wiring of every panel of this file
function dWire(){const v=S.view,st=dSt();const p=$('#panel');
 dWirePick(st);
 // import
 p.querySelectorAll('.dOv').forEach(b=>b.onchange=()=>{const sides=st.both?['A','B']:[b.dataset.side];sides.forEach(s=>{st.ov[s][b.dataset.kind]=b.checked;});dRedraw();});
 const bo=$('#dBoth');if(bo)bo.onchange=()=>{st.both=bo.checked;};
 const op=$('#dOp');if(op)op.oninput=()=>{st.op=+op.value;p.querySelectorAll('.d-stack img.ov').forEach(i=>{i.style.opacity=String(st.op/100);});};
 p.querySelectorAll('.d-el').forEach(tr=>{const go=()=>{const s=tr.dataset.side,id=+tr.dataset.id;st.matte[s]=st.matte[s]===id?null:id;dRedraw();};tr.onclick=go;
  tr.onfocus=()=>{(S.dElTab||(S.dElTab={}))[tr.dataset.side]=+tr.dataset.id;tr.closest('table').querySelectorAll('.d-el').forEach(x=>{x.tabIndex=x===tr?0:-1;});};
  tr.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go();return;}if(e.key!=='ArrowDown'&&e.key!=='ArrowUp')return;e.preventDefault();const nx=e.key==='ArrowDown'?tr.nextElementSibling:tr.previousElementSibling;if(nx&&nx.classList.contains('d-el')){nx.focus();nx.scrollIntoView({block:'nearest'});}};});
 // resolve and verdict
 const rl=$('#dRLong');if(rl)rl.onchange=()=>{st.rlong=parseInt(rl.value,10);dSyncIns();};
 const rg=$('#dResolveGo');if(rg)rg.onclick=()=>{const c=dConcept(st);if(!c){setMsg('choose a plan first','bad');return;}dPost('resolve',dResolveKnobs(st),'the resolve of '+st.pv.stem+' '+c.id,rg);};
 const vr=$('#dVerdictRun');if(vr)vr.onclick=()=>dPost('verdict',{},'Reveal\'s verdict',vr);
 // plan: every change of the set dict takes an undo step first
 const c=dConcept(st);
 p.querySelectorAll('.d-bar').forEach(b=>{b.onpointerdown=dDragStart;b.onkeydown=e=>dBarKey(e,b);});
 p.querySelectorAll('.dMute').forEach(b=>b.onchange=()=>{dSnap(st);const k=b.dataset.name+'.skip';if(b.checked)st.set[k]=true;else delete st.set[k];dRedraw();});
 p.querySelectorAll('.dSolo').forEach(b=>b.onchange=()=>{dSnap(st);c.beats.forEach(x=>{if(b.checked&&x.name!==b.dataset.name)st.set[x.name+'.skip']=true;else delete st.set[x.name+'.skip'];});dRedraw();});
 p.querySelectorAll('.dKnob').forEach(el=>el.onchange=()=>{const k=c.knobs[+el.id.slice(2)];let x;if(el.type==='checkbox')x=el.checked;else if(el.getAttribute('inputmode')==='decimal'){x=parseFloat(el.value);if(isNaN(x))x=k.default;}else{try{x=JSON.parse(el.value);}catch(e){x=el.value;}}dSnap(st);dSetKey(st,k.set_key,k.base,dSetPath(dEff(st,k.set_key,k.base),k.path,x));dRedraw();});
 p.querySelectorAll('.dSetOn').forEach(el=>el.onchange=()=>{dSnap(st);const key=el.dataset.set;if(!el.checked){delete st.set[key];}else{const val=$('#'+el.dataset.row);const x=val?dReadSet(val):null;st.set[key]=x;}dRedraw();});
 p.querySelectorAll('.dSetVal').forEach(el=>el.onchange=()=>{dSnap(st);st.set[el.dataset.set]=dReadSet(el);dRedraw();});
 const ex=$('#dExtra');if(ex){ex.onfocus=()=>{ex.dataset.was=st.extra;};ex.oninput=()=>{st.extra=ex.value;const cm=$('#dCmd');if(cm)cm.textContent=dCommand(st,true);};ex.onchange=()=>{const now=st.extra;st.extra=ex.dataset.was||'';dSnap(st);st.extra=now;dRedraw();};}
 const lr=$('#dLastRound');if(lr)lr.onclick=()=>{const l=c&&c.last_round;if(!l)return;dSnap(st);Object.entries(l.knobs||{}).forEach(([k,x])=>{st.set[k]=x;});setMsg('loaded '+Object.keys(l.knobs||{}).length+' knobs from '+l.from,'ok');dRedraw();};
 // "clear all knobs" asks first, in the row: "no" holds the focus, Escape answers no (critique B, P2 8)
 const cl=$('#dClear');if(cl)cl.onclick=()=>{st.clearAsk=true;dRedraw();const no=$('#dClearNo');if(no)focusQuiet(no);};
 const cy=$('#dClearYes'),cn=$('#dClearNo');const answer=yes=>{st.clearAsk=false;if(yes){dSnap(st);st.set={};st.extra='';setMsg('every --set key and the extra lines cleared; Cmd-Z brings them back','ok');}dRedraw();const b=$('#dClear');if(b)focusQuiet(b);};
 if(cy)cy.onclick=()=>answer(true);if(cn)cn.onclick=()=>answer(false);[cy,cn].forEach(x=>{if(x)x.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();answer(false);}};});
 // render
 dWireRender(st);
 if(S.stage==='render'){wireCands(p);if(!S.vw.render)S.vw.render={cmp:'single',a:'frame',b:'last',wipe:50,onion:50,ab:'A'};if(!S.cand&&v.candidates.length){const c2=v.candidates.slice().sort((a,b)=>a.mtime<b.mtime?1:-1)[0];selectCand(c2.kind,c2.name);}else if(S.cand)loadRender();}
 // skeptic (the loop's panel and its request button)
 const sk=$('#skGo');if(sk)sk.onclick=()=>busy(sk,async()=>{const names=[...document.querySelectorAll('.skc:checked')].map(x=>x.value);try{const r=await api('/api/jobs/'+dEnc(v.job.id)+'/requests/skeptic',{brief:$('#skBrief').value,candidates:names});setMsg('written '+r.file+'; the session lists it with reveal-studio requests','ok');await openJob(v.job.id,true);loadJobs();}catch(e){setMsg(e.message,'bad');}});
 // page
 const pg=$('#dpGo');if(pg)pg.onclick=()=>busy(pg,async()=>{const notes={};p.querySelectorAll('.dpLook,.dpFaults').forEach(i=>{const x=i.value.trim();if(!x)return;const n=notes[i.dataset.name]||(notes[i.dataset.name]={});n[i.classList.contains('dpLook')?'look':'faults']=x;});
  try{const r=await api('/api/jobs/'+dEnc(v.job.id)+'/page',{title:$('#dpTitle').value,key:$('#dpKey').value,head:$('#dpHead').value,keyframes:$('#dpKeyframes').value,notes,override:$('#dpOverride').checked});setMsg('building the page: record '+r.record+(r.override?' · '+r.override:''),'ok');await openJob(v.job.id,true);}catch(e){setMsg(e.message,'bad');}});
 // grades: one form per ungraded round, over that round's own renders
 const g=b=>{const x=dGr(st,+b.dataset.round);x.touched=true;return x;};
 p.querySelectorAll('.dgProp').forEach(b=>b.onchange=()=>{dGClip(g(b),b.dataset.name).props[b.dataset.prop]=b.checked;});
 p.querySelectorAll('.dgOk').forEach(b=>b.onchange=()=>{dGClip(g(b),b.dataset.name).acceptable=b.checked;});
 p.querySelectorAll('.dgNote').forEach(b=>b.oninput=()=>{dGClip(g(b),b.dataset.name).note=b.value;});
 p.querySelectorAll('.dgBest').forEach(b=>b.onchange=()=>{g(b).best[b.dataset.stem]=b.value;});
 p.querySelectorAll('.dgText').forEach(b=>b.oninput=()=>{g(b).text=b.value;});
 p.querySelectorAll('.dgSave').forEach(b=>b.onclick=()=>busy(b,async()=>{const n=+b.dataset.round;try{await api('/api/jobs/'+dEnc(v.job.id)+'/picks',dPicks(st,n));setMsg('round '+n+' graded: the picks file saved, his words verbatim beside it','ok');await openJob(v.job.id,true);loadJobs();}catch(e){setMsg(e.message,'bad');}}));}
// the timeline's drag: the middle moves the window, within 6 px of an end resizes it; rounded to 0.01, at least 0.02
// wide, inside 0 to 1 (director_ui.py:1042-1059); on release the window becomes <name>.window or end_window
let dDrag=null;
function dDragStart(e){const b=e.currentTarget;const st=dSt(),c=dConcept(st);if(!c)return;const r=dBeats(c)[+b.dataset.i];const w=dEff(st,r.key,r.base).map(Number);const rect=b.getBoundingClientRect();const x=e.clientX-rect.left;
 dDrag={r,w0:w,x0:e.clientX,W:$('#dTl').getBoundingClientRect().width,mode:x<6?'l':(x>rect.width-6?'r':'m'),el:b,cur:null};b.setPointerCapture(e.pointerId);b.onpointermove=dDragMove;b.onpointerup=dDragEnd;b.onpointercancel=b.onlostpointercapture=dDragCancel;e.preventDefault();}
// a cancelled pointer or a lost capture ends the drag where it started: the bar never follows a mouse with no button
// held (critique B, minor 2); after a release the capture's loss finds no drag and does nothing
function dDragCancel(){if(!dDrag)return;dDrag=null;dRedraw();}
function dClampWin(mode,w0,dx){let [a,b]=w0;const len=b-a;if(mode==='m'){a=Math.min(Math.max(0,a+dx),1-len);b=a+len;}else if(mode==='l'){a=Math.min(Math.max(0,a+dx),b-D_MIN_W);}else{b=Math.max(Math.min(1,b+dx),a+D_MIN_W);}return [Math.round(a*100)/100,Math.round(b*100)/100];}
function dDragMove(e){if(!dDrag)return;const w=dClampWin(dDrag.mode,dDrag.w0,(e.clientX-dDrag.x0)/dDrag.W);dDrag.cur=w;dDrag.el.style.left=(w[0]*100)+'%';dDrag.el.style.width=((w[1]-w[0])*100)+'%';dDrag.el.querySelector('.data').textContent=w[0].toFixed(2)+'–'+w[1].toFixed(2);}
function dDragEnd(){if(!dDrag)return;const d=dDrag;dDrag=null;if(d.cur){const st=dSt();dSnap(st);dSetKey(st,d.r.key,d.r.base,d.cur);}dRedraw();}
// the keyboard (critique B, P2 8): the arrows move a bar by 0.01, shift with the arrows its end, alt with the arrows
// its start, page up and page down the whole window by 0.1; each move is one undo step
const D_BAR_KEYS={ArrowLeft:-0.01,ArrowRight:0.01,PageDown:-0.1,PageUp:0.1};
function dBarKey(e,b){const dx=D_BAR_KEYS[e.key];if(dx===undefined||e.metaKey||e.ctrlKey)return;e.preventDefault();e.stopPropagation();const st=dSt(),c=dConcept(st);const r=dBeats(c)[+b.dataset.i];const w=dEff(st,r.key,r.base).map(Number);
 const mode=e.key.startsWith('Page')?'m':(e.shiftKey?'r':(e.altKey?'l':'m'));const nw=dClampWin(mode,w,dx);if(nw[0]===w[0]&&nw[1]===w[1])return;dSnap(st);dSetKey(st,r.key,r.base,nw);S.dFocusBar=+b.dataset.i;dRedraw();const nb=$('#dTl .d-bar[data-i="'+S.dFocusBar+'"]');if(nb)focusQuiet(nb);}
// Cmd-Z and Shift-Cmd-Z (Ctrl on another system) undo and redo a change of the set dict on the plan panel; a text field
// keeps its own undo for the text typed in it
document.addEventListener('keydown',e=>{if(!S.view||S.view.job.flow!=='director'||S.stage!=='plan'||!(e.metaKey||e.ctrlKey)||e.altKey||e.key.toLowerCase()!=='z')return;if(e.target.matches('input:not([type=checkbox]),textarea,select'))return;
 e.preventDefault();const st=dSt();if(dStep(st,!e.shiftKey)){setMsg((e.shiftKey?'redone':'undone')+': the set dict holds '+Object.keys(dAllSet(st)).length+' keys','ok');const fk=focusKey($('#dBody'));dRedraw();if(fk)restoreFocus($('#dBody'),fk);}});
// ---------------------------------------------------------------- the viewer's entries for a director render
function dSources(){const v=S.view,out=[];if(!v)return out;const r=S.render;
 if(r&&vhost()==='render'){const n=r.frames_available||r.frames||0;const t=(r.frames_tags||[])[S.frame]||{};out.push({id:'frame',label:'frame f '+S.frame+' of '+candLabel(r),url:r.frame_url+S.frame,gen:!!t.generated});if(n){out.push({id:'first',label:'frame 0: A exactly',url:r.frame_url+0});out.push({id:'last',label:'frame '+(n-1)+': B exactly',url:r.frame_url+(n-1)});}}
 const rv=v.resolve;if(rv){out.push({id:'canvasA',label:'canvas_A.png of the resolve',url:rv.urls.canvas_A});out.push({id:'canvasB',label:'canvas_B.png of the resolve',url:rv.urls.canvas_B});}
 if(S.shown)out.push({id:'shown',label:'shown: '+S.shown.label,url:S.shown.url});
 return out;}
function dCandRow(c){const sel=!!(S.cand&&S.cand.kind===c.kind&&S.cand.name===c.name);
 return '<button class="cand" data-kind="'+c.kind+'" data-name="'+esc(c.name)+'" data-hint="control.candidate" aria-selected="'+sel+'"><span class="nm"><span class="label">'+esc(c.name)+'</span>'+(c.kind==='draft'?chip('draft '+c.draft,'info'):(c.unjudged?chip('unjudged','info'):chip(c.verdict.verdict,c.verdict.verdict==='NOT READY'?'bad':'ok')))+'</span><span class="dt">'+esc(c.frames)+' f · '+esc(c.seconds)+' s · motion '+esc(c.motion_median_px!=null?c.motion_median_px:'—')+' px · B first f '+esc(c.b_inside_first!=null?c.b_inside_first:'—')+' · '+esc((c.md5_mp4||'').slice(0,8))+'</span></button>';}
// one plot on the shared axis: the points at their own frame index (a pairwise series between frame j and j + 1). The
// title, the unit and the plot's one "?" sit on a line above it, and the tick labels hold at most five characters, so
// none is cut left of the axis (critique B, P2 1 and minor 10; the drive's defect 5: "100.00 %" read ".00 %")
function dTick(v){const a=Math.abs(v);return a===0?'0':a>=100?v.toFixed(0):a>=10?v.toFixed(1):a>=1?v.toFixed(2):v.toFixed(3);}
function dPlot(title,unit,hint,pts,o){const W=plotW(),H=96,x0=40,x1=W-10,y0=8,y1=H-20;const r=S.render;const n=r.frames_available||r.frames||1;const k=o.scale||1;
 const vals=pts.map(p=>p[1]*k);const maxv=Math.max(o.bar?o.bar*k*1.25:0,...vals,1e-9);const yOf=v=>y1-(v/maxv)*(y1-y0);const xp=p=>xOf(o.pairwise?p[0]+0.5:p[0]);
 let s='<div class="d-plot"><div class="d-ptitle label">'+esc(title)+(unit?' <span class="muted">('+esc(unit)+')</span>':'')+hintBtn(hint)+'</div><svg viewBox="0 0 '+W+' '+(H+18)+'" width="'+W+'" height="'+(H+18)+'" style="width:100%;height:auto" aria-label="'+esc(title)+'"><line x1="'+x0+'" y1="'+y1+'" x2="'+x1+'" y2="'+y1+'" stroke="'+LINE+'"/><line x1="'+x0+'" y1="'+y0+'" x2="'+x0+'" y2="'+y1+'" stroke="'+LINE+'"/>';
 [0,maxv/2,maxv].forEach(v=>{s+=svgText(x0-4,yOf(v)+4,dTick(v),{anchor:'end',mono:true});});
 (o.bands||[]).forEach(i=>{const xa=xOf(i),xb=xOf(i+1);s+='<rect x="'+xa.toFixed(1)+'" y="'+y0+'" width="'+Math.max(1,xb-xa).toFixed(1)+'" height="'+(y1-y0)+'" fill="'+FAILED+'" opacity=".22"><title>'+esc(o.bandTitle||'')+' '+i+'</title></rect>';});
 (o.ticks||[]).forEach(i=>{const x=xOf(i+0.5).toFixed(1);s+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+(y1+8)+'" stroke="'+FAILED+'" stroke-width="2"><title>'+esc(o.tickTitle||'')+' '+i+'</title></line>';});
 if(o.bar!=null){const y=yOf(o.bar*k).toFixed(1);s+='<line x1="'+x0+'" y1="'+y+'" x2="'+x1+'" y2="'+y+'" stroke="'+FAILED+'" stroke-dasharray="4 4"/>'+svgText(x1,+y-3,o.barText,{anchor:'end',fill:FAILED});}
 (o.marks||[]).forEach(m=>{const x=xOf(m.at).toFixed(1);s+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+y1+'" stroke="'+m.col+'" stroke-width="1.5" stroke-dasharray="'+(m.dash||'')+'"><title>'+esc(m.title)+'</title></line>'+(+x>W*0.7?svgText(+x-3,y0+10,m.label,{fill:m.col,anchor:'end'}):svgText(+x+3,y0+10,m.label,{fill:m.col}));});
 (r.frames_tags||[]).forEach(t=>{if(t.generated){const xa=xOf(t.i-0.5),xb=xOf(t.i+0.5);s+='<rect x="'+xa.toFixed(1)+'" y="'+(y1+3)+'" width="'+(xb-xa).toFixed(1)+'" height="5" fill="'+GEN+'" opacity=".8"/>';}});
 (r.owner_frames||[]).forEach(f=>{const x=xOf(f.frame).toFixed(1);s+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+y1+'" stroke="'+FAILED+'" opacity=".7"><title>marked: '+esc(f.note||'')+'</title></line>';});
 if(pts.length)s+='<polyline points="'+pts.map(p=>xp(p).toFixed(1)+','+yOf(p[1]*k).toFixed(1)).join(' ')+'" fill="none" stroke="'+TEXT+'" stroke-width="1.5"/>';
 s+='<line class="cursor" x1="'+xOf(S.frame)+'" y1="'+y0+'" x2="'+xOf(S.frame)+'" y2="'+(y1+8)+'" stroke="'+AMBER+'" stroke-width="1.5"/>';
 for(let i=0;i<n;i+=Math.max(1,Math.round(n/18)))s+=svgText(xOf(i),H+14,String(i),{anchor:'middle',fill:FAINT,mono:true});
 return s+'</svg></div>';}
function dPlots(){const r=S.render;const p=$('#plots');if(!r||!p||!r.series)return;const s=r.series;
 const beats=(r.frames_tags||[]).find(t=>t.beats&&t.beats.length);const first=r.series.b_inside.first;
 let h=dPlot('motion_px: the mean flow between frames; pauses (band) and jumps (tick) by the renderer\'s rule','px','info.motion_px',s.motion_px.points,{pairwise:true,bands:s.motion_px.pauses,bandTitle:'pause at entry',ticks:s.motion_px.jumps.map(j=>j-0.5),tickTitle:'jump at entry'});
 h+=dPlot('steps decoded from the mp4: the mean absolute difference between frames','levels','info.steps_decoded',s.steps.points,{pairwise:true});
 h+=dPlot('b_inside: the share of A\'s region where B shows','%','info.b_inside',s.b_inside.points,{scale:100,marks:[first!=null?{at:first,col:FAILED,label:'first above 1 %: f '+first,title:'b_inside_first'}:null,beats?{at:beats.i,col:MUTED,dash:'3 3',label:'first beat',title:'the first frame of a beat'}:null].filter(Boolean)});
 h+=dPlot('residual_edges: edges in neither photo, share of pixels','%','info.residual_edges',s.residual_edges.points,{scale:100,bar:s.residual_edges.bar,barText:'0.2 % bar (rule 5)'});
 if(s.halo)h+=dPlot('halo: the largest step round the luminary','levels','info.halo_step_max',s.halo.points.map(q=>[q[0],q[1]]),{});
 h+='<p class="muted label" style="margin:4px 0 0 40px">generated frames (violet): the frames a keyframe chain draws carry model-made pixels</p>';
 p.innerHTML=h;p.querySelectorAll('svg').forEach(svg=>svg.onclick=e=>{const rect=svg.getBoundingClientRect();const W=plotW();const x=(e.clientX-rect.left)/rect.width*W;const n=r.frames_available||r.frames||1;const i=Math.round((x-40)/(W-50)*(n-1));S.frame=Math.max(0,Math.min(n-1,i));showFrame();});}
function dShare(x){return x==null?'—':(+x).toString()+' ('+(100*x).toFixed(2)+' %)';}
function dMeasures(r){const ms=r.measures||[];const pv=r.provenance||{};
 // two rows per measure in the 320 px inspector: the key and the value, then the verdict and the bar's sentence under
// them, so nothing is cut (critique B, P2 1; the drive's defect 4: the table ran 351 px and "past bar" read "pa")
let h='<section><h3>Measures '+hintBtn('info.residual_edge_max')+'</h3><table class="d-meas">'+ms.map(m=>{const list=Array.isArray(m.value);const val=list?(m.value.length?m.value.map(x=>typeof x==='object'?x.name+': '+x.why:x).join(', '):'none'):(m.value==null?'—':(/share/.test(m.unit)?dShare(m.value):m.value));const unit=list||m.value==null||/share/.test(m.unit)?'':m.unit;
  const verdict=m.bar&&m.past!=null?(m.past?chip('past bar','bad'):chip('within','ok')):'';const under=verdict||m.bar;
  return '<tr class="'+(under?'d-m1':'')+'"><td>'+esc(m.key)+hintBtn(m.hint)+'</td><td class="num">'+esc(val)+(unit?'<span class="unit">'+esc(unit)+'</span>':'')+'</td></tr>'+(under?'<tr class="d-m2"><td colspan="2">'+verdict+(m.bar?' <span class="muted">'+esc(m.bar.text)+'</span>':'')+'</td></tr>':'');}).join('')+'</table></section>';
 h+='<section><h3>Provenance</h3><div class="data" style="font-size:.75rem;word-break:break-all">renderer md5 '+esc(pv.renderer_md5||'')+hintBtn('info.renderer_md5')+'<br>record script md5 '+esc(pv.script_md5||'—')+'<br>transitions md5 '+esc(pv.transitions_md5||'')+hintBtn('info.transitions_md5')+'<br>plan '+esc(pv.plan||'')+'<br>plan sha256 '+esc(pv.plan_sha256||'')+hintBtn('info.plan_sha256')+'<br>mp4 md5 '+esc(r.md5_mp4||'')+'</div></section>';
 h+='<section><h3>Knobs of this render '+hintBtn('info.knobs')+'</h3><div class="data" style="font-size:.75rem;word-break:break-all">'+esc(JSON.stringify(r.knobs||{}))+'</div>'+((r.generated_layers||[]).length?'<p>'+chip('generated','gen')+' <span class="muted">'+esc(r.generated_layers.map(g=>g.name+': '+g.keyframes.join(', ')).join('; '))+'</span></p>':'')+'</section>';
 return h;}
// ---------------------------------------------------------------- the new-job form: a pair a plan names
// its own form under #flowForms, so the pair's form there survives it, and closeForms() first (critique B, minor 1)
async function dNewJob(){closeForms();let f=$('#dNewForm');
 if(!f){$('#flowForms').insertAdjacentHTML('beforeend','<div id="dNewForm" style="padding:8px 16px 0"><h3 class="formhead">new director job</h3><div class="label muted"><label for="dPair">a fixture pair with a plan</label> '+hintBtn('control.director_pair')+'</div><select id="dPair" data-hint="control.director_pair" style="width:100%"><option value="">loading…</option></select><div id="dPairInfo" class="muted" style="font-size:.75rem;margin-top:4px"></div><div style="margin-top:6px"><button class="btn primary" id="dNewGo" data-hint="control.director_new_job">create</button> <button class="btn ghost" id="dNewCancel" data-hint="control.director_new_job">cancel</button></div><div id="dNewErr" style="color:var(--failed);font-size:.75rem;margin-top:6px"></div></div>');
  f=$('#dNewForm');$('#dNewCancel').onclick=()=>{f.hidden=true;};
  const go=$('#dNewGo');go.onclick=()=>busy(go,async()=>{$('#dNewErr').textContent='';try{const r=await api('/api/jobs',{flow:'director',pair:$('#dPair').value});f.hidden=true;await loadJobs();openJob(r.id);}catch(e){$('#dNewErr').textContent=e.message;}});}
 f.hidden=false;const sel=$('#dPair');sel.focus();if(sel.dataset.loaded)return;
 let pairs=[];try{pairs=await api('/api/pairs');}catch(e){$('#dNewErr').textContent=e.message;return;}
 const ph=p=>p.photos?['A','B'].map(s=>{const x=p.photos[s];return s+' '+x.file+(x.layers?' · '+x.elements+' elements, '+x.mattes+' mattes':' · no layer table');}).join('; '):(p.missing||'photos missing');
 sel.innerHTML=pairs.map(p=>'<option value="'+esc(p.pair)+'">'+esc(p.pair)+' · '+p.plans.length+' plan'+(p.plans.length===1?'':'s')+'</option>').join('');sel.dataset.loaded='1';
 const info=()=>{const p=pairs.find(x=>x.pair===sel.value);$('#dPairInfo').textContent=p?ph(p)+'; plans '+p.plans.join(', '):'';};sel.onchange=info;info();}
const DIR_BODIES={import:dImport,verdict:dVerdict,resolve:dResolve,plan:dPlan,render:dRender,page:dPage,grades:dGrades};
Object.assign(flowEntry('director'),{
 panels:Object.assign(Object.fromEntries(Object.entries(DIR_BODIES).map(([k,f])=>[k,dBody(k,f)])),{skeptic:panelSkeptic}),
 wire:dWire,sources:dSources,candRow:dCandRow,plots:dPlots,measures:dMeasures,newJob:dNewJob,inputsWord:'photos',hosts:['render'],
 inspectorKnobs:dInspector,runKnobs:dRunKnobs,vside:dSide,wireSide:dWireSide,
 graph:{hosts:['render'],cost:{resolve:'A new folder under resolve/; nothing goes stale',render:'A new 480 draft under the tag the render panel holds',verdict:'The verdict folder is replaced'}}});
