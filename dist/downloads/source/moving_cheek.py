from cadgen import step
from parts import flat_part

@step(out='../STEP/moving_cheek.step')
def moving_cheek():
    return flat_part('moving_cheek')

if __name__=='__main__': moving_cheek()
