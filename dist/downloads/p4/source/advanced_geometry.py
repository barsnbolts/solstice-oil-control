"""Flat-sheet concept exploration, mm; all envelopes and interfaces are assumed.

No OEM pan, pickup, mounts, oil levels or retained-volume performance is claimed.
The open bottom, front tube relief and upper openings remain bypass/refill paths.
"""
from __future__ import annotations
import json
from math import cos, sin, radians, sqrt
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))
from cadgen import build123d as bd, revolute, srgb
from parts import gate_components, place, wall_place, flat_part
from design_parameters import T, LEAF_T, HEIGHT, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_Z, PIVOT_IN, PIVOT_Z, STOP_ANGLE

RADIAL_WIDTH, RADIAL_LENGTH, CHAMFER = 164.0, 154.0, 42.0
OUTER_WIDTH, OUTER_LENGTH = 224.0, 208.0
INNER_WIDTH, INNER_LENGTH = 136.0, 120.0
RIM = 10.0
TUBE_WIDTH, TUBE_BOTTOM = 42.0, 22.0
GUIDE_LENGTH, GUIDE_ROOT_HEIGHT, GUIDE_TIP_HEIGHT = 24.0, 34.0, 18.0
BRIDGE_WIDTH = 12.0


def _octagon(width, length):
    x, y = width/2, length/2
    return bd.Polygon((-x+CHAMFER,-y),(x-CHAMFER,-y),(x,-y+CHAMFER),
                      (x,y-CHAMFER),(x-CHAMFER,y),(-x+CHAMFER,y),
                      (-x,y-CHAMFER),(-x,-y+CHAMFER), align=None)


def _wall_profile(width, gate_offset=None, tube=False):
    profile = bd.Pos(0,HEIGHT/2)*bd.Rectangle(width,HEIGHT)
    if gate_offset is not None:
        profile -= bd.Pos(gate_offset,WINDOW_Z)*bd.Rectangle(WINDOW_WIDTH,WINDOW_HEIGHT)
    if tube:
        profile -= bd.Pos(0,(HEIGHT+TUBE_BOTTOM)/2)*bd.Rectangle(TUBE_WIDTH,HEIGHT-TUBE_BOTTOM)
    return profile


def _rim_profile(width, length, octagonal=False):
    if octagonal:
        profile = _octagon(width,length)-_octagon(width-2*RIM,length-2*RIM)
    else:
        profile = bd.Rectangle(width,length)-bd.Rectangle(width-2*RIM,length-2*RIM)
    profile -= bd.Pos(0,-length/2)*bd.Rectangle(TUBE_WIDTH,2*RIM)
    return profile


def _plate(profile, label, color='#71939D'):
    shape = bd.extrude(profile, amount=T)
    shape.label, shape.color = label, srgb(color)
    return shape


def gate_specs(kind):
    """Pure placement data. xyz is the wall-local gate origin, not chamber centre."""
    raw = []
    if kind == 'radial':
        x, y = RADIAL_WIDTH/2-T-CHAMFER/2, RADIAL_LENGTH/2-T-CHAMFER/2
        raw = [(name,theta,xyz) for name,theta,xyz in (
            ('rad_fr',45,(x,-y,0)),('rad_rr',135,(x,y,0)),
            ('rad_rl',225,(-x,y,0)),('rad_fl',315,(-x,-y,0)))]
    elif kind == 'nested':
        # Stagger the two rows of gates; their windows and hardware move together.
        for tier,width,length,offsets in (
                ('outer',OUTER_WIDTH,OUTER_LENGTH,(-25,25,25)),
                ('inner',INNER_WIDTH,INNER_LENGTH,(15,-10,-10))):
            for side,theta,centre,offset in (
                    ('rear',180,(0,length/2-T,0),offsets[0]),
                    ('left',-90,(-width/2+T,0,0),offsets[1]),
                    ('right',90,(width/2-T,0,0),offsets[2])):
                a = radians(theta)
                xyz = (centre[0]+offset*cos(a),centre[1]+offset*sin(a),0)
                raw.append((tier+'_'+side,theta,xyz))
    else:
        raise ValueError('kind must be radial or nested')
    result = []
    for name,theta,xyz in raw:
        a = radians(theta)
        result.append({'name':name,'theta':theta,'xyz':xyz,
                       'pivot':(xyz[0]-sin(a)*PIVOT_IN,xyz[1]+cos(a)*PIVOT_IN,PIVOT_Z),
                       'axis':(cos(a),sin(a),0),'wall_label':name+'_wall','door_label':name+'_door',
                       'moving_labels':[name+'_leaf',name+'_moving_cheek_0',name+'_moving_cheek_1']})
    return result


