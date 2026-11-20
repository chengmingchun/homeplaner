import * as THREE from 'three';
import {OrbitControls} from './vendor/controls/OrbitControls.js';
import {GLTFLoader} from './vendor/loaders/GLTFLoader.js';
const $=id=>document.getElementById(id),host=$('stage');
let renderer;
try {renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true});}
catch(e){$('loadtitle').textContent='当前设备无法启动三维画面';$('progress').textContent='请尝试使用其他浏览器。';throw e;}
renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.7));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;host.appendChild(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color('#f6f5f0');
let viewportAspect=1,span=18,fitHeight=18,fitWidth=18;const camera=new THREE.OrthographicCamera(-10,10,10,-10,.06,160);function frustum(){camera.left=-span*viewportAspect/2;camera.right=span*viewportAspect/2;camera.top=span/2;camera.bottom=-span/2;camera.updateProjectionMatrix();}
function fitView(height,width){fitHeight=height;fitWidth=width;span=Math.max(height,width/viewportAspect);frustum();}
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.09;controls.maxPolarAngle=Math.PI*.495;controls.minDistance=2;controls.maxDistance=65;controls.minZoom=.25;controls.maxZoom=6;controls.screenSpacePanning=true;controls.target.set(0,0,0);
scene.add(new THREE.HemisphereLight('#fffef8','#a4ac9c',1.25));scene.add(new THREE.AmbientLight('#ffffff',.2));
const sun=new THREE.DirectionalLight('#fffdf5',2.0);sun.position.set(6,15,8);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-11;sun.shadow.camera.right=11;sun.shadow.camera.top=12;sun.shadow.camera.bottom=-12;sun.shadow.normalBias=.035;sun.shadow.bias=-.0001;sun.shadow.radius=3;scene.add(sun);
const fill=new THREE.DirectionalLight('#edf3ff',.55);fill.position.set(-7,9,-6);scene.add(fill);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(45,45),new THREE.ShadowMaterial({opacity:.13}));ground.rotation.x=-Math.PI/2;ground.position.y=-.205;ground.receiveShadow=true;scene.add(ground);
let cut=false;const vertical=[];
const scheme=new URLSearchParams(location.search).get('scheme');
const cabinetScheme=scheme==='wall-cabinet';
const islandScheme=scheme==='island-layout';
if(cabinetScheme||islandScheme){
 $('page-title').textContent=islandScheme?'意式岛台与双推拉门':'承重墙包柜方案';
 $('layout-link').href='./';
 $('layout-link').textContent='原户型';
 $('scheme-link').hidden=true;
 $(islandScheme?'island-description':'scheme-description').hidden=false;
 $('plan-description').hidden=true;
 if(islandScheme){
  $('view').querySelector('[value="kitchen"]').textContent='L 型厨房';
  $('view').querySelector('[value="utility"]').textContent='家政间与洗衣区';
 }
 $('view').insertAdjacentHTML('beforeend',islandScheme
  ? '<option value="island">岛台与双门</option><option value="office">电竞间</option><option value="master">主卧</option>'
  : '<option value="cabinet">包柜整体</option><option value="cabinetStudy">电竞收纳侧</option><option value="cabinetKitchen">厨房备餐侧</option>');
}
const plan=(x,z,h=0)=>new THREE.Vector3(x-6.425,h,z-7.05);
function resize(){const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h,false);viewportAspect=w/h;span=Math.max(fitHeight,fitWidth/viewportAspect);frustum();}
new ResizeObserver(resize).observe(host);resize();
function home(){camera.up.set(0,1,0);camera.zoom=1;fitView(18,18);controls.target.set(0,.25,.45);camera.position.set(4,29,17);camera.lookAt(controls.target);controls.update();}
const focusAreas={
 living:[6.7,9.8,5,9,9,10],
 north:[4.7,3,2,8,7,8],
 kitchen:[8.1,2.7,3,8,8,8],
 bar:[6.86,4.71,-3,3.8,5,4.8,.95],
 bath:[2.02,7.30,3,6,4,5],
 utility:[10.05,7.48,-3,5,4,5],
 cabinet:[6.85,4.95,-4,5.8,9,7.7,.9],
 cabinetStudy:[6.35,3.15,-5,4,4.2,4.6,1.15],
 cabinetKitchen:[7.23,3.25,5,4,5,4.9,1.15],
 island:[6.60,6.25,-3.6,8.5,9.6,8.4,.62],
 office:[5.46,3.08,3.8,7.1,6.4,4.5,.72],
 master:[2.10,10.30,3.1,7,5.5,5.8,.62]
};
function focus(view){
 if(view==='home'){home();return;}
 camera.zoom=1;
 if(view==='top'){
  camera.up.set(0,0,-1);fitView(19.5,16);
  controls.target.set(0,0,0);camera.position.set(0,30,.001);
 }else{
  const [x,z,dx,dy,dz,viewHeight,targetHeight=.4]=focusAreas[view];
  camera.up.set(0,1,0);
  controls.target.copy(plan(x,z,targetHeight));
  fitView(viewHeight,viewHeight*.8);
  camera.position.copy(controls.target).add(new THREE.Vector3(dx,dy,dz));
 }
 camera.lookAt(controls.target);controls.update();
}
function setCut(){renderer.shadowMap.needsUpdate=true;for(const item of vertical){item.obj.scale.copy(item.scale);item.obj.position.copy(item.position);if(cut){item.obj.scale.y*=.34;item.obj.position.y*=.34;}}$('walls').textContent=cut?'恢复完整墙高':'低墙看布置';$('walls').classList.toggle('active',cut);$('walls').setAttribute('aria-pressed',String(cut));}
const modelPaths={
 'island-layout':'./models/island-layout/island-layout.glb?v=italian-2',
 'wall-cabinet':'./models/wall-cabinet/wall-cabinet.glb'
};
const modelPath=modelPaths[scheme]||'./models/20261121/home-21101.glb';
new GLTFLoader().load(modelPath,gltf=>{
 const model=gltf.scene;scene.add(model);
 model.traverse(o=>{if(o.isMesh){o.castShadow=!o.material.transparent;o.receiveShadow=true;}
  if(o.userData.wall||['Doors','Glazing','Proposed door leaves','Proposed fixed glass','KitchenDoorParked','KitchenDoorClosed','StudyDoorParked','StudyDoorClosed'].includes(o.parent?.name))vertical.push({obj:o,scale:o.scale.clone(),position:o.position.clone()});
 });
 if(islandScheme){
  for(const [id,prefix,label] of [['kitchen-door','Kitchen','厨房门'],['study-door','Study','电竞间门']]){
   const parked=model.getObjectByName(prefix+'DoorParked');
   const closed=model.getObjectByName(prefix+'DoorClosed');
   if(!parked||!closed)continue;
   const button=$(id);
   closed.visible=false;
   button.hidden=false;
   button.onclick=()=>{
    closed.visible=!closed.visible;
    parked.visible=!closed.visible;
    button.textContent=(closed.visible?'打开':'关闭')+label;
    button.setAttribute('aria-pressed',String(closed.visible));
    renderer.shadowMap.needsUpdate=true;
   };
  }
 }
 if(cabinetScheme||islandScheme){
  cut=true;
  $('view').value=islandScheme?'island':'cabinet';
  focus($('view').value);
 }else home();
 setCut();
 $('loading').classList.add('hidden');
},e=>{if(e.total)$('progress').textContent=`已载入 ${Math.min(100,Math.round(e.loaded/e.total*100))}%`;},e=>{console.error('MODEL_LOAD_FAILED',e);$('loadtitle').textContent='模型暂时没有载入成功';$('progress').classList.add('error');$('progress').textContent='请刷新页面重试。';});
$('walls').onclick=()=>{cut=!cut;setCut();};$('view').onchange=e=>focus(e.target.value);$('reset').onclick=()=>{$('view').value='home';home();};
$('plus').onclick=()=>{camera.zoom=Math.min(6,camera.zoom*1.18);camera.updateProjectionMatrix();controls.update();};$('minus').onclick=()=>{camera.zoom=Math.max(.25,camera.zoom/1.18);camera.updateProjectionMatrix();controls.update();};
$('info').onclick=()=>{const show=$('notes').hidden;$('notes').hidden=!show;$('info').setAttribute('aria-expanded',String(show));};
let lastFrame=0;function animate(now=0){requestAnimationFrame(animate);controls.update();if(now-lastFrame>30){renderer.render(scene,camera);lastFrame=now;}}animate();home();
