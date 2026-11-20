"""Fit the cabinet proposal to the November 21 plan and render the three working faces."""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / '20261121'
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


bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'home-21101.blend'))
scene = bpy.context.scene
wall = bpy.data.objects['Wall_BearingKitchenStudy']
wall_checksum = (tuple(wall.location), tuple(tuple(v.co) for v in wall.data.vertices))
joinery = bpy.data.objects.new('ThreeFaceCabinet', None)
bpy.context.collection.objects.link(joinery)
oak = material('Wrap | white oak', 'C6AB85')
oak_light = material('Wrap | pale oak', 'DDC9AB')
greige = material('Wrap | warm grey doors', 'DCD8CE', .43)
shadow = material('Wrap | bronze reveals', '5E574C', .38)
stone = material('Wrap | ivory quartz', 'EBE8E0', .38)
linen = material('Wrap | beige ceramic', 'E8DCC6', .47)
sage = material('Wrap | sage accent', '7F8E78', .65)
glow = material('Wrap | warm shelf light', 'F5DEC0', .45, 1.8)

remove = ('CoffeeBar', 'BarWall', 'CoffeeMachine', 'CoffeeDripTray', 'CoffeeCup',
          'CoffeeSurface', 'DeskReturn', 'DeskDrawers.001', 'NAS', 'ComputerTower')
for obj in list(bpy.data.objects):
    if obj.name.startswith(remove):
        bpy.data.objects.remove(obj,do_unlink=True)

# Continuous upholstery palette and the existing room and appliance positions.
bpy.data.objects['DeskNorth'].data.materials[0] = oak
for obj in bpy.data.objects:
    if obj.name.startswith('DiningIslandBase'):
        obj.data.materials[0]=oak
    if obj.name.startswith(('KitchenBase','WasherBody')):
        obj.data.materials[0]=greige

# Common datum at 2.35 m. The visible wall above stays plastered.
box('Study oak backing', (6.725,6.745,1.52,4.704,.025,H), oak, .002)
box('Kitchen oak backing', (6.975,6.995,1.13,4.704,.025,H), oak_light, .002)
box('Dining oak end panel', (6.725,6.995,4.718,4.747,.025,H), oak, .003)
box('Top edge study', (6.715,6.746,1.52,4.705,H-.027,H), oak_light, .002)
box('Top edge kitchen', (6.975,7.005,1.13,4.705,H-.027,H), oak_light, .002)
box('Top edge wall end', (6.715,7.005,4.716,4.752,H-.027,H), oak_light, .002)

# Study side. Low storage is shallow along the tabletop game zone.
box('Study desk return', (6.115,6.725,2.22,2.83,.72,.75), oak, .012)
box('Study desk return slim support', (6.125,6.16,2.77,2.81,.02,.72), shadow)
box('Study low cabinet plinth', (6.46,6.715,2.82,4.463,.025,.09), shadow)
box('Study low cabinet', (6.432,6.721,2.82,4.465,.09,.72), oak)
box('Study low cabinet top', (6.414,6.721,2.82,4.47,.72,.75), oak, .008)
for i,(a,b) in enumerate(((2.833,3.386),(3.394,3.932),(3.94,4.46)), 1):
    box(f'Study lower front {i}', (6.415,6.435,a,b,.09,.697), oak_light)
    box(f'Study lower pull {i}', (6.402,6.413,(a+b)/2-.057,(a+b)/2+.057,.626,.643), shadow)
box('Study upper cabinet carcass', (6.45,6.72,2.78,4.465,1.76,H-.035), greige)
for i in range(3):
    a=2.785+i*.56
    box(f'Study overhead front {i+1}', (6.429,6.453,a,a+.55,1.777,H-.037), greige)
for z in (1.11,1.50):
    box('Study open shelf', (6.48,6.722,2.84,4.46,z,z+.026), oak_light)
box('Study shelf light', (6.46,6.469,2.87,4.43,1.751,1.758), glow)
box('Study ventilated equipment bay', (6.53,6.715,2.92,3.32,.765,1.085), shadow, .012)
for i in range(5):
    z=.845+i*.040
    box('NAS front ventilation detail', (6.525,6.529,2.97,3.263,z,z+.009), greige, .002)
for i in range(7):
    y=3.54+i*.046
    box('Study game box', (6.52,6.706,y,y+.037,1.136,1.35+(i%3)*.039), [sage,linen,oak][i%3])
for i in range(3):
    a=3.74+i*.105
    box('Study boardgame box stack', (6.54,6.701,a,a+.095,1.529,1.587), [sage,linen,oak][i])

