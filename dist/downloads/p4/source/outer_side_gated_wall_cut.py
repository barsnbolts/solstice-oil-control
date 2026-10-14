from cadgen import dxf,flatten
from outer_side_gated_wall import outer_side_gated_wall

@dxf(out='../DXF/outer_side_gated_wall_cut.dxf')
def outer_side_gated_wall_cut():
    return flatten.flat_pattern(outer_side_gated_wall(),coordinate=1.2192,kerf=0)

if __name__=='__main__':outer_side_gated_wall_cut()
