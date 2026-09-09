'use strict';
const fs=require('node:fs');
const {join}=require('node:path');
const {randomUUID}=require('node:crypto');
class VoiceVault {
  constructor(root,storage,platform=process.platform){this.root=root;this.storage=storage;this.platform=platform;this.keys={};this.error='';}
  available(){return this.storage.isEncryptionAvailable()&&(this.platform!=='linux'||['gnome_libsecret','kwallet','kwallet5','kwallet6'].includes(this.storage.getSelectedStorageBackend()));}
  path(provider){
    if(!['openai','gemini'].includes(provider))throw new Error('Proveedor inválido.');
    fs.mkdirSync(this.root,{recursive:true,mode:0o700});
    if(fs.lstatSync(this.root).isSymbolicLink())throw new Error('Almacén de claves inválido.');
    const path=join(this.root,provider+'.bin');
    if(fs.lstatSync(path,{throwIfNoEntry:false})&&!fs.lstatSync(path).isFile())throw new Error('Archivo de clave inválido.');
    return path;
  }
  status(){
    const stored={};for(const provider of ['openai','gemini'])try{stored[provider]=fs.existsSync(this.path(provider));}catch{stored[provider]=false;this.error='No se pudo acceder al almacén cifrado.';}
    return {available:this.available(),stored,reason:this.error||(!this.available()?'El sistema no ofrece un almacén seguro disponible; la clave puede usarse solo en memoria.':'Cifrado con el almacén de claves del sistema, separado de tus proyectos.')};
  }
  load(provider){
    if(!this.available())return null;
    try{
      const path=this.path(provider);if(!fs.existsSync(path))return null;
      if(fs.statSync(path).size>16384)throw new Error('size');
      const key=this.storage.decryptString(fs.readFileSync(path));
      if(!key||key.length>2048)throw new Error('key');
      this.keys[provider]=key;return key;
    }catch{this.error='No se pudo abrir una clave guardada. Desbloqueá el almacén del sistema o reemplazala.';return null;}
  }
  save(provider,remember){
    if(typeof remember!=='boolean')throw new Error('Preferencia de guardado inválida.');
    const path=this.path(provider);
    if(!remember){fs.rmSync(path,{force:true});return;}
    if(!this.available())throw new Error('No hay almacén seguro disponible. No se guardó la clave en disco.');
    const key=this.keys[provider];if(!key)throw new Error('Ingresá la clave antes de recordarla.');
    const encrypted=this.storage.encryptString(key),temp=join(this.root,randomUUID()+'.tmp');
    try{fs.writeFileSync(temp,encrypted,{mode:0o600,flag:'wx'});fs.renameSync(temp,path);this.error='';}
    catch{throw new Error('La clave está en memoria, pero no se pudo guardar cifrada.');}
    finally{fs.rmSync(temp,{force:true});}
  }
}
module.exports={VoiceVault};
