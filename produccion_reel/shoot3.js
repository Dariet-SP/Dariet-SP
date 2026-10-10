const { chromium } = require('../build/node_modules/playwright');
(async()=>{
 const [,,html,out,spec]=process.argv;
 const b=await chromium.launch(); const p=await b.newPage({viewport:{width:1080,height:1920}});
 p.on('pageerror',e=>console.log('ERR',e.message));
 await p.goto('file://'+__dirname+'/'+html); await p.evaluate(()=>document.fonts.ready); await p.waitForTimeout(600);
 let times;
 if(spec.startsWith('range:')){const [a,bb]=spec.slice(6).split('-').map(Number); times=[]; for(let i=Math.round(a*30);i<Math.round(bb*30);i++) times.push(i/30);}
 else times=spec.split(',').map(Number);
 for(let i=0;i<times.length;i++){ await p.evaluate(t=>render(t),times[i]);
   await p.screenshot({path:`${out}/${String(i).padStart(4,'0')}.jpg`,type:'jpeg',quality:92}); }
 await b.close();
})();
