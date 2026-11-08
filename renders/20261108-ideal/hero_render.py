import bpy, math, random, sys, json
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
SOURCE=ROOT/'renders/20261108/interior-styled.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene
random.seed(1101)
S=12.85/833
def xy(x,y):
    if y>790:y=790+(y-790)*1.32125
    return ((416.5-x)*S,(481-y)*S)
def point(x,y,z):return Vector((*xy(x,y),z))
def rgb(h):
    c=[int(h[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in c)+(1,)
def mat(name,h,rough=.7,metal=0):
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes['Principled BSDF']
    bs.inputs['Base Color'].default_value=rgb(h);bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    return m
def box(name,loc,size,m,bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc);o=bpy.context.object;o.name=name;o.dimensions=size
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);o.data.materials.append(m)
    if bevel:
        mod=o.modifiers.new('Soft edges','BEVEL');mod.width=min(bevel,min(size)*.48);mod.segments=5
        mod=o.modifiers.new('Normals','WEIGHTED_NORMAL')
    return o
def cylinder(name,loc,r,depth,m):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48,radius=r,depth=depth,location=loc);o=bpy.context.object;o.name=name;o.data.materials.append(m)
    mod=o.modifiers.new('Edge softness','BEVEL');mod.width=.003;mod.segments=3
    for f in o.data.polygons:f.use_smooth=True
    return o
def line(name,a,b,r,m):
    a,b=Vector(a),Vector(b);v=b-a;o=cylinder(name,(a+b)/2,r,v.length,m);o.rotation_euler=v.to_track_quat('Z','Y').to_euler();return o
def ellipsoid(name,p,size,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1,location=p);o=bpy.context.object;o.name=name;o.scale=size;o.data.materials.append(m)
    for f in o.data.polygons:f.use_smooth=True
    return o
oak=bpy.data.materials['Oak'];metal=bpy.data.materials['Render dark bronze'];fabric=bpy.data.materials['Fabric']
sage=fabric.copy();sage.name='Ideal sage linen';sage.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rgb('#9da997')
taupe=fabric.copy();taupe.name='Ideal taupe linen';taupe.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=rgb('#b4a38e')
# Cushions keep the sofa's original position and footprint, with relaxed linen shapes.
for i,o in enumerate(sorted([o for o in bpy.data.objects if o.name.startswith('LoosePillow')],key=lambda o:o.name)):
    p=o.location.copy();name=o.name;bpy.data.objects.remove(o,do_unlink=True)
    q=box(name,p,(.20,.55,.46),[fabric,sage,taupe][i%3],.082);q.rotation_euler.y=-.12;q.rotation_euler.x=(i-1)*.12
    for f in q.data.polygons:f.use_smooth=True

# A quiet abstract artwork on the existing west living-room wall.
art_back=mat('Ideal art paper','#ddd6c8',.9)
art_sage=mat('Ideal art sage','#91a28c',.88)
art_sand=mat('Ideal art sand','#b69d7f',.85)
ax,ay=xy(567,654)
box('Ideal oak art frame',(ax+.092,ay,1.67),(.034,1.26,.82),oak,.008)
box('Ideal art paper',(ax+.112,ay,1.67),(.009,1.19,.75),art_back)
ellipsoid('Ideal abstract sage',(ax+.119,ay+.15,1.65),(.004,.25,.27),art_sage)
ellipsoid('Ideal abstract sand',(ax+.123,ay-.21,1.56),(.004,.22,.18),art_sand)
line('Ideal thin art line',(ax+.127,ay-.34,1.90),(ax+.127,ay+.31,1.48),.0035,metal)

# A linen reading lamp in the south-west corner, away from the bedroom door.
lx,ly=xy(539,748)
cylinder('Ideal reading lamp base',(lx,ly,.045),.13,.04,metal)
line('Ideal reading lamp stem',(lx,ly,.06),(lx,ly,1.45),.009,metal)
shade=mat('Ideal linen shade','#e5dfd1',.85)
bs=shade.node_tree.nodes['Principled BSDF'];bs.inputs['Emission Color'].default_value=rgb('#ffe4b9');bs.inputs['Emission Strength'].default_value=.16
bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=.21,radius2=.14,depth=.28,location=(lx,ly,1.46));o=bpy.context.object;o.name='Ideal linen lamp shade';o.data.materials.append(shade)
bpy.ops.object.light_add(type='POINT',location=(lx,ly,1.37));o=bpy.context.object;o.name='Ideal warm reading light';o.data.energy=8;o.data.color=(1,.77,.50);o.data.shadow_soft_size=.15

