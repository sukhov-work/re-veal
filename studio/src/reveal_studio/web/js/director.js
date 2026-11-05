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
function dSt(){const id=S.view.job.id;return DIR[id]||(DIR[id]={ref:null,cid:null,pv:null,loading:null,err:'',set:{},extra:'',sec:3,fps:30,tag:'',full:1920,rlong:1920,ov:{A:{elements:false,disparity:false},B:{elements:false,disparity:false}},op:70,both:true,matte:{A:null,B:null},clips:{},best:{},text:''});}
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
function dRedraw(){const b=$('#dBody');if(!b||!S.view||S.view.job.flow!=='director')return;const fn=DIR_BODIES[b.dataset.stage];if(!fn)return;const fk=focusKey(b);b.innerHTML=fn();dWire();restoreFocus(b,fk);}
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
function dElements(side){const rows=S.view.director.elements[side]||[];const sel=dSt().matte[side];if(!rows.length)return '<div class="muted">no layer table for '+esc(side)+'</div>';
 return '<div class="d-eltable"><h3>'+esc(side)+' · '+rows.length+' elements '+hintBtn('director.elements')+'</h3><div class="d-scroll"><table><tr><th class="num">id</th><th>label</th><th>group</th><th class="num">area</th><th class="num">depth rank</th><th class="num">disparity</th><th>matte</th></tr>'+rows.map(e=>'<tr class="d-el'+(e.id===sel?' sel':'')+'" data-side="'+side+'" data-id="'+esc(e.id)+'" tabindex="0" data-hint="control.director_element" aria-label="'+esc('show the matte of '+side+' element '+e.id)+'"><td class="num">'+esc(e.id)+'</td><td>'+esc(e.label)+'</td><td>'+esc(e.group)+'</td><td class="num">'+esc(e.area_share)+'</td><td class="num">'+esc(e.depth_rank)+'</td><td class="num">'+esc(e.median_disparity)+'</td><td>'+(e.matte?'file':'<span class="muted">hard</span>')+'</td></tr>').join('')+'</table></div></div>';}
