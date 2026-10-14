from cadgen import step
from pan_reference import scene

@step(out='../STEP/radial_pan_section.step')
def radial_pan_section():
    return scene('radial','section')

if __name__=='__main__':radial_pan_section()
