"""EMR-201 mounting-pattern candidate. Gold hardware is a simplified proxy.

Hole/window positions come from EMR-200_Mounting_Diagram dated 2013-10-01.
Knuckle/leaf shape and thickness are NOT manufacturer geometry; measure purchased
doors before committing. No proxy hardware is included in the custom cut files.
"""
from cadgen import step,build123d as bd,srgb
from parts import flat_part,wall_place,place,GATES,T,HEIGHT,LENGTH
from design_parameters import (
    PURCHASED_WINDOW_Z, PURCHASED_HOLE_SPACING, PURCHASED_HOLE_D, PURCHASED_HOLE_Z,
    PROXY_DOOR_WIDTH, PROXY_T, PROXY_LEAF_HEIGHT, PROXY_MOUNT_HEIGHT,
    PROXY_MOUNT_HOLE_OFFSET_Z, PROXY_HINGE_R, PROXY_HINGE_Z, PROXY_HOLE_TOOL_DEPTH,
)
from animations import gates_animation

@step(out='../STEP/v2_purchased_doors.step',animation=gates_animation(proxy=True))
def v2_purchased_doors():
    parts=[]
    for name,theta,xyz in GATES:
        wall=flat_part('purchased_rear_wall' if name=='rear' else 'purchased_side_wall')
        wall=place(wall_place(wall),theta,xyz); wall.label=name+'_wall'; parts.append(wall)
        # Simplified visible representation, NOT a reverse engineered commercial door.
        leaf=bd.Box(PROXY_DOOR_WIDTH,PROXY_T,PROXY_LEAF_HEIGHT).translate((0,2*PROXY_T,PURCHASED_WINDOW_Z))
        leaf.label='PROXY_'+name+'_EMR201_leaf'; leaf.color=srgb('#D9A441')
        flange=bd.Box(PROXY_DOOR_WIDTH,PROXY_T,PROXY_MOUNT_HEIGHT).translate(
            (0,PROXY_T/2,PURCHASED_HOLE_Z-PROXY_MOUNT_HOLE_OFFSET_Z))
        for x in (-PURCHASED_HOLE_SPACING/2,PURCHASED_HOLE_SPACING/2):
            flange-=bd.Cylinder(PURCHASED_HOLE_D/2,PROXY_HOLE_TOOL_DEPTH).rotate(bd.Axis.X,90).translate(
                (x,PROXY_T/2,PURCHASED_HOLE_Z))
        flange.label='PROXY_'+name+'_EMR201_mount'; flange.color=srgb('#D9A441')
        barrel=bd.Cylinder(PROXY_HINGE_R,PROXY_DOOR_WIDTH).rotate(bd.Axis.Y,90).translate((0,PROXY_HINGE_R,PROXY_HINGE_Z))
        barrel.label='PROXY_'+name+'_EMR201_hinge'; barrel.color=srgb('#D9A441')
        parts.extend(place(p,theta,xyz) for p in [leaf,flange,barrel])
    front=wall_place(flat_part('front_wall')).translate((0,-LENGTH/2+T,0))
    front.label='front_tube_relief_wall'; parts.append(front)
    parts.append(flat_part('top_frame').translate((0,0,HEIGHT)))
    return bd.Compound(children=parts,label='V2_ESTIMATED_purchased_doors')

if __name__=='__main__': v2_purchased_doors()
