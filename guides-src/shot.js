const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const ids=process.argv.slice(2);
for(const id of ids){for(const [tab,w,dark] of [['simple',800,false],['tech',800,true],['simple',390,false]]){
const p=await b.newPage({viewport:{width:w,height:900},colorScheme:dark?'dark':'light'});
const errs=[];p.on('pageerror',e=>errs.push(e.message));p.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
await p.goto('file://'+__dirname+'/../guides/'+id+'.html#'+tab);await p.waitForTimeout(300);
const ov=await p.evaluate(()=>document.documentElement.scrollWidth-innerWidth);
await p.screenshot({path:`shots/${id}-${tab}-${w}.png`,fullPage:true});
console.log(id,tab,w,'overflow',ov,'errors',errs.filter(e=>!/fonts/.test(e)).join('|'));await p.close();}}
await b.close();})();
