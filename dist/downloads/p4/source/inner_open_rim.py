from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/inner_open_rim.step')
def inner_open_rim():
    return cut_profiles('nested')['inner_open_rim'][0]

if __name__=='__main__':inner_open_rim()
