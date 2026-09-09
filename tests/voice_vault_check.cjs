'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path'),crypto=require('node:crypto');
const {VoiceVault}=require('../desktop/voice-vault.cjs');
const root=fs.mkdtempSync(path.join(os.tmpdir(),'sw-vault-')),key=crypto.randomBytes(32);
const storage={isEncryptionAvailable:()=>true,getSelectedStorageBackend:()=> 'gnome_libsecret',encryptString(text){const iv=crypto.randomBytes(12),cipher=crypto.createCipheriv('aes-256-gcm',key,iv);const data=Buffer.concat([cipher.update(text,'utf8'),cipher.final()]);return Buffer.concat([iv,cipher.getAuthTag(),data]);},decryptString(data){const cipher=crypto.createDecipheriv('aes-256-gcm',key,data.subarray(0,12));cipher.setAuthTag(data.subarray(12,28));return Buffer.concat([cipher.update(data.subarray(28)),cipher.final()]).toString();}};
try{
 const vault=new VoiceVault(root,storage,'linux');vault.keys.gemini='AQ.ficticia-prueba-local';vault.save('gemini',true);
 assert(!fs.readFileSync(vault.path('gemini')).includes(vault.keys.gemini));assert.equal(fs.statSync(vault.path('gemini')).mode&0o777,0o600);
 const restarted=new VoiceVault(root,storage,'linux');assert.equal(restarted.load('gemini'),vault.keys.gemini);assert.equal(restarted.status().stored.gemini,true);
 for(const backend of ['basic_text','unknown']){const unavailable=new VoiceVault(root,{...storage,getSelectedStorageBackend:()=>backend},'linux');assert.equal(unavailable.available(),false);assert.equal(unavailable.load('gemini'),null);unavailable.keys.gemini='dummy';assert.throws(()=>unavailable.save('gemini',true));}
 const editor=new VoiceVault(path.join(root,'editor'),storage,'linux',['openai','gemini','anthropic','deepseek','kimi','local']);for(const provider of editor.providers){editor.keys[provider]='ficticia-'+provider;editor.save(provider,true);assert.equal(new VoiceVault(editor.root,storage,'linux',editor.providers).load(provider),'ficticia-'+provider);}assert.equal(vault.keys.kimi,undefined);
 assert.throws(()=>vault.save('gemini','true'));assert.throws(()=>vault.save('../escape',false));
 fs.writeFileSync(vault.path('gemini'),'corrupt');assert.equal(restarted.load('gemini'),null);assert(restarted.error);
 vault.save('gemini',false);assert.equal(vault.status().stored.gemini,false);
 fs.symlinkSync(path.join(root,'other'),path.join(root,'openai.bin'));fs.writeFileSync(path.join(root,'other'),'untouched');assert.throws(()=>vault.save('openai',false));assert.equal(fs.readFileSync(path.join(root,'other'),'utf8'),'untouched');
 console.log('OK almacén: cifrado, reinicio, permisos, borrado, corrupción, rutas y rechazo del fallback basic_text. Cifrado de prueba inyectado; no prueba el almacén nativo.');
}finally{fs.rmSync(root,{recursive:true,force:true});}
