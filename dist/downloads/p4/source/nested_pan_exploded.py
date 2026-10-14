from cadgen import step
from pan_reference import scene

@step(out='../STEP/nested_pan_exploded.step')
def nested_pan_exploded():
    return scene('nested','exploded')

if __name__=='__main__':nested_pan_exploded()
