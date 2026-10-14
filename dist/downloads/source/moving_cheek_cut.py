from cadgen import dxf,flatten
from moving_cheek import moving_cheek
from parts import PARTS

@dxf(out='../DXF/moving_cheek_cut.dxf')
def moving_cheek_cut():
    return flatten.flat_pattern(moving_cheek(),coordinate=PARTS['moving_cheek'][0],kerf=0)

if __name__=='__main__': moving_cheek_cut()
