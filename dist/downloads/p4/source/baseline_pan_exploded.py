from cadgen import step
from pan_reference import scene

@step(out='../STEP/baseline_pan_exploded.step')
def baseline_pan_exploded():
    return scene('baseline','exploded')

if __name__=='__main__':baseline_pan_exploded()
