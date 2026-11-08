import bpy, math, json, random, sys
from pathlib import Path
from mathutils import Vector
random.seed(21)
OUT=Path(__file__).resolve().parent
S=12.85/833
H=2.8
# Concept calibration from the supplied terrace area, not surveyed dimensions.
TERRACE_STRETCH=1.32125
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
G={n:group(n) for n in ['Architecture','Furniture','Terrace','PartitionClosed','PartitionFolded','Glazing','Doors']}
G['PartitionFolded']['defaultHidden']=True

def xy(x,z):
 if z>790:z=790+(z-790)*TERRACE_STRETCH
 return ((416.5-x)*S,(481-z)*S)
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
 p=Vector(a).lerp(Vector(b),.83);cube(name+'_handle',p.x,p.y,1.02,.045,.10,.04,'Metal',.015,'Doors')
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
   for vert in post.data.vertices:vert.co.z+=post.location.z
   post.location.z=0;post['wall']=True;post['designHeight']=H
  segment(name+'_lower_track',v,.025,sill,.11,'Metal','Glazing')
  segment(name+'_upper_track',v,.035,top-.035,.10,'Metal','Glazing')
  segment(name+'_threshold',v,.025,.02,.17,'Stone','Glazing')


outline=[(183,10),(367,10),(367,42),(779,42),(779,420),(833,420),(833,790),(586,790),(586,886),(584,899),(576,921),(563,937),(549,946),(534,950),(32,950),(17,944),(17,744),(0,744),(0,542),(85,542),(85,317),(162,317),(162,181),(183,181)]
poly('Foundation',outline,-.2,.18,'Stone')
rooms={
 'MasterBedroom':([(567,506),(833,506),(833,790),(567,790)],'Oak'),
 'MasterBath':([(567,424),(833,424),(833,506),(567,506)],'Tile'),
 'GuestBedroomNW':([(568,43),(779,43),(779,323),(640,323),(640,307),(568,307)],'Oak'),
 'StudyGames':([(341,43),(560,43),(560,318),(341,318)],'Oak'),
 'CommonBath':([(640,325),(779,325),(779,424),(640,424)],'Tile'),
 'GuestBedroomSE':([(0,542),(202,542),(202,744),(0,744)],'Oak'),
 'Living':([(85,317),(567,317),(567,790),(202,790),(202,542),(85,542)],'Oak'),
 'KitchenUtility':([(183,10),(367,10),(367,42),(341,42),(341,317),(162,317),(162,181),(183,181)],'Stone'),
 'TerraceFloor':([(17,744),(202,744),(202,790),(586,790),(586,886),(584,899),(576,921),(563,937),(549,946),(534,950),(32,950),(17,944)],'Stone')}
for n,(pts,mat) in rooms.items():poly('Floor_'+n,pts,-.015,.035,mat)
outer=[[183,10,230,10],[335,10,367,10],[367,10,367,42],[367,42,390,42],[530,42,615,42],[745,42,779,42],[779,42,779,420],[779,420,833,420],[833,420,833,790],[833,790,800,790],[615,790,567,790],[0,744,0,542],[0,542,85,542],[85,542,85,317],[85,317,100,317],[153,317,162,317],[162,317,162,181],[162,181,183,181],[183,181,183,10]]
inside=[[341,43,341,317],[341,42,367,42],[560,43,560,70],[560,290,560,318],[568,318,578,318],[628,318,640,318],[635,323,635,345],[635,398,635,424],[635,325,779,325],[635,424,833,424],[567,424,567,506],[567,506,630,506],[685,506,833,506],[567,506,567,548],[567,609,567,790],[85,430,205,430],[205,430,205,450],[205,500,205,538],[85,538,205,538],[202,542,202,790],[0,542,140,542],[194,542,202,542],[202,790,264,790],[492,790,567,790]]
for i,v in enumerate(outer+inside):
 wall=segment('Wall_%03d'%i,v);wall['planSegment']=v
 if v==[341,43,341,317]:wall['bearing']=True
