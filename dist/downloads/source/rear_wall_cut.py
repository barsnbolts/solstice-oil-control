from cadgen import dxf,flatten
from rear_wall import rear_wall
from parts import PARTS

@dxf(out='../DXF/rear_wall_cut.dxf')
def rear_wall_cut():
    return flatten.flat_pattern(rear_wall(),coordinate=PARTS['rear_wall'][0],kerf=0)

if __name__=='__main__': rear_wall_cut()
