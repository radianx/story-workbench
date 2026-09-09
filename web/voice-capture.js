// PCM mono a 16 kHz. Chromium remuestrea el micrófono al sampleRate del AudioContext.
class VoiceCapture extends AudioWorkletProcessor {
  constructor(){super();this.buffer=new Int16Array(4096);this.offset=0;this.port.onmessage=()=>this.flush();}
  flush(){if(this.offset){this.port.postMessage(this.buffer.slice(0,this.offset));this.offset=0;}}
  process(inputs){const channel=inputs[0]?.[0];if(channel)for(const value of channel){const sample=Math.max(-1,Math.min(1,value));this.buffer[this.offset++]=Math.round(sample*(sample<0?32768:32767));if(this.offset===this.buffer.length)this.flush();}return true;}
}
registerProcessor('voice-capture',VoiceCapture);