function dOverlap(){const o=S.view.director.overlap||[];return '<div class="d-eltable"><h3>Labels in both photos '+hintBtn('director.overlap')+'</h3><div class="d-scroll"><table><tr><th>label</th><th class="num">A</th><th class="num">B</th></tr>'+(o.length?o.map(x=>'<tr><td>'+esc(x.label)+'</td><td class="num">'+esc(x.A)+'</td><td class="num">'+esc(x.B)+'</td></tr>').join(''):'<tr><td colspan="3" class="muted">none</td></tr>')+'</table></div></div>';}
// ---------------------------------------------------------------- Reveal's verdict (the shared branch)
function dVerdict(){const vd=S.view.verdict;let h='<p class="muted">'+esc(stageOf('verdict').what)+' '+hintBtn('director.verdict')+'</p>';
 if(!vd)return h+'<div class="empty">Not run: it is optional, and the inspector runs it.</div>';
 h+='<p>'+chip(vd.state,stateClass(vd.state))+(vd.reason?' <span class="muted">'+esc(vd.reason)+'</span>':'')+'</p>';
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
function dPlan(){const st=dSt();dEnsurePlan(st);let h='<p class="muted">'+esc(stageOf('plan').what)+'</p><div class="d-row">'+dPlanPick(st)+'</div>';
 if(st.err)h+='<div class="msg bad">'+esc(st.err)+'</div>';
 const c=dConcept(st);if(!c)return h+'<div class="empty">'+(st.loading?'Loading the plan…':'No director plan names this pair.')+'</div>';
 const pv=st.pv;
 h+='<p class="muted"><span class="data">'+esc(pv.path)+'</span> · sha256 <span class="data">'+esc(pv.sha256.slice(0,16))+'…</span> · relation '+esc(pv.relation||'—')+' · planner '+esc((pv.planner||{}).model||'—')+hintBtn('director.plan_identity')+'</p>';
 h+='<p class="d-prose"><b>Idea.</b> '+esc(c.idea)+hintBtn('director.idea')+'</p><p class="d-prose muted"><b>Risk.</b> '+esc(c.risk)+hintBtn('director.risk')+'</p>';
 h+=dTimeline(st,c)+dKnobTable(st,c)+dSetTables(st,c);
 const bad=dBadLines(st);
 h+='<h3 style="margin-top:16px">Extra --set lines '+hintBtn('control.director_extra')+'</h3><textarea id="dExtra" data-hint="control.director_extra" rows="3" aria-label="extra --set lines, key=JSON per line" placeholder="pane_becomes_view.matte_grow=0.05">'+esc(st.extra)+'</textarea>'+(bad.length?'<div class="msg bad">not key=JSON: '+esc(bad.join('; '))+'</div>':'');
 h+='<h3 style="margin-top:16px">The next 480 draft '+hintBtn('control.director_command')+'</h3><div class="cmd" id="dCmd">'+esc(dCommand(st,true))+'</div>';
 const lr=c.last_round;
 h+='<div class="d-acts"><button class="btn" id="dLastRound" data-hint="control.director_last_round"'+(lr?'':' disabled')+'>load the last round\'s knobs</button>'+hintBtn('control.director_last_round')+(lr?'<span class="muted">'+esc(lr.from)+': <span class="data">'+esc(JSON.stringify(lr.knobs))+'</span></span>':'<span class="muted">no round render of this plan and concept</span>')+'<button class="btn ghost" id="dClear" data-hint="control.director_clear">clear all knobs</button></div>';
 return h;}
function dBeats(c){const rows=c.beats.map(b=>({name:b.name,key:b.key,base:b.window,by:b.by,end:false,gen:!!((c.transforms.find(t=>t.name===b.name)||{}).keyframes||[]).length}));rows.push({name:'end effect · '+c.end.kind,key:'end_window',base:c.end.window,end:true,gen:false});return rows;}
function dIsSolo(st,c,n){const o=c.beats.filter(b=>b.name!==n);return o.length>0&&o.every(b=>st.set[b.name+'.skip']===true)&&!st.set[n+'.skip'];}
function dTimeline(st,c){const rows=dBeats(c);let h='<h3 style="margin-top:16px">Timeline in clip time '+hintBtn('control.director_timeline')+'</h3>';
 if(c.motion&&c.motion.kind==='continuous')h+='<p class="muted">The motion model is on: the renderer may move a beat earlier to overlap the one before; the resolve lists where.'+hintBtn('director.motion_note')+'</p>';
 h+='<div class="d-tl" id="dTl" role="group" aria-label="the beats in clip time" style="height:'+(rows.length*30+22)+'px">';
 for(let t=0;t<=10;t++)h+='<span class="d-grid" style="left:'+(t*10)+'%"></span><span class="d-tick'+(t===0?' first':(t===10?' last':''))+'" style="left:'+(t*10)+'%">'+(t/10).toFixed(1)+'</span>';
 rows.forEach((r,i)=>{const w=dEff(st,r.key,r.base);const skip=!r.end&&st.set[r.name+'.skip']===true;const ch=dHas(st.set,r.key);
  h+='<button class="d-bar'+(r.end?' end':'')+(skip?' mute':'')+(ch?' changed':'')+(r.gen?' gen':'')+((w[1]-w[0])<0.16?' narrow':'')+'" data-i="'+i+'" data-hint="control.director_timeline" aria-label="'+esc(r.name+': window '+(+w[0]).toFixed(2)+' to '+(+w[1]).toFixed(2)+'; arrows move it, shift with arrows moves its end')+'" style="top:'+(i*30+2)+'px;left:'+(w[0]*100)+'%;width:'+Math.max(0.5,(w[1]-w[0])*100)+'%"><span class="d-bt"><span class="d-bl">'+esc(r.name)+'</span> <span class="data">'+(+w[0]).toFixed(2)+'–'+(+w[1]).toFixed(2)+'</span></span></button>';});
 h+='</div><div class="d-ms">'+c.beats.map(b=>'<span><span class="data">'+esc(b.name)+'</span><label><input type="checkbox" class="dMute" data-name="'+esc(b.name)+'"'+(st.set[b.name+'.skip']===true?' checked':'')+' data-hint="control.director_mute"> mute</label><label><input type="checkbox" class="dSolo" data-name="'+esc(b.name)+'"'+(dIsSolo(st,c,b.name)?' checked':'')+' data-hint="control.director_solo"> solo</label></span>').join('')+'</div>';
 return h;}
function dKnobInput(id,range,val){const isNum=Array.isArray(range)&&range.length===2&&typeof range[0]==='number'&&typeof range[1]==='number';
 if(isNum)return '<input class="dKnob" id="'+id+'" data-hint="control.director_knob" inputmode="decimal" value="'+esc(val)+'" aria-label="knob value">';
 if(Array.isArray(range)&&range.length&&range.every(x=>typeof x==='boolean'))return '<input type="checkbox" class="dKnob" id="'+id+'" data-hint="control.director_knob"'+(val?' checked':'')+' aria-label="knob value">';
 return '<input class="dKnob" id="'+id+'" data-hint="control.director_knob" value="'+esc(JSON.stringify(val))+'" aria-label="knob value as JSON">';}
function dKnobTable(st,c){if(!c.knobs.length)return '<p class="muted">The planner named no knob for this concept.</p>';
 let h='<h3 style="margin-top:16px">The concept\'s knobs, in both name forms '+hintBtn('control.director_knob')+'</h3><table class="d-knobs"><tr><th>plan knob</th><th>--set key</th><th>range</th><th class="num">plan default</th><th>value</th><th>what</th></tr>';
 c.knobs.forEach((k,i)=>{if(k.readonly){h+='<tr class="d-ro"><td class="data">'+esc(k.name)+'</td><td>'+chip('read-only','info','director.readonly')+'</td><td class="data">'+esc(JSON.stringify(k.range))+'</td><td class="num">'+esc(JSON.stringify(k.default))+'</td><td class="muted">'+esc(k.readonly)+'</td><td class="muted">'+esc(k.what)+'</td></tr>';return;}
  const cur=dGet(dEff(st,k.set_key,k.base),k.path);const val=cur===undefined?k.default:cur;const ch=dHas(st.set,k.set_key);
  h+='<tr'+(ch?' class="d-changed"':'')+'><td class="data">'+esc(k.name)+'</td><td class="data">'+esc(k.set_key)+esc(k.path.map(x=>'['+x+']').join(''))+'</td><td class="data">'+esc(JSON.stringify(k.range))+'</td><td class="num">'+esc(JSON.stringify(k.default))+'</td><td>'+dKnobInput('dK'+i,k.range,val)+'</td><td class="muted">'+esc(k.what)+'</td></tr>';});
 return h+'</table>';}
function dSetTables(st,c){let h='<h3 style="margin-top:16px">The renderer\'s --set keys '+hintBtn('control.director_set')+'</h3><p class="muted">A ticked key is sent as --set k=JSON. The default shown is this concept\'s; a faint row\'s condition rules it out for this container.'+hintBtn('director.condition')+'</p>';
 h+=dRows(c.globals,st,'g');
 h+='<details'+(c.container.kind==='disc'?' open':'')+'><summary class="label">the sky keys, read under a disc container ('+c.sky.length+')</summary>'+dRows(c.sky,st,'s')+'</details>';
 c.transforms.forEach((t,ti)=>{h+='<details><summary class="label">'+esc(t.name)+' · '+esc(t.by)+' · '+t.rows.length+' keys'+(t.keyframes.length?' '+chip('generated','gen'):'')+'</summary>'+dRows(t.rows,st,'t'+ti)+'</details>';});
 return h;}
function dSetInput(id,r,v){const a=' id="'+id+'" class="dSetVal" data-set="'+esc(r.set_key)+'" data-type="'+esc(r.type)+'" data-hint="'+esc(r.hint)+'" aria-label="'+esc('value of '+r.set_key)+'"';
 if(r.type==='bool')return '<input type="checkbox"'+a+(v?' checked':'')+'>';
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
function dReadSet(el){const t=el.dataset.type;if(el.type==='checkbox')return el.checked;if(t==='int'||t==='float'){const n=parseFloat(el.value);return isNaN(n)?null:n;}if(t==='str')return el.value;try{return JSON.parse(el.value);}catch(e){return el.value;}}
function dCommand(st,draft){const v=S.view,c=dConcept(st);if(!c||!st.pv)return '';const set=dAllSet(st);const jd=v.job.root.replace(/\/run$/,'');const name=st.pv.stem+'_'+c.id+(st.tag?'-'+st.tag:'');
 const a=['.venv/bin/python','scripts/research/director_render.py',st.pv.path,(draft?jd+'/drafts/':v.job.root+'/')+name+'.part','--concept',c.id,'--max-long',String(draft?480:st.full),'--seconds',dSec(st.sec),'--fps',String(st.fps)];
 Object.keys(set).sort().forEach(k=>a.push('--set',k+'='+pyJson(set[k])));
 a.push('--progress','--layers-dir',v.job.layers_dir||'','--mattes-dir',v.job.mattes_dir||'');
 return a.map(x=>/[\s"']/.test(x)?"'"+x.replace(/'/g,"'\\''")+"'":x).join(' ');}
// ---------------------------------------------------------------- render: the controls over the shared viewer
function dRender(){const v=S.view,st=dSt();dEnsurePlan(st);const keys=Object.keys(dAllSet(st)).sort();
 let h='<div class="d-row">'+dPlanPick(st)+'<label class="label muted" for="dTag">tag</label><input id="dTag" data-hint="control.director_tag" value="'+esc(st.tag)+'" placeholder="v2" style="width:110px"><label class="label muted" for="dSec">seconds</label><input id="dSec" data-hint="control.director_seconds" inputmode="decimal" value="'+esc(st.sec)+'" style="width:64px"><label class="label muted" for="dFps">fps</label><input id="dFps" data-hint="control.director_fps" inputmode="decimal" value="'+esc(st.fps)+'" style="width:56px"><button class="btn primary" id="dDraft" data-hint="control.director_draft">render a 480 draft</button><label class="label muted" for="dFull">full long side</label><input id="dFull" data-hint="control.director_full" inputmode="decimal" value="'+esc(st.full)+'" style="width:72px"><button class="btn" id="dFullGo" data-hint="control.director_full">render full</button>'+hintBtn('control.director_full')+'</div>';
 h+='<p class="muted">'+(keys.length?keys.length+' --set key'+(keys.length>1?'s':'')+' from the plan panel: <span class="data">'+esc(keys.join(', '))+'</span>':'No --set key: the plan as written.')+'</p>'+(S.render&&S.render.record_knobs&&S.render.record_knobs.plan?'<div class="d-acts"><button class="btn" id="dReRender" data-hint="control.rerun">re-render '+esc(S.render.name)+' with its record\'s knobs under the tag</button>'+hintBtn('control.rerun')+'</div>':'');
 if(!v.candidates.length)return h+'<div class="empty">No render yet. Render a 480 draft first; the full renders are the page\'s candidates.</div>';
 return h+'<div id="viewerWrap"><div class="viewer"><div class="framewrap"><div class="frame" id="frameBox"></div></div><div class="vside" id="vside">'+candList()+'</div></div></div>';}
function dRenderKnobs(st,draft){const c=dConcept(st);return {plan:st.ref||dDefaultRef(),concept:c?c.id:'',name:st.tag,draft:draft?480:0,max_long:parseInt(st.full,10)||1920,seconds:parseFloat(st.sec),fps:parseInt(st.fps,10),set:dAllSet(st)};}
async function dPost(stage,knobs,what){const v=S.view;try{const r=await api('/api/jobs/'+dEnc(v.job.id)+'/stages/'+stage+'/run',{knobs});setMsg('started '+r.record+': '+what+runWarnings(r.warnings),'ok');await openJob(v.job.id,true);loadJobs();}catch(e){setMsg(e.message,'bad');}}
// ---------------------------------------------------------------- page and grades
function dPage(){const v=S.view;const full=v.candidates.filter(c=>c.kind==='full');const bad=full.filter(c=>c.unjudged||(c.verdict&&c.verdict.verdict==='NOT READY'));const n=v.rounds.length+1;const pg=stageOf('page');
 let h='<p class="muted">'+esc(pg.what)+' '+hintBtn('control.director_page')+'</p><div class="cols"><div class="box"><h3>Build the page</h3>'+(full.length?'<p class="muted">'+full.length+' full render'+(full.length>1?'s':'')+': <span class="data">'+esc(full.map(c=>c.name).join(', '))+'</span></p>':'<p class="muted">no full render yet</p>')+(bad.length?gateMessage(bad):'');
 const field=(id,label,val)=>'<label class="label muted" for="'+id+'" style="display:block;margin-top:6px">'+label+'</label><input id="'+id+'" data-hint="control.director_page" style="width:100%" value="'+esc(val)+'">';
 h+=field('dpTitle','title',v.job.seq+': round '+n)+field('dpKey','key',v.job.id+'_r'+n)+field('dpHead','head (an HTML file in the repo)','')+field('dpKeyframes','keyframes.json of the generated helpers','');
 h+='<div class="label muted" style="margin-top:8px">per clip: what to look at and the faults to expect (the skeptic\'s answers fill them on the page)</div>'+full.map(c=>'<div class="d-note"><span class="data">'+esc(c.name)+'</span><input class="dpLook" data-name="'+esc(c.name)+'" data-hint="control.director_page" aria-label="'+esc('look at, '+c.name)+'" placeholder="look at"><input class="dpFaults" data-name="'+esc(c.name)+'" data-hint="control.director_page" aria-label="'+esc('faults to expect, '+c.name)+'" placeholder="faults to expect"></div>').join('');
 h+='<div style="margin-top:8px"><label><input type="checkbox" id="dpOverride" data-hint="control.page_override"> override the gate (on his word)</label></div><div style="margin-top:8px"><button class="btn primary" id="dpGo" data-hint="control.director_page"'+(full.length?'':' disabled')+'>build the page</button></div></div>';
 h+='<div>'+(v.page.exists?'<h3>The page</h3><p><a href="'+esc(v.page.url)+'" target="_blank" data-hint="control.director_page">open index.html</a> <span class="data muted">md5 '+esc(v.page.md5)+'</span>'+(pg.previous?' · <a href="'+esc(pg.previous)+'" target="_blank" data-hint="control.director_page">the previous page</a>':'')+'</p><iframe src="'+esc(v.page.url)+'" title="the review page" style="width:100%;height:600px;border:1px solid var(--line);background:#fff"></iframe>':'<p class="muted">no page yet</p>')+'</div></div>';
 return h;}
function dSplit(name){const i=name.lastIndexOf('_');return i<0?{stem:name,ct:''}:{stem:name.slice(0,i),ct:name.slice(i+1)};}
function dClip(st,c){const k=c.kind+'/'+c.name;return st.clips[k]||(st.clips[k]={acceptable:false,note:'',props:{one_picture:false,transforms:false,not_invented:false}});}
function dGrades(){const v=S.view,st=dSt();let h='<p class="muted">'+esc(stageOf('grades').what)+' '+hintBtn('control.director_grade')+'</p>';
 if(!v.rounds.length)return h+'<div class="empty">No round yet: build the page first.</div>';
 const r=v.rounds[v.rounds.length-1];
 if(r.grade)return h+'<div class="box"><h3>Round '+esc(r.n)+' '+chip('graded','ok')+'</h3><p class="muted">saved '+esc(r.grade.at)+' on page md5 '+esc((r.grade.page_md5||'').slice(0,8))+'…'+(r.grade.picks?' · <a href="/api/jobs/'+esc(dEnc(v.job.id))+'/file/'+esc(r.grade.picks)+'" target="_blank" data-hint="control.director_grade">'+esc(r.grade.picks)+'</a>':'')+'</p>'+(r.grade.text?'<blockquote class="d-words">'+esc(r.grade.text)+'</blockquote>':'')+'</div>';
 const cands=v.candidates;const marks=v.owner_frames||[];
 h+='<p class="muted">round '+esc(r.n)+' · page md5 <span class="data">'+esc(r.page_md5)+'</span> · '+cands.length+' clip'+(cands.length===1?'':'s')+'</p>';
 cands.forEach((c,i)=>{const g=dClip(st,c);const fr=marks.filter(o=>o&&o.name===c.name&&o.kind===c.kind).map(o=>o.frame);
  h+='<div class="box d-clip"><h3><span class="data">'+esc(c.name)+'</span> '+(c.kind==='draft'?chip('draft '+c.draft,'info'):'')+'</h3><div class="d-props">'+[['one_picture','one picture'],['transforms','content transforms'],['not_invented','nothing invented']].map(([k,l])=>'<label><input type="checkbox" class="dgProp" data-i="'+i+'" data-prop="'+k+'"'+(g.props[k]?' checked':'')+' data-hint="control.director_grade"> '+l+'</label>').join('')+'<label><input type="checkbox" class="dgOk" data-i="'+i+'"'+(g.acceptable?' checked':'')+' data-hint="control.director_grade"> acceptable as-is</label>'+(fr.length?'<span class="muted">marked frames <span class="data">'+esc(fr.join(', '))+'</span></span>':'')+'</div><textarea class="dgNote" data-i="'+i+'" data-hint="control.director_grade" rows="2" aria-label="'+esc('his note on '+c.name)+'" placeholder="what is wrong, what should happen instead, which knob">'+esc(g.note)+'</textarea></div>';});
 const stems=[...new Set(cands.map(c=>dSplit(c.name).stem))];
 h+=stems.map(s=>'<p><label class="label muted">best for <span class="data">'+esc(s)+'</span> <select class="dgBest" data-stem="'+esc(s)+'" data-hint="control.director_best"><option value="none">none</option>'+cands.filter(c=>dSplit(c.name).stem===s).map(c=>{const ct=dSplit(c.name).ct;return '<option value="'+esc(ct)+'"'+(st.best[s]===ct?' selected':'')+'>'+esc(ct)+(c.kind==='draft'?' (draft)':'')+'</option>';}).join('')+'</select></label>'+hintBtn('control.director_best')+'</p>').join('');
 h+='<div class="label muted">his words, verbatim</div><textarea id="dgText" data-hint="control.director_grade" aria-label="his words for the round">'+esc(st.text)+'</textarea><div style="margin-top:8px"><button class="btn primary" id="dgSave" data-hint="control.director_grade">save the grade</button></div>';
 return h;}
function dPicks(st){const v=S.view;const r=v.rounds[v.rounds.length-1];const clips={};const marks=v.owner_frames||[];
 v.candidates.forEach(c=>{const g=dClip(st,c);const fr=marks.filter(o=>o&&o.name===c.name&&o.kind===c.kind).map(o=>o.frame);const x={acceptable:!!g.acceptable,note:g.note||'',props:{one_picture:!!g.props.one_picture,transforms:!!g.props.transforms,not_invented:!!g.props.not_invented},draft:c.kind==='draft'};if(c.record)x.render=c.record;if(fr.length)x.frames=fr;clips[c.name]=x;});
 const best={};[...new Set(v.candidates.map(c=>dSplit(c.name).stem))].forEach(s=>{best[s]=st.best[s]||'none';});
 return {round:r.n,picks:{date:new Date().toISOString(),page:(stageOf('page').latest_knobs||{}).key||(v.job.id+'_r'+r.n),best,clips},text:st.text};}
// ---------------------------------------------------------------- the wiring of every panel of this file
function dWire(){const v=S.view,st=dSt();const p=$('#panel');
 const pl=$('#dPlan');if(pl)pl.onchange=async()=>{st.ref=pl.value;st.pv=null;st.set={};st.cid=null;try{await dLoadPlan(st,pl.value);}catch(e){st.err=e.message;}dRedraw();};
 const cs=$('#dConcept');if(cs)cs.onchange=()=>{st.cid=cs.value;st.set={};dRedraw();};
 // import
 p.querySelectorAll('.dOv').forEach(b=>b.onchange=()=>{const sides=st.both?['A','B']:[b.dataset.side];sides.forEach(s=>{st.ov[s][b.dataset.kind]=b.checked;});dRedraw();});
 const bo=$('#dBoth');if(bo)bo.onchange=()=>{st.both=bo.checked;};
 const op=$('#dOp');if(op)op.oninput=()=>{st.op=+op.value;p.querySelectorAll('.d-stack img.ov').forEach(i=>{i.style.opacity=String(st.op/100);});};
 p.querySelectorAll('.d-el').forEach(tr=>{const go=()=>{const s=tr.dataset.side,id=+tr.dataset.id;st.matte[s]=st.matte[s]===id?null:id;dRedraw();};tr.onclick=go;tr.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();go();}};});
 // resolve
 const rl=$('#dRLong');if(rl)rl.onchange=()=>{st.rlong=parseInt(rl.value,10);};
 const rg=$('#dResolveGo');if(rg)rg.onclick=()=>{const c=dConcept(st);if(!c){setMsg('choose a plan first','bad');return;}dPost('resolve',{plan:st.ref||dDefaultRef(),concept:c.id,max_long:st.rlong,set:dAllSet(st)},'the resolve of '+st.pv.stem+' '+c.id);};
 // plan
 const c=dConcept(st);
 p.querySelectorAll('.d-bar').forEach(b=>{b.onpointerdown=dDragStart;b.onkeydown=e=>dBarKey(e,b);});
 p.querySelectorAll('.dMute').forEach(b=>b.onchange=()=>{const k=b.dataset.name+'.skip';if(b.checked)st.set[k]=true;else delete st.set[k];dRedraw();});
 p.querySelectorAll('.dSolo').forEach(b=>b.onchange=()=>{c.beats.forEach(x=>{if(b.checked&&x.name!==b.dataset.name)st.set[x.name+'.skip']=true;else delete st.set[x.name+'.skip'];});dRedraw();});
 p.querySelectorAll('.dKnob').forEach(el=>el.onchange=()=>{const k=c.knobs[+el.id.slice(2)];let x;if(el.type==='checkbox')x=el.checked;else if(el.getAttribute('inputmode')==='decimal'){x=parseFloat(el.value);if(isNaN(x))x=k.default;}else{try{x=JSON.parse(el.value);}catch(e){x=el.value;}}dSetKey(st,k.set_key,k.base,dSetPath(dEff(st,k.set_key,k.base),k.path,x));dRedraw();});
 p.querySelectorAll('.dSetOn').forEach(el=>el.onchange=()=>{const key=el.dataset.set;if(!el.checked){delete st.set[key];}else{const val=$('#'+el.dataset.row);const x=val?dReadSet(val):null;st.set[key]=x;}dRedraw();});
 p.querySelectorAll('.dSetVal').forEach(el=>el.onchange=()=>{st.set[el.dataset.set]=dReadSet(el);dRedraw();});
 const ex=$('#dExtra');if(ex){ex.oninput=()=>{st.extra=ex.value;const cm=$('#dCmd');if(cm)cm.textContent=dCommand(st,true);};ex.onchange=()=>dRedraw();}
 const lr=$('#dLastRound');if(lr)lr.onclick=()=>{const l=c&&c.last_round;if(!l)return;Object.entries(l.knobs||{}).forEach(([k,x])=>{st.set[k]=x;});setMsg('loaded '+Object.keys(l.knobs||{}).length+' knobs from '+l.from,'ok');dRedraw();};
 const cl=$('#dClear');if(cl)cl.onclick=()=>{st.set={};st.extra='';dRedraw();};
 // render
 [['dTag','tag'],['dSec','sec'],['dFps','fps'],['dFull','full']].forEach(([id,k])=>{const el=$('#'+id);if(el)el.oninput=()=>{st[k]=el.value;};});
 const dr=$('#dDraft');if(dr)dr.onclick=()=>dPost('render',dRenderKnobs(st,true),'a 480 draft');
 const fg=$('#dFullGo');if(fg)fg.onclick=()=>dPost('render',dRenderKnobs(st,false),'the full render');
 const rr=$('#dReRender');if(rr)rr.onclick=()=>{const k=dClone(S.render.record_knobs);k.name=st.tag;dPost('render',k,'a re-render of '+S.render.name+' under the tag '+(st.tag||'(none)'));};
 if(S.stage==='render'){wireCands(p);if(!S.vw.render)S.vw.render={cmp:'single',a:'frame',b:'last',wipe:50,onion:50,ab:'A'};if(!S.cand&&v.candidates.length){const c2=v.candidates.slice().sort((a,b)=>a.mtime<b.mtime?1:-1)[0];selectCand(c2.kind,c2.name);}else if(S.cand)loadRender();}
 // skeptic (the loop's panel and its request button)
 const sk=$('#skGo');if(sk)sk.onclick=async()=>{const names=[...document.querySelectorAll('.skc:checked')].map(x=>x.value);try{const r=await api('/api/jobs/'+dEnc(v.job.id)+'/requests/skeptic',{brief:$('#skBrief').value,candidates:names});setMsg('written '+r.file+'; the session lists it with reveal-studio requests','ok');await openJob(v.job.id,true);loadJobs();}catch(e){setMsg(e.message,'bad');}};
 // page
 const pg=$('#dpGo');if(pg)pg.onclick=async()=>{const notes={};p.querySelectorAll('.dpLook,.dpFaults').forEach(i=>{const x=i.value.trim();if(!x)return;const n=notes[i.dataset.name]||(notes[i.dataset.name]={});n[i.classList.contains('dpLook')?'look':'faults']=x;});pg.textContent='working…';pg.disabled=true;
  try{const r=await api('/api/jobs/'+dEnc(v.job.id)+'/page',{title:$('#dpTitle').value,key:$('#dpKey').value,head:$('#dpHead').value,keyframes:$('#dpKeyframes').value,notes,override:$('#dpOverride').checked});setMsg('building the page: record '+r.record+(r.override?' · '+r.override:''),'ok');await openJob(v.job.id,true);}catch(e){setMsg(e.message,'bad');pg.textContent='build the page';pg.disabled=false;}};
 // grades
 p.querySelectorAll('.dgProp').forEach(b=>b.onchange=()=>{dClip(st,v.candidates[+b.dataset.i]).props[b.dataset.prop]=b.checked;});
 p.querySelectorAll('.dgOk').forEach(b=>b.onchange=()=>{dClip(st,v.candidates[+b.dataset.i]).acceptable=b.checked;});
 p.querySelectorAll('.dgNote').forEach(b=>b.oninput=()=>{dClip(st,v.candidates[+b.dataset.i]).note=b.value;});
 p.querySelectorAll('.dgBest').forEach(b=>b.onchange=()=>{st.best[b.dataset.stem]=b.value;});
 const gt=$('#dgText');if(gt)gt.oninput=()=>{st.text=gt.value;};
 const gs=$('#dgSave');if(gs)gs.onclick=async()=>{try{await api('/api/jobs/'+dEnc(v.job.id)+'/picks',dPicks(st));setMsg('round graded: the picks file saved, his words verbatim beside it','ok');await openJob(v.job.id,true);loadJobs();}catch(e){setMsg(e.message,'bad');}};}
