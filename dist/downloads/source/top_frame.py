from cadgen import step
from parts import flat_part

@step(out='../STEP/top_frame.step')
def top_frame():
    return flat_part('top_frame')

if __name__=='__main__': top_frame()
