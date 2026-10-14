"""Illustrative GM-family pan context, not an OEM cavity reconstruction."""
from pathlib import Path
from math import acos,degrees,sqrt
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


def normalized(shape):
    return bd.Compound(children=list(shape)) if isinstance(shape,bd.ShapeList) else shape


def named(shape,label,color):
    shape.label=label;shape.color=srgb(color)
    for n,child in enumerate(shape.children):child.label=f'{label}_{n}';child.color=srgb(color)
    return shape


def pan_shell(cutaway=True):
    outer=bd.Polygon(*OUTLINE,align=None)
    sx,sy=P4_PAN_PROXY['PAN_INNER_SCALE_XY']
    inner=bd.Polygon(*[(x*sx,y*sy) for x,y in OUTLINE],align=None)
    floor=P4_PAN_PROXY['PAN_FLOOR_Z']
    shell=bd.extrude(outer,amount=PAN_DEPTH)-bd.extrude(
        inner,amount=PAN_DEPTH+P4_PAN_PROXY['PAN_INNER_CUT_EXTRA']).translate((0,0,floor))
    shelf_center=P4_PAN_PROXY['PAN_SHELF_CENTER_XY']
    shelf_size=P4_PAN_PROXY['PAN_SHELF_SIZE_XY']
    shelf=inner.intersect(bd.Pos(*shelf_center)*bd.Rectangle(*shelf_size))
    shell=shell.fuse(bd.extrude(shelf,amount=P4_PAN_PROXY['PAN_SHELF_HEIGHT']).translate((0,0,floor)))
    # Three visual stiffening ribs echo the shallow extension in source photos.
    rib_size=P4_PAN_PROXY['PAN_RIB_SIZE_XYZ']
    for x in P4_PAN_PROXY['PAN_RIB_X_POSITIONS']:
        shell=shell.fuse(bd.Box(*rib_size,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).translate(
            (x,P4_PAN_PROXY['PAN_RIB_CENTER_Y'],P4_PAN_PROXY['PAN_RIB_BOTTOM_Z'])))
    if cutaway:
        shell=shell-bd.Box(*P4_PAN_PROXY['PAN_CUTAWAY_SIZE_XYZ'],
            align=(bd.Align.MIN,bd.Align.CENTER,bd.Align.MIN)).translate(P4_PAN_PROXY['PAN_CUTAWAY_ORIGIN_XYZ'])
    return named(shell,'REFERENCE_pan_shell_ASSUMED_INTERIOR','#B8C2C7')


