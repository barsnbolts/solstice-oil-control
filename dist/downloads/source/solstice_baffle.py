"""Removable-cage prototype; OEM cover, pan and pickup intentionally not invented."""
from math import cos,sin,radians
from cadgen import step,revolute
from parts import assembly,GATES,PIVOT_IN,PIVOT_Z,STOP_ANGLE
from animations import gates_animation

def joint(name,theta,xyz):
    a=radians(theta)
    return revolute(name,parent=f'#{name}_wall',child=f'#{name}_door',
        origin=(xyz[0]-sin(a)*PIVOT_IN,xyz[1]+cos(a)*PIVOT_IN,PIVOT_Z),
        direction=(cos(a),sin(a),0),limits=(0,STOP_ANGLE))

@step(out='../STEP/solstice_baffle.step',animation=gates_animation(),kinematics={
 'mates':[joint(*g) for g in GATES],
 'poses':{'closed':{g[0]:0 for g in GATES},'open':{g[0]:STOP_ANGLE for g in GATES}}})
def solstice_baffle():
    return assembly()

if __name__=='__main__': solstice_baffle()
