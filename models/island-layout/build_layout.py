"""Furniture and door proposal on the November plan. All coordinates are in meters."""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Matrix, Vector

OUT = Path(__file__).resolve().parent
SOURCE = OUT.parent / '20261121'
CABINET_SOURCE = OUT.parent / 'wall-cabinet'
PLAN = json.loads((SOURCE / 'plan-trace.json').read_text(encoding='utf-8'))


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


def cut_box(obj, bounds):
    tool = box('Temporary joinery cutter', bounds, plaster, 0)
    modifier = obj.modifiers.new('Fitted opening', 'BOOLEAN')
    modifier.operation = 'DIFFERENCE'
    modifier.solver = 'EXACT'
    modifier.object = tool
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    bpy.data.objects.remove(tool, do_unlink=True)


def cylinder(name, x, y, z, radius, depth, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=point(x,y,z))
    obj = attach(bpy.context.object,name,mat)
    for face in obj.data.polygons:
        face.use_smooth = len(face.vertices)==4
    return obj


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
glazing_group=group('Proposed fixed glass')
open_group=group('KitchenDoorParked')
closed_group=group('KitchenDoorClosed')
study_open=group('StudyDoorParked')
study_closed=group('StudyDoorClosed')


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


ivory=material('Warm putty lacquer','C2B5A4',.39)
bone=material('Warm limestone','DAD0C1',.32)
blue=material('Muted clay upholstery','A08069',.44)
slate=material('Soft olive linen','959185',.84)
silver=material('Burnished bronze','6B5140',.31)
dark=material('Dark bronze profiles','48362C',.38)
walnut=material('Natural walnut','816349',.44)
fabric=material('Warm linen upholstery','E0D3C1',.83)
tile=material('Polished warm greige porcelain','D7CEC2',.17)
grout=material('Warm grey joints','AAA08E',.57)
plaster=bpy.data.materials['Plaster']
light=material('Cream LED diffuser','F8EEE1',.40,2)
def partition_glass(name, color, roughness, alpha):
    mat = material(name, color, roughness)
    mat.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value = alpha
    mat.surface_render_method = 'DITHERED'
    return mat


glass = partition_glass('Clear kitchen safety glazing','E6DDD0',.12,.11)
study_glass = partition_glass('Light smoked privacy glazing','AE9A84',.29,.37)

prefixes=('Boardgame','MapLand','CardDeck','GameChair','DeskNorth','DeskDrawers',
          'Desk return','Study desk return','Study ventilated','NAS front','Keyboard',
          'Monitor','WorkChair','Potato','DiningIsland','DiningChair','LivingRug',
          'MasterBed','GuestNWBed','GuestSEBed','MasterWardrobe','GuestNWWardrobe','GuestSEWardrobe',
          'KitchenBase','KitchenCounter','SinkBasin','Tap','InductionCooktop','HobRing',
          'Fridge','WasherCounter','StorageCabinet','Kitchen pantry','Kitchen prep',
          'Kitchen stone splashback','Kitchen drawer','Kitchen upper','Kitchen overhead',
          'Kitchen undercabinet','Kitchen cutting','Kitchen dry-goods','Kitchen jar',
          'Coffee end display','Coffee end shelf','TVConsole','TVBlackFrame','TVDisplay',
          'Door_GuestSE_West','WasherBody','WasherGlass','WasherBlackHatch')
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
wall_box('Study entrance left jamb',(4.38,4.52,4.63,4.81,0,2.8))
wall_box('Study entrance head',(4.52,6.751,4.63,4.81,2.35,2.8))
wall_box('Study entrance right jamb',(6.44,6.751,4.63,4.81,0,2.35))
wall_box('Kitchen painted header',(6.97,8.58,4.61,4.81,2.35,2.8))

for name in ('GuestBedroomNW','StudyGames'):
    obj=bpy.data.objects['Floor_'+name]
    for v in obj.data.vertices:
        if abs(v.co.x-(3.91-6.425))<.00001:
            v.co.x=partition_x-6.425
    PLAN['rooms'][name]=[[partition_x if x==3.91 else x,y] for x,y in PLAN['rooms'][name]]

