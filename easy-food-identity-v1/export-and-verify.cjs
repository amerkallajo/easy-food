// Run with Node.js on the original workstation. Requires the local Playwright package.
const {chromium}=require('C:/Users/amerk/AppData/Roaming/npm/node_modules/playwright');
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
const root=__dirname;
const qa=path.join(root,'verification');
fs.mkdirSync(qa,{recursive:true});
(async()=>{
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files/Google/Chrome/Application/chrome.exe'});
 const reports=[];
 try{
  for(const item of [
   {file:'docs/brand-guide.html',pdf:'docs/brand-guide.pdf',width:1400,height:1000},
   {file:'templates/menu.html',pdf:'templates/menu.pdf',png:'templates/menu.png',width:1200,height:1700},
   {file:'templates/social-square.html',png:'templates/social-square.png',width:1080,height:1080},
   {file:'templates/social-story.html',png:'templates/social-story.png',width:1080,height:1920},
   {file:'index.html',width:1440,height:1000}
  ]){
   const page=await browser.newPage({viewport:{width:item.width,height:item.height},deviceScaleFactor:1});
   const errors=[];
   page.on('pageerror',error=>errors.push(error.message));
   await page.goto(pathToFileURL(path.join(root,item.file)).href,{waitUntil:'load'});
   await page.evaluate(()=>document.fonts.ready);
   await page.evaluate(async()=>{await Promise.all([...document.images].map(i=>i.decode().catch(()=>{})))});
   const check=await page.evaluate(()=>({
    title:document.title,
    documentWidth:document.documentElement.scrollWidth,
    viewportWidth:innerWidth,
    brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.getAttribute('src')),
    localLinks:[...document.querySelectorAll('a[href],img[src],link[href]')].map(i=>i.getAttribute('href')||i.getAttribute('src')).filter(s=>s&&!/^(https?:|data:|#|mailto:)/.test(s)),
    fonts:[...document.fonts].map(f=>({family:f.family,status:f.status})),
    sections:[...document.querySelectorAll('.page,.sheet,.slide')].map((e,i)=>({index:i,width:e.clientWidth,scrollWidth:e.scrollWidth,height:e.clientHeight,scrollHeight:e.scrollHeight}))
   }));
   const brokenLinks=check.localLinks.filter(link=>!fs.existsSync(path.resolve(path.dirname(path.join(root,item.file)),decodeURIComponent(link.split('#')[0]))));
   if(item.pdf) await page.pdf({path:path.join(root,item.pdf),printBackground:true,preferCSSPageSize:true});
   if(item.png){
    const canvas=page.locator('.canvas');
    if(await canvas.count()) await canvas.screenshot({path:path.join(root,item.png)});
    else await page.screenshot({path:path.join(root,item.png),fullPage:true});
   }
   if(item.file==='docs/brand-guide.html') await page.screenshot({path:path.join(qa,'guide-first-page.png'),fullPage:false});
   if(item.file==='index.html'){
    await page.screenshot({path:path.join(qa,'gallery-desktop.png'),fullPage:false});
    await page.setViewportSize({width:390,height:844});
    const mobile=await page.evaluate(()=>({documentWidth:document.documentElement.scrollWidth,viewportWidth:innerWidth,brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length}));
    await page.screenshot({path:path.join(qa,'gallery-mobile.png'),fullPage:false});
    check.mobile=mobile;
   }
   reports.push({file:item.file,...check,brokenLinks,errors});
   await page.close();
  }
  for(const name of ['logo-primary-cream','logo-reversed-cobalt']){
   const page=await browser.newPage();
   await page.goto(pathToFileURL(path.join(root,'assets/logos',name+'.svg')).href,{waitUntil:'load'});
   await page.pdf({path:path.join(root,'assets/logos',name+'.pdf'),width:'1060px',height:'400px',printBackground:true,margin:{top:0,right:0,bottom:0,left:0}});
   await page.close();
  }
  fs.writeFileSync(path.join(qa,'browser-checks.json'),JSON.stringify(reports,null,2));
  const failures=reports.flatMap(r=>[...r.errors,...r.brokenImages,...r.brokenLinks].map(detail=>({file:r.file,detail})));
  console.log(JSON.stringify({reports:reports.map(r=>({file:r.file,title:r.title,width:r.documentWidth,viewport:r.viewportWidth,sections:r.sections,mobile:r.mobile})),failures},null,2));
  if(failures.length)process.exitCode=1;
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
