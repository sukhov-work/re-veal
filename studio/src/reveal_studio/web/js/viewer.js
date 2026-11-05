// viewer.js: the viewer: one picture under judgement with the comparator over two sources A and B (single, wipe,
// A/B, onion skin, difference, each at fit, 1:1 and 2x), the shared frame axis (the step series with its stalls and
// jumps, one stability plot per measured window), the measure control, playback and mark. The registration,
// readers, probe, render and measure panels host it; the render and measure panels add the axis and a side column
// (the render's name and chip, the modes, the sources, the list of renders, the first and last stills) beside the
// frame, so the frame takes the height the window leaves between the strip and the axis (critique A2, P1).
'use strict';
Object.assign(S,{vw:{},shown:null,measureWin:'',measureRef:'0'});
// the stages whose panel holds the viewer: the flow's hosts
function viewerHosts(){return flowUI().hosts||[];}
const CMP_MODES=[['single','single','control.cmp_single'],['wipe','wipe','control.cmp_wipe'],['ab','A/B','control.cmp_ab'],['onion','onion','control.cmp_onion'],['diff','difference','control.cmp_diff']];
const ZOOMS=[['fit','fit','control.zoom_fit'],['1:1','1:1','control.zoom_1to1'],['2x','2×','control.zoom_2x']];
const DIFF_STRETCH=4;
// the viewer's state per host: the compare mode, the sources, the split, the opacity, the side A/B shows
function vhost(){return S.stage==='measure'?'render':S.stage;}
function vstate(){const h=vhost();return S.vw[h]||(S.vw[h]=h==='render'?{cmp:'single',a:'frame',b:'k0',wipe:50,onion:50,ab:'A'}:{cmp:'single',a:'k0',b:'k1',wipe:50,onion:50,ab:'A'});}
function sources(){const f=flowUI().sources;return f?f():[];}
function loopSources(){const v=S.view,out=[];if(!v)return out;const base='/api/jobs/'+encodeURIComponent(v.job.id)+'/file/in/'+encodeURIComponent(v.job.seq)+'/';
 if(S.render&&vhost()==='render'){const t=S.render.frames_tags[S.frame]||{};out.push({id:'frame',label:'frame f '+S.frame+' of '+candLabel(S.render),url:S.render.frame_url+S.frame,gen:!!t.generated});}
 for(let i=0;i<(v.prep?v.prep.n:0);i++)out.push({id:'k'+i,label:'k'+i+'.png, the registered still '+i,url:base+'k'+i+'.png'});
 if(v.prep&&v.prep.windows_jpg)out.push({id:'windows',label:'windows.jpg',url:v.prep.windows_jpg});
 if(S.shown)out.push({id:'shown',label:'shown: '+S.shown.label,url:S.shown.url});
 return out;}
function srcOf(id){const all=sources();return all.find(s=>s.id===id)||all[0]||null;}
function showInViewer(url,label){const st=vstate();const hit=sources().find(s=>s.url===url);if(hit)st.a=hit.id;else{S.shown={url,label};st.a='shown';}st.cmp='single';renderViewer();const w=$('#viewerWrap');if(w)w.scrollIntoView({block:'nearest'});}
function panelMeasure(){return '<p class="muted">'+esc(stageOf('measure').what)+' '+hintBtn('control.measure')+'</p><p class="muted">The stability plots sit under the step series of the render chosen here; the inspector runs a measure on the render its knob names.</p>'+panelRender();}
// the render and its frames
async function selectCand(kind,name){S.cand={kind,name};S.frame=0;stopPlay();document.querySelectorAll('.cand').forEach(b=>b.setAttribute('aria-selected',b.dataset.kind===kind&&b.dataset.name===name));await loadRender();}
// An answer whose job or render changed while it was out is dropped (the phase B drive's defect 1: a director job's
// panel drew a pair render's 404 and the loop's md5 after a switch).
async function loadRender(){if(!S.cand)return;const c=S.cand,jid=S.view.job.id;let r;try{r=await api('/api/jobs/'+encodeURIComponent(jid)+'/render/'+c.kind+'/'+encodeURIComponent(c.name));}catch(e){if(S.cand===c&&S.jid===jid)setMsg(e.message,'bad');return;}
 if(S.cand!==c||S.jid!==jid||!S.view||S.view.job.id!==jid)return;S.render=r;renderViewer();syncInspector();}
