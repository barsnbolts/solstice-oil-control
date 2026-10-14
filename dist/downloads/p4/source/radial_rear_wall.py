from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/radial_rear_wall.step')
def radial_rear_wall():
    return cut_profiles('radial')['radial_rear_wall'][0]

if __name__=='__main__':radial_rear_wall()
