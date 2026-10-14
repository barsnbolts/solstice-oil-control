'use strict';
function revealLinkedStudy(){
  const target=document.getElementById(location.hash.slice(1));
  if(!target)return;
  for(let group=target.closest('details');group;group=group.parentElement?.closest('details'))group.open=true;
  target.scrollIntoView({block:'start'});
}
window.addEventListener('hashchange',revealLinkedStudy);
revealLinkedStudy();
const filterButtons=[...document.querySelectorAll('[data-filter]')];
const references=[...document.querySelectorAll('[data-level]')];
for(const button of filterButtons)button.addEventListener('click',()=>{
  for(const other of filterButtons)other.setAttribute('aria-pressed',String(other===button));
  let count=0;for(const card of references){card.hidden=button.dataset.filter!=='all'&&card.dataset.level!==button.dataset.filter;if(!card.hidden)count++;}
  document.querySelector('#reference-count').textContent=`${count} references`;
});
// Announce updates without interrupting video, reading position or an open download.
let edition=document.querySelector('meta[name="project-edition"]').content;
async function checkEdition(){
  if(document.hidden)return;
  try{
    const response=await fetch(`version.json?t=${Date.now()}`,{cache:'no-store'});
    if(!response.ok)return;
    const current=(await response.json()).edition;
    if(edition&&edition!==current)document.querySelector('#new-edition').hidden=false;
    if(!edition)edition=current;
  }catch{/* A temporary offline phone keeps its current page. */}
}
document.querySelector('#reload').addEventListener('click',()=>{const url=new URL(location.href);url.searchParams.set('edition',Date.now());location.assign(url);});
document.addEventListener('visibilitychange',checkEdition);
checkEdition();setInterval(checkEdition,60000);

const editionUrl=path=>`${path}?v=${edition}`;
const panModel=document.querySelector('#pan-model');
const panConcept=document.querySelector('#pan-concept');
const panView=document.querySelector('#pan-view');
const gatePlay=document.querySelector('#gate-play');
function changePanView(){
  if(typeof panModel.pause==='function')panModel.pause();
  gatePlay.textContent='Play gates';gatePlay.disabled=true;
  const concept=window.solsticeCatalog?.concepts[panConcept.value];
  const view=concept?.views[panView.value];
  if(!view){document.querySelector('#pan-view-status').textContent='The selected CAD view is unavailable.';return;}
  panModel.src=editionUrl(view.model);panModel.poster=editionUrl(view.poster);
  document.querySelector('#pan-step').href=editionUrl(view.step);
  document.querySelector('#pan-whole').src=editionUrl(concept.overview);
  document.querySelector('#pan-view-status').textContent='Loading selected view…';
}
panConcept.addEventListener('change',changePanView);panView.addEventListener('change',changePanView);
fetch(editionUrl('catalog.json')).then(response=>{
  if(!response.ok)throw new Error('catalog unavailable');
  return response.json();
}).then(catalog=>{
  window.solsticeCatalog=catalog;
  changePanView();
}).catch(()=>{
  document.querySelector('#pan-view-status').textContent='The interactive catalogue could not load. The pictured CAD scene and download links remain available.';
});
panModel.addEventListener('load',()=>{
  gatePlay.disabled=panModel.availableAnimations.length===0;
  document.querySelector('#pan-view-status').textContent='Drag to orbit. Pinch to zoom. This is an assumed packaging study; actual fit is unmeasured.';
});
panModel.addEventListener('error',()=>{document.querySelector('#pan-view-status').textContent='3D could not load. The still views and downloadable CAD remain available.';});
gatePlay.addEventListener('click',()=>{
  if(panModel.paused){panModel.play();gatePlay.textContent='Pause gates';}
  else{panModel.pause();gatePlay.textContent='Play gates';}
});