// The inspector draws the render's measures, stability and plan from S.render, which loadRender fetches after the
// panel and the inspector are drawn: a fetch that brings another render or other measures redraws the inspector,
// unless a field there holds the focus (T97: the Stability section came only after a second click on the render).
function inspectorSig(){const r=S.render;return JSON.stringify([S.stage,r?[r.kind,r.name,r.md5_mp4,(r.measures||[]).map(m=>m.record||m.folder),r.stability?(r.stability.record||r.stability.folder):null]:null]);}
function syncInspector(){if((S.stage==='render'||S.stage==='measure')&&inspectorSig()!==S.insSig&&!typing($('#inspector')))renderInspector();}
function seg(items,cur,attr,label){return '<div class="seg" role="group" aria-label="'+esc(label)+'">'+items.map(([k,t,hk])=>'<button '+attr+'="'+esc(k)+'" aria-pressed="'+(cur===k)+'" data-hint="'+esc(hk)+'">'+esc(t)+'</button>').join('')+'</div>';}
function srcSelect(id,cur,hk,side){return '<label class="srcpick '+side+'"><span class="label">'+side.toUpperCase()+'</span><select id="'+id+'" data-hint="'+esc(hk)+'" aria-label="source '+side.toUpperCase()+'">'+sources().map(s=>'<option value="'+esc(s.id)+'"'+(s.id===cur?' selected':'')+'>'+esc(s.label)+'</option>').join('')+'</select></label>';}
function renderViewer(){const w=$('#viewerWrap');if(!w||!S.view||!viewerHosts().includes(S.stage))return;const host=vhost(),st=vstate(),r=S.render,v=S.view;
 if(host==='render'&&!r)return;
 if(!sources().length){w.innerHTML='';return;}
 const fk=focusKey(w);const axis=host==='render';const n=axis?(r.frames_available||r.frames||0):0;
 const modes='<div class="vmodes">'+seg(ZOOMS,S.mode,'data-mode','zoom')+(axis?'<a class="btn ghost" href="'+esc(r.mp4_url)+'" target="_blank" data-hint="control.mp4">mp4</a>':'')+seg(CMP_MODES,st.cmp,'data-cmp','compare')+'</div>';
 let ctl='<div class="cmpctl">'+srcSelect('srcA',st.a,'control.cmp_a','a')+srcSelect('srcB',st.b,'control.cmp_b','b');
 if(st.cmp==='ab')ctl+='<span class="cmpmode"><button class="btn" id="abFlip" aria-pressed="'+(st.ab==='B')+'" data-hint="control.cmp_ab_flip">showing '+st.ab+'</button><span class="muted label"><span class="kbd">a</span> flips</span></span>';
 if(st.cmp==='onion')ctl+='<span class="cmpmode"><label class="label muted">B opacity <input type="range" id="onionAlpha" min="0" max="100" step="1" value="'+st.onion+'" data-hint="control.onion_opacity" aria-label="B opacity over A"></label><span class="data" id="onionVal">'+st.onion+' %</span></span>';
 if(st.cmp==='wipe')ctl+='<span class="cmpmode"><span class="muted label">drag on the picture, or focus the handle and press <span class="kbd">←</span><span class="kbd">→</span> (shift ten)</span><span class="data" id="wipeVal">'+Math.round(st.wipe)+' %</span></span>';
 if(st.cmp==='diff')ctl+='<span class="cmpmode"><span class="data">|A − B| × '+DIFF_STRETCH+'</span><span class="muted label">black is equal; B resampled to A\'s size</span></span>';
 ctl+='</div>';
 // the tag sits over the box's corner outside the scrolling box, so 1:1 and 2× keep it on screen (critique A2, P2 6)
 const frame='<div class="framewrap"><div class="tag" id="frameTag"></div><div class="frame" id="frameBox"><div class="cmpstack" id="cmpStack"><img id="frameImg" class="base" alt="A"><img id="cmpOver" class="over" alt="B"><canvas id="cmpDiff" class="over"></canvas><span class="side a" id="sideA">A</span><span class="side b" id="sideB">B</span><div class="seam" id="wipeSeam"></div><div class="wipehandle" id="wipeHandle" role="slider" tabindex="0" aria-label="the split between A and B" aria-valuemin="0" aria-valuemax="100" aria-valuenow="'+Math.round(st.wipe)+'" data-hint="control.wipe_handle"></div></div></div></div>';
 let h;
 if(axis){const last=Math.max(0,(v.prep?v.prep.n:1)-1);
  h='<div class="viewer">'+frame+'<div class="vside" id="vside"><div class="vtitle"><h3>'+esc(candLabel(r))+hintBtn('region.viewer')+'</h3>'+(r.kind==='draft'?chip('draft '+r.draft,'info'):(r.unjudged?chip('unjudged','info'):chip(r.verdict.verdict,r.verdict.verdict==='NOT READY'?'bad':'ok')))+'</div>'+(r.title?'<p class="muted vsub" title="'+esc(r.title)+'">'+esc(r.title)+'</p>':'')+modes+ctl+candList()+(flowUI().vside?flowUI().vside():'')
   +'<div class="refs">'+(v.prep?'<figure class="a"><img src="/api/jobs/'+esc(v.job.id)+'/thumb/still/0" alt="the first still"><figcaption>k0 · the first still</figcaption></figure><figure class="b"><img src="/api/jobs/'+esc(v.job.id)+'/thumb/still/'+last+'" alt="the last still"><figcaption>k'+last+' · the last still</figcaption></figure>':'')+'<div class="keys muted"><span class="kbd">space</span> play · <span class="kbd">←</span><span class="kbd">→</span> one frame · <span class="kbd">shift</span> ten · <span class="kbd">m</span> mark a fault</div></div></div></div>';
  h+='<div class="axis"><div class="ctl"><button class="btn" id="play" data-hint="control.play">'+(S.playing?'pause':'play')+'</button><span class="data" id="frameNo"></span><span class="muted label">of '+n+' · '+esc(r.fps||25)+' fps '+hintBtn('region.axis')+'</span><input id="markText" data-hint="control.mark_frame" placeholder="what you see at this frame" style="width:260px" aria-label="note for the marked frame"><button class="btn ghost" id="markBtn" data-hint="control.mark_frame">mark this frame as a fault</button>'+hintBtn('control.mark_frame')+'<span class="muted" id="markNote"></span></div><input type="range" id="scrub" data-hint="control.scrub" min="0" max="'+Math.max(0,n-1)+'" value="'+S.frame+'" step="1" aria-label="frame"><div id="plots"></div>'+(stageOf('measure')?measureCtl(r):'')+'</div>';}
 else h='<div class="head vhead"><h3>Viewer'+hintBtn('region.viewer')+'</h3>'+modes+ctl+'</div><div class="viewer solo">'+frame+'</div>';
 w.innerHTML=h;if(axis)plots();
 if(axis&&flowUI().wireSide)flowUI().wireSide(w);
 sizeFrame();wireViewer();if(axis){$('#play').onclick=togglePlay;$('#scrub').oninput=e=>{S.frame=+e.target.value;showFrame();};$('#markBtn').onclick=markFrame;}
 showFrame();
 // the focus back on the same control (a zoom or compare button after Enter: critique A2, P2 2), or on the panel's
 // element that the panel's rebuild could not find before the render was fetched
 if(!restoreFocus(w,fk)&&S.focusLater){const fl=S.focusLater;S.focusLater=null;if(Date.now()<fl.until&&document.activeElement===document.body)restoreFocus($('#panel'),fl.k);}}
