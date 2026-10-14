from cadgen import step
from access_reference import access_scene

@step(out='../STEP/radial_pin_access.step')
def radial_pin_access():
    return access_scene('radial')

if __name__=='__main__':radial_pin_access()
