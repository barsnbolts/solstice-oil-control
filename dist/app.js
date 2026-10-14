'use strict';
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