# The original wall-end joinery keeps its pale oak and bronze faces.
for obj in bpy.data.objects:
    if obj.type!='MESH':
        continue
    if obj.name.startswith(('EntryConsole','TVConsole','CoffeeTable')):
        assign(obj,walnut)
    if obj.name.startswith(('Cloud','LoosePillow')):
        assign(obj,slate if obj.name=='LoosePillow.001' else fabric)

# User-confirmed north window. Clear opening and sill are provisional.
bpy.data.objects.remove(bpy.data.objects['Wall_KitchenNorth'], do_unlink=True)
window_x1, window_x2 = 7.16, 8.98
window_sill, window_head = .965, 2.23
wall_box('Kitchen north west jamb',(6.86,window_x1,0,.23,0,2.8))
wall_box('Kitchen north east jamb',(window_x2,9.25,0,.23,0,2.8))
wall_box('Kitchen north window sill',(window_x1,window_x2,0,.23,0,window_sill))
wall_box('Kitchen north window head',(window_x1,window_x2,0,.23,window_head,2.8))
box('Kitchen north porcelain sill',(window_x1,window_x2,.074,.246,.949,.967),bone,.004)
for z in [window_sill,window_head-.039]:
    reparent(box('Kitchen north window horizontal frame',(window_x1,window_x2,.09,.151,z,z+.039),dark),glazing_group)
for x in [window_x1,(window_x1+window_x2)/2,window_x2-.037]:
    reparent(box('Kitchen north window stile',(x,x+.037,.09,.151,window_sill,window_head),dark),glazing_group)
reparent(box('Kitchen north glazing',(window_x1+.037,window_x2-.037,.116,.129,
                                     window_sill+.039,window_head-.039),glass,0),glazing_group)

# A continuous L under the window and along the east wall.
east_face, east_wall, north_face = 8.514, 9.14, .855
counter = slab('Kitchen L worktop',[(6.996,.23),(east_wall,.23),(east_wall,3.67),
                                  (east_face,3.67),(east_face,north_face),(6.996,north_face)],
               .879,.033,bone)
cut_box(counter,(7.694,8.248,.336,.718,.857,.944))
north_base=box('L north cabinet carcass',(7.007,8.52,.238,.812,.087,.879),walnut,0)
cut_box(north_base,(7.687,8.255,.325,.725,.679,.914))
box('North base recessed plinth',(7.02,8.50,.241,.774,.02,.086),dark)
box('East base recessed plinth',(8.574,east_wall,.24,3.648,.02,.086),dark)
box('L east cabinet carcass',(8.545,east_wall,.24,3.655,.087,.879),walnut)
for x0,x1 in [(7.010,7.628),(7.634,8.275),(8.281,8.513)]:
    box('Window run slab front',(x0,x1,.814,.835,.088,.855),walnut,.005)
    box('North handleless reveal',(x0+.004,x1-.004,.835,.841,.846,.876),dark,.002)
for y0,y1 in [(.847,1.418),(1.425,2.090),(2.097,2.78),(2.787,3.64)]:
    for z0,z1 in [(.089,.426),(.434,.853)]:
        box('East drawer walnut front',(8.522,8.545,y0,y1,z0,z1),walnut,.004)
    box('East dark pull recess',(8.516,8.521,y0+.006,y1-.006,.846,.876),dark,.001)
box('North low upstand',(6.996,9.14,.230,.246,.91,.95),bone,.003)
box('East limestone splashback',(9.114,9.14,.246,3.64,.911,1.65),bone,.005)
box('Kitchen flush refrigerator tower',(8.555,9.14,3.68,4.285,.021,2.28),ivory,.012)
for z0,z1 in [(.088,.641),(.65,2.245)]:
    box('Integrated refrigerator door',(8.53,8.558,3.688,4.276,z0,z1),walnut,.007)
    box('Fridge recessed pull',(8.526,8.534,4.243,4.264,z1-.16,z1-.05),dark,.002)
