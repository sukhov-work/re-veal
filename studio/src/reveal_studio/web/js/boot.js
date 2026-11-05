// boot.js: the boot: the registry, the rail, the last job from localStorage; the keyboard.
'use strict';
// The frame keys while a render's viewer is on screen: left and right (or , and .) step one frame, shift ten; m marks
// the frame. Space plays only from the picture, the scrubber or no control: a focused button keeps Space as its own
// press (critique A2, P2 1). A key with Cmd, Ctrl or Alt is the browser's or the editor's.
document.addEventListener('keydown',e=>{if(!S.render||!$('#scrub')||e.metaKey||e.ctrlKey||e.altKey)return;const t=e.target;if(t.matches('input,textarea,select')&&t.id!=='scrub')return;
 const n=S.render.frames_available||S.render.frames;const d=e.shiftKey?10:1;
 if(e.key==='ArrowRight'||e.key==='.'){S.frame=Math.min(n-1,S.frame+d);showFrame();e.preventDefault();}
 else if(e.key==='ArrowLeft'||e.key===','){S.frame=Math.max(0,S.frame-d);showFrame();e.preventDefault();}
 else if(e.key===' '){if(t!==document.body&&t.id!=='scrub'&&!t.closest('#frameBox'))return;togglePlay();e.preventDefault();}
 else if(e.key==='m'){markFrame();}});
// boot
(async()=>{S.reg=await api('/api/registry');$('#ver').textContent=S.reg.ui_version+' · 127.0.0.1:'+S.reg.port;await loadJobs();await loadModels();let j=null;try{j=localStorage.getItem('studio_job')}catch(e){}if(j&&S.jobs.find(x=>x.id===j))openJob(j);else if(S.jobs.length)openJob(S.jobs[S.jobs.length-1].id);})();
