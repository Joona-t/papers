// Screenshot every figure in a guide (both tabs) and stack them into one image for review.
const {chromium} = require('playwright');
const {execFileSync} = require('child_process');
(async () => {
  const b = await chromium.launch();
  for (const id of process.argv.slice(2)) {
    const p = await b.newPage({viewport: {width: 800, height: 900}});
    const errs = [];
    p.on('pageerror', e => errs.push(e.message));
    await p.goto('file://' + __dirname + '/../guides/' + id + '.html');
    const files = [];
    for (const tab of ['simple', 'tech']) {
      await p.click('#tab-' + tab);
      const figs = await p.$$('#' + tab + ' figure');
      let i = 0;
      for (const f of figs) { const fn = `shots/${id}-${tab}-fig${i++}.png`; await f.screenshot({path: fn}); files.push(fn); }
    }
    execFileSync('python3', [__dirname + '/stack.py', `shots/${id}-figs.png`, ...files]);
    console.log(id, files.length, 'figures', errs.length ? 'ERRORS: ' + errs.join(' | ') : 'no errors');
    await p.close();
  }
  await b.close();
})();
