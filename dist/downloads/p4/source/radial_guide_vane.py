from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/radial_guide_vane.step')
def radial_guide_vane():
    return cut_profiles('radial')['radial_guide_vane'][0]

if __name__=='__main__':radial_guide_vane()
