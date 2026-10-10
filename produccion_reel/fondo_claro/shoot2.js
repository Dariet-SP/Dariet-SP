const { chromium } = require('../build/node_modules/playwright');
const fs=require('fs');
(async()=>{
 const [,,mode,out]=process.argv; const TM=JSON.parse(fs.readFileSync(__dirname+'/timing.json'));
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1920}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.addInitScript(tm=>{window.TIMING=tm},TM);
 await p.goto('file://'+__dirname+'/reel2.html'); await p.evaluate(()=>document.fonts.ready); await p.waitForTimeout(600);
 const n=Math.round(TM.total*30);
 const times = mode==='preview' ? process.argv[4].split(',').map(Number) : [...Array(n).keys()].map(i=>i/30);
 for(let i=0;i<times.length;i++){ await p.evaluate(t=>render(t),times[i]);
   await p.screenshot({path:`${out}/${String(i).padStart(4,'0')}.jpg`,type:'jpeg',quality:92}); }
 await b.close();
})();
