from cadgen import dxf,flatten
from inner_front_relief_wall import inner_front_relief_wall

@dxf(out='../DXF/inner_front_relief_wall_cut.dxf')
def inner_front_relief_wall_cut():
    return flatten.flat_pattern(inner_front_relief_wall(),coordinate=1.2192,kerf=0)

if __name__=='__main__':inner_front_relief_wall_cut()
