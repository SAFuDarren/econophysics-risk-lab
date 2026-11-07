(function(){
 'use strict';
 const frame=document.querySelector('[data-reader]');
 if(!frame)return;
 const outline=frame.querySelector('.reader-outline');
 const compact=window.matchMedia('(max-width: 760px)');
 const groups=[...frame.querySelectorAll('[data-reader-group]')];
 const chapters=[...outline.querySelectorAll('[data-reader-chapter]')];
 const topics=[...outline.querySelectorAll('[data-reader-topic]')];
 let activeGroup;

 function render(followAnchor){
  let id=location.hash.slice(1);
  try{id=decodeURIComponent(id);}catch(error){}
  const target=document.getElementById(id);
  const selectedGroup=target?.closest('[data-reader-group]')||groups[0];
  const section=target?.closest('[data-reader-panel]')||selectedGroup.querySelector('[data-reader-panel]');
  const topicHash=topics.some(topic=>topic.hash==='#'+id)?'#'+id:'#'+section?.id;
  const key=selectedGroup.dataset.readerGroup;
  for(const group of groups)group.hidden=group!==selectedGroup;
  for(const chapter of chapters){
   if(chapter.dataset.readerChapter===key)chapter.setAttribute('aria-current','true');
   else chapter.removeAttribute('aria-current');
  }
  for(const topic of topics){
   if(topic.hash===topicHash)topic.setAttribute('aria-current','location');
   else topic.removeAttribute('aria-current');
  }
  if(activeGroup!==selectedGroup){
   activeGroup=selectedGroup;
   window.EconoApp?.redraw();
  }

  if(followAnchor&&target){
   const chapterStart=chapters.find(chapter=>chapter.hash==='#'+id);
   const anchor=chapterStart?frame:target;
   requestAnimationFrame(()=>anchor.scrollIntoView({block:'start',behavior:'instant'}));
  }
 }

 function fitOutline(){
  outline.open=!compact.matches;
 }
 compact.addEventListener('change',fitOutline);
 fitOutline();
 outline.addEventListener('click',event=>{
  const link=event.target.closest('a');
  if(!link||event.defaultPrevented||event.button!==0||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;
  event.preventDefault();
  if(location.hash!==link.hash)history.pushState(null,'',link.hash);
  if(compact.matches){
   outline.open=false;
   outline.querySelector('summary').focus({preventScroll:true});
  }
  render(true);
 });
 window.addEventListener('hashchange',()=>render(true));
 render(Boolean(location.hash));
}());
