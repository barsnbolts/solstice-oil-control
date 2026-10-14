from cadgen import step
from pan_reference import scene

@step(out='../STEP/nested_pan_section.step')
def nested_pan_section():
    return scene('nested','section')

if __name__=='__main__':nested_pan_section()
