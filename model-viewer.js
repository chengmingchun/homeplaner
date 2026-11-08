import * as THREE from 'three';
import {OrbitControls} from './vendor/controls/OrbitControls.js';
import {GLTFLoader} from './vendor/loaders/GLTFLoader.js';
const $=id=>document.getElementById(id),host=$('stage');
let renderer;
try {renderer=new THREE.WebGLRenderer({antialias:true,alpha:false,preserveDrawingBuffer:true});}
catch(e){$('loadtitle').textContent='当前设备无法启动三维画面';$('progress').innerHTML='请尝试其他浏览器，或<a href="models/home-21101.glb">下载模型</a>查看。';throw e;}
renderer.setPixelRatio(Math.min(devicePixelRatio||1,1.7));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFSoftShadowMap;renderer.shadowMap.autoUpdate=false;host.appendChild(renderer.domElement);
const scene=new THREE.Scene();scene.background=new THREE.Color('#f6f5f0');
let viewportAspect=1,span=18,fitHeight=18,fitWidth=18;const camera=new THREE.OrthographicCamera(-10,10,10,-10,.06,160);function frustum(){camera.left=-span*viewportAspect/2;camera.right=span*viewportAspect/2;camera.top=span/2;camera.bottom=-span/2;camera.updateProjectionMatrix();}
function fitView(height,width){fitHeight=height;fitWidth=width;span=Math.max(height,width/viewportAspect);frustum();}
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.09;controls.maxPolarAngle=Math.PI*.495;controls.minDistance=2;controls.maxDistance=65;controls.minZoom=.25;controls.maxZoom=6;controls.screenSpacePanning=true;controls.target.set(0,0,0);
scene.add(new THREE.HemisphereLight('#fffef8','#a4ac9c',1.25));scene.add(new THREE.AmbientLight('#ffffff',.2));
const sun=new THREE.DirectionalLight('#fffdf5',2.0);sun.position.set(6,15,8);sun.castShadow=true;sun.shadow.mapSize.set(2048,2048);sun.shadow.camera.left=-11;sun.shadow.camera.right=11;sun.shadow.camera.top=12;sun.shadow.camera.bottom=-12;sun.shadow.normalBias=.035;sun.shadow.bias=-.0001;sun.shadow.radius=3;scene.add(sun);
const fill=new THREE.DirectionalLight('#edf3ff',.55);fill.position.set(-7,9,-6);scene.add(fill);
const ground=new THREE.Mesh(new THREE.PlaneGeometry(45,45),new THREE.ShadowMaterial({opacity:.13}));ground.rotation.x=-Math.PI/2;ground.position.y=-.205;ground.receiveShadow=true;scene.add(ground);
let model,cut=false,opened=false,closedGroup,foldedGroup;const vertical=[];
const S=12.85/833;const plan=(x,z,h=0)=>new THREE.Vector3((416.5-x)*S,h,(z-481)*S);
function resize(){const w=host.clientWidth,h=host.clientHeight;renderer.setSize(w,h,false);viewportAspect=w/h;span=Math.max(fitHeight,fitWidth/viewportAspect);frustum();}
new ResizeObserver(resize).observe(host);resize();
function home(){camera.up.set(0,1,0);camera.zoom=1;fitView(18,18);controls.target.set(0,.25,.45);camera.position.set(4,29,17);camera.lookAt(controls.target);controls.update();}
function focus(v){if(v==='home'){home();return;}camera.zoom=1;if(v==='top'){camera.up.set(0,0,-1);fitView(18.5,16);controls.target.set(0,0,0);camera.position.set(0,28,.001);camera.lookAt(controls.target);controls.update();return;}camera.up.set(0,1,0);const data={living:[400,600,6,8,9,10],north:[465,175,4,8,7,8],kitchen:[260,175,4,8,8,8],bar:[341,317,-3,3.8,5,4.8,.95],bath:[700,463,3,6,4,5]}[v];if(!data)return;const target=plan(data[0],data[1],data[6]??.4);controls.target.copy(target);fitView(data[5],data[5]*.8);camera.position.copy(target).add(new THREE.Vector3(data[2],data[3],data[4]));camera.lookAt(target);controls.update();}
function setCut(){renderer.shadowMap.needsUpdate=true;for(const item of vertical){item.obj.scale.copy(item.scale);item.obj.position.copy(item.position);if(cut){item.obj.scale.y*=.34;item.obj.position.y*=.34;}}for(const obj of [closedGroup,foldedGroup])if(obj)obj.scale.y=cut?.34:1;$('walls').textContent=cut?'恢复完整墙高':'低墙看布置';$('walls').classList.toggle('active',cut);$('walls').setAttribute('aria-pressed',String(cut));}
function setPartition(){renderer.shadowMap.needsUpdate=true;if(closedGroup)closedGroup.visible=!opened;if(foldedGroup)foldedGroup.visible=opened;$('partition').textContent=opened?'关闭北侧隔断':'打开北侧隔断';$('partition').classList.toggle('active',opened);$('partition').setAttribute('aria-pressed',String(opened));}
new GLTFLoader().load('./models/home-21101.glb?v=20261108-4',gltf=>{
 model=gltf.scene;scene.add(model);closedGroup=model.getObjectByName('PartitionClosed');foldedGroup=model.getObjectByName('PartitionFolded');
 model.traverse(o=>{if(o.isMesh){o.castShadow=!o.material.transparent;o.receiveShadow=true;}
  if(o.userData.wall||o.parent?.name==='Doors'||o.parent?.name==='Glazing')vertical.push({obj:o,scale:o.scale.clone(),position:o.position.clone()});
 });setCut();setPartition();home();$('loading').classList.add('hidden');
},e=>{if(e.total)$('progress').textContent=`已载入 ${Math.round(e.loaded/e.total*100)}%`;},e=>{console.error('MODEL_LOAD_FAILED',e);$('loadtitle').textContent='模型暂时没有载入成功';$('progress').classList.add('error');$('progress').innerHTML='请刷新重试，或<a href="models/home-21101.glb">下载 GLB 模型</a>。';});
$('walls').onclick=()=>{cut=!cut;setCut();};$('partition').onclick=()=>{opened=!opened;setPartition();};$('view').onchange=e=>focus(e.target.value);$('reset').onclick=()=>{$('view').value='home';home();};
$('plus').onclick=()=>{camera.zoom=Math.min(6,camera.zoom*1.18);camera.updateProjectionMatrix();controls.update();};$('minus').onclick=()=>{camera.zoom=Math.max(.25,camera.zoom/1.18);camera.updateProjectionMatrix();controls.update();};
$('info').onclick=()=>{const show=$('notes').hidden;$('notes').hidden=!show;$('info').setAttribute('aria-expanded',String(show));};
let lastFrame=0;function animate(now=0){requestAnimationFrame(animate);controls.update();if(now-lastFrame>30){renderer.render(scene,camera);lastFrame=now;}}animate();home();