for y0,y1 in [(1.05,1.59),(1.60,2.18),(2.19,2.77),(2.78,3.35)]:
    box('East upper cabinet',(8.79,9.14,y0,y1,1.68,2.32),ivory,.006)
    box('East upper handleless front',(8.77,8.794,y0+.004,y1-.004,1.695,2.319),ivory,.004)
box('Integrated hood fascia',(8.765,9.115,2.15,2.82,1.642,1.681),dark,.004)
box('Under-cabinet task light',(8.858,8.875,1.073,3.33,1.670,1.679),light,.002)
box('Induction black glass',(8.606,9.066,2.182,2.762,.913,.924),dark,.008)
for x in [8.74,8.93]:
    for y in [2.34,2.61]:
        bpy.ops.mesh.primitive_torus_add(major_segments=32,minor_segments=6,
                                        location=point(x,y,.925),major_radius=.069,minor_radius=.0025)
        attach(bpy.context.object,'Induction zone',silver)
box('Sink bottom',(7.706,8.236,.348,.706,.697,.713),silver,.006)
for x0,x1 in [(7.684,7.71),(8.232,8.257)]:
    box('Sink side',(x0,x1,.331,.725,.704,.911),silver,.007)
for y0,y1 in [(.325,.349),(.704,.731)]:
    box('Sink back and front rim',(7.688,8.255,y0,y1,.704,.911),silver,.004)
cylinder('Axial sink mixer stem',7.965,.292,1.024,.016,.228,silver)
box('Sink mixer spout',(7.948,7.982,.277,.423,1.124,1.153),silver,.010)
cylinder('Sink outlet',7.965,.421,1.115,.012,.025,silver)
box('North integrated dishwasher control',(7.045,7.605,.836,.841,.793,.827),ivory,.002)
box('Walnut cutting block',(8.61,8.943,1.21,1.625,.913,.929),ivory,.012)
box('Dark serving bowl base',(7.02,7.265,.365,.600,.915,.960),walnut,.022)

# Add the shallow third face of the wall-end cabinetry, keeping the L as the main work zone.
pale_oak=bpy.data.materials['Wrap | pale oak']
box('Bearing wall shallow kitchen carcass',(6.996,7.299,1.16,4.407,.087,.874),pale_oak)
box('Bearing wall shallow kitchen counter',(6.992,7.329,1.145,4.42,.875,.912),bone,.008)
box('Bearing wall kitchen recessed plinth',(7.002,7.255,1.17,4.392,.021,.087),dark)
for i in range(5):
    y=1.167+i*.648
    box('Bearing wall kitchen oak door',(7.298,7.318,y,y+.632,.09,.845),pale_oak,.004)
    box('Bearing wall kitchen shadow pull',(7.317,7.324,y+.026,y+.603,.818,.839),silver,.002)
box('Shallow cabinet link to coffee return',(6.993,7.328,4.420,4.495,.875,.912),bone,.005)

# Recess the bathroom east-side partition only inside the existing bath.
bath_old_x,bath_new_x=3.91,3.245
bath_east=bpy.data.objects['Wall_MasterBathEast']
assert not bath_east.get('bearing')
bpy.data.objects.remove(bath_east,do_unlink=True)
wall_box('Master bath original corridor return',(3.80,4.02,5.77,6.42,0,2.8))
wall_box('Master bath proposed recess partition',(3.18,3.31,6.42,8.16,0,2.8))['structureUnconfirmed']=True
bath_floor=bpy.data.objects['Floor_MasterBath']
for vertex in bath_floor.data.vertices:
    if abs(vertex.co.x-(bath_old_x-6.425))<.00001:
        vertex.co.x=bath_new_x-6.425
slab('Dining joinery niche finished floor',[(3.245,6.42),(3.91,6.42),(3.91,8.16),(3.245,8.16)],
     -.018,.036,tile)

for obj in bpy.data.objects:
    if obj.name.startswith(('MasterVanity','MasterBasin')):
        obj.location += point(2.61,6.77,0)-point(3.25,6.92,0)
