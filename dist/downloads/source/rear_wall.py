from cadgen import step
from parts import flat_part

@step(out='../STEP/rear_wall.step')
def rear_wall():
    return flat_part('rear_wall')

if __name__=='__main__': rear_wall()
