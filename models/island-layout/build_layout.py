"""Furniture and door proposal on the November plan. All coordinates are in meters."""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / '20261121'
CABINET_SOURCE = OUT.parent / 'wall-cabinet'
PLAN = json.loads((SOURCE / 'plan-trace.json').read_text(encoding='utf-8'))
H = 2.35


def point(x, y, z):
    return Vector((x - 6.425, 7.05 - y, z))


def material(name, color, roughness=.52, emission=0):
    channels = [int(color[i:i+2], 16) / 255 for i in (0, 2, 4)]
    rgb = tuple(c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in channels)
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*rgb, 1)
    shader = m.node_tree.nodes.get('Principled BSDF')
    shader.inputs['Base Color'].default_value = (*rgb, 1)
    shader.inputs['Roughness'].default_value = roughness
    shader.inputs['Emission Color'].default_value = (*rgb, 1)
    shader.inputs['Emission Strength'].default_value = emission
    return m


def attach(obj, name, mat):
    obj.name = name
    obj.parent = joinery
    obj.data.materials.append(mat)
    return obj


def box(name, bounds, mat, radius=.004):
    x1, x2, y1, y2, z1, z2 = bounds
    bpy.ops.mesh.primitive_cube_add(size=1, location=point((x1+x2)/2, (y1+y2)/2, (z1+z2)/2))
    obj = bpy.context.object
    obj.dimensions = (x2-x1, y2-y1, z2-z1)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    attach(obj, name, mat)
    if radius:
        bevel = obj.modifiers.new('Edge radius', 'BEVEL')
        bevel.width = min(radius, min(obj.dimensions)*.42)
        bevel.segments = 3
        obj.modifiers.new('Weighted normals', 'WEIGHTED_NORMAL')
    return obj


def slab(name, points, z, depth, mat):
    count = len(points)
    vertices = [point(x,y,level) for level in (z,z+depth) for x,y in points]
    faces = [tuple(reversed(range(count))), tuple(range(count,2*count))]
    faces += [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name,mesh)
    bpy.context.collection.objects.link(obj)
    return attach(obj,name,mat)


def cylinder(name, x, y, z, radius, depth, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=point(x,y,z))
    obj = attach(bpy.context.object,name,mat)
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices)==4
    return obj


def south_radius(cx, cy, radius, start, stop):
    return [(cx+radius*math.cos(math.radians(start+(stop-start)*i/10)),
             cy+radius*math.sin(math.radians(start+(stop-start)*i/10))) for i in range(11)]


bpy.ops.wm.open_mainfile(filepath=str(CABINET_SOURCE/'home-21101-wall-cabinet.blend'))
scene=bpy.context.scene
wall=bpy.data.objects['Wall_BearingKitchenStudy']
bearing_snapshot=(tuple(wall.location),tuple(tuple(v.co) for v in wall.data.vertices))


def group(name,parent=None):
    obj=bpy.data.objects.new(name,None)
    bpy.context.collection.objects.link(obj)
    obj.parent=parent
    return obj


joinery=group('New furnishings')
structure=group('Proposed structural layout')
door_group=group('Proposed door leaves')
glazing_group=group('Proposed fixed glass')
open_group=group('KitchenDoorParked')
closed_group=group('KitchenDoorClosed')


def reparent(obj,parent):
    obj.parent=parent
    return obj


def wall_box(name,bounds):
    obj=box(name,bounds,plaster,0)
    x1,x2,y1,y2,z1,z2=bounds
    for v in obj.data.vertices:
        v.co.z+=obj.location.z
    obj.location.z=0
    obj['wall']=True
    obj['designHeight']=2.8
    return reparent(obj,structure)


def assign(obj,mat):
    if obj.data.materials:
        obj.data.materials[0]=mat
    else:
        obj.data.materials.append(mat)