// the timeline's drag: the middle moves the window, within 6 px of an end resizes it; rounded to 0.01, at least 0.02
// wide, inside 0 to 1 (director_ui.py:1042-1059); on release the window becomes <name>.window or end_window
let dDrag=null;
function dDragStart(e){const b=e.currentTarget;const st=dSt(),c=dConcept(st);if(!c)return;const r=dBeats(c)[+b.dataset.i];const w=dEff(st,r.key,r.base).map(Number);const rect=b.getBoundingClientRect();const x=e.clientX-rect.left;
 dDrag={r,w0:w,x0:e.clientX,W:$('#dTl').getBoundingClientRect().width,mode:x<6?'l':(x>rect.width-6?'r':'m'),el:b,cur:null};b.setPointerCapture(e.pointerId);b.onpointermove=dDragMove;b.onpointerup=dDragEnd;e.preventDefault();}
function dClampWin(mode,w0,dx){let [a,b]=w0;const len=b-a;if(mode==='m'){a=Math.min(Math.max(0,a+dx),1-len);b=a+len;}else if(mode==='l'){a=Math.min(Math.max(0,a+dx),b-D_MIN_W);}else{b=Math.max(Math.min(1,b+dx),a+D_MIN_W);}return [Math.round(a*100)/100,Math.round(b*100)/100];}
function dDragMove(e){if(!dDrag)return;const w=dClampWin(dDrag.mode,dDrag.w0,(e.clientX-dDrag.x0)/dDrag.W);dDrag.cur=w;dDrag.el.style.left=(w[0]*100)+'%';dDrag.el.style.width=((w[1]-w[0])*100)+'%';dDrag.el.querySelector('.data').textContent=w[0].toFixed(2)+'–'+w[1].toFixed(2);}
function dDragEnd(){if(!dDrag)return;const d=dDrag;dDrag=null;if(d.cur)dSetKey(dSt(),d.r.key,d.r.base,d.cur);dRedraw();}
// the keyboard: the arrows move a bar by 0.01, shift with the arrows moves its end
function dBarKey(e,b){if(e.key!=='ArrowLeft'&&e.key!=='ArrowRight')return;e.preventDefault();e.stopPropagation();const st=dSt(),c=dConcept(st);const r=dBeats(c)[+b.dataset.i];const w=dEff(st,r.key,r.base).map(Number);const dx=e.key==='ArrowLeft'?-0.01:0.01;dSetKey(st,r.key,r.base,dClampWin(e.shiftKey?'r':'m',w,dx));S.dFocusBar=+b.dataset.i;dRedraw();const nb=$('#dTl .d-bar[data-i="'+S.dFocusBar+'"]');if(nb)focusQuiet(nb);}
// ---------------------------------------------------------------- the viewer's entries for a director render
function dSources(){const v=S.view,out=[];if(!v)return out;const r=S.render;
 if(r&&vhost()==='render'){const n=r.frames_available||r.frames||0;const t=(r.frames_tags||[])[S.frame]||{};out.push({id:'frame',label:'frame f '+S.frame+' of '+candLabel(r),url:r.frame_url+S.frame,gen:!!t.generated});if(n){out.push({id:'first',label:'frame 0: A exactly',url:r.frame_url+0});out.push({id:'last',label:'frame '+(n-1)+': B exactly',url:r.frame_url+(n-1)});}}
 const rv=v.resolve;if(rv){out.push({id:'canvasA',label:'canvas_A.png of the resolve',url:rv.urls.canvas_A});out.push({id:'canvasB',label:'canvas_B.png of the resolve',url:rv.urls.canvas_B});}
 if(S.shown)out.push({id:'shown',label:'shown: '+S.shown.label,url:S.shown.url});
 return out;}
