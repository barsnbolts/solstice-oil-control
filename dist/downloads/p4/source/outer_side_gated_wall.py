from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/outer_side_gated_wall.step')
def outer_side_gated_wall():
    return cut_profiles('nested')['outer_side_gated_wall'][0]

if __name__=='__main__':outer_side_gated_wall()
