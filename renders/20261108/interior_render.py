import bpy, math, json, sys, random
from pathlib import Path
from mathutils import Vector
import bmesh

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
random.seed(21101)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'models/home-21101.blend'))
scene=bpy.context.scene
S=12.85/833
def xy(x,y):
    if y>790:y=790+(y-790)*1.32125
    return ((416.5-x)*S,(481-y)*S)
def point(x,y,z):return Vector((*xy(x,y),z))
def rgb(h):
    vals=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in vals)+(1,)
def mat(name,h,rough=.6,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=rgb(h)
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    return m
def socket(node,name,value):
    for s in node.inputs:
        if s.name.replace(' ','').lower()==name.replace(' ','').lower():s.default_value=value;return
def box(name,loc,size,m,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if m:o.data.materials.append(m)
    if bevel:
        mod=o.modifiers.new('Soft manufactured edges','BEVEL');mod.width=min(bevel,min(size)*.48);mod.segments=5
        mod=o.modifiers.new('Balanced normals','WEIGHTED_NORMAL')
    return o
def cylinder(name,loc,r,depth,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=r,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object;o.name=name;o.data.materials.append(m)
    bevel=o.modifiers.new('Edge radius','BEVEL');bevel.width=.002;bevel.segments=3
    for f in o.data.polygons:f.use_smooth=True
    return o
def line(name,a,b,r,m):
    a,b=Vector(a),Vector(b);v=b-a
    o=cylinder(name,(a+b)/2,r,v.length,m);o.rotation_euler=v.to_track_quat('Z','Y').to_euler();return o
def texture(m,kind='wood'):
    nt=m.node_tree;n=nt.nodes;l=nt.links;bs=n.get('Principled BSDF')
    tc=n.new('ShaderNodeTexCoord');mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY'
    mapping.inputs[1].default_value=(100,6,2) if kind=='wood' else (1,1,1)
    l.new(tc.outputs['Object'],mapping.inputs[0])
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1 if kind=='wood' else 190
    noise.inputs['Detail'].default_value=3;l.new(mapping.outputs[0],noise.inputs['Vector'])
    bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.0008
    l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
    if kind=='wood':
        base=tuple(bs.inputs['Base Color'].default_value)
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[1].position=.85
        ramp.color_ramp.elements[0].color=tuple(v*.83 for v in base[:3])+(1,)
        ramp.color_ramp.elements[1].color=tuple(min(1,v*1.06) for v in base[:3])+(1,)
        l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])

# Finish materials are render additions. Wall/door topology is inherited unchanged.
for name in ['Oak','Walnut']:
    m=bpy.data.materials[name];m.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.48;texture(m)
for name in ['Fabric','Cushion','Rug']:
    m=bpy.data.materials[name];texture(m,'cloth')
    bs=m.node_tree.nodes['Principled BSDF'];socket(bs,'Sheen Weight',.2);socket(bs,'Roughness',.85)
for name in ['Plaster']:
    texture(bpy.data.materials[name],'plaster')
for name,h in [('Plaster','#e4e3dc'),('Fabric','#dedbd3'),('Cushion','#bfb9ac'),('Rug','#bdb5a7')]:
    bpy.data.materials[name].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rgb(h)
floor=mat('Render white oak planks','#d3c6af',.48)
nt=floor.node_tree;n=nt.nodes;l=nt.links;bs=n.get('Principled BSDF')
tc=n.new('ShaderNodeTexCoord');brick=n.new('ShaderNodeTexBrick');l.new(tc.outputs['Object'],brick.inputs['Vector'])
for name,value in [('Scale',1),('Brick Width',1.4),('Row Height',.18),('Mortar Size',.0015),('Mortar Smooth',.001),('Color1',rgb('#d4c7b0')),('Color2',rgb('#c6b79e')),('Mortar',rgb('#b8ab93'))]:socket(brick,name,value)
l.new(brick.outputs['Color'],bs.inputs['Base Color'])
mapping=n.new('ShaderNodeVectorMath');mapping.operation='MULTIPLY';mapping.inputs[1].default_value=(2,160,4);l.new(tc.outputs['Object'],mapping.inputs[0])
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=1;noise.inputs['Detail'].default_value=4;l.new(mapping.outputs[0],noise.inputs['Vector'])
bump=n.new('ShaderNodeBump');bump.inputs['Distance'].default_value=.00065;bump.inputs['Strength'].default_value=.17;l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs[0],bs.inputs['Normal'])
for o in bpy.data.objects:
    if o.name.startswith('Floor_') and o.data.materials and o.data.materials[0].name=='Oak':o.data.materials[0]=floor
