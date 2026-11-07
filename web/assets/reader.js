(function(){
 'use strict';
 const frame=document.querySelector('[data-reader]');
 if(!frame)return;
 const groups=[...frame.querySelectorAll('[data-reader-group]')];
 const panels=[...frame.querySelectorAll('[data-reader-panel]')];
 const chapters=[...frame.querySelectorAll('[data-reader-chapter]')];
 const menus=[...frame.querySelectorAll('[data-reader-menu]')];
 const topics=[...frame.querySelectorAll('[data-reader-topic]')];
 let activePanel;

 function render(followAnchor){
  let id=location.hash.slice(1);
  try{id=decodeURIComponent(id);}catch(error){}
  const target=document.getElementById(id);
  const selectedGroup=target?.closest('[data-reader-group]')||groups[0];
  const selectedPanel=target?.closest('[data-reader-panel]')||selectedGroup.querySelector('[data-reader-panel]');
  const key=selectedGroup.dataset.readerGroup;

  for(const group of groups)group.hidden=group!==selectedGroup;
  for(const panel of panels)panel.hidden=panel!==selectedPanel;
  for(const menu of menus)menu.hidden=menu.dataset.readerMenu!==key;
  for(const chapter of chapters){
   if(chapter.dataset.readerChapter===key)chapter.setAttribute('aria-current','true');
   else chapter.removeAttribute('aria-current');
  }
  for(const topic of topics){
   if(topic.hash==='#'+selectedPanel.id)topic.setAttribute('aria-current','location');
   else topic.removeAttribute('aria-current');
  }
  if(activePanel!==selectedPanel){
   activePanel=selectedPanel;
   window.EconoApp?.redraw();
  }

  if(followAnchor&&target){
   const chapterStart=selectedGroup.querySelector('.argument-heading');
   const anchor=target===selectedPanel||target===chapterStart?frame:target;
   requestAnimationFrame(()=>anchor.scrollIntoView({block:'start',behavior:'instant'}));
  }
 }

 frame.addEventListener('click',event=>{
  const link=event.target.closest('[data-reader-chapter], [data-reader-topic]');
  if(!link||event.defaultPrevented||event.button!==0||event.altKey||event.ctrlKey||event.metaKey||event.shiftKey)return;
  event.preventDefault();
  if(location.hash!==link.hash)history.pushState(null,'',link.hash);
  render(false);
  if(frame.getBoundingClientRect().top<0)frame.scrollIntoView({block:'start',behavior:'instant'});
 });
 window.addEventListener('hashchange',()=>render(true));
 render(Boolean(location.hash));
}());
