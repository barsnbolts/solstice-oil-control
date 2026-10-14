from cadgen import dxf,flatten
from radial_front_relief_wall import radial_front_relief_wall

@dxf(out='../DXF/radial_front_relief_wall_cut.dxf')
def radial_front_relief_wall_cut():
    return flatten.flat_pattern(radial_front_relief_wall(),coordinate=1.2192,kerf=0)

if __name__=='__main__':radial_front_relief_wall_cut()
