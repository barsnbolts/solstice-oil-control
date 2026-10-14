from cadgen import dxf,flatten
from purchased_rear_wall import purchased_rear_wall
from parts import PARTS

@dxf(out='../DXF/purchased_rear_wall_cut.dxf')
def purchased_rear_wall_cut():
    return flatten.flat_pattern(purchased_rear_wall(),coordinate=PARTS['purchased_rear_wall'][0],kerf=0)

if __name__=='__main__': purchased_rear_wall_cut()