function dCandRow(c){const sel=!!(S.cand&&S.cand.kind===c.kind&&S.cand.name===c.name);
 return '<button class="cand" data-kind="'+c.kind+'" data-name="'+esc(c.name)+'" data-hint="control.candidate" aria-selected="'+sel+'"><span class="nm"><span class="label">'+esc(c.name)+'</span>'+(c.kind==='draft'?chip('draft '+c.draft,'info'):(c.unjudged?chip('unjudged','info'):chip(c.verdict.verdict,c.verdict.verdict==='NOT READY'?'bad':'ok')))+'</span><span class="dt">'+esc(c.frames)+' f · '+esc(c.seconds)+' s · motion '+esc(c.motion_median_px!=null?c.motion_median_px:'—')+' px · B first f '+esc(c.b_inside_first!=null?c.b_inside_first:'—')+' · '+esc((c.md5_mp4||'').slice(0,8))+'</span></button>';}
// one plot on the shared axis: the points at their own frame index (a pairwise series between frame j and j + 1)
function dPlot(title,pts,o){const W=plotW(),H=104,x0=40,x1=W-10,y0=16,y1=H-20;const r=S.render;const n=r.frames_available||r.frames||1;
 const vals=pts.map(p=>p[1]);const maxv=Math.max(o.bar?o.bar*1.25:0,...vals,1e-9);const yOf=v=>y1-(v/maxv)*(y1-y0);const xp=p=>xOf(o.pairwise?p[0]+0.5:p[0]);
 let s='<svg viewBox="0 0 '+W+' '+(H+18)+'" width="'+W+'" height="'+(H+18)+'" style="width:100%;height:auto;margin-top:8px" aria-label="'+esc(title)+'"><line x1="'+x0+'" y1="'+y1+'" x2="'+x1+'" y2="'+y1+'" stroke="'+LINE+'"/><line x1="'+x0+'" y1="'+y0+'" x2="'+x0+'" y2="'+y1+'" stroke="'+LINE+'"/>';
 [0,maxv/2,maxv].forEach(v=>{s+=svgText(x0-4,yOf(v)+4,o.fmt(v),{anchor:'end',mono:true});});
 s+=svgText(x0+4,y0-4,title,{fill:TEXT});
 (o.bands||[]).forEach(i=>{const xa=xOf(i),xb=xOf(i+1);s+='<rect x="'+xa.toFixed(1)+'" y="'+y0+'" width="'+Math.max(1,xb-xa).toFixed(1)+'" height="'+(y1-y0)+'" fill="'+FAILED+'" opacity=".22"><title>'+esc(o.bandTitle||'')+' '+i+'</title></rect>';});
 (o.ticks||[]).forEach(i=>{const x=xOf(i+0.5).toFixed(1);s+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+(y1+8)+'" stroke="'+FAILED+'" stroke-width="2"><title>'+esc(o.tickTitle||'')+' '+i+'</title></line>';});
 if(o.bar!=null){const y=yOf(o.bar).toFixed(1);s+='<line x1="'+x0+'" y1="'+y+'" x2="'+x1+'" y2="'+y+'" stroke="'+FAILED+'" stroke-dasharray="4 4"/>'+svgText(x1,+y-3,o.barText,{anchor:'end',fill:FAILED});}
 (o.marks||[]).forEach(m=>{const x=xOf(m.at).toFixed(1);s+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+y1+'" stroke="'+m.col+'" stroke-width="1.5" stroke-dasharray="'+(m.dash||'')+'"><title>'+esc(m.title)+'</title></line>'+svgText(+x+3,y0+10,m.label,{fill:m.col});});
 (r.frames_tags||[]).forEach(t=>{if(t.generated){const xa=xOf(t.i-0.5),xb=xOf(t.i+0.5);s+='<rect x="'+xa.toFixed(1)+'" y="'+(y1+3)+'" width="'+(xb-xa).toFixed(1)+'" height="5" fill="'+GEN+'" opacity=".8"/>';}});
 (r.owner_frames||[]).forEach(f=>{const x=xOf(f.frame).toFixed(1);s+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+y1+'" stroke="'+FAILED+'" opacity=".7"><title>marked: '+esc(f.note||'')+'</title></line>';});
 if(pts.length)s+='<polyline points="'+pts.map(p=>xp(p).toFixed(1)+','+yOf(p[1]).toFixed(1)).join(' ')+'" fill="none" stroke="'+TEXT+'" stroke-width="1.5"/>';
 s+='<line class="cursor" x1="'+xOf(S.frame)+'" y1="'+y0+'" x2="'+xOf(S.frame)+'" y2="'+(y1+8)+'" stroke="'+AMBER+'" stroke-width="1.5"/>';
 for(let i=0;i<n;i+=Math.max(1,Math.round(n/18)))s+=svgText(xOf(i),H+14,String(i),{anchor:'middle',fill:FAINT,mono:true});
 return s+'</svg>';}
