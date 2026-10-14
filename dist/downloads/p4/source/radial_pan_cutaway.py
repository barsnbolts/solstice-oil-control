from cadgen import step
from pan_reference import scene

@step(out='../STEP/radial_pan_cutaway.step')
def radial_pan_cutaway():
    return scene('radial','cutaway')

if __name__=='__main__':radial_pan_cutaway()
