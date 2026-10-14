from cadgen import dxf,flatten
from fixed_divider import fixed_divider
from parts import PARTS

@dxf(out='../DXF/fixed_divider_cut.dxf')
def fixed_divider_cut():
    return flatten.flat_pattern(fixed_divider(),coordinate=PARTS['fixed_divider'][0],kerf=0)

if __name__=='__main__': fixed_divider_cut()
