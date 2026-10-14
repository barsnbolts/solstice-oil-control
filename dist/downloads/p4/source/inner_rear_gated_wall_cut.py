from cadgen import dxf,flatten
from inner_rear_gated_wall import inner_rear_gated_wall

@dxf(out='../DXF/inner_rear_gated_wall_cut.dxf')
def inner_rear_gated_wall_cut():
    return flatten.flat_pattern(inner_rear_gated_wall(),coordinate=1.2192,kerf=0)

if __name__=='__main__':inner_rear_gated_wall_cut()