stone=bpy.data.materials['Stone'];socket(stone.node_tree.nodes['Principled BSDF'],'Roughness',.31)
texture(stone,'plaster')
for name in ['Glass','SouthGlass']:
    m=bpy.data.materials[name];m.node_tree.nodes.clear();n=m.node_tree.nodes;l=m.node_tree.links
    out=n.new('ShaderNodeOutputMaterial');mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.065
    trans=n.new('ShaderNodeBsdfTransparent');refl=n.new('ShaderNodeBsdfPrincipled');socket(refl,'Base Color',rgb('#d7e5e7'));socket(refl,'Roughness',.06);socket(refl,'Metallic',.8)
    l.new(trans.outputs[0],mix.inputs[1]);l.new(refl.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0])

white=mat('Render ceiling matte','#f1f0e9',.88)
metal=mat('Render dark bronze','#4a4940',.32,.65)
warm=mat('Render warm white luminaire','#fff1d9',.4)
bs=warm.node_tree.nodes['Principled BSDF'];socket(bs,'Emission Color',rgb('#fff1d9'));socket(bs,'Emission Strength',3)
curtain_mat=mat('Render ivory linen','#e8e5dc',.9);texture(curtain_mat,'cloth')
green=mat('Render stems','#6f795b',.85)

# Smooth soft furniture, preserving the original footprint and seat level.
replacement=[]
for o in list(bpy.data.objects):
    if o.name.startswith(('CloudSeat','CloudBack','CloudChaise','CloudArmNorth')):
        size=tuple(o.dimensions);loc=o.location.copy();m=o.data.materials[0];name=o.name
        bpy.data.objects.remove(o,do_unlink=True)
        q=box(name,loc,size,m,min(size)*.35)
        for f in q.data.polygons:f.use_smooth=True
    elif o.type=='MESH' and o.name.startswith(('LoosePillow','Potato','OutdoorChair')):
        mod=o.modifiers.new('Smooth upholstery silhouette','SUBSURF');mod.levels=1;mod.render_levels=2
sx,sy=xy(477,655)
box('Render sofa upholstered plinth',(sx,sy,.18),(.99,2.52,.17),bpy.data.materials['Fabric'],.07)
for px in [-.36,.36]:
    for py in [-1.02,1.02]:cylinder('Render sofa shadow foot',(sx+px,sy+py,.085),.035,.09,metal)

# Continuous kitchen worktop and individual joinery fronts.
counter=[o for o in bpy.data.objects if o.name.startswith('KitchenCounter') or o.name=='WasherCounter']
for o in counter:bpy.data.objects.remove(o,do_unlink=True)
kx,kn=xy(207,72);_,ks=xy(207,282)
worktop=box('Render continuous kitchen worktop',(kx,(kn+ks)/2,.8925),(.65,kn-ks+.65,.045),stone,.012)
for o in list(bpy.data.objects):
    if o.name.startswith('KitchenBase'):
        p=o.location
        box('Render kitchen front',(p.x-.315,p.y,.45),(.018,.60,.78),bpy.data.materials['Oak'],.006)
        box('Render recessed cabinet pull',(p.x-.327,p.y,.79),(.008,.37,.012),metal,.003)
