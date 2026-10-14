from cadgen import dxf,flatten
from outer_front_relief_wall import outer_front_relief_wall

@dxf(out='../DXF/outer_front_relief_wall_cut.dxf')
def outer_front_relief_wall_cut():
    return flatten.flat_pattern(outer_front_relief_wall(),coordinate=1.2192,kerf=0)

if __name__=='__main__':outer_front_relief_wall_cut()
