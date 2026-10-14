from cadgen import step
from parts import flat_part

@step(out='../STEP/door_leaf.step')
def door_leaf():
    return flat_part('door_leaf')

if __name__=='__main__': door_leaf()
