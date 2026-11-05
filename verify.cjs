const fs=require('fs'),vm=require('vm'),assert=require('assert');
const html=fs.readFileSync('index.html','utf8');const scripts=[...html.matchAll(/<script[^>]*>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');
const ids=new Map([...html.matchAll(/id="([^"]+)"/g)].map(m=>[m[1],{id:m[1],value:'',textContent:'',style:{},classList:{toggle(){},add(){},remove(){}},children:[],append(e){this.children.push(e)},addEventListener(){},replaceChildren(){},getBoundingClientRect(){return {width:1000,height:700,x:0,y:0}},setPointerCapture(){}}]));
const gradient={addColorStop(){}};const ctx=new Proxy({createLinearGradient(){return gradient},measureText(){return {width:50}}},{get(t,k){return k in t?t[k]:(()=>{})}});ids.get('scene').getContext=()=>ctx;
const sandbox={console,Math,JSON,Map,Set,Blob,URL,setTimeout,clearTimeout,requestAnimationFrame:()=>1,localStorage:{getItem(){return null},setItem(){}},ResizeObserver:class{observe(){}},window:{devicePixelRatio:1,addEventListener(){}},document:{querySelector(s){assert(s.startsWith('#'),'unsupported selector '+s);assert(ids.has(s.slice(1)),'missing DOM '+s);return ids.get(s.slice(1))},querySelectorAll(){return []},createElement(){return {}}}};
vm.createContext(sandbox);vm.runInContext(scripts,sandbox);
vm.runInContext(`
 if(state.showLabels)throw Error('Labels default must be off');
 if(ROOMS.some(r=>r.id==='bath2'))throw Error('Third bathroom');
 if(ROOMS.filter(r=>r.category==='卫浴').length!==2)throw Error('Bathroom count');
 if(state.mirror!==false)throw Error('Unexpected mirror');
 for(const v of [[191,317,241,317],[339,317,355,317],[365,318,499,318],[546,318,558,318]])if(!isOpenKitchenWall(v))throw Error('South wall remains');
 for(const style of Object.keys(DESIGN_STYLES)){state.style=style;draw()}
 state.style='warm';for(const value of ['B','original','A']){document.querySelector('#kitchenplan').onchange({target:{value}});draw()}
 state.showLabels=true;draw();state.showLabels=false;
`,sandbox);
function svg(){const data=vm.runInContext(`faces.map(fc=>({...fc,pr:fc.points.map(project)})).filter(fc=>fc.pr.every(p=>p.d>.03)).sort((a,b)=>b.pr.reduce((s,p)=>s+p.d,0)/b.pr.length-a.pr.reduce((s,p)=>s+p.d,0)/a.pr.length)`,sandbox);return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 760"><rect width="1000" height="760" fill="#f4f5ef"/>'+data.map(fc=>'<polygon points="'+fc.pr.map(p=>p.x.toFixed(2)+','+(p.y+30).toFixed(2)).join(' ')+'" fill="'+fc.color+'"/>').join('')+'<text x="24" y="732" font-family="Microsoft YaHei" font-size="16" fill="#537164">同源3D概念视图 · 未实测校准 · 非写实竣工效果</text></svg>'}
vm.runInContext("state.showLabels=false;setView('iso');draw()",sandbox);fs.writeFileSync('axon.svg',svg());
vm.runInContext("setView('low');draw()",sandbox);fs.writeFileSync('low-view.svg',svg());
console.log('PASS: initialization, 6 palettes, kitchen A/B/original, labels, bathroom count, south wall filtering, drawing; exported shared-geometry 3D views');
