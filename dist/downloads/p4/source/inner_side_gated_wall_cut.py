from cadgen import dxf,flatten
from inner_side_gated_wall import inner_side_gated_wall

@dxf(out='../DXF/inner_side_gated_wall_cut.dxf')
def inner_side_gated_wall_cut():
    return flatten.flat_pattern(inner_side_gated_wall(),coordinate=1.2192,kerf=0)

if __name__=='__main__':inner_side_gated_wall_cut()
