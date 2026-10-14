from cadgen import step
from heading_reference import heading_scene


@step(out='../STEP/heading_hinge_setup.step')
def heading_hinge_setup():
    return heading_scene('baseline', 'rear', 'hinge')


if __name__ == '__main__':
    heading_hinge_setup()