toilet_old=point(3.16,7.67,0)
toilet_new=point(2.91,7.62,0)
toilet_motion=Matrix.Translation(toilet_new) @ Matrix.Rotation(-math.pi/2,4,'Z') @ Matrix.Translation(-toilet_old)
for obj in bpy.data.objects:
    if obj.name.startswith('MasterToilet'):
        obj.matrix_world=toilet_motion @ obj.matrix_world

# Both machines open toward dining; the upper wine cabinet has its own shallow carcass.
box('Dining laundry left gable',(3.31,4.057,6.52,6.554,.02,2.40),ivory)
box('Dining laundry right gable',(3.31,4.057,8.031,8.070,.02,2.40),ivory)
box('Dining laundry limestone counter',(3.31,4.073,6.52,8.07,.903,.94),bone,.008)
box('Wine cabinet painted back',(3.316,3.345,6.556,8.03,1.36,2.40),walnut)
for z in [1.366,1.685,2.009,2.371]:
    box('Wine cabinet warm wood shelf',(3.339,3.707,6.555,8.032,z,z+.026),pale_oak)
box('Wine cabinet center partition',(3.344,3.705,7.28,7.304,1.39,2.372),pale_oak)
for y in [6.63,6.73,6.83,7.40,7.50,7.61]:
    cylinder('Wine display bottle',3.565,y,1.506,.035,.19,slate)
    cylinder('Wine display neck',3.565,y,1.627,.013,.06,dark)
for y in [6.62,6.74,7.5,7.61,7.72]:
    cylinder('Glass stem',3.56,y,1.757,.009,.09,silver)
    cylinder('Glass bowl',3.56,y,1.828,.030,.07,study_glass)
box('Wine cabinet LED',(3.683,3.697,6.564,8.02,2.356,2.366),light)
for y in [6.934,7.665]:
    box('Laundry appliance body',(3.376,3.981,y-.296,y+.296,.03,.874),fabric,.022)
    drum=cylinder('Laundry appliance door',3.986,y,.443,.225,.043,dark)
    drum.rotation_euler.y=math.pi/2
    lens=cylinder('Laundry appliance porthole',4.010,y,.443,.174,.010,bpy.data.materials['Screen'])
    lens.rotation_euler.y=math.pi/2
    box('Laundry appliance controls',(3.982,3.996,y-.235,y+.235,.753,.832),silver,.006)
    knob=cylinder('Laundry control knob',4.004,y,.791,.028,.017,ivory)
    knob.rotation_euler.y=math.pi/2

laundry_door_pairs=[]
for y1,y2 in [(6.557,7.29),(7.294,8.028)]:
    middle=(y1+y2)/2
    pair=[]
    for south,north in [(y1,middle-.002),(middle+.002,y2)]:
        leaf=box('Dining laundry folding front',(4.055,4.079,south,north,.025,.901),ivory,0)
        leaf['concept']='Folding front. Operating conditions depend on selected appliance instructions.'
        pair.append(leaf)
        for i in range(4):
            y=south+.052+i*.073
            cut_box(leaf,(4.049,4.088,y,y+.042,.09,.108))
        edge=leaf.modifiers.new('Soft panel edges','BEVEL')
        edge.width=.002
        edge.segments=2
    laundry_door_pairs.append((pair,y1,y2))

# Open-floor utility store with adjustable shelving and a tall bay for luggage.
for z in [.31,.77,1.22,1.66,2.05]:
    box('Utility adjustable rear shelf',(10.285,10.629,6.674,7.451,z,z+.024),pale_oak)
for y in [6.692,7.43,8.13]:
    box('Utility slotted upright',(10.607,10.632,y,y+.018,.098,2.28),silver)
for y in [7.60,7.83]:
    box('Utility upright suitcase',(10.29,10.62,y,y+.164,.024,.665),slate,.023)
box('Utility cleaning tool rack',(9.565,10.074,8.192,8.208,1.38,1.433),pale_oak)
for x in [9.63,9.87]:
    cylinder('Utility cleaning handle',x,8.12,.817,.015,1.20,silver)

