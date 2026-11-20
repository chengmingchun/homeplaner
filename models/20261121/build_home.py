import bpy, math, json, random, sys
from pathlib import Path
from mathutils import Vector
random.seed(21)
OUT=Path(__file__).resolve().parent
H=2.8
PLAN=json.loads((OUT/"plan-trace.json").read_text(encoding="utf-8"))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for d in list(bpy.data.materials):bpy.data.materials.remove(d)

def linear(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def material(name,hex,rough=.65,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True
 rgb=[linear(int(hex[i:i+2],16)/255) for i in (1,3,5)]
 m.diffuse_color=(*rgb,1);bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*rgb,1);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
 return m
M={k:material(k,c,r,mt) for k,c,r,mt in [('Plaster','#eeeee7',.9,0),('Oak','#c8b898',.55,0),('Walnut','#8f765b',.6,0),('Fabric','#e7e2d6',.95,0),('Cushion','#d8cbb4',.95,0),('Stone','#e8e7df',.4,0),('Tile','#d3d2c9',.7,0),('Metal','#444e4b',.38,.6),('White','#faf9f3',.35,0),('Screen','#243a46',.28,.1),('Foliage','#70875b',.9,0),('LeafLight','#9ca97b',.9,0),('Soil','#514738',1,0),('Rug','#c6bfb2',1,0),('Map','#8aafa3',.9,0),('Flower','#f4f0d3',.8,0),('Water','#b0cbd0',.25,0)]}
M['Glass']=material('Glass','#bbd5db',.12,0);bs=M['Glass'].node_tree.nodes.get('Principled BSDF');bs.inputs['Alpha'].default_value=.23
try:M['Glass'].surface_render_method='DITHERED'
except:pass

M['SouthGlass']=material('SouthGlass','#b5c7cc',.18,0)
M['SouthGlass'].node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.43
try:M['SouthGlass'].surface_render_method='DITHERED'
except:pass

def group(name):
 o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);return o
G={n:group(n) for n in ['Architecture','Furniture','Terrace','Glazing','Doors']}

def xy(x,y):
 return (x-6.425,7.05-y)
def attach(o,name,mat,parent='Furniture'):
 o.name=name
 if mat:o.data.materials.append(M[mat])
 if parent:o.parent=G[parent]
 return o

def cube(name,x,y,z,w,d,h,mat='Oak',bevel=0,parent='Furniture'):
 bpy.ops.mesh.primitive_cube_add(size=1,location=(x,y,z+h/2));o=bpy.context.object;o.dimensions=(w,d,h)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);attach(o,name,mat,parent)
 if bevel:
  mod=o.modifiers.new('Soft edges','BEVEL');mod.width=min(bevel,w*.45,d*.45,h*.45);mod.segments=3
  mod=o.modifiers.new('Normals','WEIGHTED_NORMAL')
 return o

def c(name,x,z,base,w,d,h,mat='Oak',bevel=0,parent='Furniture'):
 a,b=xy(x,z);return cube(name,a,b,base,w,d,h,mat,bevel,parent)
def ellipsoid(name,x,y,z,sx,sy,sz,mat='Fabric',parent='Furniture'):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=(x,y,z));o=bpy.context.object;o.scale=(sx,sy,sz)
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);attach(o,name,mat,parent)
 for p in o.data.polygons:p.use_smooth=True
 return o

def sphere_at(name,x,z,base,sx,sy,sz,mat='Fabric',parent='Furniture'):
 a,b=xy(x,z);return ellipsoid(name,a,b,base,sx,sy,sz,mat,parent)
def rod(name,a,b,r=.025,mat='Metal',parent='Furniture'):
 a,b=Vector(a),Vector(b);delta=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r,depth=delta.length,location=(a+b)/2);o=bpy.context.object;o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return attach(o,name,mat,parent)
def poly(name,points,base,height,mat,parent='Architecture'):
 pts=[xy(*q) for q in points];n=len(pts);verts=[(x,y,base) for x,y in pts]+[(x,y,base+height) for x,y in pts]
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o)
 import bmesh
 bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free();attach(o,name,mat,parent);return o

