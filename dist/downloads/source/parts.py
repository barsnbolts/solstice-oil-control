"""Flat stock prototype; all dimensions mm. Vehicle interfaces are unverified."""
from __future__ import annotations
from cadgen import build123d as bd
from cadgen import srgb
from design_parameters import (
    T, LEAF_T, WIDTH, LENGTH, HEIGHT, PIN_D, BORE_D, PIVOT_IN, PIVOT_Z,
    MOVING_X, FIXED_X, TUBE_SLOT, FRAME_BORDER, TUBE_RELIEF_BOTTOM_Z,
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_Z, LEAF_WIDTH, LEAF_HEIGHT, LEAF_Z,
    FIXED_CHEEK_DEPTH, FIXED_CHEEK_HEIGHT, FIXED_CHEEK_Z,
    PIN_AXIAL_FLOAT, PIN_HEAD_D, PIN_HEAD_T, STOP_ANGLE as STOP_ANGLE,
    V1_DIVIDER_OFFSET as V1_DIVIDER_OFFSET,
    MOUNT_WIDTH, MOUNT_HEIGHT, MOUNT_RADIUS, V1_RETURN_WIDTH, V1_RETURN_HEIGHT,
    PURCHASED_WINDOW_WIDTH, PURCHASED_WINDOW_HEIGHT, PURCHASED_WINDOW_Z,
    PURCHASED_WINDOW_RADIUS, PURCHASED_HOLE_SPACING, PURCHASED_HOLE_D,
    PURCHASED_HOLE_Z, moving_cheek_points, validate_dimensions,
)

# Preserve the established parts imports used by models, drawings and checks.
validate_dimensions()


def rect(w, h, x=0, y=0):
    return bd.Pos(x, y) * bd.Rectangle(w, h)


def profile(name):
    if name == 'side_wall':
        p = rect(LENGTH, HEIGHT, y=HEIGHT/2)
        p -= rect(WINDOW_WIDTH, WINDOW_HEIGHT, y=WINDOW_Z)
    elif name == 'rear_wall':
        p = rect(WIDTH-2*T, HEIGHT, y=HEIGHT/2)
        p -= rect(WINDOW_WIDTH, WINDOW_HEIGHT, y=WINDOW_Z)
    elif name == 'front_wall':
        p = rect(WIDTH-2*T, HEIGHT, y=HEIGHT/2)
        p -= rect(TUBE_SLOT, HEIGHT-TUBE_RELIEF_BOTTOM_Z, y=(HEIGHT+TUBE_RELIEF_BOTTOM_Z)/2)
    elif name == 'top_frame':
        p = rect(WIDTH, LENGTH) - rect(WIDTH-2*FRAME_BORDER, LENGTH-2*FRAME_BORDER)
        p -= rect(TUBE_SLOT, 2*FRAME_BORDER, y=-LENGTH/2)
    elif name == 'door_leaf':
        p = rect(LEAF_WIDTH, LEAF_HEIGHT, y=LEAF_Z)
    elif name == 'fixed_cheek':
        p = rect(FIXED_CHEEK_DEPTH, FIXED_CHEEK_HEIGHT, x=FIXED_CHEEK_DEPTH/2, y=FIXED_CHEEK_Z)
        p -= bd.Pos(PIVOT_IN, PIVOT_Z) * bd.Circle(BORE_D/2)
    elif name == 'moving_cheek':
        # Broad inward arm balances the thin leaf so gravity biases it closed.
        p = bd.Polygon(*moving_cheek_points(), align=None)
        p -= bd.Pos(PIVOT_IN,PIVOT_Z) * bd.Circle(BORE_D/2)
    elif name == 'mount_blank':
        p = bd.RectangleRounded(MOUNT_WIDTH,MOUNT_HEIGHT,MOUNT_RADIUS)
    elif name == 'fixed_divider':
        p = rect(LENGTH,HEIGHT,y=HEIGHT/2) - rect(V1_RETURN_WIDTH,V1_RETURN_HEIGHT,y=V1_RETURN_HEIGHT/2)
    elif name in ('purchased_side_wall','purchased_rear_wall'):
        w=LENGTH if name=='purchased_side_wall' else WIDTH-2*T
        p=rect(w,HEIGHT,y=HEIGHT/2)
        p-=bd.Pos(0,PURCHASED_WINDOW_Z)*bd.RectangleRounded(
            PURCHASED_WINDOW_WIDTH,PURCHASED_WINDOW_HEIGHT,PURCHASED_WINDOW_RADIUS)
        for x in (-PURCHASED_HOLE_SPACING/2,PURCHASED_HOLE_SPACING/2):
            p-=bd.Pos(x,PURCHASED_HOLE_Z)*bd.Circle(PURCHASED_HOLE_D/2)
    else:
        raise ValueError(name)
    return p


