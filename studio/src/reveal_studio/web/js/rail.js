// rail.js: the rail: the jobs list, the running tasks, the requests, the models, the new-job and adopt forms.
'use strict';
// the rail
async function loadJobs(){S.jobs=await api('/api/jobs');const ul=$('#jobs');const jsig=JSON.stringify(S.jobs)+'|'+S.jid;if(jsig!==S.jobsSig){S.jobsSig=jsig;const focusedJob=document.activeElement&&document.activeElement.closest('.job')?document.activeElement.dataset.id:null;ul.innerHTML=S.jobs.length?S.jobs.map(j=>'<li class="job" data-id="'+esc(j.id)+'" data-hint="region.rail" tabindex="0" aria-current="'+(j.id===S.jid)+'"><div class="name">'+esc(j.seq)+' <span class="muted">'+esc(j.source||j.flow)+'</span></div><div class="meta">'+esc(j.id)+'</div><div>'+chip(j.last_render,stateClass(j.last_render))+' '+(j.candidates?chip(j.candidates+(j.candidates===1?' candidate':' candidates')+(j.unjudged?', '+j.unjudged+' unjudged':''),j.unjudged?'info':'','chip.candidates'):'')+' '+(j.round?chip('round '+j.round+(j.graded?' graded':(j.ungraded_by_his_word?' ungraded by his word':' ungraded')),j.graded?'ok':'info'):'')+(j.adopted?' '+chip('adopted'):'')+'</div></li>').join(''):'<li class="muted" style="padding:4px 16px">no jobs yet</li>';
 ul.querySelectorAll('.job').forEach(li=>{li.onclick=()=>openJob(li.dataset.id);li.onkeydown=e=>{e.stopPropagation();if(e.key==='Enter')openJob(li.dataset.id);if(e.key==='ArrowDown'&&li.nextElementSibling)li.nextElementSibling.focus();if(e.key==='ArrowUp'&&li.previousElementSibling)li.previousElementSibling.focus();};});
 if(focusedJob){const li=ul.querySelector('.job[data-id="'+focusedJob+'"]');if(li)focusQuiet(li);}}
 // a running record as "render · a2 · 12/50 · 38 s" (critique A2, P2 8); the job and the record id in its title
 const running=[];S.jobs.forEach(j=>j.running.forEach(r=>running.push({job:j,rec:r})));
 $('#tasks').innerHTML=running.length?running.map(({job,rec})=>'<li class="kv"><span class="data" title="'+esc(job.seq+' · '+job.id+' · '+rec.id)+'">'+esc([rec.stage,rec.name,rec.progress?rec.progress.i+'/'+rec.progress.n:null,rec.elapsed_s!=null?fmtElapsed(rec.elapsed_s):null].filter(x=>x!=null&&x!=='').join(' · '))+'</span>'+chip('running','run')+'</li>').join(''):'<li class="kv muted">idle</li>';
 const reqs=await api('/api/requests');$('#reqs').innerHTML=reqs.length?reqs.map(r=>'<li class="kv"><span class="data" title="'+esc(r.file)+'">'+esc(r.name)+'</span>'+chip('waiting '+fmtAge(r.age_s),'run')+'</li>').join(''):'<li class="kv muted">none open</li>';}
function fmtElapsed(s){return s<60?Math.round(s)+' s':fmtS(s);}
async function loadModels(){const ms=await api('/api/models');$('#models').innerHTML=ms.map(m=>'<li class="kv"><span>'+esc(m.name)+'</span>'+chip(m.ready?'ready, offline':'missing',m.ready?'ok':'bad',m.ready?'chip.model_ready':'chip.model_missing')+'</li>').join('');}
// one "new <flow> job…" button per enabled flow that registers newJob, drawn once the registry is in (boot.js); the
// loop's keeps its id, its text and its hint
function drawNewJobs(){const box=$('#newJobs');if(!box||!S.reg)return;const flows=Object.keys(S.reg.flows||{}).filter(f=>FLOW_UI[f]&&FLOW_UI[f].newJob);
 box.innerHTML=flows.map(f=>f==='loop'?'<button class="btn" id="btnNew" data-flow="loop" data-hint="control.new_job">new loop job…</button>':'<button class="btn" id="btnNew_'+esc(f)+'" data-flow="'+esc(f)+'" data-hint="'+esc('control.'+f+'_new_job')+'">new '+esc(f)+' job…</button>').join(' ');
 box.querySelectorAll('button[data-flow]').forEach(b=>b.onclick=()=>FLOW_UI[b.dataset.flow].newJob());}
// one new-job form at a time: every opener closes the others first, the flows' own forms under #flowForms included
// (critique B, minor 1: the director's and the pair's forms showed together with two amber "create" buttons)
function closeForms(){$('#newForm').style.display='none';$('#adoptForm').style.display='none';document.querySelectorAll('#flowForms > *').forEach(f=>{f.hidden=true;});}
function openLoopForm(){closeForms();$('#newForm').style.display='';$('#newFolder').focus();}
$('#newCancel').onclick=()=>{$('#newForm').style.display='none';};
$('#btnAdopt').onclick=()=>{closeForms();$('#adoptForm').style.display='';$('#adoptRoot').focus();};
$('#adoptCancel').onclick=()=>{$('#adoptForm').style.display='none';};
$('#newGo').onclick=()=>busy($('#newGo'),async()=>{$('#newErr').textContent='';try{const r=await api('/api/jobs',{flow:'loop',folder:$('#newFolder').value,seq:$('#newSeq').value||undefined});$('#newForm').style.display='none';await loadJobs();openJob(r.id);}catch(e){$('#newErr').textContent=e.message;}});
$('#adoptGo').onclick=()=>busy($('#adoptGo'),async()=>{$('#adoptErr').textContent='';try{const r=await api('/api/jobs',{flow:'loop',adopt:$('#adoptRoot').value,seq:$('#adoptSeq').value});$('#adoptForm').style.display='none';await loadJobs();openJob(r.id);}catch(e){$('#adoptErr').textContent=e.message;}});
function alertMsg(t){setMsg(t,'bad');if(!$('#msg')){$('#panel').insertAdjacentHTML('afterbegin','<div class="msg bad" id="msg">'+esc(t)+'</div>');}}
Object.assign(flowEntry('loop'),{newJob:openLoopForm,inputsWord:'stills'});