# The TV niche and flush leaf stay on the living side of the original wall.
tv_face=9.322
box('TV wall backing',(9.478,9.681,9.379,12.412,.02,2.418),pale_oak)
box('TV media plinth',(9.365,9.66,9.40,12.385,.022,.087),dark)
for i in range(4):
    y=9.395+i*.748
    box('TV low push-to-open front',(tv_face,9.499,y,y+.742,.088,.513),ivory,.004)
box('TV floating limestone ledge',(tv_face,9.687,9.389,12.401,.513,.548),bone,.006)
box('TV top aligned cabinets',(tv_face,9.684,9.385,12.405,1.97,2.425),ivory,.005)
for y1,y2 in [(9.385,9.496),(12.277,12.405)]:
    box('TV niche side panel',(tv_face,9.498,y1,y2,.548,1.97),ivory,.004)
box('TV recessed display',(9.412,9.475,9.971,11.829,.795,1.865),dark,.021)
box('TV glass',(9.404,9.413,9.994,11.806,.814,1.847),bpy.data.materials['Screen'],.016)
box('TV niche light',(9.453,9.471,9.576,12.19,1.961,1.970),light)

# Extend the original doorway reveal to the cabinet face without changing the original opening.
for y1,y2 in [(8.325,8.500),(9.342,9.38)]:
    box('Hidden bedroom jamb lining',(tv_face,9.805,y1,y2,.02,2.22),ivory)
box('Hidden bedroom upper panel',(tv_face,9.823,8.323,9.382,2.222,2.425),ivory,.004)
hidden_leaf=box('Hidden bedroom flush leaf',(tv_face,9.368,8.502,9.339,.024,2.215),ivory,.003)
reparent(hidden_leaf,glazing_group)
box('Housekeeping wall matching facing',(tv_face,9.349,8.206,8.325,.02,2.425),ivory,.003)

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

# Matching door heads, recessed guides and jambs. All sliding motion stays on the room side.
def sliding_leaf(parent,name,x1,x2,y,mat,pull=False):
    frame=.024
    z1,z2=.030,2.314
    reparent(box(name+' glazing',(x1+frame,x2-frame,y-.006,y+.006,z1+.031,z2-.025),mat,0),parent)
    for x in [x1,x2-frame]:
        reparent(box(name+' stile',(x,x+frame,y-.019,y+.019,z1,z2),dark,.003),parent)
    for lo,hi in [(z1,z1+.031),(z2-.025,z2)]:
        reparent(box(name+' rail',(x1,x2,y-.019,y+.019,lo,hi),dark,.003),parent)
    if pull:
        reparent(box(name+' narrow pull',(x1+.018,x1+.038,y+.017,y+.036,.950,1.234),silver,.004),parent)


def track(name,x1,x2,y1,y2):
    reparent(box(name+' bronze head cover',(x1,x2,y1,y2,2.314,2.35),dark,.003),glazing_group)


# One active leaf parks on the inside of the fixed glass.
track('Study',4.519,6.442,4.566,4.684)
sliding_leaf(glazing_group,'Study fixed panel',5.455,6.44,4.646,study_glass)
sliding_leaf(study_closed,'Study closed moving panel',4.527,5.497,4.596,study_glass,True)
sliding_leaf(study_open,'Study parked moving panel',5.459,6.429,4.596,study_glass,True)
for x in [4.52,6.419]:
    reparent(box('Study perimeter jamb',(x,x+.022,4.569,4.674,.019,2.315),dark,.002),glazing_group)
reparent(box('Study guide behind fixed pane',(5.452,6.439,4.577,4.653,.018,.025),dark,.002),glazing_group)

# The service box blocks the inside parking run. Both leaves stack in front of
# the right return, stopping before the actual entrance jamb.
track('Kitchen',7.467,9.203,4.809,4.931)
for i,(y,closed_x) in enumerate([(4.839,7.472),(4.889,8.046)],1):
    sliding_leaf(open_group,f'Kitchen parked leaf {i}',8.593,9.188,y,glass,i==1)
    sliding_leaf(closed_group,f'Kitchen closed leaf {i}',closed_x,closed_x+.595,y,glass,i==1)