PARTS = {
 'side_wall': (T,2), 'rear_wall': (T,1), 'front_wall': (T,1),
 'top_frame': (T,1), 'door_leaf': (LEAF_T,3),
 'fixed_cheek': (T,6), 'moving_cheek': (T,6), 'mount_blank': (T,5),
 'fixed_divider':(T,2), 'purchased_side_wall':(T,2), 'purchased_rear_wall':(T,1),
}


def flat_part(name):
    p = bd.extrude(profile(name), amount=PARTS[name][0])
    p.label = name
    p.color = srgb('#E0B45B' if name=='door_leaf' else '#82949F')
    return p


def wall_place(p):
    # Local X is along a wall, Y points inward, Z is up. Inner seat is Y=0.
    return p.rotate(bd.Axis.X,90)


def cheek_place(p, x):
    # Profile coordinates are (inward distance,height), thickness along X.
    return p.rotate(bd.Axis.Y,90).rotate(bd.Axis.X,90).translate((x-T/2,0,0))


def gate_components():
    fixed = [cheek_place(flat_part('fixed_cheek'),s*FIXED_X) for s in (-1,1)]
    moving = [cheek_place(flat_part('moving_cheek'),s*MOVING_X) for s in (-1,1)]
    # Leaf extrudes toward inward Y after the orientation transform.
    leaf = wall_place(flat_part('door_leaf')).translate((0,LEAF_T,0))
    for n,p in enumerate(moving): p.label=f'moving_cheek_{n}'
    leaf.label='leaf'
    door = bd.Compound(children=[leaf,*moving],label='door')
    for n,p in enumerate(fixed): p.label=f'fixed_cheek_{n}'
    span=2*FIXED_X+T+PIN_AXIAL_FLOAT
    # Simplified purchased 1/8 inch rod, owner-formed permanent heads; not cut parts.
    pin = bd.Cylinder(PIN_D/2,span).rotate(bd.Axis.Y,90).translate((0,PIVOT_IN,PIVOT_Z))
    heads=[bd.Cylinder(PIN_HEAD_D/2,PIN_HEAD_T).rotate(bd.Axis.Y,90).translate(
        (s*(span/2+PIN_HEAD_T/2),PIVOT_IN,PIVOT_Z)) for s in (-1,1)]
    pin=pin.fuse(*heads); pin.label='captive_pin'; pin.color=srgb('#64727C')
    return fixed,door,pin


# theta rotates local +Y inward toward the pickup; world origin is cage-floor centre.
GATES = [('rear',180,(0,LENGTH/2-T,0)),
         ('left',-90,(-WIDTH/2+T,0,0)),
         ('right',90,(WIDTH/2-T,0,0))]


def place(p, theta, xyz):
    return p.rotate(bd.Axis.Z,theta).translate(xyz)


def assembly(angle=0):
    children=[]
    for name,theta,xyz in GATES:
        w=flat_part('rear_wall' if name=='rear' else 'side_wall')
        w=place(wall_place(w),theta,xyz); w.label=f'{name}_wall'
        fixed,door,pin=gate_components()
        for child in door.children:
            child.label=f'{name}_{child.label}'
        door=door.rotate(bd.Axis((0,PIVOT_IN,PIVOT_Z),(1,0,0)),angle)
        door=place(door,theta,xyz); door.label=f'{name}_door'
        children.extend([w,door])
        for i,p in enumerate(fixed):
            p=place(p,theta,xyz); p.label=f'{name}_fixed_{i}'; children.append(p)
        pin=place(pin,theta,xyz); pin.label=f'{name}_pin'; children.append(pin)
    front=wall_place(flat_part('front_wall')).translate((0,-LENGTH/2+T,0))
    front.label='front_tube_relief_wall'; children.append(front)
    top=flat_part('top_frame').translate((0,0,HEIGHT)); top.label='top_frame'; children.append(top)
    return bd.Compound(children=children,label='ESTIMATED_solstice_baffle')
