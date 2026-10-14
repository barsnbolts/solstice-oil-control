from cadgen import dxf,flatten
from mount_blank import mount_blank
from parts import PARTS

@dxf(out='../DXF/mount_blank_cut.dxf')
def mount_blank_cut():
    return flatten.flat_pattern(mount_blank(),coordinate=PARTS['mount_blank'][0],kerf=0)

if __name__=='__main__': mount_blank_cut()