function measureCtl(r){const runs=r.measures||[];let h='<div class="measurectl"><span class="label">measure this render '+hintBtn('control.measure')+'</span><input id="mWin" data-hint="control.measure" value="'+esc(S.measureWin)+'" placeholder="name:x0,y0,x1,y1;… in px of the mp4 ('+esc((r.canvas||[]).join('×'))+')" aria-label="windows in px of the mp4"><label class="label muted">ref <input id="mRef" data-hint="control.measure" value="'+esc(S.measureRef)+'" inputmode="decimal" aria-label="the frame the windows are read from"></label><button class="btn" id="mGo" data-hint="control.measure">measure</button><span class="muted" id="mNote"></span></div>';
 if(runs.length)h+='<table class="runs"><tr><th>run '+hintBtn('measure.stability_max')+'</th><th>at</th><th>window</th><th>box (px)</th><th class="num">|dx| max</th><th class="num">|dy| max</th><th class="num">corr min</th><th>edge frames</th></tr>'+runs.slice().reverse().map(m=>{const ws=Object.entries(m.stability_max||{});if(!ws.length)return '<tr><td class="data">'+esc(m.record||m.folder.split('/').pop())+'</td><td class="data">'+esc(m.at)+'</td><td class="muted" colspan="6">no window measured</td></tr>';return ws.map(([nm,p],k)=>'<tr><td class="data">'+(k?'':esc(m.record||m.folder.split('/').pop()))+'</td><td class="data">'+(k?'':esc(m.at))+'</td><td>'+esc(nm)+'</td><td class="data">'+esc((p.box||[]).join(','))+'</td><td class="num">'+fmtPx(p.dx_max)+' <span class="unit">f '+p.dx_max_at+'</span></td><td class="num">'+fmtPx(p.dy_max)+' <span class="unit">f '+p.dy_max_at+'</span></td><td class="num">'+(p.corr_min!=null?(+p.corr_min).toFixed(3):'—')+'</td><td class="data">'+((p.edge_frames||[]).length?esc(p.edge_frames.join(', ')):'none')+'</td></tr>').join('');}).join('')+'</table>';
 return h;}
