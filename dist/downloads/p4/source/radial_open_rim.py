from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/radial_open_rim.step')
def radial_open_rim():
    return cut_profiles('radial')['radial_open_rim'][0]

if __name__=='__main__':radial_open_rim()