def segment(name,v,h=H,base=0,th=.15,mat='Plaster',parent='Architecture'):
 a,b=xy(v[0],v[1]),xy(v[2],v[3]);delta=Vector((b[0]-a[0],b[1]-a[1]));length=delta.length
 o=cube(name,(a[0]+b[0])/2,(a[1]+b[1])/2,base,length,th,h,mat,0,parent);o.rotation_euler.z=math.atan2(delta.y,delta.x)
 # Put origin at ground, keeping geometry in place, so runtime can safely cut walls vertically.
 if parent=='Architecture':
  dz=o.location.z
  for vert in o.data.vertices:vert.co.z+=dz
  o.location.z=0;o['wall']=True;o['designHeight']=H
 return o

def door(name,v):
 a,b=xy(v[0],v[1]),xy(v[2],v[3]);o=segment(name,v,2.12,.015,.055,'Oak','Doors');o['door']=True
 for t in [0,1]:
  p=Vector(a).lerp(Vector(b),t);cube(name+'_jamb',p.x,p.y,0,.07,.08,2.2,'Walnut',0,'Doors')
 p=Vector(a).lerp(Vector(b),.83);lever=cube(name+'_handle',p.x,p.y,1.02,.10,.12,.04,'Metal',.015,'Doors');lever.rotation_euler.z=o.rotation_euler.z
 o['planSegment']=v
 o['leafHeightEstimated']=True
 segment(name+'_lintel',v,H-2.2,2.2,.15)
 return o

def window(name,v,sill=.8,top=2.3,closed=False):
 segment('Wall_'+name+'_sill',v,sill,0);segment('Wall_'+name+'_head',v,H-top,top)
 glass=segment(name+'_glass',v,top-sill,sill,.018,'SouthGlass' if closed else 'Glass','Glazing');glass['closedGlazing']=closed
 for z in [sill,top]:segment(name+'_frame',v,.045,z,.05,'Metal','Glazing')
 a,b=xy(v[0],v[1]),xy(v[2],v[3])
 for t in [0,.5,1]:
  p=Vector(a).lerp(Vector(b),t);cube(name+'_mullion',p.x,p.y,sill,.04,.04,top-sill,'Metal',0,'Glazing')
 if closed:
  # Complete the reveal and threshold, while retaining the original glazed opening.
  for t in [0,1]:
   point=Vector(a).lerp(Vector(b),t)
   post=cube('Wall_'+name+'_reveal',point.x,point.y,0,.09,.15,top,'Plaster',0,'Architecture')
   post.rotation_euler.z=math.atan2(b[1]-a[1],b[0]-a[0])
   for vert in post.data.vertices:vert.co.z+=post.location.z
   post.location.z=0;post['wall']=True;post['designHeight']=H
  segment(name+'_lower_track',v,.025,sill,.11,'Metal','Glazing')
  segment(name+'_upper_track',v,.035,top-.035,.10,'Metal','Glazing')
  segment(name+'_threshold',v,.025,.02,.17,'Stone','Glazing')


poly('Foundation',PLAN['footprint'],-.20,.180,'Stone')
for name,points in PLAN['rooms'].items():
 poly('Floor_'+name,points,-.018,.036,'Tile' if name in ('MasterBath','CommonBath','Housekeeping') else 'Stone' if name=='Kitchen' else 'Oak')
poly('Floor_TerraceFloor',PLAN['terrace'],-.016,.028,'Stone','Terrace')
for name,points,thickness,*status in PLAN['walls']:
    # Short wall returns are visible in the photo but their heights are unresolved.
    h=.32 if status==['heightUnconfirmed'] else H
    wall=segment('Wall_'+name,points,h,th=thickness)
    wall['planSegment']=points
    if status:wall[status[0]]=True
for name,points in PLAN['doors'].items():
    door('Door_'+name,points)
for name,(points,sill,top) in PLAN['glazing'].items():
    window(name,points,sill,top,closed=name in ('GuestSESouth','MasterSouth','LivingTerrace'))
