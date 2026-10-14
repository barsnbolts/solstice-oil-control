"""Saved-insert pin-end approach geometry; cylindrical tools are explicit proxies."""
from math import cos, isfinite, radians, sin
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))
from cadgen import build123d as bd, read_scene, srgb
from advanced_geometry import gate_specs
from design_parameters import P5_TOOL_ACCESS, PIVOT_IN, PIVOT_Z
from pan_reference import tube_segment
from parts import GATES

ACCESS_CONTEXTS = {
    'isolated_hinge_before_wall_attachment': 'Fixed cheeks, moving gate and pin only; wall attachment deferred.',
    'isolated_wall_gate_module': 'Wall and its complete gate hardware before cage joining.',
    'completed_insert_on_bench': 'All saved insert parts, closed gates; pan absent.',
    'installed_proxy_cover_removed': 'Complete insert in nominal pan/pickup/tube proxies; cover absent.',
}
DISPLAY_GATES = {'baseline': 'rear', 'radial': 'rad_fr', 'nested': 'inner_rear'}


def insert_gate_specs(kind):
    if kind != 'baseline':
        return gate_specs(kind)
    result = []
    for name, theta, xyz in GATES:
        a = radians(theta)
        result.append({'name': name, 'wall_label': name+'_wall',
                       'pivot': (xyz[0]-sin(a)*PIVOT_IN, xyz[1]+cos(a)*PIVOT_IN, PIVOT_Z),
                       'axis': (cos(a), sin(a), 0),
                       'moving_labels': [name+'_'+part for part in
                                         ('leaf', 'moving_cheek_0', 'moving_cheek_1')]})
    return result


def module_labels(spec):
    name = spec['name']
    return [spec['wall_label'], name+'_fixed_0', name+'_fixed_1',
            name+'_pin', *spec['moving_labels']]


def pin_end_probes(pin, spec, diameter, extent, obstacles=()):
    """The full coaxial nose approach occupies this continuous cylinder."""
    axis, pivot = spec['axis'], spec['pivot']
    if (not all(isfinite(v) for v in (*axis, *pivot, diameter, extent))
            or diameter <= 0 or extent <= 0
            or abs(sum(v*v for v in axis)-1) > 1e-9):
        raise ValueError('Tool envelope needs a finite unit axis and positive dimensions')
    projections = [sum((tuple(vertex)[i]-pivot[i])*axis[i] for i in range(3))
                   for vertex in pin.vertices()]
    if not projections or min(projections) >= 0 or max(projections) <= 0:
        raise ValueError('Saved pin does not straddle the declared gate pivot')
    for name, sign, projection in (('minus', -1, min(projections)),
                                   ('plus', 1, max(projections))):
        contact = tuple(pivot[i]+projection*axis[i] for i in range(3))
        outward = tuple(sign*v for v in axis)
        reach = extent
        for obstacle in obstacles:
            box = obstacle.bounding_box()
            lower, upper = tuple(box.min), tuple(box.max)
            # Project every AABB corner to bound the approach beyond all obstacles.
            outer = sum((max(lower[i]*outward[i], upper[i]*outward[i])
                         - contact[i]*outward[i]) for i in range(3))
            reach = max(reach, outer+P5_TOOL_ACCESS['EXTERIOR_STANDOFF_MM'])
        end = tuple(contact[i]+reach*outward[i] for i in range(3))
        probe = tube_segment(contact, end, diameter)
        probe.label = f'REFERENCE_{spec["name"]}_{name}_nose_sweep_ASSUMED'
        probe.color = srgb('#D9AA46')
        yield name, contact, outward, reach, probe


def access_scene(kind):
    path = ROOT/'STEP/solstice_baffle.step' if kind == 'baseline' else (
        ROOT/'concepts/p4/STEP'/f'{kind}_collector.step')
    shapes = {leaf.label: leaf.shape() for leaf in read_scene(path).leaves()}
    spec = next(s for s in insert_gate_specs(kind) if s['name'] == DISPLAY_GATES[kind])
    probes = [p for _, _, _, _, p in pin_end_probes(shapes[spec['name']+'_pin'], spec,
              P5_TOOL_ACCESS['DISPLAY_DIAMETER_MM'], P5_TOOL_ACCESS['MIN_APPROACH_EXTENT_MM'],
              shapes.values())]
    return bd.Compound(children=[*shapes.values(), *probes],
                       label=f'{kind}_REPRESENTATIVE_PIN_APPROACH_ASSUMED_TOOL')
