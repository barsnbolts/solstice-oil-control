from cadgen import dxf,flatten
from front_wall import front_wall
from parts import PARTS

@dxf(out='../DXF/front_wall_cut.dxf')
def front_wall_cut():
    return flatten.flat_pattern(front_wall(),coordinate=PARTS['front_wall'][0],kerf=0)

if __name__=='__main__': front_wall_cut()
