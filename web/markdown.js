// markdown-it 15.0.1, distribuido localmente; ver MARKDOWN-IT-LICENSE.txt.
const markdownParser=markdownit({html:false,breaks:true,linkify:true});
markdownParser.validateLink=url=>{
  try{const parsed=new URL(url);return ['http:','https:'].includes(parsed.protocol)&&!parsed.username&&!parsed.password;}catch{return false;}
};
markdownParser.renderer.rules.link_open=(tokens,index,options,env,self)=>{
  tokens[index].attrSet('target','_blank');tokens[index].attrSet('rel','noopener noreferrer');
  return self.renderToken(tokens,index,options);
};
// No cargar imágenes remotas ni locales indicadas por una respuesta del agente.
markdownParser.renderer.rules.image=(tokens,index)=>markdownParser.utils.escapeHtml(tokens[index].content);
markdownParser.renderer.rules.table_open=()=>'<div class="markdown-table" tabindex="0" role="region" aria-label="Tabla; desplazamiento horizontal"><table>\n';
markdownParser.renderer.rules.table_close=()=>'</table></div>\n';
for(const rule of ['th_open','td_open'])markdownParser.renderer.rules[rule]=(tokens,index,options,env,self)=>{
  const token=tokens[index],alignment=token.attrGet('style')?.match(/^text-align:(left|center|right)$/)?.[1];
  token.attrs=alignment?[['class','align-'+alignment]]:null;
  return self.renderToken(tokens,index,options);
};
function markdown(text){return markdownParser.render(text);}