# Verify important topology instead of guessing new openings.
G['Architecture']['bearingWall']='Kitchen / study x=341, intact; north partition alteration unverified'
for name,v in [('Entry_NorthFacing',[100,317,153,317]),('GuestNW_South',[578,318,628,318]),('CommonBath_East',[635,345,635,398]),('MasterBath_South',[630,506,685,506]),('MasterBedroom_East',[567,548,567,609]),('Storage',[205,450,205,500]),('GuestSE_North',[140,542,194,542])]:door('Door_'+name,v)
window('UtilityNorth',[230,10,335,10]);window('StudyNorth',[390,42,530,42]);window('GuestNWNorth',[615,42,745,42]);window('MasterSouth',[615,790,800,790],.12,2.3,closed=True)
window('GuestSESouth',[0,744,202,744],.12,2.3,closed=True)
window('LivingTerrace',[264,790,492,790],.06,2.3,closed=True)
# North-room movable partition: proposed opening, not a permit to cut structural walls.
for i in range(5):
 a=70+i*44;b=a+43
 segment('PanelClosed_%d'%i,[560,a,560,b],2.5,0,.065,'Oak','PartitionClosed')
for i in range(5):
 o=segment('PanelFolded_%d'%i,[553+i*2,71+i*3,566+i*2,88+i*3],2.5,0,.05,'Oak','PartitionFolded')
 o.hide_render=True;o.hide_set(True)
G['PartitionClosed']['conditional']='Verify original partition before alteration'

# Basic furniture, all original geometry with consistent nominal units.
def bed(name,x,z,width=1.5):
 c(name+'_frame',x,z,.05,width+.08,2.08,.25,'Walnut',.06)
 c(name+'_mattress',x,z,.3,width,2,.20,'White',.10)
 c(name+'_duvet',x,z+18,.50,width*.97,1.35,.10,'Fabric',.08)
 c(name+'_headboard',x,z-65,.08,width+.12,.12,1.02,'Cushion',.05)
 for dx in [-width*.24,width*.24]:
  a,b=xy(x,z-42);ellipsoid(name+'_pillow',a+dx,b,.58,width*.22,.29,.08,'Fabric')
 c(name+'_bedside',x-width/S*.65,z-45,.02,.37,.40,.48,'Oak',.04)

def wardrobe(name,x,z,w,d=.6):
 c(name,x,z,.02,w,d,2.35,'Oak',.025)
 a,b=xy(x,z)
 for i in range(max(2,round(w/.48))):
  xx=a-w/2+(i+.5)*w/max(2,round(w/.48));cube(name+'_pull',xx,b-d/2-.02,1.02,.02,.025,.28,'Walnut',.008)

bed('MasterBed',704,685,1.8);wardrobe('MasterWardrobeWest',767,528,1.8,.56);wardrobe('MasterWardrobeEast',600,528,.75,.56)
bed('GuestNWBed',700,155,1.5);wardrobe('GuestNWWardrobe',725,280,1.35,.55)
bed('GuestSEBed',87,680,1.5)
se_center=Vector((*xy(87,680),0))
for obj in [o for o in bpy.data.objects if o.name.startswith('GuestSEBed')]:
 delta=obj.location-se_center;obj.location=se_center+Vector((delta.y,-delta.x,delta.z));obj.rotation_euler.z-=math.pi/2
wardrobe('GuestSEWardrobe',70,566,1.20,.55)
# Continuous wall-following desk, dual articulated monitor arms.
c('DeskNorth',450,80,.69,3.05,.65,.06,'Walnut',.025);c('DeskReturn',364,150,.69,.58,1.68,.06,'Walnut',.025)
for x in [370,536]:c('DeskDrawers',x,80,.03,.42,.55,.65,'Oak',.02)
for i,x in enumerate([435,493]):
 a,b=xy(x,80);rod('MonitorArm_%d_base'%i,(a,b+.17,.755),(a,b+.17,1.075),.025)
 rod('MonitorArm_%d_link'%i,(a,b+.17,1.075),(a+.15,b-.08,1.225),.025)
 rod('MonitorArm_%d_elbow'%i,(a+.15,b-.08,1.225),(a,b-.18,1.175),.025)
 cube('Monitor_%d'%i,a,b-.20,.995,.74,.045,.43,'Metal',.018)
 cube('MonitorScreen_%d'%i,a,b-.227,1.02,.69,.007,.37,'Screen',.008)