# Correct an appliance/partition collision in the source's previous concept placement.
fridge=bpy.data.objects.get('Fridge');fx,fy=xy(314,52);fridge.location.x=fx
box('Render fridge door seam',(fx-.335,fy,.64),(.006,.64,.008),metal)
box('Render fridge handle',(fx-.345,fy-.25,1.22),(.025,.018,.40),metal,.007)
wx,wy=xy(207,282)
box('Render washer control strip',(wx-.307,wy,.75),(.012,.52,.085),bpy.data.materials['White'],.005)
cylinder('Render washer dial',(wx-.32,wy-.10,.75),.025,.016,metal,(0,math.pi/2,0))
box('Render washer display',(wx-.321,wy+.12,.75),(.009,.13,.036),metal,.003)
# Sink recess, stainless bowl, extraction hood and a shallow wall cabinet.
sink=bpy.data.objects.get('SinkBasin');sink_loc=sink.location.copy();bpy.data.objects.remove(sink,do_unlink=True)
cutter=box('Temporary sink cut',(sink_loc.x,sink_loc.y,.89),(.47,.44,.24),None,.04)
bpy.context.view_layer.objects.active=cutter
for mod in list(cutter.modifiers):bpy.ops.object.modifier_apply(modifier=mod.name)
mod=worktop.modifiers.new('Sink opening','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=cutter
bpy.context.view_layer.objects.active=worktop;bpy.ops.object.modifier_apply(modifier=mod.name)
bpy.data.objects.remove(cutter,do_unlink=True)
box('Render sink bottom',(sink_loc.x,sink_loc.y,.79),(.44,.41,.02),metal,.015)
for sign in [-1,1]:
    box('Render sink wall',(sink_loc.x+sign*.226,sink_loc.y,.85),(.015,.43,.13),metal,.006)
    box('Render sink wall',(sink_loc.x,sink_loc.y+sign*.211,.85),(.44,.015,.13),metal,.006)
hx,hy=xy(207,177)
box('Render extraction hood',(hx+.07,hy,1.68),(.43,.63,.105),metal,.018)
box('Render extraction chimney',(hx+.17,hy,2.21),(.20,.26,.98),white,.015)
for j in range(7):box('Render hood filter',(hx+.035,hy+(j-3)*.067,1.622),(.30,.025,.008),bpy.data.materials['Metal'],.003)
box('Render upper kitchen cabinet',(sink_loc.x+.15,sink_loc.y,1.95),(.28,.73,.72),bpy.data.materials['Oak'],.012)
box('Render upper cabinet door',(sink_loc.x+.001,sink_loc.y,1.95),(.018,.71,.70),bpy.data.materials['Oak'],.006)
# Coffee machine details at the existing footprint.
coffee=bpy.data.objects['CoffeeMachine'];cx,cy,cz=coffee.location
cylinder('Render coffee button',(cx-.045,cy-.131,1.095),.013,.009,metal,(math.pi/2,0,0))
cylinder('Render coffee button',(cx+.015,cy-.131,1.095),.010,.009,white,(math.pi/2,0,0))
box('Render coffee spout',(cx,cy-.144,1.025),(.033,.055,.018),metal,.006)

# Ceiling closes the rooms for ordinary eye-level interior photography.
outline=[(183,10),(367,10),(367,42),(779,42),(779,420),(833,420),(833,790),(202,790),(202,744),(0,744),(0,542),(85,542),(85,317),(162,317),(162,181),(183,181)]
pts=[xy(*p) for p in outline];count=len(pts)
verts=[(x,y,z) for z in [2.80,2.92] for x,y in pts]
faces=[tuple(range(count-1,-1,-1)),tuple(range(count,count*2))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
mesh=bpy.data.meshes.new('Render ceiling');mesh.from_pydata(verts,[],faces);mesh.update()
bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(mesh);bm.free()
o=bpy.data.objects.new('Render ceiling',mesh);bpy.context.collection.objects.link(o);o.data.materials.append(white)
# Finished door heads and a functional pelmet over the full-height screen track.
for door in list(bpy.data.objects):
    if door.get('door'):
        width=max(v.co.x for v in door.data.vertices)-min(v.co.x for v in door.data.vertices)
        head=box('Render door head casing',(door.location.x,door.location.y,2.17),(width+.07,.085,.08),bpy.data.materials['Oak'],.004)
        head.rotation_euler.z=door.rotation_euler.z
pa=point(560,70,2.65);pb=point(560,290,2.65)
box('Render folding screen pelmet',(pa+pb)/2,(.11,(pb-pa).length,.30),white)
track=(pa+pb)/2;track.z=2.485
box('Render folding screen top track',track,(.085,(pb-pa).length,.03),metal,.003)
# Low skirting follows existing wall segments; openings remain open.
for o in list(bpy.data.objects):
    if o.get('planSegment'):
        a,b,c,d=list(o['planSegment']);va=Vector((*xy(a,b),0));vb=Vector((*xy(c,d),0));v=vb-va
        if v.length<.12:continue
        normal=Vector((-v.y,v.x,0)).normalized()
        for sign in [-1,1]:
            mid=(va+vb)/2+normal*.081*sign;mid.z=.055
            sk=box('Render white skirting',mid,(v.length,.014,.07),white,.002);sk.rotation_euler.z=math.atan2(v.y,v.x)

# Soft linen side panels at the existing south opening.
for xedge,sign in [(264,1),(492,-1)]:
    a,b=xy(xedge,790);width=.48;nx=48;ny=12;vs=[];fs=[]
    for j in range(ny+1):
        for i in range(nx+1):
            u=i/nx;v=j/ny;vs.append((a+sign*u*width,b+.10+.028*math.sin(u*math.pi*16),.08+v*2.54))
    for j in range(ny):
        for i in range(nx):
            k=j*(nx+1)+i;fs.append((k,k+1,k+nx+2,k+nx+1))
    me=bpy.data.meshes.new('Linen drape');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Render linen side curtain',me);bpy.context.collection.objects.link(o);o.data.materials.append(curtain_mat)
    for f in me.polygons:f.use_smooth=True

# Tabletop accents, with enough clear tabletop for everyday use.
ix,iy=xy(401,480)
vase=mat('Render ceramic vase','#a89b84',.55)
cylinder('Render island vase',(ix-.55,iy+.04,.84),.055,.18,vase)
for j in range(3):
    tip=(ix-.55+random.uniform(-.13,.13),iy+.04+random.uniform(-.08,.08),1.12+j*.035)
    line('Render small branch',(ix-.55,iy+.04,.91),tip,.003,green)
    for k in [0,1]:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,radius=1,location=(tip[0]+.025*k,tip[1],tip[2]-.03*k));o=bpy.context.object;o.name='Render leaf';o.scale=(.04,.014,.018);o.data.materials.append(green)
# Cards and tokens are grouped as a tabletop board game, not rows of tiles.
for o in list(bpy.data.objects):
    if o.name.startswith('CardDeck'):bpy.data.objects.remove(o,do_unlink=True)
paper=mat('Render card stock','#efebdf',.78)
ink=mat('Render game ink','#688d92',.65)
for j,(px,py) in enumerate([(418,250),(514,285)]):
    a,b=xy(px,py);box('Render card deck',(a,b,.776),(.065,.095,.018),paper,.002)
    box('Render card motif',(a,b,.786),(.043,.068,.001),ink)
for j in range(10):
    a,b=xy(446+random.uniform(0,35),255+random.uniform(0,25));cylinder('Render wooden game token',(a,b,.779),.012,.02,ink if j%2 else bpy.data.materials['Walnut'])
for o in bpy.data.objects:
    if o.name.startswith('MonitorScreen'):
        m=o.data.materials[0].copy();m.name='Render monitor display';o.data.materials[0]=m
        bs=m.node_tree.nodes['Principled BSDF'];socket(bs,'Emission Color',rgb('#29434d'));socket(bs,'Emission Strength',.3)
# A book and soft folded throw add everyday scale without filling circulation space.
tx,ty=xy(384,652)
box('Render coffee table book',(tx,ty+.17,.403),(.24,.18,.025),paper,.004)
throw=mat('Render warm grey wool','#aaa598',.9);texture(throw,'cloth')
vs=[];fs=[];nx=36;ny=30
for j in range(ny+1):
    for i in range(nx+1):
        u=i/nx;v=j/ny;x=-.25+u*.57;y=-3.70-v*.57
        z=.451+.006*math.sin(u*math.pi*8)+.004*math.sin(v*math.pi*10)-max(0,-4.14-y)*.9
        vs.append((x,y,z))
for j in range(ny):
    for i in range(nx):
        k=j*(nx+1)+i;fs.append((k,k+1,k+nx+2,k+nx+1))
me=bpy.data.meshes.new('Folded throw');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new('Render folded wool throw',me);bpy.context.collection.objects.link(o);o.data.materials.append(throw)
for f in me.polygons:f.use_smooth=True

# Natural south and north window light, plus restrained warm white interior light.
for o in list(bpy.data.objects):
    if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
def area(name,location,target,power,size,size_y=None,color=(1,1,1)):
    bpy.ops.object.light_add(type='AREA',location=location);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.color=color
    o.data.shape='RECTANGLE';o.data.size=size;o.data.size_y=size_y or size
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
for name,p,q,power,size,sy in [
    ('South daylight',point(378,830,1.8),point(378,600,1),500,3.5,2.2),
    ('Study north daylight',point(463,20,1.7),point(463,200,1),250,2.2,1.8),
    ('Utility north daylight',point(280,-20,1.7),point(280,200,1),250,2.0,1.7),
    ('Living ceiling fill',point(390,610,2.72),point(390,610,0),70,3.0,3.0),
    ('Dining ceiling fill',point(400,440,2.72),point(400,440,0),50,2.4,2.4),
    ('Study ceiling fill',point(460,180,2.72),point(460,180,0),40,2.2,2.2),
    ('Kitchen ceiling fill',point(270,170,2.72),point(270,170,0),50,1.6,2.2)]:
    area(name,p,q,power,size,sy,(1,.92,.82) if 'ceiling' in name else (.94,.97,1))
for x,y in [(315,570),(490,570),(315,700),(490,700),(400,360),(285,245),(450,180)]:
    a,b=xy(x,y);cylinder('Render recessed light trim',(a,b,2.79),.044,.012,white);cylinder('Render recessed light lens',(a,b,2.78),.031,.008,warm)
box('Render linear dining pendant',(ix,iy,2.12),(1.06,.035,.035),metal,.01)
box('Render pendant diffuser',(ix,iy,2.098),(1.02,.026,.008),warm,.003)
for dx in [-.40,.40]:line('Render pendant wire',(ix+dx,iy,2.14),(ix+dx,iy,2.80),.0025,metal)
area('Dining pendant glow',(ix,iy,2.09),(ix,iy,.75),22,1.0,.04,(1,.90,.76))
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.78,.83,.9,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.35
# Bright neutral sky through glazing, without inventing a site-specific view.
wn=scene.world.node_tree.nodes;wl=scene.world.node_tree.links
ambient=wn.get('Background');visible=wn.new('ShaderNodeBackground');visible.inputs[0].default_value=(.78,.84,.92,1);visible.inputs[1].default_value=1.5
path=wn.new('ShaderNodeLightPath');mix=wn.new('ShaderNodeMixShader')
wl.new(path.outputs['Is Camera Ray'],mix.inputs[0]);wl.new(ambient.outputs[0],mix.inputs[1]);wl.new(visible.outputs[0],mix.inputs[2]);wl.new(mix.outputs[0],wn.get('World Output').inputs[0])
bpy.ops.object.light_add(type='SUN',location=point(280,940,10));sun=bpy.context.object;sun.name='Render soft south sun';sun.data.energy=1.7;sun.data.angle=.15;sun.data.color=(1,.97,.91)
sun.rotation_euler=(point(410,500,0)-sun.location).to_track_quat('-Z','Y').to_euler()

# Cameras stay inside the plan and use ordinary interior photography lenses.
specs={
    '01-living-to-kitchen':((360,740,1.55),(365,300,1.35),24,'From living room: dining island, wall-end U counter, kitchen and study'),
    '02-wall-wrap-counter':((450,405,1.52),(336,311,1.05),30,'Furniture notch wraps the intact bearing wall; kitchen and study sides'),
    '03-study-to-living':((455,140,1.50),(380,600,1.33),24,'From study: boardgame area, counter, island, living room and terrace'),
    '04-dining-and-living':((260,380,1.55),(435,678,1.22),25,'From dining area: dining island and soft L sofa facing east TV')
}
cams={}
for name,(loc,target,lens,caption) in specs.items():
    bpy.ops.object.camera_add(location=point(*loc));o=bpy.context.object;o.name='Interior_'+name;o.data.type='PERSP';o.data.lens=lens;o.data.sensor_width=36
    o.data.clip_start=.03;o.data.clip_end=120;o.rotation_euler=(point(*target)-o.location).to_track_quat('-Z','Y').to_euler();cams[name]=o
scene.render.engine='CYCLES';scene.cycles.samples=128;scene.cycles.use_denoising=True
scene.cycles.max_bounces=10;scene.cycles.transparent_max_bounces=16
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.render.resolution_x=2000;scene.render.resolution_y=1250;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.view_settings.exposure=-.65
try:scene.view_settings.look='AgX - Medium High Contrast'
except:pass
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    available=[d for d in prefs.devices if d.type=='OPTIX']
    if available:
        for d in prefs.devices:d.use=d.type=='OPTIX'
        scene.cycles.device='GPU';print('RENDER_DEVICE',[d.name for d in available],flush=True)
except Exception as e:print('GPU selection:',str(e),flush=True)
scene['render_note']='Same wall, door and main furniture plan; finish/lighting/appliance details added. Unmeasured concept. Fridge moved clear of partition. Window background is neutral lighting only, not a verified site view.'
scene.camera=cams['01-living-to-kitchen']
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'interior-styled.blend'))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
draft='--draft' in args
selected=args[args.index('--shot')+1] if '--shot' in args else None
if draft:scene.render.resolution_percentage=48;scene.cycles.samples=32
manifest={'source':str(ROOT/'models/home-21101.blend'),'surveyed':False,'renderer':'Blender Cycles','draft':draft,'notes':scene['render_note'],'shots':[]}
for name,(loc,target,lens,caption) in specs.items():
    if selected and selected!=name:continue
    scene.camera=cams[name];scene.render.filepath=str(OUT/(name+('-draft' if draft else '')+'.png'))
    bpy.ops.render.render(write_still=True)
    manifest['shots'].append({'file':Path(scene.render.filepath).name,'caption':caption,'cameraSourceCoordinates':loc,'targetSourceCoordinates':target,'lensMm':lens})
    print('INTERIOR_READY',name,flush=True)
(OUT/('draft-manifest.json' if draft else 'render-manifest.json')).write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