function fmtPx(x){return x==null?'—':(+x).toFixed(2)+'<span class="unit">px</span>';}
function wireViewer(){const st=vstate();const w=$('#viewerWrap');
 // a zoom opens at the picture's centre once the picture has its size (sizeBase centres it on the next frame)
 w.querySelectorAll('[data-mode]').forEach(b=>b.onclick=()=>{S.mode=b.dataset.mode;S.centre=S.mode!=='fit';renderViewer();});
 w.querySelectorAll('[data-cmp]').forEach(b=>b.onclick=()=>{st.cmp=b.dataset.cmp;renderViewer();});
 wireCands(w);
 $('#srcA').onchange=e=>{st.a=e.target.value;renderViewer();};$('#srcB').onchange=e=>{st.b=e.target.value;renderViewer();};
 const fl=$('#abFlip');if(fl)fl.onclick=()=>{st.ab=st.ab==='A'?'B':'A';applyCompare();};
 const oa=$('#onionAlpha');if(oa)oa.oninput=e=>{st.onion=+e.target.value;applyCompare();};
 const stack=$('#cmpStack'),hd=$('#wipeHandle');
 // the drag ends on the button's release, a cancelled pointer or a lost capture, so the split never follows a mouse
 // with no button held (critique B, harden; backlog T106)
 stack.onpointerdown=e=>{if(st.cmp!=='wipe')return;stack.setPointerCapture(e.pointerId);const move=ev=>{const rc=stack.getBoundingClientRect();st.wipe=Math.max(0,Math.min(100,(ev.clientX-rc.left)/rc.width*100));applyCompare();};move(e);stack.onpointermove=move;stack.onpointerup=stack.onpointercancel=stack.onlostpointercapture=()=>{stack.onpointermove=null;};};
 hd.onkeydown=e=>{if(e.key!=='ArrowLeft'&&e.key!=='ArrowRight')return;e.preventDefault();e.stopPropagation();st.wipe=Math.max(0,Math.min(100,st.wipe+(e.shiftKey?10:1)*(e.key==='ArrowLeft'?-1:1)));applyCompare();};
 $('#frameImg').onload=()=>{sizeBase();if(st.cmp==='diff')applyCompare();};
 const mg=$('#mGo');if(mg){$('#mWin').oninput=e=>{S.measureWin=e.target.value;};$('#mRef').oninput=e=>{S.measureRef=e.target.value;};mg.onclick=runMeasure;}}
async function runMeasure(){const r=S.render;if(!r)return;const b=$('#mGo');b.textContent='working…';b.disabled=true;try{const res=await api('/api/jobs/'+encodeURIComponent(S.view.job.id)+'/stages/measure/run',{knobs:{render:r.kind+':'+r.name,windows:S.measureWin.trim(),ref:parseInt(S.measureRef||'0',10)||0}});setMsg('started '+res.record+': loop_seq.py measure on '+r.name+'; the plot appears when it finishes','ok');await openJob(S.view.job.id,true);loadJobs();}catch(e){setMsg(e.message,'bad');b.textContent='measure';b.disabled=false;}}
// The frame takes the height the window leaves between its top (the work area at its start; a sticky viewer at its
// place in the flow) and the axis under it: the scrubber and the step plot when that leaves the frame FRAME_FULL px or
// more, else the scrubber only, the plots then below the fold; never below FRAME_MIN, a floor for a tiny window, so at
// 1280×800 the frame and its scrubber share the screen (critique A2, P1 (d)).
const FRAME_MIN=240,FRAME_FULL=480;
function sizeFrame(){const fb=$('#frameBox');if(!fb)return;const work=$('#work');const hv=fb.closest('.hostview'),grid=fb.closest('.hostgrid');
 const stuck=hv&&grid?hv.getBoundingClientRect().top-grid.getBoundingClientRect().top:0;
 const top=fb.getBoundingClientRect().top-stuck+(work?work.scrollTop:0)+scrollY;
 let h=innerHeight-top-16;const vw=fb.closest('.viewer'),sc=$('#scrub');
 if(vw&&sc){const vb=vw.getBoundingClientRect().bottom,sb=sc.getBoundingClientRect().bottom,pl=document.querySelector('#plots svg');
  h=innerHeight-top-((pl?pl.getBoundingClientRect().bottom:sb)-vb+8);if(h<FRAME_FULL)h=innerHeight-top-(sb-vb+8);}
 h=Math.max(FRAME_MIN,Math.round(h));fb.style.height=h+'px';const sd=$('#vside');if(sd)sd.style.maxHeight=h+'px';sizeBase();}
