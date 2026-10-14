"""Four diagonal gates with an octagonal well and joined outer guide vanes."""
from cadgen import step
from advanced_geometry import concept, kinematics, animation


@step(out='../STEP/radial_collector.step',kinematics=kinematics('radial'),animation=animation('radial'))
def radial_collector():
    return concept('radial')


if __name__ == '__main__':
    radial_collector()
