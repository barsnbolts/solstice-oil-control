from cadgen import step
from parts import flat_part

@step(out='../STEP/purchased_rear_wall.step')
def purchased_rear_wall():
    return flat_part('purchased_rear_wall')

if __name__=='__main__': purchased_rear_wall()
