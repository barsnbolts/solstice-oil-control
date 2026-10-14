from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/radial_cardinal_side_wall.step')
def radial_cardinal_side_wall():
    return cut_profiles('radial')['radial_cardinal_side_wall'][0]

if __name__=='__main__':radial_cardinal_side_wall()
