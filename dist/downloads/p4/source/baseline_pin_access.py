from cadgen import step
from access_reference import access_scene

@step(out='../STEP/baseline_pin_access.step')
def baseline_pin_access():
    return access_scene('baseline')

if __name__=='__main__':baseline_pin_access()