# The small boxed symbol at the entry side of the kitchen has unknown services.
c('KitchenServiceBox_Unconfirmed',8.97,4.43,.02,.30,.33,.44,'Plaster')['meaningUnconfirmed']=True
def bed(name,x,z,width=1.5):
 c(name+'_frame',x,z,.05,width+.08,2.08,.25,'Walnut',.06)
 c(name+'_mattress',x,z,.3,width,2,.20,'White',.10)
 c(name+'_duvet',x,z+.28,.50,width*.97,1.35,.10,'Fabric',.08)
 c(name+'_headboard',x,z-1.03,.08,width+.12,.12,1.02,'Cushion',.05)
 for dx in [-width*.24,width*.24]:
  a,b=xy(x,z-.65);ellipsoid(name+'_pillow',a+dx,b,.58,width*.22,.29,.08,'Fabric')
 c(name+'_bedside',x+width*.65,z-.70,.02,.37,.40,.48,'Oak',.04)

def wardrobe(name,x,z,w,d=.6):
 c(name,x,z,.02,w,d,2.35,'Oak',.025)
 a,b=xy(x,z)
 for i in range(max(2,round(w/.48))):
  xx=a-w/2+(i+.5)*w/max(2,round(w/.48));cube(name+'_pull',xx,b-d/2-.02,1.02,.02,.025,.28,'Walnut',.008)


bed('MasterBed',1.84,11.31,1.8)
wardrobe('MasterWardrobeWest',.94,8.57,1.10,.56)
wardrobe('MasterWardrobeEast',3.07,8.57,1.02,.56)
bed('GuestNWBed',2.02,2.73,1.5)
wardrobe('GuestNWWardrobe',1.81,4.26,1.32,.55)
bed('GuestSEBed',11.51,10.49,1.5)
se_center=Vector((*xy(11.51,10.49),0))
for obj in [o for o in bpy.data.objects if o.name.startswith('GuestSEBed')]:
 delta=obj.location-se_center
 obj.location=se_center+Vector((delta.y,-delta.x,delta.z))
 obj.rotation_euler.z-=math.pi/2
wardrobe('GuestSEWardrobe',11.82,8.83,1.33,.55)
# Continuous wall-following desk, dual articulated monitor arms.
c('DeskNorth',5.36,1.90,.69,2.56,.65,.06,'Walnut',.025);c('DeskReturn',6.43,2.51,.69,.58,1.35,.06,'Walnut',.025)
for x in [4.33,6.43]:c('DeskDrawers',x,1.90,.03,.42,.55,.65,'Oak',.02)
for i,x in enumerate([4.94,5.84]):
 a,b=xy(x,1.90);rod('MonitorArm_%d_base'%i,(a,b+.17,.755),(a,b+.17,1.075),.025)
 rod('MonitorArm_%d_link'%i,(a,b+.17,1.075),(a+.15,b-.08,1.225),.025)
 rod('MonitorArm_%d_elbow'%i,(a+.15,b-.08,1.225),(a,b-.18,1.175),.025)
 cube('Monitor_%d'%i,a,b-.20,.995,.74,.045,.43,'Metal',.018)
 cube('MonitorScreen_%d'%i,a,b-.227,1.02,.69,.007,.37,'Screen',.008)
c('Keyboard',5.40,2.12,.755,.43,.15,.02,'Metal',.008);c('ComputerTower',6.43,2.78,.05,.24,.48,.5,'Metal',.03)
c('NAS',6.43,2.31,.79,.22,.25,.25,'Metal',.02)
def chair(name,x,z,rot=0):
 a,b=xy(x,z);o=c(name+'_seat',x,z,.41,.45,.45,.07,'Cushion',.06);o.rotation_euler.z=rot
 for dx in [-.16,.16]:
  for dy in [-.16,.16]:rod(name+'_leg',(a+dx,b+dy,.04),(a+dx,b+dy,.43),.024,'Walnut')
 back=cube(name+'_back',a-.20*math.sin(rot),b+.20*math.cos(rot),.48,.46,.09,.38,'Fabric',.08);back.rotation_euler.z=rot