// The picture at fit, 1:1 or 2×; the box centres a picture narrower than itself (CSS: safe center) and scrolls a
// larger one, which a zoom opens at its centre (critique A2, minor 13).
function sizeBase(){const fb=$('#frameBox'),base=$('#frameImg');if(!fb||!base)return;const nw=base.naturalWidth||0;
 if(S.mode==='fit'){base.style.width='';base.style.height='';base.style.maxWidth=Math.max(50,fb.clientWidth-2)+'px';base.style.maxHeight=Math.max(50,fb.clientHeight-2)+'px';}
 else{const k=S.mode==='2x'?2:1;base.style.maxWidth='none';base.style.maxHeight='none';base.style.width=nw?(k*nw)+'px':'';base.style.height='auto';}
 ['#frameImg','#cmpOver','#cmpDiff'].forEach(q=>{const el=$(q);if(el)el.classList.toggle('px',S.mode==='2x');});
 fb.style.overflow=S.mode==='fit'?'hidden':'auto';
 if(S.centre&&nw&&S.mode!=='fit'){S.centre=false;requestAnimationFrame(()=>fb.scrollTo((fb.scrollWidth-fb.clientWidth)/2,(fb.scrollHeight-fb.clientHeight)/2));}}
// the comparator: A in the flow (it sets the size), B over it at A's size, the difference on a canvas over both
function applyCompare(){const st=vstate();const A=srcOf(st.a),B=srcOf(st.b);const base=$('#frameImg'),over=$('#cmpOver'),cv=$('#cmpDiff'),stack=$('#cmpStack');if(!base||!A)return;const m=st.cmp;
 if(base.dataset.src!==A.url){base.dataset.src=A.url;base.src=A.url;}
 if(B&&over.dataset.src!==B.url){over.dataset.src=B.url;over.src=B.url;}
 const showB=B&&(m==='wipe'||m==='onion'||(m==='ab'&&st.ab==='B'));
 over.style.display=showB?'':'none';over.style.clipPath=m==='wipe'?'inset(0 0 0 '+st.wipe+'%)':'none';over.style.opacity=m==='onion'?String(st.onion/100):'1';
 cv.style.display=m==='diff'?'':'none';
 ['#wipeSeam','#wipeHandle'].forEach(q=>{const el=$(q);el.style.display=m==='wipe'?'':'none';el.style.left=st.wipe+'%';});
 $('#wipeHandle').setAttribute('aria-valuenow',Math.round(st.wipe));
 $('#sideA').style.display=(m==='wipe'||m==='onion'||(m==='ab'&&st.ab==='A')||m==='diff')?'':'none';$('#sideA').textContent=m==='diff'?'|A − B| × '+DIFF_STRETCH:'A';
 $('#sideB').style.display=(m==='wipe'||(m==='ab'&&st.ab==='B'))?'':'none';
 const fl=$('#abFlip');if(fl){fl.textContent='showing '+st.ab;fl.setAttribute('aria-pressed',st.ab==='B');}
 const ov=$('#onionVal');if(ov)ov.textContent=st.onion+' %';const wv=$('#wipeVal');if(wv)wv.textContent=Math.round(st.wipe)+' %';
 // the violet mark: on the picture's edge at fit, on the box at 1:1 and 2×, where the picture's edges leave the screen
 const shownGen=!!((A.gen&&!(m==='ab'&&st.ab==='B'))||(B&&B.gen&&(showB||m==='diff')));const fb=$('#frameBox');stack.classList.toggle('gen',shownGen&&S.mode==='fit');if(fb)fb.classList.toggle('gen',shownGen&&S.mode!=='fit');stack.classList.toggle('wiping',m==='wipe');
 if(m==='diff')drawDiff(A,B);}
const IMGS=new Map();
function loadImg(url){if(IMGS.has(url))return IMGS.get(url);const p=new Promise((res,rej)=>{const im=new Image();im.onload=()=>res(im);im.onerror=()=>rej(new Error('cannot load '+url));im.src=url;});IMGS.set(url,p);if(IMGS.size>60)IMGS.delete(IMGS.keys().next().value);return p;}
let diffJob=0;
function drawDiff(A,B){const cv=$('#cmpDiff');if(!cv||!A||!B)return;const job=++diffJob;
 Promise.all([loadImg(A.url),loadImg(B.url)]).then(([ia,ib])=>{if(job!==diffJob)return;const w=ia.naturalWidth,h=ia.naturalHeight;if(!w||!h)return;const off=document.createElement('canvas');off.width=w;off.height=h;const c=off.getContext('2d',{willReadFrequently:true});
  c.drawImage(ia,0,0);const da=c.getImageData(0,0,w,h);c.clearRect(0,0,w,h);c.drawImage(ib,0,0,w,h);const db=c.getImageData(0,0,w,h);const p=da.data,q=db.data;
  for(let i=0;i<p.length;i+=4){p[i]=Math.min(255,DIFF_STRETCH*Math.abs(p[i]-q[i]));p[i+1]=Math.min(255,DIFF_STRETCH*Math.abs(p[i+1]-q[i+1]));p[i+2]=Math.min(255,DIFF_STRETCH*Math.abs(p[i+2]-q[i+2]));p[i+3]=255;}
  if(job!==diffJob)return;cv.width=w;cv.height=h;cv.getContext('2d').putImageData(da,0,0);}).catch(e=>setMsg(e.message,'bad'));}
