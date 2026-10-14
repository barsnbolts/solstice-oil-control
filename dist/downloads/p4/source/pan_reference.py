"""Illustrative GM-family pan context, not an OEM cavity reconstruction."""
from pathlib import Path
from math import acos,degrees,sqrt
import sys
import json
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'src'))
from cadgen import build123d as bd,srgb

# Only overall envelope is published GM12601240 data. Interior/datum/cover/tube are assumed.
PAN_LENGTH,PAN_WIDTH,PAN_DEPTH=474.7,316.0,117.99
CAGE_ORIGIN=(0,112,7)
CAGE_ROTATION=180
PICKUP_KEEP_OUT_D=60.0  # Design test case, NOT a recovered screen diameter.
COVER_UNDERSIDE_Z=70.0  # Illustrative placement, NOT a measured available height.
OUTLINE=((-120,-237.35),(115,-237.35),(135,-205),(136,-90),(150,-55),
         (158,180),(135,237.35),(-132,237.35),(-158,190),(-145,0),(-130,-70))


def normalized(shape):
    return bd.Compound(children=list(shape)) if isinstance(shape,bd.ShapeList) else shape


def named(shape,label,color):
    shape.label=label;shape.color=srgb(color)
    for n,child in enumerate(shape.children):child.label=f'{label}_{n}';child.color=srgb(color)
    return shape


def pan_shell(cutaway=True):
    outer=bd.Polygon(*OUTLINE,align=None)
    inner=bd.Polygon(*[(x*.90,y*.95) for x,y in OUTLINE],align=None)
    shell=bd.extrude(outer,amount=PAN_DEPTH)-bd.extrude(inner,amount=PAN_DEPTH+10).translate((0,0,4))
    shelf=inner.intersect(bd.Pos(0,-150)*bd.Rectangle(400,220))
    shell=shell.fuse(bd.extrude(shelf,amount=70).translate((0,0,4)))
    # Three visual stiffening ribs echo the shallow extension in source photos.
    for x in (-65,0,65):
        shell=shell.fuse(bd.Box(6,160,8,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).translate((x,-136,74)))
    if cutaway:
        shell=shell-bd.Box(100,290,150,align=(bd.Align.MIN,bd.Align.CENTER,bd.Align.MIN)).translate((110,100,15))
    return named(shell,'REFERENCE_pan_shell_ASSUMED_INTERIOR','#B8C2C7')


def tube_segment(a,b):
    direction=tuple(y-x for x,y in zip(a,b));length=sqrt(sum(v*v for v in direction))
    tube=bd.Cylinder(9,length,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN))
    axis=(-direction[1],direction[0],0)
    if sqrt(sum(v*v for v in axis))>1e-10:
        tube=tube.rotate(bd.Axis((0,0,0),axis),degrees(acos(direction[2]/length)))
    return tube.translate(a)


def pickup_reference():
    # A visible design keep-out, not a replicated OEM screen or tube.
    keepout=bd.Cylinder(PICKUP_KEEP_OUT_D/2,10).translate((0,112,18))
    named(keepout,'REFERENCE_pickup_60mm_DESIGN_TEST_CASE','#986f96')
    points=[(0,112,25),(0,158,44),(0,198,44),(0,220,70),(0,220,95)]
    pipe=tube_segment(points[0],points[1])
    for a,b in zip(points[1:],points[2:]):pipe=pipe.fuse(tube_segment(a,b),bd.Sphere(9).translate(a))
    named(pipe,'REFERENCE_tube_route_UNKNOWN','#986f96')
    return [keepout,pipe]


def cover_reference(lift=0):
    points=[(-113,-80),(-98,-108),(-45,-100),(8,-94),(84,-98),(113,-55),
            (104,-9),(119,31),(90,96),(32,111),(-36,100),(-91,102),(-114,55)]
    profile=bd.Polygon(*points,align=None)-bd.Pos(0,88)*bd.Rectangle(42,100)
    cover=bd.extrude(profile,amount=1.0).translate((0,112,COVER_UNDERSIDE_Z+lift))
    named(cover,'REFERENCE_OEM_cover_shape_and_height_UNKNOWN','#C9BEA3')
    # Raised relief is a geometric visual cue only; no mounting holes are invented.
    outer=bd.Cylinder(23,90,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).rotate(bd.Axis.X,-90)
    inner=bd.Cylinder(22,92,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).rotate(bd.Axis.X,-90).translate((0,-1,0))
    hood=normalized((outer-inner).intersect(bd.Box(80,100,30,align=(bd.Align.CENTER,bd.Align.MIN,bd.Align.MIN))))
    hood=hood.translate((0,112+20,COVER_UNDERSIDE_Z+lift))
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
        pan=normalized(pan.intersect(bd.Box(400,260,150).translate((0,115,65))))
        named(pan,'REFERENCE_deep_sump_cutaway_ASSUMED_INTERIOR','#B8C2C7')
    children=[pan,*pickup_reference()]
    body=insert(kind)
    if stage=='exploded':body=body.translate((0,0,90))
    children.append(body)
    if stage in ('exploded','whole'):children+=cover_reference(190 if stage=='exploded' else 0)
    if stage=='section':
        tool=bd.Box(500,600,500,align=(bd.Align.MIN,bd.Align.CENTER,bd.Align.MIN)).translate((0,0,-10))
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
    return ('const gates='+json.dumps(targets)+';export const clips={demo:{label:"Illustrative pan context; arbitrary independent gate travel",duration:6,loop:true,update(t,m){for(const g of gates){const a=30*(1-Math.cos(2*Math.PI*(t/6+g.phase)));for(const label of g.labels)m.get(label).rotate(g.axis,a,g.pivot);}}}};')


def scene_kinematics(kind):
    from cadgen import revolute
    specs=scene_gate_specs(kind)
    return {'mates':[revolute(s['name'],parent='#'+s['wall_label'],child='#'+s['door_label'],origin=s['pivot'],direction=s['axis'],limits=(0,60)) for s in specs],
            'poses':{'closed':{s['name']:0 for s in specs},'open':{s['name']:60 for s in specs}}}
