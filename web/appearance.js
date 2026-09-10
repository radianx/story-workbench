'use strict';
// Antes del primer pintado: preferencias del usuario de este navegador/escritorio.
const appearancePalettes={light:{sage:'Original · salvia',sky:'Blanco · celeste',cream:'Blanco · crema / amarillo',pink:'Blanco · rosado',neon:'Claro · neón',vice:'Claro · Vice City',custom:'Claro · personalizado'},dark:{sage:'Original · salvia',violet:'Negro · violeta',red:'Negro · rojo',blue:'Negro · azul',neon:'Negro · neón',vice:'Oscuro · Vice City',custom:'Oscuro · personalizado'}};
function storedAppearance(key,fallback){try{return localStorage.getItem(key)||fallback;}catch{return fallback;}}
const appFonts={system:{label:'Sistema · sans-serif',family:'system-ui, sans-serif'},arial:{label:'Arial / Liberation Sans',family:'Arial, "Liberation Sans", sans-serif'},georgia:{label:'Georgia · serif',family:'Georgia, serif'},times:{label:'Times New Roman / Liberation Serif',family:'"Times New Roman", "Liberation Serif", serif'},mono:{label:'Courier New / Liberation Mono',family:'"Courier New", "Liberation Mono", monospace'}};
function applyAppFont(value){
  const font=Object.hasOwn(appFonts,value)?value:'system';
  document.documentElement.dataset.font=font;
  document.documentElement.style.setProperty('--app-font',appFonts[font].family);
  const selector=document.getElementById('app-font');if(selector)selector.value=font;
}
applyAppFont(storedAppearance('sw-font','system'));
const initialTheme=storedAppearance('sw-theme','system');
document.documentElement.dataset.theme=['light','dark'].includes(initialTheme)?initialTheme:'system';
for(const mode of ['light','dark']){const value=storedAppearance('sw-palette-'+mode,'sage');document.documentElement.dataset[mode+'Palette']=Object.hasOwn(appearancePalettes[mode],value)?value:'sage';}

const themeColors={ink:'Texto',muted:'Texto secundario',line:'Bordes',paper:'Página',bg:'Fondo',surface:'Paneles',field:'Campo de mensaje',green:'Resaltes',pale:'Fondo de resaltes'};
function validateCustomTheme(value){
  if(!value||value.version!==1||!['light','dark'].includes(value.mode)||typeof value.name!=='string'||!value.name.trim()||value.name.length>80||!value.colors||typeof value.backgroundOpacity!=='number'||!Number.isFinite(value.backgroundOpacity)||value.backgroundOpacity<0||value.backgroundOpacity>100)throw Error('Tema inválido: usá el formato JSON de Story Workbench.');
  const colors={};for(const key of Object.keys(themeColors)){if(typeof value.colors[key]!=='string'||!/^#[0-9a-f]{6}$/i.test(value.colors[key]))throw Error('Cada color debe tener formato #RRGGBB.');colors[key]=value.colors[key];}
  return {version:1,name:value.name.trim(),mode:value.mode,colors,backgroundOpacity:value.backgroundOpacity};
}
function customTheme(mode){try{return validateCustomTheme(JSON.parse(storedAppearance('sw-custom-'+mode,'null')));}catch{return null;}}
function applyCustomThemes(){
  for(const mode of ['light','dark']){
    const value=document.documentElement.dataset[mode+'Palette']==='custom'?customTheme(mode):null;
    for(const key of Object.keys(themeColors)){
      if(value)document.documentElement.style.setProperty('--'+mode+'-'+key,value.colors[key]);
      else document.documentElement.style.removeProperty('--'+mode+'-'+key);
    }
    if(document.documentElement.dataset[mode+'Palette']==='custom'&&!value)document.documentElement.dataset[mode+'Palette']='sage';
    // El texto de los botones conserva contraste con el color de resalte elegido.
    if(value){const rgb=value.colors.green.slice(1).match(/../g).map(v=>{const c=parseInt(v,16)/255;return c<=.04045?c/12.92:((c+.055)/1.055)**2.4;});document.documentElement.style.setProperty('--'+mode+'-button-ink',rgb[0]*.2126+rgb[1]*.7152+rgb[2]*.0722>.179?'#000000':'#ffffff');}
    else document.documentElement.style.removeProperty('--'+mode+'-button-ink');
  }
}
function applyBackgroundOpacity(value){const number=Number(value),level=Number.isFinite(number)&&number>=0&&number<=100?number:10;document.documentElement.style.setProperty('--ambient-opacity',level/100);return level;}
applyCustomThemes();applyBackgroundOpacity(storedAppearance('sw-background-opacity','10'));
