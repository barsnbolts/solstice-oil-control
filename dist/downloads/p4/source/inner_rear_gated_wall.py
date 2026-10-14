from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/inner_rear_gated_wall.step')
def inner_rear_gated_wall():
    return cut_profiles('nested')['inner_rear_gated_wall'][0]

if __name__=='__main__':inner_rear_gated_wall()