# Kitchen side. The full depth of the added counter is 450 mm.
box('Kitchen pantry plinth', (7.008,7.389,1.21,4.482,.023,.09), shadow)
box('Kitchen prep lower cabinets', (6.998,7.412,1.205,4.483,.09,.869), greige)
box('Kitchen prep counter', (6.98,7.43,1.19,4.49,.869,.90), stone, .003)
box('Kitchen stone splashback', (6.994,7.014,1.19,4.49,.90,1.28), stone, .002)
for i in range(5):
    a=1.217+i*.652
    for j,(z,top) in enumerate(((.105,.465),(.474,.837))):
        box(f'Kitchen drawer {i+1}-{j+1}', (7.411,7.428,a,a+.639,z,top), greige)
        box('Kitchen drawer bronze pull', (7.428,7.441,a+.239,a+.400,top-.058,top-.041), shadow)
box('Kitchen upper cabinet', (6.999,7.255,2.44,4.468,1.68,H-.035), greige)
for i in range(4):
    a=2.447+i*.503
    box('Kitchen overhead face', (7.254,7.274,a,a+.494,1.693,H-.038), greige)
box('Kitchen undercabinet light', (7.224,7.24,2.50,4.41,1.669,1.675), glow)
box('Kitchen cutting board', (7.044,7.066,2.66,2.93,.906,1.23), oak, .008)
for i,h in enumerate((.18,.22,.12)):
    y=3.47+i*.108
    cylinder('Kitchen dry-goods jar',7.16,y,.901+h/2,.042,h,linen)
    cylinder('Kitchen jar lid',7.16,y,.905+h,.044,.015,oak)

# South face. The two arms meet the side faces at their own worktop heights.
bar_outline = [(6.270,4.49),(6.718,4.49),(6.718,4.758),(7.007,4.758),
               (7.007,4.49),(7.458,4.49)]
bar_outline += south_radius(7.348,5.005,.110,0,90)
bar_outline += south_radius(6.380,5.005,.110,90,180)
bar = slab('Cabinet coffee top | U return',bar_outline,.869,.031,stone)
bar['wrapsWallEnd']=True
box('Coffee cabinet recessed toe-kick', (6.63,7.362,4.768,5.018,.026,.092), shadow)
box('Coffee cabinet carcass', (6.575,7.394,4.757,5.040,.092,.869), oak)
for i,(x1,x2) in enumerate(((6.585,6.977),(6.983,7.386)), 1):
    box(f'Coffee cabinet front {i}', (x1,x2,5.039,5.058,.101,.826), oak_light)
    box('Coffee cabinet pull', (x1+.095,x2-.095,5.059,5.077,.756,.772), shadow)
box('Coffee end display shelf', (6.704,7.016,4.747,4.95,1.48,1.508), oak_light)
box('Coffee end shelf glow', (6.731,6.988,4.793,4.92,1.474,1.480), glow)
for x in [6.64,6.77]:
    cylinder('Coffee ceramic cup',x,4.995,.938,.034,.076,linen)
    cylinder('Coffee in cup',x,4.995,.977,.028,.003,shadow)
box('Coffee machine main body', (7.151,7.378,4.797,4.992,.90,1.144), shadow, .022)
box('Coffee machine face', (7.178,7.351,4.989,5.011,1.01,1.120), greige, .008)
box('Coffee machine drip tray', (7.167,7.365,4.991,5.073,.908,.934), shadow, .006)
box('Coffee machine spout', (7.249,7.275,5.009,5.039,1.001,1.020), shadow)

# Shared dimensions come from finished face positions, not a ceiling perspective.
aisle=(8.77-.65/2)-7.441
assert abs(aisle-1.004)<1e-5
assert 4.758 > 4.747
assert wall_checksum == (tuple(wall.location), tuple(tuple(v.co) for v in wall.data.vertices))
scene['scheme']='Three cabinet faces around the intact kitchen wall'
scene['nominalKitchenAisleM']=aisle
scene['surveyed']=False

args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
draft='--draft' in args
bpy.context.preferences.filepaths.save_version=0

# Set up the renders after saving the roofless model and exporting the browser geometry.
if not draft:
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'home-21101-wall-cabinet.blend'))
    bpy.ops.export_scene.gltf(filepath=str(OUT/'wall-cabinet-raw.glb'),export_format='GLB',
                             export_extras=True,export_cameras=False,export_lights=False,export_apply=True)