function dPlots(){const r=S.render;const p=$('#plots');if(!r||!p||!r.series)return;const s=r.series;const px=v=>v.toFixed(1)+' px',lv=v=>v.toFixed(1),pc=v=>(v*100).toFixed(2)+' %';
 const beats=(r.frames_tags||[]).find(t=>t.beats&&t.beats.length);const first=r.series.b_inside.first;
 let h=dPlot('motion_px: the mean flow between frames, px; pauses (band) and jumps (tick) by the renderer\'s rule',s.motion_px.points,{pairwise:true,fmt:px,bands:s.motion_px.pauses,bandTitle:'pause at entry',ticks:s.motion_px.jumps.map(j=>j-0.5),tickTitle:'jump at entry'});
 h+=dPlot('steps decoded from the mp4: the mean absolute difference between frames, levels',s.steps.points,{pairwise:true,fmt:lv});
 h+=dPlot('b_inside: the share of A\'s region where B shows',s.b_inside.points,{fmt:pc,marks:[first!=null?{at:first,col:FAILED,label:'first above 1 %: f '+first,title:'b_inside_first'}:null,beats?{at:beats.i,col:MUTED,dash:'3 3',label:'first beat',title:'the first frame of a beat'}:null].filter(Boolean)});
 h+=dPlot('residual_edges: edges in neither photo, share of pixels',s.residual_edges.points,{fmt:pc,bar:s.residual_edges.bar,barText:'0.2 % bar (rule 5)'});
 if(s.halo)h+=dPlot('halo: the largest step round the luminary, levels',s.halo.points.map(q=>[q[0],q[1]]),{fmt:lv});
 h+='<p class="muted label" style="margin:4px 0 0 40px">generated frames (violet) · the frames a keyframe chain draws carry model-made pixels '+hintBtn('info.steps_decoded')+hintBtn('info.motion_px')+hintBtn('info.b_inside')+hintBtn('info.residual_edges')+'</p>';
 p.innerHTML=h;p.querySelectorAll('svg').forEach(svg=>svg.onclick=e=>{const rect=svg.getBoundingClientRect();const W=plotW();const x=(e.clientX-rect.left)/rect.width*W;const n=r.frames_available||r.frames||1;const i=Math.round((x-40)/(W-50)*(n-1));S.frame=Math.max(0,Math.min(n-1,i));showFrame();});}
