from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/outer_front_relief_wall.step')
def outer_front_relief_wall():
    return cut_profiles('nested')['outer_front_relief_wall'][0]

if __name__=='__main__':outer_front_relief_wall()
