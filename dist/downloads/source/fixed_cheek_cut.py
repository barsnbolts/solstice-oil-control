from cadgen import dxf,flatten
from fixed_cheek import fixed_cheek
from parts import PARTS

@dxf(out='../DXF/fixed_cheek_cut.dxf')
def fixed_cheek_cut():
    return flatten.flat_pattern(fixed_cheek(),coordinate=PARTS['fixed_cheek'][0],kerf=0)

if __name__=='__main__': fixed_cheek_cut()
