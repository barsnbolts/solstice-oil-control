from cadgen import step
from parts import flat_part

@step(out='../STEP/mount_blank.step')
def mount_blank():
    return flat_part('mount_blank')

if __name__=='__main__': mount_blank()
