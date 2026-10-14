from cadgen import step
from access_reference import access_scene

@step(out='../STEP/nested_pin_access.step')
def nested_pin_access():
    return access_scene('nested')

if __name__=='__main__':nested_pin_access()
