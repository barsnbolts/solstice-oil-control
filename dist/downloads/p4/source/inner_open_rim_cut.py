from cadgen import dxf,flatten
from inner_open_rim import inner_open_rim

@dxf(out='../DXF/inner_open_rim_cut.dxf')
def inner_open_rim_cut():
    return flatten.flat_pattern(inner_open_rim(),coordinate=1.2192,kerf=0)

if __name__=='__main__':inner_open_rim_cut()
