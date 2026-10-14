from cadgen import step
from pan_reference import scene

@step(out='../STEP/nested_pan_cutaway.step')
def nested_pan_cutaway():
    return scene('nested','cutaway')

if __name__=='__main__':nested_pan_cutaway()
