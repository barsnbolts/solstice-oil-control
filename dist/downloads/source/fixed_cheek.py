from cadgen import step
from parts import flat_part

@step(out='../STEP/fixed_cheek.step')
def fixed_cheek():
    return flat_part('fixed_cheek')

if __name__=='__main__': fixed_cheek()