ivory=material('Ivory satin lacquer','F2EFE8',.37)
bone=material('Rounded ivory stone','E7E5DF',.30)
blue=material('Sea-salt pale blue','AFBBC2',.45)
slate=material('Soft blue-grey textile','9AABB4',.83)
silver=material('Warm silver trim','8E9697',.32)
dark=material('Warm charcoal window frames','575D5B',.40)
fabric=material('Oatmeal bouclé','EBE6DC',.78)
tile=material('Polished pearl porcelain','E7E5DF',.14)
grout=material('Pearl joints','CFCBC3',.57)
plaster=bpy.data.materials['Plaster']
light=material('Cream LED diffuser','F8EEE1',.40,2)
glass=material('Clear partition glass','B6C8CE',.13)
glass.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=.16
glass.surface_render_method='DITHERED'

prefixes=('Boardgame','MapLand','CardDeck','GameChair','DeskNorth','DeskDrawers',
          'Desk return','Study desk return','Study ventilated','NAS front','Keyboard',
          'Monitor','WorkChair','Potato','DiningIsland','DiningChair','LivingRug',
          'MasterBed','GuestNWBed','GuestSEBed','MasterWardrobe','GuestNWWardrobe','GuestSEWardrobe')
for obj in list(bpy.data.objects):
    if obj.name.startswith(prefixes) and not obj.get('wall'):
        bpy.data.objects.remove(obj,do_unlink=True)

# This replacement is a design option that requires confirmation of the existing partition.
old_partition=bpy.data.objects['Wall_NorthBedroomPartition']
assert old_partition.get('structureUnconfirmed')
bpy.data.objects.remove(old_partition,do_unlink=True)
partition_x=4.33
wall_box('Proposed north room partition',(4.28,4.38,1.414,4.71,0,2.8))['structureUnconfirmed']=True
wall_box('Proposed end next to original guest door',(3.91,4.39,4.606,4.803,0,2.8))
wall_box('Study entrance left jamb',(4.38,4.60,4.645,4.775,0,2.8))
wall_box('Study entrance head',(4.60,6.747,4.645,4.775,2.34,2.8))
wall_box('Study entrance right jamb',(6.65,6.751,4.645,4.775,0,2.34))

for name in ('GuestBedroomNW','StudyGames'):
    obj=bpy.data.objects['Floor_'+name]
    for v in obj.data.vertices:
        if abs(v.co.x-(3.91-6.425))<.00001:
            v.co.x=partition_x-6.425
    PLAN['rooms'][name]=[[partition_x if x==3.91 else x,y] for x,y in PLAN['rooms'][name]]

# Flat-front cabinetry. Existing three-sided wrap gets a warm ivory finish.
for obj in bpy.data.objects:
    if obj.type!='MESH':
        continue
    if obj.name.startswith(('Study oak','Kitchen oak','Dining oak','Top edge',
                            'Study lower front','Study low cabinet','Coffee cabinet','StorageCabinet',
                            'EntryConsole','Kitchen pantry','Kitchen prep lower','Kitchen Base','KitchenBase',
                            'Kitchen drawer','Study overhead','Study upper','Kitchen upper','Kitchen overhead')):
        assign(obj,ivory if 'pull' not in obj.name else silver)
    if obj.name.startswith(('Coffee end display','Study open shelf')):
        assign(obj,blue)
    if obj.name.startswith(('Cloud','LoosePillow')):
        assign(obj,slate if obj.name=='LoosePillow.001' else fabric)

# Main desk runs along the west partition and starts beyond the north wall and window reveal.
box('Office west desk top',(4.39,5.01,1.99,3.71,.723,.75),bone,.010)
box('Office west drawers',(4.408,4.97,2.02,2.48,.035,.722),ivory,.008)
for z in [.25,.48,.70]:
    box('Office drawer reveal',(4.971,4.975,2.04,2.462,z-.002,z+.002),silver,.001)
box('Office far leg',(4.411,4.974,3.637,3.678,.035,.722),ivory)
box('Office cable tray',(4.415,4.55,2.50,3.52,.62,.72),silver,.006)
for y in [2.55,3.18]:
    cylinder('Desk monitor pole',4.535,y,.87,.019,.24,dark)
    box('Desk monitor arm',(4.54,4.67,y-.035,y+.035,.967,1.005),dark,.008)
    box('Desk monitor',(4.651,4.693,y-.275,y+.275,.897,1.211),dark,.012)
    box('Desk monitor display',(4.693,4.697,y-.260,y+.260,.913,1.196),blue,.002)
