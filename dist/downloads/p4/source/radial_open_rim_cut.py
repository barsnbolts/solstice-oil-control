from cadgen import dxf,flatten
from radial_open_rim import radial_open_rim

@dxf(out='../DXF/radial_open_rim_cut.dxf')
def radial_open_rim_cut():
    return flatten.flat_pattern(radial_open_rim(),coordinate=1.2192,kerf=0)

if __name__=='__main__':radial_open_rim_cut()
