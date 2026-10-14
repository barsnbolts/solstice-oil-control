from cadgen import dxf,flatten
from door_leaf import door_leaf
from parts import PARTS

@dxf(out='../DXF/door_leaf_cut.dxf')
def door_leaf_cut():
    return flatten.flat_pattern(door_leaf(),coordinate=PARTS['door_leaf'][0],kerf=0)

if __name__=='__main__': door_leaf_cut()
