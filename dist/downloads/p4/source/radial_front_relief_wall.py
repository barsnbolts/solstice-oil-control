from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/radial_front_relief_wall.step')
def radial_front_relief_wall():
    return cut_profiles('radial')['radial_front_relief_wall'][0]

if __name__=='__main__':radial_front_relief_wall()
