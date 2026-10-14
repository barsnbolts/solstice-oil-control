from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/inner_front_relief_wall.step')
def inner_front_relief_wall():
    return cut_profiles('nested')['inner_front_relief_wall'][0]

if __name__=='__main__':inner_front_relief_wall()