c('Keyboard',464,95,.755,.43,.15,.02,'Metal',.008);c('ComputerTower',364,178,.05,.24,.48,.5,'Metal',.03)
c('NAS',364,125,.79,.22,.25,.25,'Metal',.02)
def chair(name,x,z,rot=0):
 a,b=xy(x,z);o=c(name+'_seat',x,z,.41,.45,.45,.07,'Cushion',.06);o.rotation_euler.z=rot
 for dx in [-.16,.16]:
  for dy in [-.16,.16]:rod(name+'_leg',(a+dx,b+dy,.04),(a+dx,b+dy,.43),.024,'Walnut')
 back=cube(name+'_back',a-.20*math.sin(rot),b+.20*math.cos(rot),.48,.46,.09,.38,'Fabric',.08);back.rotation_euler.z=rot
chair('WorkChair',467,133,math.pi)
a,b=xy(467,133)
for obj in list(bpy.data.objects):
 if obj.name.startswith('WorkChair_leg'):bpy.data.objects.remove(obj,do_unlink=True)
rod('WorkChairColumn',(a,b,.17),(a,b,.43),.035)
for i in range(5):
 angle=i*2*math.pi/5;p=(a+.28*math.cos(angle),b+.28*math.sin(angle),.08)
 rod('WorkChairSpoke',(a,b,.18),p,.024)
 ellipsoid('WorkChairCaster',*p,.045,.035,.045,'Metal')
# Potato-shaped lounge.
sphere_at('PotatoSeat',525,151,.27,.40,.42,.14);sphere_at('PotatoBack',525,133,.46,.44,.18,.22)
for dx in [-.30,.30]:
 a,b=xy(525,151);ellipsoid('PotatoArm',a+dx,b,.42,.17,.38,.18)
# Real rectangular tabletop boardgame, map and separate decks (not mahjong).
def table(name,x,z,w,d,height=.75):
 c(name+'_top',x,z,height-.045,w,d,.045,'Walnut',.035);a,b=xy(x,z)
 for dx in [-w*.42,w*.42]:
  for dy in [-d*.36,d*.36]:cube(name+'_leg',a+dx,b+dy,.02,.06,.06,height-.065,'Walnut',.015)
table('Boardgame',463,269,1.80,.90)
c('BoardgameMap',463,269,.756,1.12,.70,.008,'Map')
for i in range(16):
 x=463+random.uniform(-31,31);z=269+random.uniform(-18,18);c('MapLand',x,z,.766,random.uniform(.05,.16),random.uniform(.05,.12),.006,'Cushion',.015)
for i in range(8):c('CardDeck',463+(-48 if i<4 else 48),250+(i%4)*12,.766,.07,.10,.015,'White',.003)
for x in [425,502]:
 for z in [221,315]:chair('GameChair',x,z,math.pi if z==315 else 0)
# Kitchen kept north; washer at south end next to foyer.
for z in [72,113,154,195,236]:
 c('KitchenBase',207,z,.03,.61,.64,.84,'Oak',.015);c('KitchenCounter',207,z,.87,.65,.65,.045,'Stone',.012)
c('SinkBasin',207,112,.92,.46,.43,.018,'Metal',.04)
a,b=xy(207,112);rod('Tap',(a+.1,b,.92),(a+.1,b,1.18),.018);rod('TapSpout',(a+.1,b,1.18),(a,b,1.18),.018)
c('InductionCooktop',207,177,.926,.50,.50,.018,'Metal',.02)
for dx in [-.13,.13]:
 for dz in [-.13,.13]:
  a,b=xy(207,177);bpy.ops.mesh.primitive_torus_add(major_segments=12,minor_segments=6,location=(a+dx,b+dz,.95),major_radius=.085,minor_radius=.005);attach(bpy.context.object,'HobRing','Metal')
