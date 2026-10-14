from cadgen import dxf,flatten
from radial_rear_wall import radial_rear_wall

@dxf(out='../DXF/radial_rear_wall_cut.dxf')
def radial_rear_wall_cut():
    return flatten.flat_pattern(radial_rear_wall(),coordinate=1.2192,kerf=0)

if __name__=='__main__':radial_rear_wall_cut()
