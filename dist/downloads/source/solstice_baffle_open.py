from cadgen import step
from parts import assembly,STOP_ANGLE

@step(out='../STEP/solstice_baffle_open.step')
def solstice_baffle_open():
    return assembly(STOP_ANGLE)

if __name__=='__main__': solstice_baffle_open()