box('Keyboard',(4.78,4.929,2.65,3.09,.752,.766),dark,.008)
box('Keyboard pad',(4.747,4.997,2.595,3.273,.7505,.752),slate,.001)
box('Desk mouse',(4.829,4.91,3.164,3.225,.753,.775),silver,.009)
box('Office chair seat',(5.14,5.60,2.62,3.10,.405,.49),fabric,.034)
box('Office chair back',(5.529,5.619,2.63,3.095,.49,.925),slate,.034)
cylinder('Office chair pedestal',5.38,2.86,.257,.045,.33,silver)
for i in range(5):
    angle=i*math.tau/5
    plate=box('Office chair base arm',(5.38,5.655,2.838,2.882,.064,.102),silver,.009)
    plate.location=point(5.38+.1375*math.cos(angle),2.86+.1375*math.sin(angle),.083)
    plate.rotation_euler.z=-angle
    cylinder('Office caster',5.38+.258*math.cos(angle),2.86+.258*math.sin(angle),.047,.028,.047,dark)
box('Office open network cubby',(6.49,6.713,3.34,3.65,.76,1.016),silver,.008)
for z in [.812,.861,.91,.959]:
    box('Office ventilation slots',(6.484,6.491,3.39,3.60,z,z+.012),dark,.003)

# Solid inward-opening study leaf. The hinge is at the left jamb of the usable opening.
box('Study leaf west jamb',(4.796,4.826,4.65,4.77,.023,2.15),ivory,.004).parent=door_group
box('Study leaf east jamb',(5.703,5.733,4.65,4.77,.023,2.15),ivory,.004).parent=door_group
box('Study leaf head jamb',(4.796,5.733,4.65,4.77,2.121,2.151),ivory,.004).parent=door_group
box('Study painted door leaf',(4.828,5.700,4.665,4.711,.047,2.121),blue,.005).parent=door_group
box('Study handle',(5.601,5.685,4.712,4.768,1.006,1.034),silver,.007).parent=door_group
box('Study threshold',(4.80,5.73,4.65,4.77,.018,.023),silver,.001).parent=door_group
for x1,x2 in [(4.60,4.792),(5.735,6.65)]:
    box('Study fixed glass',(x1+.017,x2-.017,4.688,4.704,.032,2.319),glass,0).parent=glazing_group
    for x in [x1,x2-.016]:
        box('Study side glazing profile',(x,x+.016,4.672,4.721,.023,2.34),dark,.002).parent=glazing_group
    box('Study side glazing transom',(x1,x2,4.672,4.721,2.319,2.34),dark,.002).parent=glazing_group
box('Study door upper light',(4.80,5.73,4.685,4.707,2.151,2.32),glass,0).parent=glazing_group

# Kitchen telescoping leaves stack in front of the short return, clear of the entry door.
track_y=4.865
box('Kitchen telescopic top track',(6.999,9.203,4.818,4.927,2.246,2.296),dark,.003).parent=glazing_group
box('Kitchen fixed coffee-top glass',(7.014,7.450,4.838,4.853,.905,2.246),glass,0).parent=glazing_group
for x in [6.999,7.45]:
    box('Kitchen fixed glass jamb',(x,x+.018,4.823,4.881,.898,2.26),dark,.002).parent=glazing_group
box('Kitchen fixed panel bottom frame',(7.003,7.467,4.829,4.874,.897,.926),dark,.002).parent=glazing_group
box('Kitchen café base return filler',(7.384,7.456,4.829,4.876,.02,.873),ivory,.006)
box('Kitchen upper fixed transom',(7.017,8.563,4.845,4.861,2.293,2.775),glass,0).parent=glazing_group
box('Kitchen transom top frame',(6.999,8.581,4.831,4.877,2.774,2.797),dark,.002).parent=glazing_group
for x in [6.999,8.563]:
    box('Kitchen transom side frame',(x,x+.018,4.831,4.877,2.288,2.797),dark,.002).parent=glazing_group


