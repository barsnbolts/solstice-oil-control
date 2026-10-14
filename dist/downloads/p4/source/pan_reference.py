"""Illustrative GM-family pan context, not an OEM cavity reconstruction."""
from pathlib import Path
from math import acos,cos,degrees,radians,sin,sqrt
import sys
import json
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from cadgen import build123d as bd,srgb
from design_parameters import P4_PAN_PROXY, P4_NOMINALS, STOP_ANGLE

# Public names retained for validation.py and display labels; values have one source.
PAN_LENGTH, PAN_WIDTH, PAN_DEPTH = (P4_PAN_PROXY[name] for name in
                                    ('PAN_LENGTH', 'PAN_WIDTH', 'PAN_DEPTH'))
CAGE_ORIGIN = P4_PAN_PROXY['CAGE_ORIGIN_XYZ']
CAGE_ROTATION = P4_PAN_PROXY['CAGE_ROTATION_DEG']
PICKUP_KEEP_OUT_D = P4_PAN_PROXY['PICKUP_KEEP_OUT_DIAMETER']
COVER_UNDERSIDE_Z = P4_PAN_PROXY['COVER_UNDERSIDE_Z']
OUTLINE = P4_PAN_PROXY['PAN_OUTLINE_XY']


def digital_fit_scenarios():
    """Return nominal and deliberately perturbed digital contexts.

    Perturbations are design stress cases, not measured confidence intervals or
    estimates of the actual OEM cavity. Their purpose is to reveal sensitivity.
    """
    base = dict(P4_PAN_PROXY)
    low_roof = dict(base)
    low_roof['COVER_UNDERSIDE_Z'] = base['COVER_UNDERSIDE_Z'] - 12.0
    larger_hardware = dict(base)
    larger_hardware['PICKUP_KEEP_OUT_DIAMETER'] = base['PICKUP_KEEP_OUT_DIAMETER'] * 1.25
    larger_hardware['TUBE_DIAMETER'] = base['TUBE_DIAMETER'] * 1.25
    shifted = dict(base)
    dx, dy = 12.0, -8.0
    shifted['PICKUP_CENTER_XYZ'] = (base['PICKUP_CENTER_XYZ'][0] + dx,
                                    base['PICKUP_CENTER_XYZ'][1] + dy,
                                    base['PICKUP_CENTER_XYZ'][2])
    shifted['TUBE_CENTERLINE_XYZ'] = tuple((x + dx, y + dy, z)
                                           for x, y, z in base['TUBE_CENTERLINE_XYZ'])
    narrow = dict(base)
    narrow['PAN_INNER_SCALE_XY'] = tuple(max(0.5, value - 0.04)
                                         for value in base['PAN_INNER_SCALE_XY'])
    return [
        {'name': 'nominal_visual_proxy', 'label': 'Nominal pan proxy',
         'description': 'Current editable pan proxy values.',
         'overrides': {}, 'values': base},
        {'name': 'cover_12mm_lower_stress', 'label': 'Cover underside 12 mm lower',
         'description': 'Cover underside lowered by 12 mm as a design sensitivity case.',
         'overrides': {'COVER_UNDERSIDE_Z': low_roof['COVER_UNDERSIDE_Z']}, 'values': low_roof},
        {'name': 'pickup_and_tube_25pct_larger_stress',
         'label': 'Pickup and tube 25% larger',
         'description': 'Pickup and tube test envelopes enlarged by 25 percent.',
         'overrides': {'PICKUP_KEEP_OUT_DIAMETER': larger_hardware['PICKUP_KEEP_OUT_DIAMETER'],
                       'TUBE_DIAMETER': larger_hardware['TUBE_DIAMETER']},
         'values': larger_hardware},
        {'name': 'pickup_route_offset_stress', 'label': 'Pickup route shifted +12 / −8 mm',
         'description': 'Pickup screen and tube route shifted together by +12/-8 mm in proxy X/Y.',
         'overrides': {'PICKUP_CENTER_XYZ': shifted['PICKUP_CENTER_XYZ'],
                       'TUBE_CENTERLINE_XYZ': shifted['TUBE_CENTERLINE_XYZ']}, 'values': shifted},
        {'name': 'narrower_shell_stress', 'label': 'Pan interior narrowed',
         'description': 'Pan interior scale reduced by 0.04 in X and Y.',
         'overrides': {'PAN_INNER_SCALE_XY': narrow['PAN_INNER_SCALE_XY']}, 'values': narrow},
    ]


def normalized(shape):
    return bd.Compound(children=list(shape)) if isinstance(shape,bd.ShapeList) else shape


def named(shape,label,color):
    shape.label=label;shape.color=srgb(color)
    for n,child in enumerate(shape.children):child.label=f'{label}_{n}';child.color=srgb(color)
    return shape