reparent(box('Kitchen finished wall side lining',(6.974,7.474,4.743,4.815,.917,2.35),ivory,.005),glazing_group)
reparent(box('Kitchen coffee side jamb',(7.449,7.474,4.813,4.925,.02,2.35),walnut,.003),glazing_group)
reparent(box('Kitchen return stop and seal',(8.601,8.644,4.808,4.817,.019,2.35),dark,.002),glazing_group)
wall_box('Kitchen matching upper filler',(7.445,9.21,4.809,4.934,2.35,2.8))
reparent(box('Kitchen concealed guide behind return',(8.610,8.695,4.820,4.907,.018,.026),dark,.002),glazing_group)
for group_closed in [closed_group,study_closed]:
    group_closed['defaultHidden']=True
    for obj in group_closed.children:
        obj.hide_set(True)
        obj.hide_render=True

# Keep the console return shallow so it clears the entry lanes.
for obj in bpy.data.objects:
    if obj.name.startswith('Coffee machine'):
        obj.location.x-=.34
    if obj.name.startswith(('Coffee ceramic cup','Coffee in cup')):
        obj.location.x-=.008

# Three bedrooms share a west-oriented bed and flat-front storage.
def bedroom_bed(name,head_x,center_y,width,length,head_height):
    bounds=(center_y-width/2,center_y+width/2)
    y1,y2=bounds
    box(name+' platform',(head_x+.01,head_x+length+.09,y1-.04,y2+.04,.06,.32),ivory,.032)
    box(name+' mattress',(head_x+.042,head_x+length+.052,y1,y2,.32,.513),fabric,.054)
    box(name+' low headboard',(head_x-.018,head_x+.055,y1-.075,y2+.075,.215,head_height),blue,.029)
    box(name+' duvet',(head_x+.54,head_x+length+.038,y1+.032,y2-.032,.51,.591),fabric,.033)
    for shift in [-width*.226,width*.226]:
        y=center_y+shift
        box(name+' pillow',(head_x+.13,head_x+.48,y-.201,y+.201,.513,.601),ivory,.036)
    box(name+' woven throw',(head_x+length-.46,head_x+length+.02,y1+.036,y2-.037,.588,.619),slate,.015)


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

# A cabinet island with an attached lower dining wing.
island_n,island_s=7.16,8.24
box('Island full cabinet body',(5.29,6.372,7.21,8.194,.086,.873),walnut,.032)
box('Island recessed toe-kick',(5.33,6.34,7.246,8.159,.02,.086),dark,.009)
box('Island stone prep worktop',(5.244,6.424,island_n,island_s,.873,.925),bone,.022)
for y1,y2 in [(7.226,7.69),(7.696,8.178)]:
    box('Island concealed storage doors',(5.269,5.295,y1,y2,.087,.853),walnut,.008)
    box('Island cabinet finger pull',(5.264,5.271,y1+.025,y2-.025,.828,.847),dark,.003)
box('Attached lower dining worktop',(6.344,8.233,7.218,8.186,.715,.758),pale_oak,.018)
box('Dining outer inset panel support',(8.082,8.135,7.515,7.885,.029,.715),walnut,.012)
for x in [6.724,7.313,7.907]:
    for y in [6.971,8.480]:
        box('Island chair seat',(x-.212,x+.212,y-.202,y+.202,.418,.469),fabric,.023)
        back=y-.21 if y<island_n else y+.21
        box('Island chair back',(x-.214,x+.214,back-.025,back+.025,.456,.818),blue,.022)
        for dx in [-.153,.153]:
            for dy in [-.149,.149]:
                cylinder('Island chair leg',x+dx,y+dy,.216,.015,.406,silver)
