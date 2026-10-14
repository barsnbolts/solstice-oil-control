from cadgen import step
from pan_reference import scene

@step(out='../STEP/radial_pan_exploded.step')
def radial_pan_exploded():
    return scene('radial','exploded')

if __name__=='__main__':radial_pan_exploded()