// the frame under the scrubber
function showFrame(){if(!$('#cmpStack'))return;applyCompare();const r=S.render,st=vstate();const A=srcOf(st.a);const tg=$('#frameTag');
 if(r&&vhost()==='render'){const t=r.frames_tags[S.frame]||{};const tag=t.tag||'';tg.innerHTML=(A&&A.id==='frame'?chip('f '+S.frame,'','chip.frame')+(t.generated?chip('generated'+(t.t!=null?' t '+t.t:''),'gen'):chip(tag+(t.key!=null?' k'+t.key:'')+(t.t!=null?' t '+t.t:''),'','chip.tag'))+(t.method&&!t.generated&&t.tag!=='photo'?chip(t.method,'','chip.method'):'')+(t.dexp!=null?chip('dexp '+t.dexp,'','chip.dexp'):''):chip('A: '+(A?A.label:'—'),'','control.cmp_a'));
  const marks=(r.owner_frames||[]).filter(o=>o.frame===S.frame);const mn=$('#markNote');if(mn)mn.textContent=marks.length?'marked: '+marks.map(o=>o.note||'(no note)').join('; '):'';
  const fno=$('#frameNo');if(fno)fno.textContent='f '+S.frame+(t.t!=null?' · t '+t.t:'');const sc=$('#scrub');if(sc&&+sc.value!==S.frame)sc.value=S.frame;
  const so=$('#srcA');if(so){const o=so.querySelector('option[value="frame"]');if(o)o.textContent='frame f '+S.frame+' of '+candLabel(r);}const sb=$('#srcB');if(sb){const o=sb.querySelector('option[value="frame"]');if(o)o.textContent='frame f '+S.frame+' of '+candLabel(r);}
  document.querySelectorAll('#plots .cursor').forEach(c=>{const x=xOf(S.frame);c.setAttribute('x1',x);c.setAttribute('x2',x);});}
 else tg.innerHTML=chip('A: '+(A?A.label:'—'),'','control.cmp_a');}