def tube_segment(a,b):
    direction=tuple(y-x for x,y in zip(a,b));length=sqrt(sum(v*v for v in direction))
    tube=bd.Cylinder(P4_PAN_PROXY['TUBE_DIAMETER']/2,length,
                     align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
    axis=(-direction[1],direction[0],0)
    if sqrt(sum(v*v for v in axis))>1e-10:
        tube=tube.rotate(bd.Axis((0,0,0),axis),degrees(acos(direction[2]/length)))
    return tube.translate(a)


def pickup_reference():
    # A visible design keep-out, not a replicated OEM screen or tube.
    keepout=bd.Cylinder(PICKUP_KEEP_OUT_D/2,P4_PAN_PROXY['PICKUP_KEEP_OUT_HEIGHT']).translate(
        P4_PAN_PROXY['PICKUP_CENTER_XYZ'])
    named(keepout,'REFERENCE_pickup_60mm_DESIGN_TEST_CASE','#986f96')
    points=P4_PAN_PROXY['TUBE_CENTERLINE_XYZ']
    pipe=tube_segment(points[0],points[1])
    for a,b in zip(points[1:],points[2:]):
        pipe=pipe.fuse(tube_segment(a,b),bd.Sphere(P4_PAN_PROXY['TUBE_DIAMETER']/2).translate(a))
    named(pipe,'REFERENCE_tube_route_UNKNOWN','#986f96')
    return [keepout,pipe]


def cover_reference(lift=0):
    points=P4_PAN_PROXY['COVER_OUTLINE_XY']
    relief_center=P4_PAN_PROXY['COVER_RELIEF_CENTER_XY']
    relief_size=P4_PAN_PROXY['COVER_RELIEF_SIZE_XY']
    profile=bd.Polygon(*points,align=None)-bd.Pos(*relief_center)*bd.Rectangle(*relief_size)
    cover=bd.extrude(profile,amount=P4_PAN_PROXY['COVER_THICKNESS']).translate(
        (0,CAGE_ORIGIN[1],COVER_UNDERSIDE_Z+lift))
    named(cover,'REFERENCE_OEM_cover_shape_and_height_UNKNOWN','#C9BEA3')
    # Raised relief is a geometric visual cue only; no mounting holes are invented.
    outer=bd.Cylinder(P4_PAN_PROXY['COVER_HOOD_OUTER_DIAMETER']/2,
        P4_PAN_PROXY['COVER_HOOD_OUTER_LENGTH'],align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).rotate(bd.Axis.X,-90)
    inner=bd.Cylinder(P4_PAN_PROXY['COVER_HOOD_INNER_DIAMETER']/2,
        P4_PAN_PROXY['COVER_HOOD_INNER_LENGTH'],align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).rotate(
            bd.Axis.X,-90).translate((0,P4_PAN_PROXY['COVER_HOOD_INNER_Y_OFFSET'],0))
    hood=normalized((outer-inner).intersect(bd.Box(*P4_PAN_PROXY['COVER_HOOD_CLIP_SIZE_XYZ'],
        align=(bd.Align.CENTER,bd.Align.MIN,bd.Align.MIN))))
    hood=hood.translate((0,CAGE_ORIGIN[1]+P4_PAN_PROXY['COVER_HOOD_CENTER_Y_OFFSET'],COVER_UNDERSIDE_Z+lift))
    named(hood,'REFERENCE_raised_pickup_relief_UNKNOWN','#C9BEA3')
    return [cover,hood]


def insert(kind,angle=0):
    if kind=='baseline':
        from parts import assembly
        body=assembly(angle)
    else:
        from advanced_geometry import concept
        body=concept(kind,angle)
    body=body.rotate(bd.Axis.Z,CAGE_ROTATION).translate(CAGE_ORIGIN)
    body.label='CUSTOM_'+kind+'_insert'
    return body


def scene(kind,stage='cutaway'):
    pan=pan_shell(cutaway=stage!='whole')
    if stage=='detail':
        pan=normalized(pan.intersect(bd.Box(*P4_PAN_PROXY['DETAIL_CROP_SIZE_XYZ']).translate(
            P4_PAN_PROXY['DETAIL_CROP_CENTER_XYZ'])))
        named(pan,'REFERENCE_deep_sump_cutaway_ASSUMED_INTERIOR','#B8C2C7')
    children=[pan,*pickup_reference()]
    body=insert(kind)
    if stage=='exploded':body=body.translate((0,0,P4_PAN_PROXY['INSERT_EXPLODED_Z']))
    children.append(body)
    if stage in ('exploded','whole'):
        lift=P4_PAN_PROXY['COVER_EXPLODED_LIFT'] if stage=='exploded' else 0
        children+=cover_reference(lift)
    if stage=='section':
        tool=bd.Box(*P4_PAN_PROXY['SECTION_TOOL_SIZE_XYZ'],
                    align=(bd.Align.MIN,bd.Align.CENTER,bd.Align.MIN)).translate(
                        P4_PAN_PROXY['SECTION_TOOL_ORIGIN_XYZ'])
        sections=[]
        for child in children:
            clipped=normalized(child.cut(tool))
            if clipped.volume>1e-8:
                clipped.label=child.label;clipped.color=child.color;sections.append(clipped)
        children=sections
    return bd.Compound(children=children,label='ILLUSTRATIVE_'+kind+'_in_pan_NOT_MEASURED_FIT')


def scene_gate_specs(kind):
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
    return [{**s,'pivot':(-s['pivot'][0]+CAGE_ORIGIN[0],-s['pivot'][1]+CAGE_ORIGIN[1],s['pivot'][2]+CAGE_ORIGIN[2]),
             'axis':(-s['axis'][0],-s['axis'][1],s['axis'][2])} for s in raw]


def scene_animation(kind):
    targets=[{'labels':s['moving_labels'],'axis':s['axis'],'pivot':s['pivot'],'phase':i/len(scene_gate_specs(kind))}
             for i,s in enumerate(scene_gate_specs(kind))]
    duration=P4_NOMINALS['DEMO_DURATION_S']
    return (f'const gates={json.dumps(targets)};export const clips={{demo:{{label:"Illustrative pan context; arbitrary independent gate travel",'
            f'duration:{duration:g},loop:true,update(t,m){{for(const g of gates){{const a={STOP_ANGLE/2:g}*(1-Math.cos(2*Math.PI*(t/{duration:g}+g.phase)));'
            'for(const label of g.labels)m.get(label).rotate(g.axis,a,g.pivot);}}}};')


def scene_kinematics(kind):
    from cadgen import revolute
    specs=scene_gate_specs(kind)
    return {'mates':[revolute(s['name'],parent='#'+s['wall_label'],child='#'+s['door_label'],origin=s['pivot'],direction=s['axis'],limits=(0,STOP_ANGLE)) for s in specs],
            'poses':{'closed':{s['name']:0 for s in specs},'open':{s['name']:STOP_ANGLE for s in specs}}}
