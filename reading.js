'use strict';
const controls=[...document.querySelectorAll('[data-size]')];
function setSize(value){if(!['18','21','25'].includes(value))value='21';document.documentElement.style.setProperty('--reading-size',value+'px');controls.forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.size===value)));try{localStorage.setItem('anxin-reading-size',value);}catch{}}
let saved='21';try{saved=localStorage.getItem('anxin-reading-size')||saved;}catch{}setSize(saved);controls.forEach(button=>button.addEventListener('click',()=>setSize(button.dataset.size)));