def pan_shell(cutaway=True, proxy=None):
    p = P4_PAN_PROXY if proxy is None else proxy
    outer=bd.Polygon(*p['PAN_OUTLINE_XY'],align=None)
    sx,sy=p['PAN_INNER_SCALE_XY']
    inner=bd.Polygon(*[(x*sx,y*sy) for x,y in p['PAN_OUTLINE_XY']],align=None)
    floor=p['PAN_FLOOR_Z']
    shell=bd.extrude(outer,amount=p['PAN_DEPTH'])-bd.extrude(
        inner,amount=p['PAN_DEPTH']+p['PAN_INNER_CUT_EXTRA']).translate((0,0,floor))
    shelf_center=p['PAN_SHELF_CENTER_XY']
    shelf_size=p['PAN_SHELF_SIZE_XY']
    shelf=inner.intersect(bd.Pos(*shelf_center)*bd.Rectangle(*shelf_size))
    shell=shell.fuse(bd.extrude(shelf,amount=p['PAN_SHELF_HEIGHT']).translate((0,0,floor)))
    # Three visual stiffening ribs echo the shallow extension in source photos.
    rib_size=p['PAN_RIB_SIZE_XYZ']
    for x in p['PAN_RIB_X_POSITIONS']:
        shell=shell.fuse(bd.Box(*rib_size,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).translate(
            (x,p['PAN_RIB_CENTER_Y'],p['PAN_RIB_BOTTOM_Z'])))
    if cutaway:
        shell=shell-bd.Box(*p['PAN_CUTAWAY_SIZE_XYZ'],
            align=(bd.Align.MIN,bd.Align.CENTER,bd.Align.MIN)).translate(p['PAN_CUTAWAY_ORIGIN_XYZ'])
    return named(shell,'REFERENCE_pan_shell_ASSUMED_INTERIOR','#B8C2C7')


