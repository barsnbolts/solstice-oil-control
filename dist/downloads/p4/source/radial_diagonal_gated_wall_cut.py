from cadgen import dxf,flatten
from radial_diagonal_gated_wall import radial_diagonal_gated_wall

@dxf(out='../DXF/radial_diagonal_gated_wall_cut.dxf')
def radial_diagonal_gated_wall_cut():
    return flatten.flat_pattern(radial_diagonal_gated_wall(),coordinate=1.2192,kerf=0)

if __name__=='__main__':radial_diagonal_gated_wall_cut()