# A slender indoor tree at the north end of the television wall.
px,py=xy(225,562)
pot=mat('Ideal greige ceramic','#b8af9f',.65);soil=mat('Ideal potting soil','#51493b',.95);leaf=mat('Ideal olive foliage','#687a60',.86);bark=mat('Ideal olive bark','#8c7c64',.8)
cylinder('Ideal ceramic planter',(px,py,.17),.135,.30,pot)
cylinder('Ideal planter soil',(px,py,.322),.123,.009,soil)
line('Ideal olive trunk',(px,py,.32),(px+.025,py,1.56),.012,bark)
for i in range(10):
    angle=i*2.4;z=.70+i*.085
    end=Vector((px+.22*math.cos(angle),py+.18*math.sin(angle),z+.17))
    start=Vector((px+.01,py,z));line('Ideal olive branch',start,end,.004,bark)
    for j in range(8):
        t=.22+j*.10;p=start.lerp(end,t)
        side=-1 if j%2 else 1;p+=Vector((side*.03*math.sin(angle),-side*.03*math.cos(angle),.015))
        o=ellipsoid('Ideal olive leaf',p,(.045,.012,.004),leaf);o.rotation_euler.z=angle+side*.7;o.rotation_euler.y=.25

# Two simple place settings leave most of the island free for everyday use.
ix,iy=xy(401,480)
linen=mat('Ideal oatmeal placemats','#c8bca7',.9);ceramic=mat('Ideal ivory stoneware','#e4e1d7',.32)
def plate(name,x,y):
    rings=[(0,.757),(.067,.757),(.097,.764),(.105,.773)];segments=48;vs=[];fs=[]
    for r,z in rings:
        for i in range(segments):
            a=i*math.pi*2/segments;vs.append((x+r*math.cos(a),y+r*math.sin(a),z))
    for j in range(len(rings)-1):
        for i in range(segments):
            a=j*segments+i;b=j*segments+(i+1)%segments;fs.append((a,b,b+segments,a+segments))
    me=bpy.data.meshes.new(name);me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(ceramic)
    for f in me.polygons:f.use_smooth=True
for offset in [.51,-.12]:
    x=ix+offset;y=iy+.18
    box('Ideal linen placemat',(x,y,.753),(.40,.29,.003),linen,.001)
    plate('Ideal dinner plate',x,y)
    line('Ideal cutlery',(x+.14,y-.08,.762),(x+.14,y+.09,.762),.003,metal)

book=bpy.data.objects.get('Render coffee table book')
table=bpy.data.objects.get('CoffeeTable_top')
top=max((table.matrix_world@Vector(v)).z for v in table.bound_box)
book.location.z=top+.014
cover=mat('Ideal book cloth cover','#8e9185',.85)
box('Ideal book cover',(book.location.x,book.location.y,top+.028),(.242,.182,.003),cover,.001)
mx,my=book.location.x-.18,book.location.y-.35
cylinder('Ideal living coffee cup',(mx,my,top+.035),.033,.064,bpy.data.materials['White'])
cylinder('Ideal living coffee',(mx,my,top+.067),.028,.002,bpy.data.materials['Soil'])
bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=8,major_radius=.022,minor_radius=.004,location=(mx+.033,my,top+.036),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='Ideal coffee handle';o.data.materials.append(bpy.data.materials['White'])

# One continuous view includes the sofa, dining island, fitted bar and north spaces.
views={
    'whole-living-dining':((240,775,1.60),(500,418,1.34),20.5),
    'whole-alternative':((245,767,1.58),(490,425,1.33),19.5)
}
cams={}
for name,(loc,target,lens) in views.items():
    bpy.ops.object.camera_add(location=point(*loc));cam=bpy.context.object;cam.name='Ideal_'+name;cam.data.type='PERSP';cam.data.lens=lens;cam.data.sensor_width=36;cam.data.clip_start=.03;cam.data.clip_end=100
    cam.data.shift_y=-.05
    cam.rotation_euler=(point(*target)-cam.location).to_track_quat('-Z','Y').to_euler();cams[name]=cam
scene.render.engine='CYCLES';scene.cycles.samples=192;scene.cycles.use_denoising=True
scene.render.resolution_x=2560;scene.render.resolution_y=1440;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.view_settings.exposure=-.5
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    if any(d.type=='OPTIX' for d in prefs.devices):
        for d in prefs.devices:d.use=d.type=='OPTIX'
        scene.cycles.device='GPU'
except:pass
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
draft='--draft' in args
scene.camera=cams['whole-living-dining']
scene['ideal_scene_note']='Finish and lived-in styling only; source architecture, bearing wall, bar and main furniture locations retained. Dimensions not surveyed.'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'ideal-living.blend'))
if draft:scene.render.resolution_percentage=40;scene.cycles.samples=32
for name,cam in cams.items():
    if not draft and name!='whole-living-dining':continue
    scene.camera=cam;scene.render.filepath=str(OUT/(name+('-draft' if draft else '')+'.png'))
    bpy.ops.render.render(write_still=True);print('IDEAL_READY',name,flush=True)
if not draft:
    (OUT/'render-manifest.json').write_text(json.dumps({'source':str(SOURCE),'renderer':'Blender Cycles','resolution':[2560,1440],'camera':views['whole-living-dining'],'surveyed':False,'note':scene['ideal_scene_note']},indent=2),encoding='utf-8')
