from cadgen import step
from parts import flat_part

@step(out='../STEP/purchased_side_wall.step')
def purchased_side_wall():
    return flat_part('purchased_side_wall')

if __name__=='__main__': purchased_side_wall()