def oak_grain(mat):
    nodes=mat.node_tree.nodes
    links=mat.node_tree.links
    shader=nodes.get('Principled BSDF')
    rgb=shader.inputs['Base Color'].default_value[:3]
    xyz=nodes.new('ShaderNodeTexCoord')
    stretch=nodes.new('ShaderNodeVectorMath')
    stretch.operation='MULTIPLY'
    stretch.inputs[1].default_value=(82,82,3.9)
    noise=nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=1
    noise.inputs['Detail'].default_value=2.5
    ramp=nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(*(v*.82 for v in rgb),1)
    ramp.color_ramp.elements[1].color=(*(min(1,v*1.09) for v in rgb),1)
    links.new(xyz.outputs['Object'],stretch.inputs[0])
    links.new(stretch.outputs[0],noise.inputs['Vector'])
    links.new(noise.outputs['Fac'],ramp.inputs[0])
    links.new(ramp.outputs[0],shader.inputs['Base Color'])


for mat in (oak,oak_light):
    oak_grain(mat)
ceiling=material('Render ceiling', 'F1EFE8', .88)
slab('Render ceiling', PLAN['footprint'][:7]+[(9.80,11.79),(9.80,12.65)]+PLAN['footprint'][14:], 2.8,.10,ceiling)
for obj in list(bpy.data.objects):
    if obj.type=='LIGHT':
        bpy.data.objects.remove(obj,do_unlink=True)


def area(name, loc, target, power, size, size_y, color):
    bpy.ops.object.light_add(type='AREA',location=point(*loc))
    obj=bpy.context.object
    obj.name=name
    obj.data.energy=power
    obj.data.shape='RECTANGLE'
    obj.data.size=size
    obj.data.size_y=size_y
    obj.data.color=color
    obj.rotation_euler=(point(*target)-obj.location).to_track_quat('-Z','Y').to_euler()


day=(.95,.97,1)
interior=(1,.93,.85)
area('North study daylight',(5.4,1.12,1.65),(5.4,3,1),300,2,.95,day)
area('South living daylight',(7.0,12.86,1.8),(6.6,8.5,.9),600,4,1.9,day)
area('Study fill',(5.23,3.41,2.72),(5.55,3.55,0),85,2.1,1.45,interior)
area('Kitchen fill',(7.9,2.66,2.72),(7.80,2.64,0),110,1.65,3.0,interior)
area('Hall fill',(7.35,6.13,2.72),(6.9,5.1,.5),155,3.50,2.55,interior)
box('Dining pendant', (5.99,7.37,7.78,7.825,2.151,2.204), shadow,.012)
box('Dining pendant diffuser', (6.02,7.34,7.789,7.817,2.141,2.151), glow,.003)
for x in [6.15,7.21]:
    cylinder('Pendant suspension',x,7.8,2.50,.004,.60,shadow)
cylinder('Dining table vase',6.20,7.89,.84,.048,.18,linen)
for mat in (bpy.data.materials.get('Glass'),bpy.data.materials.get('SouthGlass')):
    if mat:
        shader=mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Alpha'].default_value=.12
scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.76,.82,.90,1)
scene.world.node_tree.nodes['Background'].inputs[1].default_value=.44

views={
 '01-dining-overview':((5.22,9.16,1.64),(6.76,4.39,1.18),24),
 '02-kitchen-side':((8.43,5.93,1.64),(7.27,3.25,1.27),23),
 '03-study-side':((4.25,3.93,1.59),(6.64,2.95,1.34),23)
}
scene.render.engine='CYCLES'
scene.cycles.samples=96 if not draft else 24
scene.cycles.use_denoising=True
scene.cycles.transparent_max_bounces=12
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX'
    prefs.get_devices()
    if any(d.type=='OPTIX' for d in prefs.devices):
        for device in prefs.devices:
            device.use=device.type=='OPTIX'
        scene.cycles.device='GPU'
except (AttributeError, TypeError, RuntimeError):
    pass
scene.view_settings.view_transform='AgX'
scene.view_settings.exposure=-.37
scene.render.image_settings.file_format='PNG'
scene.render.resolution_x=1800
scene.render.resolution_y=1125
scene.render.resolution_percentage=48 if draft else 100
for name,(loc,target,lens) in views.items():
    bpy.ops.object.camera_add(location=point(*loc))
    cam=bpy.context.object
    cam.name=name
    cam.data.lens=lens
    cam.data.clip_start=.05
    cam.rotation_euler=(point(*target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.camera=cam
    scene.render.filepath=str(OUT/(name+('-draft' if draft else '')+'.png'))
    bpy.ops.render.render(write_still=True)