def kitchen_leaf(parent,x1,x2,y,leaf):
    frame=.019
    box(f'{leaf} glass',(x1+frame,x2-frame,y-.006,y+.006,.049,2.225),glass,0).parent=parent
    for x in [x1,x2-frame]:
        box(f'{leaf} side rail',(x,x+frame,y-.012,y+.012,.035,2.246),dark,.002).parent=parent
    for z1,z2 in [(.035,.055),(2.225,2.246)]:
        box(f'{leaf} top or bottom rail',(x1,x2,y-.012,y+.012,z1,z2),dark,.002).parent=parent


for i in range(3):
    y=track_y+(i-1)*.029
    kitchen_leaf(open_group,8.59,9.19,y,f'Parked panel {i+1}')
    x=7.456+i*.570
    kitchen_leaf(closed_group,x,x+.600,y,f'Closed panel {i+1}')
for obj in closed_group.children:
    obj.hide_set(True)
    obj.hide_render=True
closed_group['defaultHidden']=True

# Coffee hardware moves clear of both the fixed return and the sliding track.
for obj in bpy.data.objects:
    if obj.name.startswith('Coffee machine'):
        obj.location.x-=.74
    if obj.name.startswith(('Coffee ceramic cup','Coffee in cup')):
        obj.location.x+=.45
        obj.location.y-=.045

# Three bedrooms share a west-oriented bed and flat-front storage.
def bedroom_bed(name,head_x,center_y,width,length,head_height):
    bounds=(center_y-width/2,center_y+width/2)
    y1,y2=bounds
    box(name+' platform',(head_x+.01,head_x+length+.09,y1-.04,y2+.04,.06,.32),ivory,.032)
    box(name+' mattress',(head_x+.042,head_x+length+.052,y1,y2,.32,.513),fabric,.054)
    box(name+' low headboard',(head_x-.018,head_x+.055,y1-.075,y2+.075,.215,head_height),slate,.029)
    box(name+' duvet',(head_x+.54,head_x+length+.038,y1+.032,y2-.032,.51,.591),fabric,.033)
    for shift in [-width*.226,width*.226]:
        y=center_y+shift
        box(name+' pillow',(head_x+.13,head_x+.48,y-.201,y+.201,.513,.601),ivory,.036)
    box(name+' salt-blue throw',(head_x+length-.46,head_x+length+.02,y1+.036,y2-.037,.588,.619),slate,.015)


def east_wardrobe(name,x1,x2,y_start,y_end,count):
    box(name+' recessed toe-kick',(x1+.061,x2,y_start+.013,y_end-.013,.02,.085),dark,.003)
    box(name+' body',(x1+.02,x2,y_start,y_end,.085,2.43),ivory,.006)
    bay=(y_end-y_start)/count
    for i in range(count):
        y=y_start+i*bay
        box(name+f' panel {i+1}',(x1,x1+.020,y+.003,y+bay-.003,.09,2.421),ivory,.003)
        box(name+' recessed pull',(x1-.002,x1+.004,y+bay-.040,y+bay-.025,.924,1.125),silver,.002)


bedroom_bed('Master west-head bed',.28,10.73,1.8,2.0,1.04)
box('Master north nightstand',(.25,.69,9.39,9.76,.05,.49),ivory,.032)
box('Master south nightstand',(.25,.69,11.69,12.09,.05,.49),ivory,.032)
east_wardrobe('Master east wardrobes',3.207,3.793,9.49,12.30,5)
bedroom_bed('NW west-head bed',1.002,3.36,1.5,2.0,.78)
box('NW bedside cabinet',(1.01,1.38,2.16,2.51,.05,.48),ivory,.022)
east_wardrobe('NW east wardrobes',3.683,4.27,1.62,3.94,4)
bedroom_bed('SE west-head bed',9.955,10.57,1.5,2.0,.93)
box('SE bedside cabinet',(9.939,10.27,11.39,11.64,.05,.47),ivory,.023)
# The narrow southeast bedroom uses the north wall for its matching cabinet.
box('SE north wardrobe body',(10.48,12.54,8.455,9.054,.065,2.41),ivory,.008)
for i in range(4):
    x=10.49+i*.507
    box(f'SE north wardrobe front {i+1}',(x,x+.499,9.054,9.077,.087,2.402),ivory,.004)