// the shared frame axis: one x for the scrubber and every plot
function xOf(i){const n=S.render.frames_available||S.render.frames||1;return 40+(i/(Math.max(1,n-1)))*(plotW()-40-10);}
function plotW(){const p=$('#plots');return Math.max(600,(p&&p.clientWidth)||1000);}
const FAILED='#e8706a',MUTED='#9aa1a8',FAINT='#8a9198',LINE='#454b52',TEXT='#e8e8e6',AMBER='#e0a65a',GEN='#b48ef0',MONO='ui-monospace,Menlo,monospace';
function svgText(x,y,t,o){o=o||{};return '<text x="'+x+'" y="'+y+'" font-size="12" text-anchor="'+(o.anchor||'start')+'" fill="'+(o.fill||MUTED)+'"'+(o.mono?' font-family="'+MONO+'"':'')+'>'+esc(t)+'</text>';}
function drawPlots(){const r=S.render;const m=r.measure||{};const steps=m.steps||[];const n=r.frames_available||r.frames||steps.length+1;const W=plotW(),H=120,x0=40,x1=W-10,y0=10,y1=H-22;const maxv=Math.max(1,...steps,m.seam_step||0);const yOf=v=>y1-(v/maxv)*(y1-y0);const sj=r.stalls_and_jumps||{stalls:[],jumps:[]};
 const pts=steps.map((v,i)=>xOf(i+0.5).toFixed(1)+','+yOf(v).toFixed(1)).join(' ');
 let s='<svg viewBox="0 0 '+W+' '+(H+48)+'" width="'+W+'" height="'+(H+48)+'" style="width:100%;height:auto" aria-label="the step series, its stalls and jumps, and the frame tags">';
 s+='<line x1="'+x0+'" y1="'+y1+'" x2="'+x1+'" y2="'+y1+'" stroke="'+LINE+'"/><line x1="'+x0+'" y1="'+y0+'" x2="'+x0+'" y2="'+y1+'" stroke="'+LINE+'"/>';
 [0,maxv/2,maxv].forEach(v=>{s+=svgText(x0-4,yOf(v)+4,v.toFixed(1),{anchor:'end',mono:true});});
 s+=svgText(x0+4,y0+10,'step, grey levels');
 sj.stalls.forEach(([a,b])=>{const xa=xOf(a),xb=xOf(b+1);s+='<rect x="'+xa.toFixed(1)+'" y="'+y0+'" width="'+(xb-xa).toFixed(1)+'" height="'+(y1-y0)+'" fill="'+FAILED+'" opacity=".22"><title>stall: steps '+a+'–'+b+' below 0.3</title></rect>';});
 sj.jumps.forEach(i=>{const x=xOf(i+0.5).toFixed(1);s+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+(y1+12)+'" stroke="'+FAILED+'" stroke-width="2"><title>jump: step '+i+' (f '+i+' to f '+(i+1)+')</title></line>';});
 s+='<line x1="'+x0+'" y1="'+yOf(0.3)+'" x2="'+x1+'" y2="'+yOf(0.3)+'" stroke="'+FAILED+'" stroke-dasharray="4 4" opacity=".8"/>'+svgText(x1,yOf(0.3)-3,'0.3 stall bar',{anchor:'end',fill:FAILED});
 r.frames_tags.forEach(t=>{if(t.generated){const xa=xOf(t.i-0.5),xb=xOf(t.i+0.5);s+='<rect x="'+xa+'" y="'+(y1+4)+'" width="'+(xb-xa)+'" height="8" fill="'+GEN+'" opacity=".8"/>';}});
 s+=svgText(x0,H+44,'generated frames (violet) · step: mean '+m.step_mean+' · max '+m.step_max+' at f '+m.step_max_at+' · seam '+m.seam_step+' · stalls (band) '+sj.stalls.length+' · jumps (tick) '+sj.jumps.length);
 (r.owner_frames||[]).forEach(o=>{const x=xOf(o.frame);s+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+y1+'" stroke="'+FAILED+'" opacity=".7"/>';});
 s+='<polyline points="'+pts+'" fill="none" stroke="'+TEXT+'" stroke-width="1.5"/>';
 s+='<line class="cursor" x1="'+xOf(S.frame)+'" y1="'+y0+'" x2="'+xOf(S.frame)+'" y2="'+(y1+12)+'" stroke="'+AMBER+'" stroke-width="1.5"/>';
 for(let i=0;i<n;i+=Math.max(1,Math.round(n/20))){s+=svgText(xOf(i),H+24,String(i),{anchor:'middle',fill:FAINT,mono:true});}
 s+='</svg>';s+=stabilityPlots(r,W,n);const p=$('#plots');p.innerHTML=s;
 p.querySelectorAll('svg').forEach(svg=>svg.onclick=e=>{const rect=svg.getBoundingClientRect();const x=(e.clientX-rect.left)/rect.width*W;const i=Math.round((x-x0)/(x1-x0)*(n-1));S.frame=Math.max(0,Math.min(n-1,i));showFrame();});}
