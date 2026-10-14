"""Vendor accessory geometry and a proposed reaction saddle; no forming mechanics."""
from functools import lru_cache
from hashlib import sha256
from math import acos, ceil, degrees, isfinite, sqrt
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))
from cadgen import build123d as bd, read_scene, read_step, srgb
from design_parameters import (FIXED_X, T, PIN_AXIAL_FLOAT, PIN_HEAD_D,
                               PIN_HEAD_T, PIVOT_Z, FIXED_CHEEK_Z,
                               FIXED_CHEEK_HEIGHT, P5_HEADING_STUDY as P)
from access_reference import insert_gate_specs, module_labels, pin_end_probes

SOURCE = ROOT/'research/heading-accessory-source/Orbitform_HL200_original.step'
SOURCE_SHA = 'e760a01279d6adf2162973f5130710f8f4c7a0520cae738f5431172d8b0705e4'
VOLUME_TOL = 1e-5


def _xyz(point):
    return (point.X(), point.Y(), point.Z())


@lru_cache(maxsize=1)
def source_accessory():
    """Map audited native surfaces to a machine-axis/terminal-face datum, in mm."""
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import GeomAbs_Cylinder, GeomAbs_Plane

    if sha256(SOURCE.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('Vendor STEP changed; re-audit its datums before use')
    solids = list(read_step(SOURCE).solids())
    if len(solids) != 8 or any(not s.is_valid for s in solids):
        raise ValueError('Expected eight valid native accessory solids')
    housing = max(solids, key=lambda s: s.volume)
    cylinders = [BRepAdaptor_Surface(f.wrapped) for f in housing.faces()
                 if BRepAdaptor_Surface(f.wrapped).GetType() == GeomAbs_Cylinder]
    outer = max(cylinders, key=lambda a: a.Cylinder().Radius()).Cylinder()
    main_origin = _xyz(outer.Location())
    main_axis = _xyz(outer.Axis().Direction())
    if abs(abs(main_axis[1])-1) > 1e-9:
        raise ValueError('Audited source housing axis must be parallel to native Y')
    distal_index = min(range(len(solids)), key=lambda i: solids[i].bounding_box().min.Y)
    planes = [(f, BRepAdaptor_Surface(f.wrapped).Plane())
              for f in solids[distal_index].faces()
              if BRepAdaptor_Surface(f.wrapped).GetType() == GeomAbs_Plane]
    tip, plane = min(planes, key=lambda item: item[0].center().Y)
    tip_center, normal = tuple(tip.center()), _xyz(plane.Axis().Direction())
    # Intersect the main cylinder axis with the terminal blank's tilted plane.
    tip_y = tip_center[1] - (normal[0]*(main_origin[0]-tip_center[0])
                            + normal[2]*(main_origin[2]-tip_center[2]))/normal[1]
    origin = (main_origin[0], tip_y, main_origin[2])
    peen_cylinders = [BRepAdaptor_Surface(f.wrapped).Cylinder()
                     for f in solids[distal_index].faces()
                     if BRepAdaptor_Surface(f.wrapped).GetType() == GeomAbs_Cylinder]
    peen_radius = max(c.Radius() for c in peen_cylinders)
    peen_direction = _xyz(peen_cylinders[0].Axis().Direction())
    if peen_direction[1] < 0:
        peen_direction = tuple(-v for v in peen_direction)
    peen_axis = (peen_direction[1], -peen_direction[0], peen_direction[2])
    center_local = (tip_center[1]-origin[1], -(tip_center[0]-origin[0]),
                    tip_center[2]-origin[2])
    tilt = degrees(acos(abs(peen_axis[0])))
    diameter = 2*outer.Radius()
    mount_y = max(f.center().Y for f in housing.faces()
                  if BRepAdaptor_Surface(f.wrapped).GetType() == GeomAbs_Plane)
    datum_length = mount_y-tip_y
    if (abs(diameter-1.26*25.4) > .01*25.4 or
            abs(datum_length-4.517*25.4) > .005*25.4 or
            abs(2*peen_radius-.313*25.4) > .005*25.4 or abs(tilt-4) > .5):
        raise ValueError('Native datum dimensions contradict the retained drawing tolerances')
    parts = []
    for index, solid in enumerate(solids):
        part = solid.translate(tuple(-v for v in origin)).rotate(bd.Axis.Z, -90)
        part.label = f'SOURCED_HL200_STATIC_solid_{index}'
        part.color = srgb('#D4A631' if index == distal_index else '#708999')
        parts.append(part)
    peen_container = bd.Cylinder(peen_radius, 200).moved(bd.Plane(
        origin=center_local, x_dir=(0, 0, 1), z_dir=peen_axis).location)
    peen_residual = abs(parts[distal_index].cut(peen_container).volume)
    if peen_residual > VOLUME_TOL:
        raise ValueError('Terminal solid is not contained by the audited cylindrical blank')
    audit = {'source_sha256': SOURCE_SHA, 'solid_count': len(parts),
             'native_machine_axis_tip_plane_intersection_mm': origin,
             'native_tip_face_center_mm': tip_center, 'body_diameter_mm': diameter,
             'mount_to_tip_plane_on_main_axis_mm': datum_length,
             'distal_blank_diameter_mm': 2*peen_radius, 'tilt_deg': tilt,
             'distal_solid_index': distal_index, 'distal_axis_xyz': peen_axis,
             'distal_tip_center_local_mm': center_local,
             'distal_cylinder_residual_mm3': peen_residual,
             'scope': 'Native surfaces and drawing datums; eight component roles/joints are not manufacturer-mapped. Terminal geometry is a blank, not a qualified contact profile.'}
    return tuple(parts), audit


@lru_cache(maxsize=1)
def rigid_clock_bound():
    """Continuous upper envelope of the declared rigid clocking, not real kinematics."""
    parts, audit = source_accessory()
    parts = [s.translate((P['TIP_STANDOFF_MM'], 0, 0)) for s in parts]
    boxes = [s.bounding_box() for s in parts]
    start, end = min(b.min.X for b in boxes), max(b.max.X for b in boxes)
    if start <= 0 or P['ENVELOPE_SLAB_MM'] <= 0 or P['ENVELOPE_RADIAL_PAD_MM'] <= 0:
        raise ValueError('Clearance study needs positive tip separation and envelope dimensions')
    global_radius = audit['body_diameter_mm']/2+P['ENVELOPE_RADIAL_PAD_MM']
    container = bd.Cylinder(global_radius, end-start+2).rotate(bd.Axis.Y, 90).translate(
        ((start+end)/2, 0, 0))
    residual = sum(abs(s.cut(container).volume) for s in parts)
    if residual > VOLUME_TOL:
        raise ValueError('Native accessory is outside the verified global radial bound')
    edges = {start, end, *(b.min.X for b in boxes), *(b.max.X for b in boxes)}
    edges.update(min(end, start+i*P['ENVELOPE_SLAB_MM'])
                 for i in range(1, ceil((end-start)/P['ENVELOPE_SLAB_MM'])))
    bounds, slabs = [], []
    for lower, upper in zip(sorted(edges), sorted(edges)[1:]):
        if upper-lower < 1e-6:
            continue
        active, clipped = [], []
        cutter = bd.Box(upper-lower, 100, 100).translate(((lower+upper)/2, 0, 0))
        for index, (shape, box) in enumerate(zip(parts, boxes)):
            if min(upper, box.max.X)-max(lower, box.min.X) <= 1e-7:
                continue
            piece = shape.intersect(cutter)
            if isinstance(piece, list):
                piece = bd.Compound(piece)
            if piece is not None and abs(piece.volume) > 1e-7:
                active.append(index); clipped.append(piece)
        if not clipped:
            continue
        box = bd.Compound(clipped).bounding_box()
        radius = sqrt(max(abs(box.min.Y), abs(box.max.Y))**2
                      + max(abs(box.min.Z), abs(box.max.Z))**2)
        basis = 'Circle around slab AABB; capped by verified global radial cylinder'
        if active == [audit['distal_solid_index']]:
            c, axis = audit['distal_tip_center_local_mm'], audit['distal_axis_xyz']
            c = (c[0]+P['TIP_STANDOFF_MM'], c[1], c[2])
            offsets = [sqrt(sum((c[j]+(x-c[0])*axis[j]/axis[0])**2
                               for j in (1, 2))) for x in (lower, upper)]
            radius = min(radius, max(offsets)+audit['distal_blank_diameter_mm']/2/abs(axis[0]))
            basis = 'Oblique cylindrical blank cross-section bound'
        radius = min(global_radius, radius+P['ENVELOPE_RADIAL_PAD_MM'])
        bound = bd.Cylinder(radius, upper-lower).rotate(bd.Axis.Y, 90).translate(
            ((lower+upper)/2, 0, 0))
        bound.label = f'ASSUMED_RIGID_CLOCK_BOUND_slab_{len(bounds)}'
        bounds.append(bound)
        slabs.append({'start_x_mm': lower, 'end_x_mm': upper, 'radius_mm': radius,
                      'source_solids': active, 'basis': basis})
    envelope = bounds[0].fuse(*bounds[1:])
    if not envelope.is_valid or len(envelope.solids()) != 1:
        raise ValueError('Rigid clock bound must be one valid closed solid')
    envelope.label = 'ASSUMED_CONTINUOUS_RIGID_CLOCK_BOUND'
    return envelope, {'global_radial_residual_mm3': residual, 'slabs': slabs,
        'scope': 'Continuous bound only for rigid rotations of all eight saved solids about the declared main axis. It is not a bound for unverified internal machine motion or axial approach.'}


def reaction_fixture():
    """Three removable concept pieces; clamping, strength and load rating unresolved."""
    outer = FIXED_X+T/2
    length, width, height = (P[name] for name in
                            ('FIXTURE_BLOCK_LENGTH_MM', 'FIXTURE_BLOCK_WIDTH_MM', 'FIXTURE_BLOCK_HEIGHT_MM'))
    if (not all(isfinite(v) and v > 0 for name, v in P.items() if name.startswith('FIXTURE_'))
            or P['FIXTURE_POST_SETBACK_MM'] >= length
            or PIN_AXIAL_FLOAT/2+PIN_HEAD_T >= length):
        raise ValueError('Fixture needs positive finite dimensions and retained support material')
    bottom = FIXED_CHEEK_Z-FIXED_CHEEK_HEIGHT/2-PIVOT_Z
    base_top = -PIVOT_Z
    pads = []
    for sign, name in ((-1, 'anvil'), (1, 'forming_side')):
        block = bd.Box(length, width, height).translate(
            (sign*(outer+length/2), 0, bottom+height/2))
        setback = P['FIXTURE_POST_SETBACK_MM']
        post = bd.Box(length-setback, width, bottom-base_top).translate(
            (sign*(outer+setback+(length-setback)/2), 0, (bottom+base_top)/2))
        block = block.fuse(post)
        depth = PIN_AXIAL_FLOAT/2+PIN_HEAD_T if sign < 0 else length
        radius = PIN_HEAD_D/2+P['FIXTURE_HEAD_RADIAL_CLEARANCE_MM'] if sign < 0 else (
            P['FIXTURE_TOOL_BORE_DIAMETER_MM']/2)
        relief = bd.Cylinder(radius, depth).rotate(bd.Axis.Y, 90).translate(
            (sign*(outer+depth/2), 0, 0))
        block = block.cut(relief)
        block.label = f'FIXTURE_{name}_DESIGN_ASSUMPTION'
        block.color = srgb('#896BA1'); pads.append(block)
    base = bd.Box(2*(outer+length), width, P['FIXTURE_BASE_THICKNESS_MM']).translate(
        (0, 0, base_top-P['FIXTURE_BASE_THICKNESS_MM']/2))
    base.label = 'FIXTURE_base_DESIGN_ASSUMPTION'; base.color = srgb('#AE96BE')
    parts = tuple([*pads, base])
    if any(not p.is_valid or len(p.solids()) != 1 or p.volume <= 0 for p in parts):
        raise ValueError('Each fixture piece must be a valid positive solid')
    return parts


def fixture_frame(pivot, outward):
    if (not all(isfinite(v) for v in (*pivot, *outward)) or abs(outward[2]) > 1e-9
            or abs(sum(v*v for v in outward)-1) > 1e-9):
        raise ValueError('Heading placement needs a finite horizontal unit axis')
    return bd.Plane(origin=pivot, x_dir=outward, z_dir=(0, 0, 1)).location


def placed_accessory(contact, outward, clock_angle=0):
    frame = fixture_frame(contact, outward)
    return tuple(s.translate((P['TIP_STANDOFF_MM'], 0, 0)).rotate(bd.Axis.X, clock_angle).moved(frame)
                 for s in source_accessory()[0])


def heading_scene(kind, gate, context):
    path = ROOT/'STEP/solstice_baffle.step' if kind == 'baseline' else (
        ROOT/'concepts/p4/STEP'/f'{kind}_collector.step')
    shapes = {leaf.label: leaf.shape() for leaf in read_scene(path).leaves()}
    spec = next(s for s in insert_gate_specs(kind) if s['name'] == gate)
    labels = module_labels(spec)
    if context == 'hinge':
        labels.remove(spec['wall_label'])
    elif context == 'cage':
        labels = list(shapes)
    elif context != 'wall':
        raise ValueError('Unknown heading scene context')
    _, contact, outward, _, _ = next(p for p in pin_end_probes(
        shapes[gate+'_pin'], spec, 6, 150) if p[0] == 'plus')
    fixtures = [s.moved(fixture_frame(spec['pivot'], outward)) for s in reaction_fixture()]
    return bd.Compound(children=[*(shapes[label] for label in labels),
                                  *placed_accessory(contact, outward), *fixtures],
                       label='STATIC_ACCESSORY_AND_ASSUMED_FIXTURE_NO_FORMING_QUALIFICATION')