# One island for dining and a game board, with three seats on each long side.
island_x1,island_x2,island_n,island_s=5.58,7.78,7.25,8.25
box('Game island top',(island_x1,island_x2,island_n,island_s,.716,.758),bone,.021)
box('Game island rounded storage end',(5.65,6.18,7.575,7.925,.041,.716),ivory,.067)
for z in [.273,.493]:
    box('Island north drawer line',(5.70,6.12,7.571,7.577,z,z+.005),silver,.002)
box('Game island thin outer support',(7.63,7.687,7.452,8.048,.033,.716),ivory,.012)
for x in [5.97,6.65,7.31]:
    for y in [6.96,8.54]:
        box('Island chair seat',(x-.218,x+.218,y-.214,y+.214,.418,.469),fabric,.023)
        back=y-.217 if y<island_n else y+.217
        box('Island chair back',(x-.225,x+.225,back-.027,back+.027,.456,.83),blue,.022)
        for dx in [-.158,.158]:
            for dy in [-.153,.153]:
                cylinder('Island chair leg',x+dx,y+dy,.216,.016,.406,silver)
box('Island table tray',(6.36,6.71,7.54,7.84,.759,.771),slate,.006)
for y in [7.62,7.76]:
    cylinder('Island ceramic tumbler',6.516,y,.817,.036,.09,ivory)

# Dry-area tile is continuous on a single 800-mm grid through the house.
dry_rooms=('Living','Kitchen','StudyGames','MasterBedroom','GuestBedroomNW','GuestBedroomSE')
for room in dry_rooms:
    assign(bpy.data.objects['Floor_'+room],tile)


def grid_spans(polygon, axis, at):
    cross=[]
    other=1-axis
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if min(a[axis],b[axis])<=at<max(a[axis],b[axis]):
            t=(at-a[axis])/(b[axis]-a[axis])
            cross.append(a[other]+t*(b[other]-a[other]))
    cross.sort()
    return zip(cross[::2],cross[1::2])


vertices=[]
faces=[]
for room in dry_rooms:
    poly=PLAN['rooms'][room]
    for axis in [0,1]:
        for step in range(1,17):
            at=step*.80
            for a,b in grid_spans(poly,axis,at):
                i=len(vertices)
                sides=((at-.0016,a),(at+.0016,a),(at+.0016,b),(at-.0016,b))
                vertices.extend(point(x,y,.0187) if axis==0 else point(y,x,.0188) for x,y in sides)
                faces.append((i,i+3,i+2,i+1) if axis==0 else (i,i+1,i+2,i+3))
mesh=bpy.data.meshes.new('800 mm continuous grout lines')
mesh.from_pydata(vertices,[],faces)
mesh.update()
obj=bpy.data.objects.new('Pearl porcelain joint grid',mesh)
bpy.context.collection.objects.link(obj)
attach(obj,'Pearl porcelain joint grid',grout)

assert bearing_snapshot==(tuple(wall.location),tuple(tuple(v.co) for v in wall.data.vertices))
scene['scheme']='Warm Italian minimalism with sea-salt blue accents'
scene['partitionChange']='+420 mm east, conceptual and subject to wall verification'
scene['surveyed']=False
scene['islandSizeM']=[2.20,1.00,.758]
scene['studyDoorClearM']=.87
scene['kitchenDoorClearM']=1.12
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
draft='--draft' in args
bpy.context.preferences.filepaths.save_version=0
if not draft:
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'home-21101-island-layout.blend'))
    bpy.ops.export_scene.gltf(filepath=str(OUT/'island-layout-raw.glb'),export_format='GLB',
                             export_extras=True,export_cameras=False,export_lights=False,
                             use_visible=False,export_apply=True)

