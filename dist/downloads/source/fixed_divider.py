from cadgen import step
from parts import flat_part

@step(out='../STEP/fixed_divider.step')
def fixed_divider():
    return flat_part('fixed_divider')

if __name__=='__main__': fixed_divider()