c('WasherBody_SouthKitchen',207,282,.02,.60,.62,.84,'White',.025)
a,b=xy(207,282)
# Front faces west into kitchen, away from outer east wall.
ellipsoid('WasherBlackHatch',a-.307,b,.43,.017,.205,.205,'Metal');ellipsoid('WasherGlass',a-.326,b,.43,.009,.157,.157,'Screen')
c('WasherCounter',207,282,.88,.65,.65,.045,'Stone',.012)
c('Fridge',337,52,.02,.66,.70,1.9,'White',.025)
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
wall_x,wall_y=xy(341,317)
bar_z=317+.07/S
bar=rounded_slab('CoffeeBarStone',341,bar_z,1.65,.70,.865,.035,'Stone',.12)
# The notch belongs to the furniture; the structural wall stays a complete prism.
notch=cube('CounterNotchTool',wall_x,wall_y+.15,.78,.17,.312,.20,None,0,None)
mod=bar.modifiers.new('Fitted around intact wall','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=notch
bpy.context.view_layer.objects.active=bar;bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(notch,do_unlink=True)
bar['wrapsWallEnd']=True;bar['wallNotCut']=True
for side in [-1,1]:
 cube('BarWallSideCladding',wall_x+side*.091,wall_y+.12,.025,.026,.30,.84,'Oak',.005)
cube('BarWallEndCladding',wall_x,wall_y-.019,.025,.208,.026,.84,'Oak',.005)
# Concealed support is within the furniture base, with no freestanding outer leg.
cube('CoffeeBarFittedCabinet',wall_x+.40,wall_y-.02,.025,.52,.54,.84,'Oak',.018)
cube('CoffeeBarCabinetDoor',wall_x+.40,wall_y-.30,.04,.49,.018,.80,'Oak',.01)
# A compact coffee station makes this a useful transition counter.
c('CoffeeMachine',310,327,.90,.20,.25,.27,'Metal',.025)
c('CoffeeMachineFront',310,335,1.00,.15,.015,.13,'Walnut',.01)
c('CoffeeDripTray',310,339,.905,.18,.11,.016,'Metal',.005)
for xx in [355,370]:
 a,b=xy(xx,334);bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.038,depth=.075,location=(a,b,.95));attach(bpy.context.object,'CoffeeCup','White')
 bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.032,depth=.004,location=(a,b,.989));attach(bpy.context.object,'CoffeeSurface','Soil')
 bpy.ops.mesh.primitive_torus_add(major_segments=20,minor_segments=8,major_radius=.026,minor_radius=.006,location=(a+.04,b,.952),rotation=(math.pi/2,0,0));attach(bpy.context.object,'CoffeeCupHandle','White')

# Dining island-table: compact storage at one end and open knee space at the other.
c('DiningIslandBase',434,480,.03,.95,.58,.68,'Oak',.035)
rounded_slab('DiningIslandStone',401,480,2.0,.90,.71,.04,'Stone',.16)
a,b=xy(350,480);rod('DiningIslandLeg',(a,b,.03),(a,b,.71),.032,'Walnut')
for x in [360,405,450]:chair('DiningChair',x,428)
# Very soft L sofa: west back, seating east, chaise toward south.
c('LivingRug',395,657,.025,3.9,3.0,.016,'Rug',.12)
a,b=xy(477,655)
for i in range(3):
 yy=b+(i-1)*.78;ellipsoid('CloudSeat',a,yy,.28,.49,.47,.16)
 ellipsoid('CloudBack',a-.40,yy,.64,.21,.48,.28)
 ellipsoid('LoosePillow',a-.19,yy,.72,.19,.34,.20,'Cushion' if i==1 else 'Fabric')
ellipsoid('CloudArmNorth',a,b+1.08,.49,.54,.19,.20);ellipsoid('CloudChaise',a+.48,b-1.02,.28,.86,.47,.16)
table('CoffeeTable',384,652,.73,1.05,.34)
c('TVConsole',230,655,.03,.38,2.0,.42,'Walnut',.04)
c('TVBlackFrame',214,655,.65,.055,1.58,.91,'Metal',.02);c('TVDisplay',218,655,.68,.008,1.50,.83,'Screen',.005)
c('EntryConsole',145,407,.03,1.0,.35,.76,'Oak',.04)
c('StorageCabinet',153,479,.02,1.05,.48,1.35,'Oak',.02)
# Two bathrooms only. Compact east-west tub in master bath; no room enlargement.
c('MasterBathtubOuter',755,459,.03,1.48,.70,.55,'White',.25)
c('MasterBathtubInterior',755,459,.54,1.22,.48,.035,'Water',.20)
c('MasterVanity',651,443,.04,.63,.42,.76,'Oak',.04);c('MasterBasin',651,443,.81,.51,.34,.075,'White',.08)
def toilet(name,x,z):
 c(name+'_base',x,z,.02,.35,.46,.32,'White',.12);c(name+'_seat',x,z,.34,.40,.53,.08,'White',.14);c(name+'_tank',x,z-19,.09,.38,.16,.67,'White',.05)