box('Island table tray',(6.925,7.265,7.51,7.81,.759,.771),slate,.006)
for y in [7.587,7.727]:
    cylinder('Island ceramic tumbler',7.074,y,.817,.036,.09,ivory)

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
scene['scheme']='Warm understated Italian interiors with a split-height island'
scene['kitchenNorthWindow']='Confirmed by owner; opening width and sill height are provisional'
scene['laundryLocation']='Conditional recess at east of master bath; confirm partition and plumbing'
scene['doorFrameHeightM']=2.35
scene['partitionChange']='+420 mm east, conceptual and subject to wall verification'
scene['surveyed']=False
scene['islandHeightM']=.925
scene['diningWingHeightM']=.758
scene['bathRecessM']=bath_old_x-bath_new_x
scene['studyDoorClearM']=round(5.459-4.542,2)
scene['kitchenDoorClearM']=round(8.593-7.474,2)
scene['kitchenParking']='Stack at the dining side of the existing right return, before the entry jamb'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
draft='--draft' in args
render_only=next((arg.split('=',1)[1] for arg in args if arg.startswith('--view=')),None)
bpy.context.preferences.filepaths.save_version=0
if not draft and not render_only:
    bpy.ops.export_scene.gltf(filepath=str(OUT/'island-layout-raw.glb'),export_format='GLB',
                             export_extras=True,export_cameras=False,export_lights=False,
                             use_visible=False,export_apply=True)

# Blender resolves the grain procedurally; the browser model uses the same base colors.
def add_wood_grain(mat):
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get('Principled BSDF')
    base = tuple(shader.inputs['Base Color'].default_value)
    coord = nodes.new('ShaderNodeTexCoord')
    scale = nodes.new('ShaderNodeVectorMath')
    scale.operation = 'MULTIPLY'
    scale.inputs[1].default_value = (82,82,2.4)
    grain = nodes.new('ShaderNodeTexNoise')
    grain.inputs['Scale'].default_value = 1
    grain.inputs['Detail'].default_value = 2.5
    ramp = nodes.new('ShaderNodeValToRGB')
    for stop,pos,gain in zip(ramp.color_ramp.elements,[.20,.77],[.65,1.24]):
        stop.position = pos
        stop.color = (*(min(channel*gain,1) for channel in base[:3]),1)
    links.new(coord.outputs['Object'],scale.inputs[0])
    links.new(scale.outputs[0],grain.inputs['Vector'])
    links.new(grain.outputs['Fac'],ramp.inputs[0])
    links.new(ramp.outputs['Color'],shader.inputs['Base Color'])


for wood in [walnut,bpy.data.materials['Wrap | white oak'],bpy.data.materials['Wrap | pale oak']]:
    add_wood_grain(wood)
if not draft and not render_only:
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'home-21101-island-layout.blend'))

if '--model-only' in args:
    sys.exit(0)

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
warm=(1,.97,.93)
area('North kitchen daylight',(8.03,-.18,1.611),(8.07,2.8,.82),220,1.78,1.22,day)
area('North office daylight',(5.39,1.12,1.68),(5.39,3,.75),270,1.8,.96,day)
area('South daylight',(6.9,12.86,1.78),(6.7,8.6,.9),570,4.1,1.85,day)
area('Master daylight',(2.01,12.79,1.59),(2.21,10.00,.8),230,2.15,1.6,day)
area('Office ceiling wash',(5.18,3.1,2.70),(5.18,3.3,.64),66,1.1,1.7,warm)
area('Kitchen ceiling wash',(7.9,2.68,2.73),(7.85,2.65,0),104,1.6,3.0,warm)
area('Dining fill',(6.99,6.62,2.73),(6.93,6.6,.6),140,2.75,2.5,warm)
area('Living fill',(6.55,10.05,2.73),(6.95,10.05,.6),71,2.8,2.15,warm)
area('Laundry cabinet wash',(4.95,7.05,2.68),(3.75,7.30,.90),75,1.18,1.45,warm)
area('Utility ceiling fill',(10.04,7.43,2.68),(10.40,7.18,.9),38,.86,1.2,warm)
area('Master bath ceiling fill',(1.68,7.26,2.69),(1.80,7.04,.65),87,1.4,.93,warm)
area('Master fill',(2.65,9.7,2.73),(2.03,10.83,.75),86,1.95,1.55,warm)
box('Island silver pendant blade',(6.15,7.84,7.732,7.775,2.123,2.171),silver,.009)
box('Island pendant light',(6.20,7.79,7.74,7.767,2.114,2.124),light,.004)
for x in [6.26,7.71]:
    cylinder('Pendant suspension',x,7.754,2.477,.004,.617,silver)