function dShare(x){return x==null?'—':(+x).toString()+' ('+(100*x).toFixed(2)+' %)';}
function dMeasures(r){const ms=r.measures||[];const pv=r.provenance||{};
 let h='<section><h3>Measures '+hintBtn('info.residual_edge_max')+'</h3><table style="width:100%">'+ms.map(m=>{const list=Array.isArray(m.value);const val=list?(m.value.length?m.value.map(x=>typeof x==='object'?x.name+': '+x.why:x).join(', '):'none'):(m.value==null?'—':(/share/.test(m.unit)?dShare(m.value):m.value));const unit=list||m.value==null||/share/.test(m.unit)?'':m.unit;
  const verdict=m.bar&&m.past!=null?(m.past?chip('past bar','bad'):chip('within','ok')):'';
  return '<tr><td>'+esc(m.key)+hintBtn(m.hint)+'</td><td class="num">'+esc(val)+(unit?'<span class="unit">'+esc(unit)+'</span>':'')+'</td><td>'+verdict+(m.bar?'<div class="muted" style="font-size:.75rem">'+esc(m.bar.text)+'</div>':'')+'</td></tr>';}).join('')+'</table></section>';
 h+='<section><h3>Provenance</h3><div class="data" style="font-size:.75rem;word-break:break-all">renderer md5 '+esc(pv.renderer_md5||'')+hintBtn('info.renderer_md5')+'<br>record script md5 '+esc(pv.script_md5||'—')+'<br>transitions md5 '+esc(pv.transitions_md5||'')+hintBtn('info.transitions_md5')+'<br>plan '+esc(pv.plan||'')+'<br>plan sha256 '+esc(pv.plan_sha256||'')+hintBtn('info.plan_sha256')+'<br>mp4 md5 '+esc(r.md5_mp4||'')+'</div></section>';
 h+='<section><h3>Knobs of this render '+hintBtn('info.knobs')+'</h3><div class="data" style="font-size:.75rem;word-break:break-all">'+esc(JSON.stringify(r.knobs||{}))+'</div>'+((r.generated_layers||[]).length?'<p>'+chip('generated','gen')+' <span class="muted">'+esc(r.generated_layers.map(g=>g.name+': '+g.keyframes.join(', ')).join('; '))+'</span></p>':'')+'</section>';
 return h;}
