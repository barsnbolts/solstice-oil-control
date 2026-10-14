from cadgen import dxf,flatten
from outer_open_rim import outer_open_rim

@dxf(out='../DXF/outer_open_rim_cut.dxf')
def outer_open_rim_cut():
    return flatten.flat_pattern(outer_open_rim(),coordinate=1.2192,kerf=0)

if __name__=='__main__':outer_open_rim_cut()