chair('WorkChair',5.37,2.68,math.pi)
a,b=xy(5.37,2.68)
for obj in list(bpy.data.objects):
 if obj.name.startswith('WorkChair_leg'):bpy.data.objects.remove(obj,do_unlink=True)
rod('WorkChairColumn',(a,b,.17),(a,b,.43),.035)
for i in range(5):
 angle=i*2*math.pi/5;p=(a+.28*math.cos(angle),b+.28*math.sin(angle),.08)
 rod('WorkChairSpoke',(a,b,.18),p,.024)
 ellipsoid('WorkChairCaster',*p,.045,.035,.045,'Metal')
# Potato-shaped lounge.
sphere_at('PotatoSeat',4.48,2.72,.27,.40,.42,.14);sphere_at('PotatoBack',4.40,2.47,.46,.44,.18,.22)
for dx in [-.30,.30]:
 a,b=xy(4.48,2.72);ellipsoid('PotatoArm',a+dx,b,.42,.17,.38,.18)
def table(name,x,z,w,d,height=.75):
 c(name+'_top',x,z,height-.045,w,d,.045,'Walnut',.035);a,b=xy(x,z)
 for dx in [-w*.42,w*.42]:
  for dy in [-d*.36,d*.36]:cube(name+'_leg',a+dx,b+dy,.02,.06,.06,height-.065,'Walnut',.015)
table('Boardgame',5.25,3.90,1.80,.90)
c('BoardgameMap',5.25,3.90,.756,1.12,.70,.008,'Map')
for i in range(16):
 x=5.25+random.uniform(-.48,.48);z=3.90+random.uniform(-.27,.27);c('MapLand',x,z,.766,random.uniform(.05,.16),random.uniform(.05,.12),.006,'Cushion',.015)
for i in range(8):c('CardDeck',5.25+(-.73 if i<4 else .73),3.63+(i%4)*.18,.766,.07,.10,.015,'White',.003)
for x in [4.68,5.77]:
 for z in [3.20,4.61]:chair('GameChair',x,z,math.pi if z==4.61 else 0)
# Kitchen kept north; washer at south end next to foyer.
for z in [.55,1.20,1.85,2.50,3.15]:
 c('KitchenBase',8.77,z,.03,.61,.64,.84,'Oak',.015);c('KitchenCounter',8.77,z,.87,.65,.65,.045,'Stone',.012)
c('SinkBasin',8.77,1.20,.92,.46,.43,.018,'Metal',.04)
a,b=xy(8.77,1.20);rod('Tap',(a+.1,b,.92),(a+.1,b,1.18),.018);rod('TapSpout',(a+.1,b,1.18),(a,b,1.18),.018)
c('InductionCooktop',8.77,2.50,.926,.50,.50,.018,'Metal',.02)
for dx in [-.13,.13]:
 for dz in [-.13,.13]:
  a,b=xy(8.77,2.50);bpy.ops.mesh.primitive_torus_add(major_segments=12,minor_segments=6,location=(a+dx,b+dz,.95),major_radius=.085,minor_radius=.005);attach(bpy.context.object,'HobRing','Metal')
c('WasherBody_SouthKitchen',8.77,3.83,.02,.60,.62,.84,'White',.025)
a,b=xy(8.77,3.83)
# Front faces west into kitchen, away from outer east wall.
ellipsoid('WasherBlackHatch',a-.307,b,.43,.017,.205,.205,'Metal');ellipsoid('WasherGlass',a-.326,b,.43,.009,.157,.157,'Screen')
c('WasherCounter',8.77,3.83,.88,.65,.65,.045,'Stone',.012)
c('Fridge',7.39,.63,.02,.66,.70,1.9,'White',.025)
# A fitted coffee bar wraps the intact bearing wall end.
# It has no stools in the dining-chair circulation zone.
def rounded_slab(name,x,z,w,d,base,h,mat,r=.18):
 a,b=xy(x,z);r=min(r,w/2,d/2);pts=[]
 for cx,cy,start in [(a+w/2-r,b+d/2-r,0),(a-w/2+r,b+d/2-r,90),(a-w/2+r,b-d/2+r,180),(a+w/2-r,b-d/2+r,270)]:
  for j in range(9):
   angle=math.radians(start+j*90/8);pts.append((cx+r*math.cos(angle),cy+r*math.sin(angle)))
 n=len(pts);verts=[(px,py,base) for px,py in pts]+[(px,py,base+h) for px,py in pts]
 faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);attach(o,name,mat)
 return o
