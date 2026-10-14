from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/outer_rear_gated_wall.step')
def outer_rear_gated_wall():
    return cut_profiles('nested')['outer_rear_gated_wall'][0]

if __name__=='__main__':outer_rear_gated_wall()