scene.world.use_nodes=True
world=scene.world.node_tree.nodes['Background']
world.inputs[0].default_value=(.79,.85,.94,1)
world.inputs[1].default_value=.48
scene.render.engine='CYCLES'
scene.cycles.samples=96 if not draft else 20
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
scene.view_settings.look='AgX - Medium High Contrast'
scene.view_settings.exposure=-.42
scene.render.image_settings.file_format='PNG'
scene.render.resolution_x=1800
scene.render.resolution_y=1125
scene.render.resolution_percentage=48 if draft else 100
views={
    '01-island-and-doors':((4.46,10.24,1.65),(6.94,6.34,1.08),22),
    '02-office':((6.18,4.38,1.58),(4.62,2.49,1.18),22),
    '03-master-bedroom':((2.96,8.83,1.60),(1.99,10.92,1.15),20),
    '04-kitchen-door-closed':((6.05,8.20,1.60),(6.67,4.62,1.23),26),
    '05-kitchen-north-window':((7.55,4.38,1.62),(8.35,1.05,1.25),21),
    '06-laundry':((5.172,7.41,1.44),(3.93,7.30,1.22),16),
    '07-tv-hidden-door':((5.31,10.85,1.59),(9.34,9.96,1.18),23),
    '08-tv-hidden-door-open':((5.31,10.85,1.59),(9.34,9.96,1.18),23),
    '09-laundry-open':((5.172,7.41,1.44),(3.93,7.30,1.22),16),
    '10-utility-store':((9.59,7.72,1.51),(10.60,7.45,1.13),16),
    '11-master-bath':((2.12,8.00,1.45),(1.85,6.85,.90),15),
}
def swing_about(obj, pivot, angle):
    obj.matrix_world = Matrix.Translation(pivot) @ Matrix.Rotation(angle,4,'Z') @ Matrix.Translation(-pivot) @ obj.matrix_world


laundry_closed_matrices=[(leaf,leaf.matrix_world.copy()) for pair,_,_ in laundry_door_pairs for leaf in pair]
for name,(location,target,lens) in views.items():
    if render_only and name!=render_only:
        continue
    for leaf,matrix in laundry_closed_matrices:
        leaf.matrix_world=matrix
    if name=='08-tv-hidden-door-open':
        swing_about(hidden_leaf,point(9.346,9.312,0),-math.pi/2)
    if name=='09-laundry-open':
        north_pair,y1,y2=laundry_door_pairs[0]
        south_pair,y3,y4=laundry_door_pairs[1]
        swing_about(north_pair[0],point(4.067,y1,0),math.pi/2)
        swing_about(north_pair[1],point(4.067,(y1+y2)/2,0),math.pi/2)
        north_pair[1].location.y+=(y2-y1)/2-.033
        swing_about(south_pair[1],point(4.067,y4,0),-math.pi/2)
        swing_about(south_pair[0],point(4.067,(y3+y4)/2,0),-math.pi/2)
        south_pair[0].location.y-=(y4-y3)/2-.033
    close=name=='04-kitchen-door-closed'
    for parked,closed in [(open_group,closed_group),(study_open,study_closed)]:
        for obj in parked.children:
            obj.hide_render=close
        for obj in closed.children:
            obj.hide_render=not close
    bpy.ops.object.camera_add(location=point(*location))
    cam=bpy.context.object
    cam.name=name
    cam.data.lens=lens
    cam.data.clip_start=.05
    cam.rotation_euler=(point(*target)-cam.location).to_track_quat('-Z','Y').to_euler()
    scene.camera=cam
    scene.render.resolution_x=1125 if name in ('06-laundry','09-laundry-open','10-utility-store','11-master-bath') else 1800
    scene.render.filepath=str(OUT/(name+('-draft' if draft else '')+'.png'))
    bpy.ops.render.render(write_still=True)


