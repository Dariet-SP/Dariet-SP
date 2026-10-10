// usage: node shoot.js stills <outdir> t1,t2,...   |   node shoot.js frames <outdir> [fps] [dur]
const { chromium } = require('/tmp/claude-0/-home-user-Dariet-SP/f7fc9ee6-7f70-5c95-8f1e-201b5d4b0ea7/scratchpad/build/node_modules/playwright');
const fs = require('fs');
(async () => {
  const [, , mode, out, arg3, arg4] = process.argv;
  fs.mkdirSync(out, { recursive: true });
  let b;
  try { b = await chromium.launch(); }
  catch (e) { b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' }); }
  const p = await b.newPage({ viewport: { width: 1080, height: 1920 } });
  p.on('pageerror', e => console.log('ERR', e.message));
  p.on('console', m => console.log('LOG', m.text()));
  await p.goto('file://' + __dirname + '/usage.html');
  await p.evaluate(() => document.fonts.ready);
  await p.waitForTimeout(400);
  if (mode === 'stills') {
    const times = arg3.split(',').map(Number);
    for (const t of times) {
      await p.evaluate(t => render(t), t);
      await p.screenshot({ path: `${out}/still_t${t.toFixed(1)}.png` });
    }
  } else {
    const fps = Number(arg3 || 30), dur = Number(arg4 || 7.5);
    const n = Math.round(fps * dur);
    for (let i = 0; i < n; i++) {
      await p.evaluate(t => render(t), i / fps);
      await p.screenshot({ path: `${out}/${String(i).padStart(4, '0')}.jpg`, type: 'jpeg', quality: 93 });
    }
  }
  await b.close();
})();
