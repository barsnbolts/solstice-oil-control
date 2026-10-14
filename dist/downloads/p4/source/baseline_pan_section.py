from cadgen import step
from pan_reference import scene

@step(out='../STEP/baseline_pan_section.step')
def baseline_pan_section():
    return scene('baseline','section')

if __name__=='__main__':baseline_pan_section()