// one plot per window of the latest measure run: dx solid in the text colour, dy dashed in the muted colour (the photo
// colours stay with k0 and the last still: critique A2, P2 12), the max annotated
function stabilityPlots(r,W,n){const st=r.stability;if(!st||!st.series)return r.measures&&r.measures.length?'':'<p class="muted label" style="margin:4px 0 0 40px">No stability plot yet: measure a window below '+hintBtn('measure.stability')+'</p>';let s='';const H=110,x0=40,x1=W-10,y0=14,y1=H-18;
 Object.entries(st.series).forEach(([name,rows])=>{const mx=(st.max||{})[name]||{};const lim=Math.max(1,...rows.map(v=>Math.max(Math.abs(v[0]),Math.abs(v[1]))));const yOf=v=>(y0+y1)/2-(v/lim)*((y1-y0)/2);
  const line=(k,col,dash)=>'<polyline points="'+rows.map((v,i)=>xOf(i).toFixed(1)+','+yOf(v[k]).toFixed(1)).join(' ')+'" fill="none" stroke="'+col+'" stroke-width="1.5"'+(dash?' stroke-dasharray="5 3"':'')+'/>';
  s+='<svg viewBox="0 0 '+W+' '+(H+20)+'" width="'+W+'" height="'+(H+20)+'" style="width:100%;height:auto;margin-top:6px" aria-label="the stability of window '+esc(name)+'">';
  s+='<line x1="'+x0+'" y1="'+yOf(0)+'" x2="'+x1+'" y2="'+yOf(0)+'" stroke="'+LINE+'"/><line x1="'+x0+'" y1="'+y0+'" x2="'+x0+'" y2="'+y1+'" stroke="'+LINE+'"/>';
  [lim,0,-lim].forEach(v=>{s+=svgText(x0-4,yOf(v)+4,(v>0?'+':'')+v.toFixed(1),{anchor:'end',mono:true});});
  s+=line(0,TEXT,false)+line(1,MUTED,true);
  if(mx.dx_max_at!=null&&rows[mx.dx_max_at])s+='<circle cx="'+xOf(mx.dx_max_at).toFixed(1)+'" cy="'+yOf(rows[mx.dx_max_at][0]).toFixed(1)+'" r="3.5" fill="'+TEXT+'"/>';
  if(mx.dy_max_at!=null&&rows[mx.dy_max_at])s+='<circle cx="'+xOf(mx.dy_max_at).toFixed(1)+'" cy="'+yOf(rows[mx.dy_max_at][1]).toFixed(1)+'" r="3.5" fill="'+MUTED+'"/>';
  (mx.edge_frames||[]).forEach(f=>{const x=xOf(f).toFixed(1);s+='<line x1="'+x+'" y1="'+y0+'" x2="'+x+'" y2="'+y1+'" stroke="'+FAILED+'" stroke-dasharray="2 3"/>';});
  s+=svgText(x0+4,y0-2,name+' · box '+(mx.box||[]).join(',')+' px · ref f '+st.ref,{fill:TEXT});
  s+=svgText(x1,y0-2,'dx max '+(mx.dx_max!=null?(+mx.dx_max).toFixed(2):'—')+' px at f '+mx.dx_max_at+' · dy max '+(mx.dy_max!=null?(+mx.dy_max).toFixed(2):'—')+' px at f '+mx.dy_max_at,{anchor:'end',mono:true,fill:TEXT});
  s+='<line x1="'+(x0+4)+'" y1="'+(H+10)+'" x2="'+(x0+28)+'" y2="'+(H+10)+'" stroke="'+TEXT+'" stroke-width="2"/>'+svgText(x0+32,H+14,'dx',{fill:TEXT})+'<line x1="'+(x0+60)+'" y1="'+(H+10)+'" x2="'+(x0+84)+'" y2="'+(H+10)+'" stroke="'+MUTED+'" stroke-width="2" stroke-dasharray="5 3"/>'+svgText(x0+88,H+14,'dy',{fill:MUTED})+svgText(x0+116,H+14,'px, positive right and down · corr min '+mx.corr_min+' · '+(st.record||st.folder.split('/').pop())+' · no bar is recorded');
  s+='<line class="cursor" x1="'+xOf(S.frame)+'" y1="'+y0+'" x2="'+xOf(S.frame)+'" y2="'+y1+'" stroke="'+AMBER+'" stroke-width="1.5"/></svg>';});
 return s;}
// the flow's axis plots under the scrubber (the loop's step series and stability)
function plots(){const p=flowUI().plots;if(p)p();}
// playback at the clip's own rate: 1000/fps ms a frame (40 ms at the loop's 25 fps, 33.3 ms at 30)
function togglePlay(){if(!S.render||!$('#scrub'))return;if(S.playing)stopPlay();else{const n=S.render.frames_available||S.render.frames;S.playing=setInterval(()=>{S.frame=(S.frame+1)%n;showFrame();},1000/(S.render.fps||25));const b=$('#play');if(b)b.textContent='pause';}}
function stopPlay(){if(S.playing){clearInterval(S.playing);S.playing=null;}const b=$('#play');if(b)b.textContent='play';}
async function markFrame(){const b=$('#markBtn');if(!S.render||!b)return;await busy(b,async()=>{const inp=$('#markText');const note=inp?inp.value:'';try{await api('/api/jobs/'+encodeURIComponent(S.view.job.id)+'/frames/mark',{kind:S.cand.kind,name:S.cand.name,frame:S.frame,note});if(inp)inp.value='';const f=S.frame;await loadRender();S.frame=f;showFrame();}catch(e){setMsg(e.message,'bad');}});}
// the a key flips A and B in the A/B mode (the frame keys stay boot.js's)
document.addEventListener('keydown',e=>{if(e.key!=='a'||e.metaKey||e.ctrlKey||e.altKey||e.target.matches('input,textarea,select'))return;if(!$('#cmpStack')||!viewerHosts().includes(S.stage))return;const st=vstate();if(st.cmp!=='ab')return;st.ab=st.ab==='A'?'B':'A';applyCompare();e.preventDefault();});
window.addEventListener('resize',()=>{if($('#frameBox'))sizeFrame();if(S.render&&$('#plots'))plots();});
flowEntry('loop').panels.measure=panelMeasure;
Object.assign(flowEntry('loop'),{sources:loopSources,plots:drawPlots,hosts:['registration','readers','probe','render','measure']});