// ---------------------------------------------------------------- the new-job form: a pair a plan names
async function dNewJob(){const box=$('#flowForms');$('#newForm').style.display='none';$('#adoptForm').style.display='none';
 box.innerHTML='<div id="dNewForm" style="padding:8px 16px 0"><div class="label muted"><label for="dPair">a fixture pair with a plan</label> '+hintBtn('control.director_pair')+'</div><select id="dPair" data-hint="control.director_pair" style="width:100%"><option value="">loading…</option></select><div id="dPairInfo" class="muted" style="font-size:.75rem;margin-top:4px"></div><div style="margin-top:6px"><button class="btn primary" id="dNewGo" data-hint="control.director_new_job">create</button> <button class="btn ghost" id="dNewCancel" data-hint="control.director_new_job">cancel</button></div><div id="dNewErr" style="color:var(--failed);font-size:.75rem;margin-top:6px"></div></div>';
 $('#dNewCancel').onclick=()=>{box.innerHTML='';};
 let pairs=[];try{pairs=await api('/api/pairs');}catch(e){$('#dNewErr').textContent=e.message;return;}
 const ph=p=>p.photos?['A','B'].map(s=>{const x=p.photos[s];return s+' '+x.file+(x.layers?' · '+x.elements+' elements, '+x.mattes+' mattes':' · no layer table');}).join('; '):(p.missing||'photos missing');
 const sel=$('#dPair');sel.innerHTML=pairs.map(p=>'<option value="'+esc(p.pair)+'">'+esc(p.pair)+' · '+p.plans.length+' plan'+(p.plans.length===1?'':'s')+'</option>').join('');
 const info=()=>{const p=pairs.find(x=>x.pair===sel.value);$('#dPairInfo').textContent=p?ph(p)+'; plans '+p.plans.join(', '):'';};sel.onchange=info;info();sel.focus();
 $('#dNewGo').onclick=async()=>{$('#dNewErr').textContent='';try{const r=await api('/api/jobs',{flow:'director',pair:sel.value});box.innerHTML='';await loadJobs();openJob(r.id);}catch(e){$('#dNewErr').textContent=e.message;}};}
const DIR_BODIES={import:dImport,verdict:dVerdict,resolve:dResolve,plan:dPlan,render:dRender,page:dPage,grades:dGrades};
Object.assign(flowEntry('director'),{
 panels:Object.assign(Object.fromEntries(Object.entries(DIR_BODIES).map(([k,f])=>[k,dBody(k,f)])),{skeptic:panelSkeptic}),
 wire:dWire,sources:dSources,candRow:dCandRow,plots:dPlots,measures:dMeasures,newJob:dNewJob,inputsWord:'photos',hosts:['render'],
 graph:{hosts:['render'],cost:{resolve:'A new folder under resolve/; nothing goes stale',render:'A new render under the tag the inspector holds',verdict:'The verdict folder is replaced'}}});
