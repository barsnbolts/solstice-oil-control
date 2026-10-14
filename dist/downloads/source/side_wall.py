from cadgen import step
from parts import flat_part

@step(out='../STEP/side_wall.step')
def side_wall():
    return flat_part('side_wall')

if __name__=='__main__': side_wall()
