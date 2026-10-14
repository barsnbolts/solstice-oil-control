from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/radial_diagonal_gated_wall.step')
def radial_diagonal_gated_wall():
    return cut_profiles('radial')['radial_diagonal_gated_wall'][0]

if __name__=='__main__':radial_diagonal_gated_wall()
