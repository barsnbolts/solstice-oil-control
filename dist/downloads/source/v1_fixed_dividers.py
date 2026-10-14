"""Simplest comparison: two fixed fences under the retained OEM lid."""
from cadgen import step,build123d as bd
from parts import flat_part,wall_place,HEIGHT,V1_DIVIDER_OFFSET
from animations import FIXED

@step(out='../STEP/v1_fixed_dividers.step',animation=FIXED)
def v1_fixed_dividers():
    a=wall_place(flat_part('fixed_divider')).rotate(bd.Axis.Z,90).translate((V1_DIVIDER_OFFSET,0,0))
    b=wall_place(flat_part('fixed_divider')).rotate(bd.Axis.Z,-90).translate((-V1_DIVIDER_OFFSET,0,0))
    a.label='right_fixed_divider'; b.label='left_fixed_divider'
    top=flat_part('top_frame').translate((0,0,HEIGHT))
    return bd.Compound(children=[top,a,b],label='V1_ESTIMATED_fixed_dividers')

if __name__=='__main__': v1_fixed_dividers()
