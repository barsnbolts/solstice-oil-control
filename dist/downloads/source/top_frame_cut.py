from cadgen import dxf,flatten
from top_frame import top_frame
from parts import PARTS

@dxf(out='../DXF/top_frame_cut.dxf')
def top_frame_cut():
    return flatten.flat_pattern(top_frame(),coordinate=PARTS['top_frame'][0],kerf=0)

if __name__=='__main__': top_frame_cut()
