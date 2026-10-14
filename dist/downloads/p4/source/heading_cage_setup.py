from cadgen import step
from heading_reference import heading_scene


@step(out='../STEP/heading_cage_setup.step')
def heading_cage_setup():
    return heading_scene('nested', 'inner_rear', 'cage')


if __name__ == '__main__':
    heading_cage_setup()