def cut_profiles(kind):
    """name -> (extruded flat XY stock part, quantity, thickness_mm), excluding round pins.

    All new walls/rims/guides/bridges and unchanged shared hinge plates are included.
    Pins are purchased/process hardware: one per gate, not laser-cut profiles.
    """
    profiles = {}

    def add(name, profile, quantity=1, color='#71939D'):
        profiles[name] = (_plate(profile,name,color),quantity,T)

    if kind == 'radial':
        add('radial_diagonal_gated_wall',_wall_profile(CHAMFER*sqrt(2),0),4)
        add('radial_cardinal_side_wall',_wall_profile(RADIAL_LENGTH-2*T-2*CHAMFER),2)
        add('radial_rear_wall',_wall_profile(RADIAL_WIDTH-2*T-2*CHAMFER))
        add('radial_front_relief_wall',_wall_profile(RADIAL_WIDTH-2*T-2*CHAMFER,tube=True))
        add('radial_open_rim',_rim_profile(RADIAL_WIDTH,RADIAL_LENGTH,True))
        add('radial_guide_vane',bd.Polygon((0,0),(GUIDE_LENGTH,0),(GUIDE_LENGTH,GUIDE_TIP_HEIGHT),
                                         (0,GUIDE_ROOT_HEIGHT),align=None),5)
    elif kind == 'nested':
        for tier,width,length,offsets,color in (
                ('outer',OUTER_WIDTH,OUTER_LENGTH,(-25,25,25),'#627D8B'),
                ('inner',INNER_WIDTH,INNER_LENGTH,(15,-10,-10),'#579F9C')):
            add(tier+'_rear_gated_wall',_wall_profile(width-2*T,offsets[0]),color=color)
            # Left and right have the same local offset, even though their world Y differs.
            add(tier+'_side_gated_wall',_wall_profile(length,offsets[1]),2,color)
            add(tier+'_front_relief_wall',_wall_profile(width-2*T,tube=True),color=color)
            add(tier+'_open_rim',_rim_profile(width,length),color=color)
        bridge_length = (OUTER_WIDTH-INNER_WIDTH)/2-RIM
        if abs(bridge_length-((OUTER_LENGTH-INNER_LENGTH)/2-RIM)) > 1e-8:
            raise ValueError('Current equal-length connector design requires equal reservoir spacing')
        add('nested_rim_bridge',bd.Rectangle(bridge_length,BRIDGE_WIDTH),5,'#A0B5BC')
    else:
        raise ValueError('kind must be radial or nested')
    gates = len(gate_specs(kind))
    for name,multiplier,thickness in [('door_leaf',1,LEAF_T),('fixed_cheek',2,T),('moving_cheek',2,T)]:
        profiles[name] = (flat_part(name),gates*multiplier,thickness)
    return profiles


def _gate_hardware(spec, angle):
    fixed, door, pin = gate_components()
    name, theta, xyz = spec['name'],spec['theta'],spec['xyz']
    for part in door.children:
        part.label = name+'_'+part.label
    door = door.rotate(bd.Axis((0,PIVOT_IN,PIVOT_Z),(1,0,0)),angle)
    door = place(door,theta,xyz)
    door.label = spec['door_label']
    result = [door]
    for index,part in enumerate(fixed):
        part = place(part,theta,xyz)
        part.label = f'{name}_fixed_{index}'
        result.append(part)
    pin = place(pin,theta,xyz)
    pin.label = name+'_pin'
    result.append(pin)
    return result


