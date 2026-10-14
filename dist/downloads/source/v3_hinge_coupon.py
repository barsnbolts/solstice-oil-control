"""One unchanged V3 gate and wall for process trials; not a vehicle insert."""
from cadgen import step,build123d as bd,revolute
from parts import flat_part,wall_place,gate_components,PIVOT_IN,PIVOT_Z,STOP_ANGLE

@step(out='../STEP/v3_hinge_coupon.step',kinematics={
 'mates':[revolute('coupon_gate',parent='#coupon_wall',child='#coupon_door',
     origin=(0,PIVOT_IN,PIVOT_Z),direction=(1,0,0),limits=(0,STOP_ANGLE))],
 'poses':{'closed':{'coupon_gate':0},'open':{'coupon_gate':STOP_ANGLE}}})
def v3_hinge_coupon():
    wall=wall_place(flat_part('side_wall'));wall.label='coupon_wall'
    fixed,door,pin=gate_components();door.label='coupon_door'
    return bd.Compound(children=[wall,*fixed,door,pin],label='V3_PROCESS_COUPON_NOT_ENGINE_PART')

if __name__=='__main__':v3_hinge_coupon()