# Counter wraps the south end and both faces of the uncut bearing wall.
wall_x,wall_y=xy(6.86,4.71)
bar_z=4.78
bar=rounded_slab('CoffeeBarStone',6.86,bar_z,1.65,.70,.865,.035,'Stone',.12)
# The notch belongs to the furniture; the structural wall stays a complete prism.
notch=cube('CounterNotchTool',wall_x,wall_y+.15,.78,.24,.312,.20,None,0,None)
mod=bar.modifiers.new('Fitted around intact wall','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=notch
bpy.context.view_layer.objects.active=bar;bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(notch,do_unlink=True)
bar['wrapsWallEnd']=True;bar['wallNotCut']=True
for side in [-1,1]:
 cube('BarWallSideCladding',wall_x+side*.126,wall_y+.12,.025,.026,.30,.84,'Oak',.005)
cube('BarWallEndCladding',wall_x,wall_y-.019,.025,.279,.026,.84,'Oak',.005)
# Concealed support is within the furniture base, with no freestanding outer leg.
cube('CoffeeBarFittedCabinet',wall_x+.40,wall_y-.02,.025,.52,.54,.84,'Oak',.018)
cube('CoffeeBarCabinetDoor',wall_x+.40,wall_y-.30,.04,.49,.018,.80,'Oak',.01)
# A compact coffee station makes this a useful transition counter.
c('CoffeeMachine',7.33,4.84,.90,.20,.25,.27,'Metal',.025)
c('CoffeeMachineFront',7.33,4.96,1.00,.15,.015,.13,'Walnut',.01)
c('CoffeeDripTray',7.33,5.02,.905,.18,.11,.016,'Metal',.005)
for xx in [6.49,6.28]:
 a,b=xy(xx,4.89);bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.038,depth=.075,location=(a,b,.95));attach(bpy.context.object,'CoffeeCup','White')
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.032,depth=.004,location=(a,b,.989));attach(bpy.context.object,'CoffeeSurface','Soil')
 bpy.ops.mesh.primitive_torus_add(major_segments=20,minor_segments=8,major_radius=.026,minor_radius=.006,location=(a+.04,b,.952),rotation=(math.pi/2,0,0));attach(bpy.context.object,'CoffeeCupHandle','White')

# Dining island-table: compact storage at one end and open knee space at the other.
c('DiningIslandBase',6.19,7.80,.03,.95,.58,.68,'Oak',.035)
rounded_slab('DiningIslandStone',6.68,7.80,2.0,.90,.71,.04,'Stone',.16)
a,b=xy(7.46,7.80);rod('DiningIslandLeg',(a,b,.03),(a,b,.71),.032,'Walnut')
for x in [7.30,6.64,5.98]:chair('DiningChair',x,6.98)
# Very soft L sofa: west back, seating east, chaise toward south.
c('LivingRug',6.66,10.70,.025,3.9,3.0,.016,'Rug',.12)
a,b=xy(5.10,10.64)
for i in range(3):
 yy=b+(i-1)*.78;ellipsoid('CloudSeat',a,yy,.28,.49,.47,.16)
 ellipsoid('CloudBack',a-.40,yy,.64,.21,.48,.28)
 ellipsoid('LoosePillow',a-.19,yy,.72,.19,.34,.20,'Cushion' if i==1 else 'Fabric')