def concept(kind, angle=0):
    """Assembly at a uniform angle, or independent {gate_name: angle} diagnostic pose."""
    profiles = cut_profiles(kind)
    children = []

    def plate(name, label, theta=0, xyz=(0,0,0), upright=False):
        part = profiles[name][0]
        if upright:
            part = wall_place(part)
        part = place(part,theta,xyz)
        part.label = label
        children.append(part)

    for spec in gate_specs(kind):
        name = spec['name']
        if kind == 'radial':
            plate('radial_diagonal_gated_wall',spec['wall_label'],spec['theta'],spec['xyz'],True)
        else:
            tier,side = name.split('_')
            width,length = (OUTER_WIDTH,OUTER_LENGTH) if tier == 'outer' else (INNER_WIDTH,INNER_LENGTH)
            centre = {'rear':(0,length/2-T,0),'left':(-width/2+T,0,0),'right':(width/2-T,0,0)}[side]
            plate(tier+('_rear_gated_wall' if side == 'rear' else '_side_gated_wall'),
                  spec['wall_label'],spec['theta'],centre,True)
        pose = angle.get(name,0) if isinstance(angle,dict) else angle
        children.extend(_gate_hardware(spec,pose))
    if kind == 'radial':
        plate('radial_rear_wall','radial_rear_wall',180,(0,RADIAL_LENGTH/2-T,0),True)
        plate('radial_front_relief_wall','radial_front_relief_wall',0,(0,-RADIAL_LENGTH/2+T,0),True)
        plate('radial_cardinal_side_wall','radial_left_wall',-90,(-RADIAL_WIDTH/2+T,0,0),True)
        plate('radial_cardinal_side_wall','radial_right_wall',90,(RADIAL_WIDTH/2-T,0,0),True)
        plate('radial_open_rim','radial_open_rim',xyz=(0,0,HEIGHT))
        for name,theta,xyz in [('rear',90,(0,RADIAL_LENGTH/2,0)),
                               ('left',180,(-RADIAL_WIDTH/2,0,0)),('right',0,(RADIAL_WIDTH/2,0,0)),
                               ('front_left',-90,(-32,-RADIAL_LENGTH/2,0)),
                               ('front_right',-90,(32,-RADIAL_LENGTH/2,0))]:
            plate('radial_guide_vane','guide_'+name,theta,xyz,True)
    else:
        for tier,length in [('outer',OUTER_LENGTH),('inner',INNER_LENGTH)]:
            width = OUTER_WIDTH if tier == 'outer' else INNER_WIDTH
            plate(tier+'_front_relief_wall',tier+'_front_relief_wall',0,(0,-length/2+T,0),True)
            plate(tier+'_open_rim',tier+'_open_rim',xyz=(0,0,HEIGHT))
        for name,theta,xy in [('left',0,(-(INNER_WIDTH/2+OUTER_WIDTH/2-RIM)/2,0)),
                              ('right',0,((INNER_WIDTH/2+OUTER_WIDTH/2-RIM)/2,0)),
                              ('rear',90,(0,(INNER_LENGTH/2+OUTER_LENGTH/2-RIM)/2)),
                              ('front_left',90,(-45,-(INNER_LENGTH/2+OUTER_LENGTH/2-RIM)/2)),
                              ('front_right',90,(45,-(INNER_LENGTH/2+OUTER_LENGTH/2-RIM)/2))]:
            plate('nested_rim_bridge','bridge_'+name,theta,(*xy,HEIGHT))
    return bd.Compound(children=children,label=kind.upper()+'_DESIGN_ASSUMED_NO_OEM_FIT')


def kinematics(kind):
    specs = gate_specs(kind)
    return {'mates':[revolute(s['name'],parent='#'+s['wall_label'],child='#'+s['door_label'],
                             origin=s['pivot'],direction=s['axis'],limits=(0,STOP_ANGLE)) for s in specs],
            'poses':{'closed':{s['name']:0 for s in specs},'open':{s['name']:STOP_ANGLE for s in specs}}}


def animation(kind):
    specs = gate_specs(kind)
    targets = [{'labels':s['moving_labels'],'axis':s['axis'],'pivot':s['pivot'],
                'phase':index/len(specs)} for index,s in enumerate(specs)]
    return ('const gates='+json.dumps(targets)+';\nexport const clips={demo:{label:'+
            json.dumps(kind+' collector — arbitrary phased kinematics; no oil forces')+
            ',duration:6,loop:true,update(t,m){for(const g of gates){'+
            'const a='+str(STOP_ANGLE/2)+'*(1-Math.cos(2*Math.PI*(t/6+g.phase)));'+
            'for(const label of g.labels)m.get(label).rotate(g.axis,a,g.pivot);}}}};')