toilet('MasterToilet',601,477);toilet('CommonToilet',735,392)
c('CommonVanity',680,344,.03,.62,.43,.75,'Oak',.03);c('CommonBasin',680,344,.80,.51,.34,.07,'White',.06)
c('CommonShowerTray',742,353,.03,.72,.74,.025,'Tile',.03)
segment('ShowerGlass',[710,327,710,376],1.9,.05,.015,'Glass','Glazing')
# Terrace railing following actual left curved contour, low and open.
rail=[(17,744),(17,944),(32,950),(534,950),(549,946),(563,937),(576,921),(584,899),(586,886),(586,790)]
for i in range(len(rail)-1):
 a,b=xy(*rail[i]),xy(*rail[i+1]);rod('TerraceRailTop',(*a,1.1),(*b,1.1),.025,'Metal','Terrace')
 rod('TerraceRailBottom',(*a,.13),(*b,.13),.018,'Metal','Terrace')
 length=(Vector(a)-Vector(b)).length
 for j in range(max(1,math.ceil(length/.70))+1):
  p=Vector(a).lerp(Vector(b),j/max(1,math.ceil(length/.70)));rod('TerracePost',(p.x,p.y,.08),(p.x,p.y,1.1),.018,'Metal','Terrace')
# Modular continuous wave ribbon; fine seams and four casters under each module.
for i in range(7):
 xa=43+i*70;xb=xa+69
 pts=[]
 for j in range(9):
  xx=xa+(xb-xa)*j/8;pts.append((xx,932+12*math.sin((xx-43)/70*math.pi*2)))
 for j in range(8,-1,-1):
  xx=xa+(xb-xa)*j/8;pts.append((xx,900+12*math.sin((xx-43)/70*math.pi*2)))
 h=.40+.045*math.sin(i*1.8)
 poly('WavePlanter_%d'%i,pts,.12,h,'Oak','Terrace')
 inner=[(x, (z+916)/2) for x,z in pts];poly('PlanterSoil_%d'%i,inner,.12+h,.015,'Soil','Terrace')
 for xx in [xa+8,xb-8]:
  for zz in [908,927]:sphere_at('Caster',xx,zz,.075,.045,.035,.045,'Metal','Terrace')
 for j in range(9):
  xx=xa+6+j*7;zz=915+random.uniform(-6,6);a,b=xy(xx,zz);t=.15+random.random()*.20
  rod('PlantStem',(a,b,h+.13),(a,b,h+.13+t),.008,'Foliage','Terrace')
  for k in range(3):ellipsoid('Leaves',a+random.uniform(-.08,.08),b+random.uniform(-.06,.06),h+.2+t*k/3,.10,.045,.05,'Foliage' if k%2 else 'LeafLight','Terrace')
  if j%3==0:ellipsoid('WhiteFlower',a,b,h+.18+t,.055,.055,.04,'Flower','Terrace')
# Corner modules bend along southwest curve without blocking access.
for idx,(xx,zz,ang) in enumerate([(553,908,.3),(567,872,.95)]):
 o=c('CornerPlanter',xx,zz,.12,.42,.73,.40,'Oak',.10,'Terrace');o.rotation_euler.z=ang
 for j in range(4):sphere_at('CornerPlant',xx+random.uniform(-7,7),zz+random.uniform(-15,15),.66,.13,.11,.18,'Foliage','Terrace')
 for d in [-10,10]:sphere_at('CornerCaster',xx,zz+d,.075,.045,.035,.045,'Metal','Terrace')
for x in [285,405]:
 sphere_at('OutdoorChairSeat',x,846,.32,.36,.36,.15,'Fabric','Terrace');sphere_at('OutdoorChairBack',x,826,.52,.36,.12,.29,'Fabric','Terrace')
 for dx in [-.22,.22]:
  a,b=xy(x,846);rod('OutdoorChairLeg',(a+dx,b,.04),(a+dx,b,.33),.025,'Walnut','Terrace')