def tube_segment(a,b,diameter):
    direction=tuple(y-x for x,y in zip(a,b));length=sqrt(sum(v*v for v in direction))
    tube=bd.Cylinder(diameter/2,length,
                     align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
    axis=(-direction[1],direction[0],0)
    if sqrt(sum(v*v for v in axis))>1e-10:
        tube=tube.rotate(bd.Axis((0,0,0),axis),degrees(acos(direction[2]/length)))
    return tube.translate(a)


def pickup_reference(proxy=None):
    p = P4_PAN_PROXY if proxy is None else proxy
    # A visible design keep-out, not a replicated OEM screen or tube.
    keepout=bd.Cylinder(p['PICKUP_KEEP_OUT_DIAMETER']/2,p['PICKUP_KEEP_OUT_HEIGHT']).translate(
        p['PICKUP_CENTER_XYZ'])
    named(keepout,'REFERENCE_pickup_design_test_case','#986f96')
    points=p['TUBE_CENTERLINE_XYZ']
    pipe=tube_segment(points[0],points[1],p['TUBE_DIAMETER'])
    for a,b in zip(points[1:],points[2:]):
        pipe=pipe.fuse(tube_segment(a,b,p['TUBE_DIAMETER']),bd.Sphere(p['TUBE_DIAMETER']/2).translate(a))
    pipe=pipe.fuse(bd.Sphere(p['TUBE_DIAMETER']/2).translate(points[-1]))
    named(pipe,'REFERENCE_tube_route_UNKNOWN','#986f96')
    return [keepout,pipe]


def cover_reference(lift=0, proxy=None):
    p = P4_PAN_PROXY if proxy is None else proxy
    origin = p['CAGE_ORIGIN_XYZ']
    points=p['COVER_OUTLINE_XY']
    relief_center=p['COVER_RELIEF_CENTER_XY']
    relief_size=p['COVER_RELIEF_SIZE_XY']
    profile=bd.Polygon(*points,align=None)-bd.Pos(*relief_center)*bd.Rectangle(*relief_size)
    cover=bd.extrude(profile,amount=p['COVER_THICKNESS']).translate(
        (0,origin[1],p['COVER_UNDERSIDE_Z']+lift))
    named(cover,'REFERENCE_OEM_cover_shape_and_height_UNKNOWN','#C9BEA3')
    # Raised relief is a geometric visual cue only; no mounting holes are invented.
    outer=bd.Cylinder(p['COVER_HOOD_OUTER_DIAMETER']/2,
        p['COVER_HOOD_OUTER_LENGTH'],align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).rotate(bd.Axis.X,-90)
    inner=bd.Cylinder(p['COVER_HOOD_INNER_DIAMETER']/2,
        p['COVER_HOOD_INNER_LENGTH'],align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).rotate(
            bd.Axis.X,-90).translate((0,p['COVER_HOOD_INNER_Y_OFFSET'],0))
    hood=normalized((outer-inner).intersect(bd.Box(*p['COVER_HOOD_CLIP_SIZE_XYZ'],
        align=(bd.Align.CENTER,bd.Align.MIN,bd.Align.MIN))))
    hood=hood.translate((0,origin[1]+p['COVER_HOOD_CENTER_Y_OFFSET'],p['COVER_UNDERSIDE_Z']+lift))
    named(hood,'REFERENCE_raised_pickup_relief_UNKNOWN','#C9BEA3')
    return [cover,hood]


def insert(kind,angle=0,proxy=None):
    p = P4_PAN_PROXY if proxy is None else proxy
    if kind=='baseline':
        from parts import assembly
        body=assembly(angle)
    else:
        from advanced_geometry import concept
        body=concept(kind,angle)
    body=body.rotate(bd.Axis.Z,p['CAGE_ROTATION_DEG']).translate(p['CAGE_ORIGIN_XYZ'])
    body.label='CUSTOM_'+kind+'_insert'
    return body


def scene(kind,stage='cutaway',proxy=None):
    p = P4_PAN_PROXY if proxy is None else proxy
    pan=pan_shell(cutaway=stage!='whole',proxy=p)
    if stage=='detail':
        pan=normalized(pan.intersect(bd.Box(*p['DETAIL_CROP_SIZE_XYZ']).translate(
            p['DETAIL_CROP_CENTER_XYZ'])))
        named(pan,'REFERENCE_deep_sump_cutaway_ASSUMED_INTERIOR','#B8C2C7')
    children=[pan,*pickup_reference(p)]
    body=insert(kind,proxy=p)
    if stage=='exploded':body=body.translate((0,0,p['INSERT_EXPLODED_Z']))
    children.append(body)
    if stage in ('exploded','whole'):
        lift=p['COVER_EXPLODED_LIFT'] if stage=='exploded' else 0
        children+=cover_reference(lift,proxy=p)
    if stage=='section':
        tool=bd.Box(*p['SECTION_TOOL_SIZE_XYZ'],
                    align=(bd.Align.MIN,bd.Align.CENTER,bd.Align.MIN)).translate(
                        p['SECTION_TOOL_ORIGIN_XYZ'])
        sections=[]
        for child in children:
            clipped=normalized(child.cut(tool))
            if clipped.volume>1e-8:
                clipped.label=child.label;clipped.color=child.color;sections.append(clipped)
        children=sections
    return bd.Compound(children=children,label='ILLUSTRATIVE_'+kind+'_in_pan_NOT_MEASURED_FIT')


def transform_point(point, proxy):
    angle = radians(proxy['CAGE_ROTATION_DEG'])
    c, s = cos(angle), sin(angle)
    ox, oy, oz = proxy['CAGE_ORIGIN_XYZ']
    x, y, z = point
    return (c*x-s*y+ox, s*x+c*y+oy, z+oz)


def transform_vector(vector, proxy):
    angle = radians(proxy['CAGE_ROTATION_DEG'])
    c, s = cos(angle), sin(angle)
    x, y, z = vector
    return (c*x-s*y, s*x+c*y, z)


def scene_gate_specs(kind, proxy=None):
    p = P4_PAN_PROXY if proxy is None else proxy
    if kind=='baseline':
        from parts import GATES,PIVOT_IN,PIVOT_Z
        from math import radians,cos,sin
        raw=[]
        for name,theta,xyz in GATES:
            a=radians(theta)
            raw.append({'name':name,'pivot':(xyz[0]-sin(a)*PIVOT_IN,xyz[1]+cos(a)*PIVOT_IN,PIVOT_Z),
                        'axis':(cos(a),sin(a),0),'wall_label':name+'_wall','door_label':name+'_door',
                        'moving_labels':[name+'_leaf',name+'_moving_cheek_0',name+'_moving_cheek_1']})
    else:
        from advanced_geometry import gate_specs
        raw=gate_specs(kind)
    return [{**s,'pivot':transform_point(s['pivot'],p),
             'axis':transform_vector(s['axis'],p)} for s in raw]


def scene_animation(kind, proxy=None):
    specs = scene_gate_specs(kind, proxy)
    targets=[{'labels':s['moving_labels'],'axis':s['axis'],'pivot':s['pivot'],'phase':i/len(specs)}
             for i,s in enumerate(specs)]
    duration=P4_NOMINALS['DEMO_DURATION_S']
    return (f'const gates={json.dumps(targets)};export const clips={{demo:{{label:"Illustrative pan context; arbitrary independent gate travel",'
            f'duration:{duration:g},loop:true,update(t,m){{for(const g of gates){{const a={STOP_ANGLE/2:g}*(1-Math.cos(2*Math.PI*(t/{duration:g}+g.phase)));'
            'for(const label of g.labels)m.get(label).rotate(g.axis,a,g.pivot);}}}};')


def scene_kinematics(kind, proxy=None):
    from cadgen import revolute
    specs=scene_gate_specs(kind, proxy)
    return {'mates':[revolute(s['name'],parent='#'+s['wall_label'],child='#'+s['door_label'],origin=s['pivot'],direction=s['axis'],limits=(0,STOP_ANGLE)) for s in specs],
            'poses':{'closed':{s['name']:0 for s in specs},'open':{s['name']:STOP_ANGLE for s in specs}}}
