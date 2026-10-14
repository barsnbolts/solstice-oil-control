from cadgen import dxf,flatten
from radial_cardinal_side_wall import radial_cardinal_side_wall

@dxf(out='../DXF/radial_cardinal_side_wall_cut.dxf')
def radial_cardinal_side_wall_cut():
    return flatten.flat_pattern(radial_cardinal_side_wall(),coordinate=1.2192,kerf=0)

if __name__=='__main__':radial_cardinal_side_wall_cut()