ellipsoid('CloudArmNorth',a,b+1.08,.49,.54,.19,.20);ellipsoid('CloudChaise',a+.48,b-1.02,.28,.86,.47,.16)
table('CoffeeTable',6.66,10.59,.73,1.05,.34)
c('TVConsole',9.46,10.57,.03,.38,2.0,.42,'Walnut',.04)
c('TVBlackFrame',9.64,10.57,.65,.055,1.58,.91,'Metal',.02);c('TVDisplay',9.605,10.57,.68,.008,1.50,.83,'Screen',.005)
c('EntryConsole',10.26,6.27,.03,.68,.34,.76,'Oak',.04)
c('StorageCabinet',10.43,7.48,.02,.38,1.09,1.35,'Oak',.02)
# Two bathrooms only. Compact east-west tub in master bath; no room enlargement.
c('MasterBathtubOuter',1.18,6.95,.03,1.48,.70,.55,'White',.25)
c('MasterBathtubInterior',1.18,6.95,.54,1.22,.48,.035,'Water',.20)
c('MasterVanity',3.25,6.92,.04,.63,.42,.76,'Oak',.04);c('MasterBasin',3.25,6.92,.81,.51,.34,.075,'White',.08)
def toilet(name,x,z):
 c(name+'_base',x,z,.02,.35,.46,.32,'White',.12);c(name+'_seat',x,z,.34,.40,.53,.08,'White',.14);c(name+'_tank',x,z-.28,.09,.38,.16,.67,'White',.05)
toilet('MasterToilet',3.16,7.67);toilet('CommonToilet',2.24,5.99)
c('CommonVanity',1.49,6.06,.03,.62,.43,.75,'Oak',.03);c('CommonBasin',1.49,6.06,.80,.51,.34,.07,'White',.06)
c('CommonShowerTray',1.30,5.20,.03,.72,.74,.025,'Tile',.03)
segment('ShowerGlass',[1.76,4.86,1.76,5.52],1.9,.05,.015,'Glass','Glazing')
rail=PLAN['rail']
for i in range(len(rail)-1):
 a,b=xy(*rail[i]),xy(*rail[i+1]);rod('TerraceRailTop',(*a,1.1),(*b,1.1),.025,'Metal','Terrace')
 rod('TerraceRailBottom',(*a,.13),(*b,.13),.018,'Metal','Terrace')
 length=(Vector(a)-Vector(b)).length
 for j in range(max(1,math.ceil(length/.70))+1):
  p=Vector(a).lerp(Vector(b),j/max(1,math.ceil(length/.70)));rod('TerracePost',(p.x,p.y,.08),(p.x,p.y,1.1),.018,'Metal','Terrace')

# Moveable modules follow the south edge with a gentle alternating wave.
for i in range(7):
 start=4.55+i*1.13
 points=[(start+j*.14,15.41-.10*math.sin(j*math.pi/8)) for j in range(9)]
 points+= [(start+j*.14,14.98-.10*math.sin(j*math.pi/8)) for j in reversed(range(9))]
 h=.38+.055*math.sin(i*1.50)
 poly('WavePlanter_'+str(i),points,.10,h,'Oak','Terrace')
 soil=[(x,15.18+(y-15.18)*.75) for x,y in points]
 poly('PlanterSoil_'+str(i),soil,.10+h,.015,'Soil','Terrace')
 for x in [start+.13,start+1.0]:
  for y in [15.03,15.32]:sphere_at('Caster',x,y,.055,.042,.038,.042,'Metal','Terrace')
 for j in range(8):
  x=start+.065+j*.139;y=15.13+random.uniform(-.085,.085)
  a,b=xy(x,y);height=.12+random.random()*.17
  rod('PlantStem',(a,b,h+.107),(a,b,h+.107+height),.008,'Foliage','Terrace')
  for k in range(3):ellipsoid('Leaves',a+random.uniform(-.07,.07),b+random.uniform(-.06,.06),h+.18+height*k/3,.10,.05,.045,'Foliage' if k%2 else 'LeafLight','Terrace')
for x,y,ang in [(4.30,15.09,-.55),(4.16,14.51,-.08)]:
 o=c('CornerPlanter',x,y,.10,.34,.57,.38,'Oak',.08,'Terrace');o.rotation_euler.z=ang
 for j in range(4):sphere_at('CornerPlant',x+random.uniform(-.10,.10),y+random.uniform(-.18,.18),.58,.11,.10,.13,'Foliage','Terrace')
 for dx in [-.10,.10]:
  for dy in [-.17,.17]:sphere_at('CornerCaster',x+dx,y+dy,.055,.035,.035,.04,'Metal','Terrace')