# Add the ceiling and light sources only for the interior renders.
ceiling=material('Soft white painted ceiling','F2F0EA',.83)
slab('Render ceiling',PLAN['footprint'][:7]+[(9.8,11.79),(9.8,12.65)]+PLAN['footprint'][14:],2.8,.10,ceiling)
for obj in list(bpy.data.objects):
    if obj.type=='LIGHT':
        bpy.data.objects.remove(obj,do_unlink=True)


def area(name,loc,target,power,size,size_y,color=(1,1,1)):
    bpy.ops.object.light_add(type='AREA',location=point(*loc))
    obj=bpy.context.object
    obj.name=name
    obj.data.energy=power
    obj.data.shape='RECTANGLE'
    obj.data.size=size
    obj.data.size_y=size_y
    obj.data.color=color
    obj.rotation_euler=(point(*target)-obj.location).to_track_quat('-Z','Y').to_euler()


day=(.95,.98,1)
warm=(1,.95,.88)
area('North office daylight',(5.39,1.12,1.68),(5.39,3,.75),270,1.8,.96,day)
area('South daylight',(6.9,12.86,1.78),(6.7,8.6,.9),570,4.1,1.85,day)
area('Master daylight',(2.01,12.79,1.59),(2.21,10.00,.8),230,2.15,1.6,day)
area('Office ceiling wash',(5.18,3.1,2.70),(5.18,3.3,.64),66,1.1,1.7,warm)
area('Kitchen ceiling wash',(7.9,2.68,2.73),(7.85,2.65,0),104,1.6,3.0,warm)
area('Dining fill',(6.99,6.62,2.73),(6.93,6.6,.6),140,2.75,2.5,warm)
area('Living fill',(6.55,10.05,2.73),(6.95,10.05,.6),71,2.8,2.15,warm)
area('Master fill',(2.65,9.7,2.73),(2.03,10.83,.75),86,1.95,1.55,warm)
box('Island silver pendant blade',(5.97,7.40,7.732,7.775,2.123,2.171),silver,.009)
box('Island pendant light',(6.02,7.35,7.74,7.767,2.114,2.124),light,.004)
for x in [6.11,7.24]:
    cylinder('Pendant suspension',x,7.754,2.477,.004,.617,silver)
scene.world.use_nodes=True
world=scene.world.node_tree.nodes['Background']
world.inputs[0].default_value=(.79,.85,.94,1)
world.inputs[1].default_value=.48
scene.render.engine='CYCLES'
scene.cycles.samples=112 if not draft else 24
scene.cycles.use_denoising=True
scene.cycles.transparent_max_bounces=14
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX'
    prefs.get_devices()
    if any(d.type=='OPTIX' for d in prefs.devices):
        for d in prefs.devices:
            d.use=d.type=='OPTIX'
        scene.cycles.device='GPU'
except (AttributeError,TypeError,RuntimeError):
    pass
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=-.34
scene.render.image_settings.file_format='PNG'
scene.render.resolution_x=1800
scene.render.resolution_y=1125
scene.render.resolution_percentage=48 if draft else 100
views={
    '01-island-and-doors':((4.50,10.15,1.63),(6.79,5.64,1.12),24),
    '02-office':((6.18,4.38,1.58),(4.62,2.49,1.18),22),
    '03-master-bedroom':((2.96,8.83,1.60),(1.99,10.92,1.15),20),
    '04-kitchen-door-closed':((8.12,6.34,1.59),(7.58,4.13,1.23),24),
}
for name,(location,target,lens) in views.items():
    close=name=='04-kitchen-door-closed'
    for obj in open_group.children:
        obj.hide_render=close
    for obj in closed_group.children:
        obj.hide_render=not close
    bpy.ops.object.camera_add(location=point(*location))
    cam=bpy.context.object
    cam.name=name
    cam.data.lens=lens
    cam.data.clip_start=.05
    cam.rotation_euler=(point(*target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.camera=cam
    scene.render.filepath=str(OUT/(name+('-draft' if draft else '')+'.png'))
    bpy.ops.render.render(write_still=True)


