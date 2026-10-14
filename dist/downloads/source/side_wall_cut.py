from cadgen import dxf,flatten
from side_wall import side_wall
from parts import PARTS

@dxf(out='../DXF/side_wall_cut.dxf')
def side_wall_cut():
    return flatten.flat_pattern(side_wall(),coordinate=PARTS['side_wall'][0],kerf=0)

if __name__=='__main__': side_wall_cut()
