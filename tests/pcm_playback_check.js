// Sin red ni sonido: formato WAV, cola, interrupción, errores y límite de memoria.
'use strict';
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
(async()=>{
  const urls=new Map(),played=[];let id=0;
  class Audio {
    constructor(url){this.url=url;this.volume=1;this.paused=true;}
    play(){this.paused=false;played.push(this);return Promise.resolve();}
    pause(){this.paused=true;}
    removeAttribute(){} load(){}
  }
  const c=vm.createContext({setTimeout,clearTimeout,navigator:{userAgent:'Linux AppleWebKit Safari'},Audio,Blob,atob,Uint8Array,ArrayBuffer,DataView,URL:{createObjectURL:blob=>{const url='blob:'+ ++id;urls.set(url,blob);return url;},revokeObjectURL:url=>urls.delete(url)}});
  vm.runInContext('let voiceVolume=.35;'+fs.readFileSync('web/gemini-voice.js','utf8'),c);
  const session=()=>({output:new Set(),stats:{chunks:0,seconds:0,peak:0,played:0}});
  const part=values=>({mimeType:'audio/pcm;rate=24000',data:Buffer.from(new Int16Array(values).buffer).toString('base64')});
  const s=session();c.playGeminiAudio(s,part([0,1000,-1000]));c.playGeminiAudio(s,part([32767,-32768]));
  assert.equal(played.length,0);c.flushGeminiAudio(s);
  const wav=Buffer.from(await urls.get(s.audio.url).arrayBuffer());
  assert.equal(wav.toString('ascii',0,4),'RIFF');assert.equal(wav.readUInt32LE(4),wav.length-8);
  assert.equal(wav.toString('ascii',8,12),'WAVE');assert.equal(wav.readUInt16LE(20),1);
  assert.equal(wav.readUInt16LE(22),1);assert.equal(wav.readUInt32LE(24),24000);
  assert.equal(wav.readUInt32LE(28),48000);assert.equal(wav.readUInt16LE(32),2);assert.equal(wav.readUInt16LE(34),16);
  assert.equal(wav.readUInt32LE(40),10);assert.deepEqual([...new Int16Array(wav.buffer.slice(wav.byteOffset+44,wav.byteOffset+wav.length))],[0,1000,-1000,32767,-32768]);
  assert.equal(s.audio.volume,.35);assert.equal(s.stats.peak,1);
  const first=s.audio,lateEnd=first.onended;
  c.playGeminiAudio(s,part([2000]));c.flushGeminiAudio(s);assert.equal(played.length,1);
  first.onended();assert.equal(s.stats.played,2);assert.equal(played.length,2);assert.equal(urls.size,1);
  c.clearGeminiAudio(s);lateEnd();assert.equal(s.output.size,0);assert.equal(urls.size,0);assert.equal(s.audio,null);assert.equal(s.queuedBytes,0);
  c.playGeminiAudio(s,part([3000]));c.clearGeminiAudio(s);c.flushGeminiAudio(s);assert.equal(played.length,2);
  c.playGeminiAudio(s,part([4000]));c.flushGeminiAudio(s);let failed=0;s.onPlaybackError=()=>failed++;s.audio.onerror();
  assert.equal(failed,1);assert.equal(urls.size,0);assert.equal(s.output.size,0);
  assert.throws(()=>c.playGeminiAudio(s,{mimeType:'audio/pcm;rate=16000',data:'AA=='}));
  assert.throws(()=>c.playGeminiAudio(s,{mimeType:'audio/pcm',data:'AA=='}));
  s.queuedBytes=48000*90;assert.throws(()=>c.playGeminiAudio(s,part([1])));assert.equal(s.pcmBytes,0);
  const streaming=session(),before=played.length;
  c.playGeminiAudio(streaming,part(new Array(24000).fill(1000)));
  assert.equal(played.length,before+1); // Sin turnComplete ni flush externo.
  const current=streaming.audio;current.duration=1;current.currentTime=.2;
  c.playGeminiAudio(streaming,part(new Array(6000).fill(2000)));
  assert.equal(streaming.output.size,1);current.currentTime=.8;current.ontimeupdate();
  const next=[...streaming.output][1];assert.ok(next.audio);assert.equal(played.length,before+1);
  vm.runInContext('voiceVolume=.6',c);current.onended();
  assert.equal(streaming.audio,next.audio);assert.equal(streaming.audio.volume,.6);
  c.clearGeminiAudio(streaming);
  const short=session();c.playGeminiAudio(short,part([1000]));
  await new Promise(resolve=>setTimeout(resolve,650));assert.ok(short.audio);c.clearGeminiAudio(short);
  const cancelled=session(),count=played.length;c.playGeminiAudio(cancelled,part([1000]));c.clearGeminiAudio(cancelled);
  await new Promise(resolve=>setTimeout(resolve,650));assert.equal(played.length,count);assert.equal(urls.size,0);
  console.log('OK PCM: WAV exacto, volumen, orden, cancelación, errores y memoria acotada.');
})().catch(error=>{console.error(error);process.exitCode=1;});