table('TerraceSideTable',345,847,.46,.46,.43)
# Useful native viewport and cameras.
scene=bpy.context.scene;scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
scene['status']='CONCEPT - no measured internal dimensions; nominal furniture sizes, uncertain walls/clearances not approved'
scene['orientation']='North +Y. Entry on right foyer north horizontal edge. Master SW, kitchen NE.'
scene['model_revision']='2026-11-08-south-facade-wall-wrap-bar'
scene['room_count']='Four original rooms, one used as open study; TWO bathrooms'
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.75,.79,.82,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
for loc,power,size in [((1,-4,14),2200,10),((-7,6,12),1700,8)]:
 bpy.ops.object.light_add(type='AREA',location=loc);light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size
 light.rotation_euler=(Vector((0,0,0))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(7,-18,26));cam=bpy.context.object;cam.name='Camera_WholeHome';cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=21.8;scene.camera=cam
for area in (bpy.context.screen.areas if bpy.context.screen else []):
 if area.type=='VIEW_3D':
  area.spaces.active.shading.type='MATERIAL';area.spaces.active.region_3d.view_distance=23
  area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
# Verify key invariants in the authored source before export.
assert len([o for o in bpy.data.objects if o.name.endswith('_tank')])==2
assert 'Door_MasterBath_South' in bpy.data.objects and 'Door_MasterBedroom_East' in bpy.data.objects
assert 'Door_Entry_NorthFacing' in bpy.data.objects
assert not any('StudySouthDoor' in o.name for o in bpy.data.objects)
for o in bpy.data.objects:
 if o.type=='MESH' and o.parent==G['PartitionFolded']:o.hide_render=True;o.hide_set(True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'home-21101.blend'))
# Export geometry, excluding camera/lights; include hidden folded option as a named variant.
import logging
logging.getLogger('io_scene_gltf2').setLevel(logging.ERROR)
bpy.ops.export_scene.gltf(filepath=str(OUT/'home-21101-raw.glb'),export_format='GLB',export_extras=True,export_cameras=False,export_lights=False,use_visible=False,export_apply=True)
dimensions={'units':'m','surveyed':False,'masterMattress':[1.8,2.0,.20],'guestMattress':[1.5,2.0,.20],'wardrobeDepth':.56,'wardrobeHeight':2.35,'deskHeight':.75,'deskDepth':.65,'diningIsland':[2.0,.90,.75],'boardgameTable':[1.80,.90,.75],'sofaSeatHeight':.44,'sofaBackHeight':.92,'coffeeBar':[1.65,.70,.90],'barWrapNotchWidth':.17,'bearingWallThickness':.15,'coffeeBarStools':0,'doorHeight':2.12,'wallHeight':H}
(OUT/'nominal-dimensions.json').write_text(json.dumps(dimensions,indent=2),encoding='utf-8')
manifest={'status':scene['status'],'nominalCoordinateScale':S,'notSurveyed':True,'wallHeight':H,'objects':len(bpy.data.objects),'meshes':len([o for o in bpy.data.objects if o.type=='MESH']),'bathrooms':2,'variants':['PartitionClosed','PartitionFolded'],'source':'Blender 4.5 authoring script','revision':scene['model_revision'],'terraceReferenceArea':30.36}
(OUT/'model-info.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
# Render a genuine Blender preview with a low-wall cutaway; native file retains full-height walls.
for o in G['Architecture'].children:
 if o.get('wall'):o.scale.z=.34
for o in G['Doors'].children:o.scale.z=.34;o.location.z*=.34
for o in G['Glazing'].children:o.scale.z=.34;o.location.z*=.34
for o in G['PartitionClosed'].children:o.scale.z=.34;o.location.z*=.34
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
scene.render.resolution_x=1500;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.filepath=str(OUT/'blender-preview.png')
scene.view_settings.view_transform='AgX';scene.render.film_transparent=False
bpy.ops.render.render(write_still=True)
print('HOME_MODEL_READY',json.dumps(manifest),flush=True)