for x in [6.60,8.23]:
 sphere_at('OutdoorChairSeat',x,14.11,.32,.34,.34,.15,'Fabric','Terrace')
 sphere_at('OutdoorChairBack',x,14.36,.52,.34,.12,.29,'Fabric','Terrace')
 for dx in [-.21,.21]:
  for dy in [-.18,.18]:
   a,b=xy(x,14.11);rod('OutdoorChairLeg',(a+dx,b+dy,.02),(a+dx,b+dy,.25),.025,'Walnut','Terrace')
table('TerraceSideTable',7.42,14.12,.46,.46,.43)

scene=bpy.context.scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1
scene['status']='Photo-traced plan with two labelled overall dimensions. Local sizes still require measurement.'
scene['model_revision']=PLAN['revision']
scene['dimensionReferencesM']=[12.85,12.65]
scene['orientation']='North +Y. Source image already shows main bedroom southwest and entry northeast.'
scene['walls']='North bedroom partition retained. Kitchen bearing wall retained. Structures and heights pending verification.'
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.75,.79,.82,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
def aim(obj,target):
 obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()
for loc,power,size in [((1,-4,14),2100,10),((-7,6,12),1500,8)]:
 bpy.ops.object.light_add(type='AREA',location=loc)
 light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size
 aim(light,(0,0,0))
def camera(name,loc,target,scale):
 bpy.ops.object.camera_add(location=loc)
 o=bpy.context.object;o.name=name;o.data.type='ORTHO';o.data.ortho_scale=scale
 aim(o,target)
 return o
whole=camera('Camera_WholeHome',(7,-18,26),(0,-.6,0),21.8)
top=camera('Camera_Plan',(0,0,24),(0,0,0),19.5)
scene.camera=whole
for area in (bpy.context.screen.areas if bpy.context.screen else []):
 if area.type=='VIEW_3D':
  area.spaces.active.shading.type='MATERIAL'
  area.spaces.active.region_3d.view_distance=23
  area.spaces.active.region_3d.view_rotation=whole.rotation_euler.to_quaternion()
bpy.context.preferences.filepaths.save_version=0
scene.render.engine='CYCLES';scene.cycles.samples=36;scene.cycles.use_denoising=True
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 if any(d.type=='OPTIX' for d in prefs.devices):
  for d in prefs.devices:d.use=d.type=='OPTIX'
  scene.cycles.device='GPU'
except Exception as exc:
 print('Render device:',exc)
scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'home-21101.blend'))
import logging
logging.getLogger('io_scene_gltf2').setLevel(logging.ERROR)
bpy.ops.export_scene.gltf(filepath=str(OUT/'home-21101-raw.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,use_visible=False,export_apply=True)
manifest={
 'revision':PLAN['revision'],'dimensionReferencesM':PLAN['dimensionReferencesM'],'notSurveyed':True,
 'wallHeightAssumptionM':H,'bathrooms':2,'bedroomsAndStudy':4,'doors':list(PLAN['doors']),
 'northPartition':'intact; future moveable partition is separate from the traced plan',
 'terraceRail':'open railing, southwest rounded edge','barWrap':'furniture notch wraps intact kitchen wall',
 'renderFiles':['blender-preview.png','top-plan.png']
}
(OUT/'model-info.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
for o in G['Architecture'].children:
 if o.get('wall'):o.scale.z=.34
for group_name in ['Doors','Glazing']:
 for o in G[group_name].children:o.scale.z=.34;o.location.z*=.34
for cam,file in [(whole,'blender-preview.png'),(top,'top-plan.png')]:
 scene.camera=cam;scene.render.filepath=str(OUT/file)
 bpy.ops.render.render(write_still=True)
print('HOME_MODEL_READY',PLAN['revision'],flush=True)
