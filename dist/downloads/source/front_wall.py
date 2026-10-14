from cadgen import step
from parts import flat_part

@step(out='../STEP/front_wall.step')
def front_wall():
    return flat_part('front_wall')

if __name__=='__main__': front_wall()
