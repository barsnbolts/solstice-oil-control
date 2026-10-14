from cadgen import step
from heading_reference import heading_scene


@step(out='../STEP/heading_wall_setup.step')
def heading_wall_setup():
    return heading_scene('baseline', 'rear', 'wall')


if __name__ == '__main__':
    heading_wall_setup()
