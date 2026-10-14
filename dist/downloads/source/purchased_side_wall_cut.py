from cadgen import dxf,flatten
from purchased_side_wall import purchased_side_wall
from parts import PARTS

@dxf(out='../DXF/purchased_side_wall_cut.dxf')
def purchased_side_wall_cut():
    return flatten.flat_pattern(purchased_side_wall(),coordinate=PARTS['purchased_side_wall'][0],kerf=0)

if __name__=='__main__': purchased_side_wall_cut()
