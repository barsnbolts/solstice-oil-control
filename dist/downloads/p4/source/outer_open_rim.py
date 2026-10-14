from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/outer_open_rim.step')
def outer_open_rim():
    return cut_profiles('nested')['outer_open_rim'][0]

if __name__=='__main__':outer_open_rim()
