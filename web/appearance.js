'use strict';
// Antes del primer pintado: preferencias del usuario de este navegador/escritorio.
const appearancePalettes={light:{sage:'Original · salvia',sky:'Blanco · celeste',cream:'Blanco · crema / amarillo',pink:'Blanco · rosado'},dark:{sage:'Original · salvia',violet:'Negro · violeta',red:'Negro · rojo',blue:'Negro · azul'}};
function storedAppearance(key,fallback){try{return localStorage.getItem(key)||fallback;}catch{return fallback;}}
const initialTheme=storedAppearance('sw-theme','system');
document.documentElement.dataset.theme=['light','dark'].includes(initialTheme)?initialTheme:'system';
for(const mode of ['light','dark']){const value=storedAppearance('sw-palette-'+mode,'sage');document.documentElement.dataset[mode+'Palette']=Object.hasOwn(appearancePalettes[mode],value)?value:'sage';}
