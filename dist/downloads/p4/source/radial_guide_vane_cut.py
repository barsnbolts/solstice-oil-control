from cadgen import dxf,flatten
from radial_guide_vane import radial_guide_vane

@dxf(out='../DXF/radial_guide_vane_cut.dxf')
def radial_guide_vane_cut():
    return flatten.flat_pattern(radial_guide_vane(),coordinate=1.2192,kerf=0)

if __name__=='__main__':radial_guide_vane_cut()
