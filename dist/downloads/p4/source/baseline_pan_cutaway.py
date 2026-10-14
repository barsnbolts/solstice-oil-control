from cadgen import step
from pan_reference import scene

@step(out='../STEP/baseline_pan_cutaway.step')
def baseline_pan_cutaway():
    return scene('baseline','cutaway')

if __name__=='__main__':baseline_pan_cutaway()
