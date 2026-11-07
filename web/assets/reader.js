(function(){
 'use strict';
 const frame=document.querySelector('[data-reader]');
 if(!frame)return;
 const outline=frame.querySelector('.reader-outline');
 const compact=window.matchMedia('(max-width: 760px)');
 const groups=[...frame.querySelectorAll('[data-reader-group]')];
 const chapters=[...outline.querySelectorAll('[data-reader-chapter]')];
 const topics=[...outline.querySelectorAll('[data-reader-topic]')];
 const outlineNav=outline.querySelector('nav');
 const destinations=topics.map(link=>({link,target:document.getElementById(link.hash.slice(1))}));
 let activeGroup,activeTopic,outlineFrame;

 function highlightTopic(topic){
  if(activeTopic===topic)return;
  activeTopic?.removeAttribute('aria-current');
  activeTopic=topic;
  if(!topic)return;
  topic.setAttribute('aria-current','location');
  revealTopic();
 }

 function revealTopic(){
  if(!outline.open||!activeTopic)return;
  const item=activeTopic.getBoundingClientRect();
  const visible=outlineNav.getBoundingClientRect();
  if(item.top<visible.top)outlineNav.scrollTop+=item.top-visible.top;
  else if(item.bottom>visible.bottom)outlineNav.scrollTop+=item.bottom-visible.bottom;
 }

 function followScroll(){
  outlineFrame=undefined;
  if(!activeGroup)return;
  const readingLine=Math.min(200,Math.max(120,window.innerHeight*.23));
  let nearestTop=-Infinity,topic;
  for(const destination of destinations){
   const {link,target}=destination;
   if(!target||!activeGroup.contains(target)||!target.getClientRects().length)continue;
   const top=target.getBoundingClientRect().top;
   if(top<=readingLine&&top>=nearestTop){
    nearestTop=top;
    topic=link;
   }
  }
  highlightTopic(topic);
 }

 function queueFollowScroll(){
  if(outlineFrame===undefined)outlineFrame=requestAnimationFrame(followScroll);
 }

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
  highlightTopic(topics.find(topic=>topic.hash===topicHash));
  if(activeGroup!==selectedGroup){
   activeGroup=selectedGroup;
   window.EconoApp?.redraw();
  }

  if(followAnchor&&target){
   const chapterStart=chapters.find(chapter=>chapter.hash==='#'+id);
   const anchor=chapterStart?frame:target;
   requestAnimationFrame(()=>{
    anchor.scrollIntoView({block:'start',behavior:'instant'});
    queueFollowScroll();
   });
  }else queueFollowScroll();
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
 outline.addEventListener('toggle',revealTopic);
 window.addEventListener('scroll',queueFollowScroll,{passive:true});
 window.addEventListener('resize',queueFollowScroll);
 if(window.ResizeObserver)new ResizeObserver(queueFollowScroll).observe(frame.querySelector('.reader-body'));
 window.addEventListener('hashchange',()=>render(true));
 render(Boolean(location.hash));
}());
