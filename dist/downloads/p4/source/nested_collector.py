"""Two staggered, three-gate reservoirs connected by open-front flat rims."""
from cadgen import step
from advanced_geometry import concept, kinematics, animation


@step(out='../STEP/nested_collector.step',kinematics=kinematics('nested'),animation=animation('nested'))
def nested_collector():
    return concept('nested')


if __name__ == '__main__':
    nested_collector()
