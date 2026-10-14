"""Nominal mm dimensions, not measured Solstice interfaces.

Edit the explicit constants to tune a concept, then rebuild and inspect it.
The custom hinge contour is calibrated to one configuration, not a resize engine.
validate_dimensions accepts isolated proposed values without changing the model.

P4_NOMINALS and P4_PAN_PROXY are the shared dimension source for the current
alternatives and their illustrative pan scene. Proxy inputs remain unmeasured.
"""
import json
from math import isfinite, sqrt

T = 1.2192  # SendCutSend SST-048 nominal stock
LEAF_T = 0.762  # SendCutSend SST-030 nominal stock
WIDTH, LENGTH, HEIGHT = 160.0, 120.0, 46.0
FRAME_BORDER = 12.0
TUBE_SLOT, TUBE_RELIEF_BOTTOM_Z = 42.0, 22.0
WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_Z = 36.0, 16.0, 14.0
LEAF_WIDTH, LEAF_HEIGHT, LEAF_Z = 44.0, 22.0, 14.0
PIN_D, BORE_D = 3.175, 3.6
PIVOT_IN, PIVOT_Z = 4.0, 30.0
MOVING_X, CHEEK_GAP = 20.0, 0.30
FIXED_CHEEK_DEPTH, FIXED_CHEEK_HEIGHT, FIXED_CHEEK_Z = 14.0, 14.0, 33.0
PIN_AXIAL_FLOAT, PIN_HEAD_D, PIN_HEAD_T = 0.6, 6.0, 1.2
STOP_ANGLE = 60.0
MOVING_ATTACH_BOTTOM_Z, MOVING_ATTACH_TOP_Z = 10.0, 24.0
MOVING_KNEE_IN, MOVING_ARM_IN = 6.0, 20.5
MOVING_ARM_BOTTOM_Z, MOVING_ARM_TOP_Z = 20.0, 29.0
STOP_CONTACT_IN = (14.0, 12.0)
MOVING_UPPER_POINTS = ((8.0, 34.0), (4.0, 34.0), (1.0, 32.0))
MOUNT_WIDTH, MOUNT_HEIGHT, MOUNT_RADIUS = 45.0, 20.0, 3.0
V1_FRAME_SETBACK = 30.0
V1_RETURN_WIDTH, V1_RETURN_HEIGHT = 36.0, 12.0
PURCHASED_WINDOW_WIDTH, PURCHASED_WINDOW_HEIGHT = 38.1, 15.24
PURCHASED_WINDOW_Z, PURCHASED_WINDOW_RADIUS = 15.24, 3.0
PURCHASED_HOLE_SPACING, PURCHASED_HOLE_D, PURCHASED_HOLE_Z = 19.05, 3.2512, 40.64
# Display envelopes only: not a reconstruction of the purchased hardware.
PROXY_DOOR_WIDTH, PROXY_T, PROXY_LEAF_HEIGHT = 44.45, 0.8, 23.0
PROXY_MOUNT_HEIGHT, PROXY_MOUNT_HOLE_OFFSET_Z = 13.0, 3.0
PROXY_HINGE_R, PROXY_HINGE_Z, PROXY_HOLE_TOOL_DEPTH = 1.5, 28.5, 4.0

# P4 concepts B and C. Values feed geometry, generated registers and the site.
P4_NOMINALS = {
    'RADIAL_WIDTH': 164.0, 'RADIAL_LENGTH': 154.0, 'CHAMFER': 42.0,
    'OUTER_WIDTH': 224.0, 'OUTER_LENGTH': 208.0,
    'INNER_WIDTH': 136.0, 'INNER_LENGTH': 120.0, 'RIM': 10.0,
    'TUBE_WIDTH': 42.0, 'TUBE_BOTTOM': 22.0,
    'GUIDE_LENGTH': 24.0, 'GUIDE_ROOT_HEIGHT': 34.0, 'GUIDE_TIP_HEIGHT': 18.0,
    'BRIDGE_WIDTH': 12.0,
    'RADIAL_GATE_ANGLES_DEG': (45, 135, 225, 315),
    'NESTED_OUTER_GATE_OFFSETS': (-25, 25, 25),
    'NESTED_INNER_GATE_OFFSETS': (15, -10, -10),
    'RADIAL_FRONT_GUIDE_OFFSET': 32.0,
    'NESTED_FRONT_BRIDGE_OFFSET': 45.0,
    'DEMO_DURATION_S': 6.0,
}

# Cylindrical nose-sweep sensitivities, not a purchased or qualified heading tool.
P5_TOOL_ACCESS = {
    'PROBE_DIAMETERS_MM': (6.0, 9.525, 12.7),
    'MIN_APPROACH_EXTENT_MM': 150.0,
    'EXTERIOR_STANDOFF_MM': 10.0,
    'DISPLAY_DIAMETER_MM': 12.7,
}

# Illustrative pan, cover, pickup and tube geometry. Only the three overall pan
# maxima are sourced; every interior/profile/placement value is a proxy input.
P4_PAN_PROXY = {
    'PAN_LENGTH': 474.7, 'PAN_WIDTH': 316.0, 'PAN_DEPTH': 117.99,
    'CAGE_ORIGIN_XYZ': (0, 112, 7), 'CAGE_ROTATION_DEG': 180,
    'PICKUP_KEEP_OUT_DIAMETER': 60.0, 'PICKUP_KEEP_OUT_HEIGHT': 10.0,
    'PICKUP_CENTER_XYZ': (0, 112, 18),
    'TUBE_DIAMETER': 18.0,
    'TUBE_CENTERLINE_XYZ': ((0, 112, 25), (0, 158, 44), (0, 198, 44),
                            (0, 220, 70), (0, 220, 95)),
    'COVER_UNDERSIDE_Z': 70.0,
    'PAN_OUTLINE_XY': ((-120, -237.35), (115, -237.35), (135, -205), (136, -90),
                       (150, -55), (158, 180), (135, 237.35), (-132, 237.35),
                       (-158, 190), (-145, 0), (-130, -70)),
    'PAN_INNER_SCALE_XY': (0.90, 0.95), 'PAN_FLOOR_Z': 4.0,
    'PAN_INNER_CUT_EXTRA': 10.0,
    'PAN_SHELF_CENTER_XY': (0, -150), 'PAN_SHELF_SIZE_XY': (400, 220),
    'PAN_SHELF_HEIGHT': 70.0,
    'PAN_RIB_X_POSITIONS': (-65, 0, 65), 'PAN_RIB_SIZE_XYZ': (6, 160, 8),
    'PAN_RIB_CENTER_Y': -136.0, 'PAN_RIB_BOTTOM_Z': 74.0,
    'PAN_CUTAWAY_SIZE_XYZ': (100, 290, 150),
    'PAN_CUTAWAY_ORIGIN_XYZ': (110, 100, 15),
    'DETAIL_CROP_SIZE_XYZ': (400, 260, 150),
    'DETAIL_CROP_CENTER_XYZ': (0, 115, 65),
    'INSERT_EXPLODED_Z': 90.0, 'COVER_EXPLODED_LIFT': 190.0,
    'SECTION_TOOL_SIZE_XYZ': (500, 600, 500),
    'SECTION_TOOL_ORIGIN_XYZ': (0, 0, -10),
    'COVER_OUTLINE_XY': ((-113, -80), (-98, -108), (-45, -100), (8, -94),
                         (84, -98), (113, -55), (104, -9), (119, 31), (90, 96),
                         (32, 111), (-36, 100), (-91, 102), (-114, 55)),
    'COVER_RELIEF_CENTER_XY': (0, 88), 'COVER_RELIEF_SIZE_XY': (42, 100),
    'COVER_THICKNESS': 1.0,
    'COVER_HOOD_OUTER_DIAMETER': 46.0, 'COVER_HOOD_OUTER_LENGTH': 90.0,
    'COVER_HOOD_INNER_DIAMETER': 44.0, 'COVER_HOOD_INNER_LENGTH': 92.0,
    'COVER_HOOD_INNER_Y_OFFSET': -1.0,
    'COVER_HOOD_CLIP_SIZE_XYZ': (80, 100, 30),
    'COVER_HOOD_CENTER_Y_OFFSET': 20.0,
}

# These values couple the profiled stop, bore, attachment and gravity balance.
# Changes require renewed contour/motion checks rather than silent extrapolation.
_CALIBRATED_HINGE = {
    'LEAF_T': 0.762, 'LEAF_WIDTH': 44.0, 'LEAF_HEIGHT': 22.0, 'LEAF_Z': 14.0,
    'PIVOT_IN': 4.0, 'PIVOT_Z': 30.0, 'MOVING_X': 20.0, 'STOP_ANGLE': 60.0,
    'MOVING_ATTACH_BOTTOM_Z': 10.0, 'MOVING_ATTACH_TOP_Z': 24.0,
    'MOVING_KNEE_IN': 6.0, 'MOVING_ARM_IN': 20.5,
    'MOVING_ARM_BOTTOM_Z': 20.0, 'MOVING_ARM_TOP_Z': 29.0,
    'STOP_CONTACT_IN': (14.0, 12.0),
    'MOVING_UPPER_POINTS': ((8.0, 34.0), (4.0, 34.0), (1.0, 32.0)),
}


def _values():
    return {name: value for name, value in globals().items()
            if name.isupper() and not name.startswith('_')
            and (isinstance(value, (int, float)) or name in ('STOP_CONTACT_IN', 'MOVING_UPPER_POINTS'))
            and name not in ('FIXED_X', 'V1_DIVIDER_OFFSET')}


def moving_cheek_points(values=None):
    """The reviewed fixed contour; stop equation is valid only at 60 degrees."""
    p = _values() if values is None else values

    def stop_height(inward):
        return p['PIVOT_Z'] + (p['PIVOT_IN'] + 0.5 * (inward-p['PIVOT_IN'])) / (sqrt(3)/2)

    return ((p['LEAF_T'], p['MOVING_ATTACH_BOTTOM_Z']),
            (p['MOVING_KNEE_IN'], p['MOVING_ATTACH_BOTTOM_Z']),
            (p['MOVING_ARM_IN'], p['MOVING_ARM_BOTTOM_Z']),
            (p['MOVING_ARM_IN'], p['MOVING_ARM_TOP_Z']),
            *((inward, stop_height(inward)) for inward in p['STOP_CONTACT_IN']),
            *p['MOVING_UPPER_POINTS'], (p['LEAF_T'], p['MOVING_ATTACH_TOP_Z']))


def validate_dimensions(**overrides):
    """Return checked proposed dimensions and derived offsets; never mutate globals.

    These are nominal topology/assembly guards, not fit or tolerance approval.
    ValueError remains active with python -O, unlike assertion-only validation.
    """
    p = _values()
    unknown = overrides.keys() - p.keys()
    if unknown:
        raise ValueError(f'Unknown dimension names: {sorted(unknown)}')
    p.update(overrides)

    def require(condition, message):
        if not condition:
            raise ValueError(message)

    for name, value in p.items():
        if isinstance(value, tuple):
            continue
        require(isinstance(value, (int, float)) and not isinstance(value, bool)
                and isfinite(value) and value > 0, f'{name} must be finite and positive')
    require(all(p[k] == v for k, v in _CALIBRATED_HINGE.items()),
            'Custom hinge contour is calibrated: changed leaf/pivot/profile/stop needs requalification')
    p['FIXED_X'] = p['MOVING_X'] + p['T'] + p['CHEEK_GAP']
    p['V1_DIVIDER_OFFSET'] = p['WIDTH']/2 - p['V1_FRAME_SETBACK']
    wall_width = min(p['LENGTH'], p['WIDTH']-2*p['T'])
    require(2*p['FRAME_BORDER'] < min(p['WIDTH'], p['LENGTH']), 'Frame opening must remain positive')
    require(p['TUBE_SLOT'] < p['WIDTH']-2*p['FRAME_BORDER'], 'Tube slot must leave front frame corners')
    require(p['TUBE_RELIEF_BOTTOM_Z'] < p['HEIGHT'], 'Tube relief must leave a lower wall')
    require(p['WINDOW_WIDTH']+2*p['T'] < wall_width, 'Window must leave side-wall material borders')
    require(p['WINDOW_Z']-p['WINDOW_HEIGHT']/2 > p['T'], 'Window must leave bottom-wall material')
    require(p['WINDOW_Z']+p['WINDOW_HEIGHT']/2 < p['HEIGHT']-p['T'], 'Window must leave top-wall material')
    require(p['LEAF_WIDTH'] > p['WINDOW_WIDTH'], 'Door leaf must overlap both window sides')
    require(p['LEAF_Z']-p['LEAF_HEIGHT']/2 < p['WINDOW_Z']-p['WINDOW_HEIGHT']/2
            and p['LEAF_Z']+p['LEAF_HEIGHT']/2 > p['WINDOW_Z']+p['WINDOW_HEIGHT']/2,
            'Door leaf must overlap both window height edges')
    require(p['LEAF_WIDTH'] < wall_width, 'Door leaf must fit its wall')
    require(p['LEAF_WIDTH']/2 > p['MOVING_X']+p['T']/2, 'Moving cheeks must land on the leaf')
    require(p['PIN_D'] < p['BORE_D'] < p['PIN_HEAD_D'], 'Pin must clear bore and both heads must retain it')
    radius = p['BORE_D']/2
    require(radius+p['T'] <= min(p['PIVOT_IN'], p['FIXED_CHEEK_DEPTH']-p['PIVOT_IN'],
                         p['PIVOT_Z']-(p['FIXED_CHEEK_Z']-p['FIXED_CHEEK_HEIGHT']/2),
                         p['FIXED_CHEEK_Z']+p['FIXED_CHEEK_HEIGHT']/2-p['PIVOT_Z']),
            'Fixed cheek bore must leave at least one sheet thickness of material on every side')
    points = moving_cheek_points(p)
    # Distance from pivot to every exterior segment bounds the remaining bore ligament.
    for a, b in zip(points, (*points[1:], points[0])):
        dx, dz = b[0]-a[0], b[1]-a[1]
        u = max(0, min(1, ((p['PIVOT_IN']-a[0])*dx+(p['PIVOT_Z']-a[1])*dz)/(dx*dx+dz*dz)))
        distance = ((a[0]+u*dx-p['PIVOT_IN'])**2+(a[1]+u*dz-p['PIVOT_Z'])**2)**0.5
        require(distance-radius >= p['T'], 'Moving cheek bore must leave at least one sheet thickness of ligament')
    require(2*(p['FIXED_X']+p['T']/2+p['PIN_AXIAL_FLOAT']/2+p['PIN_HEAD_T']) < wall_width,
            'Pin and heads must fit inside the wall width')
    require(max(z for _, z in points) < p['HEIGHT'], 'Cheek profile must fit below frame')
    # Conservative whole-plane roof bound over the declared 0-to-60-degree swing.
    from math import atan2, cos, radians, sin
    for inward, z in (*points, (0, p['LEAF_Z']+p['LEAF_HEIGHT']/2),
                      (p['LEAF_T'], p['LEAF_Z']+p['LEAF_HEIGHT']/2)):
        dy, dz = inward-p['PIVOT_IN'], z-p['PIVOT_Z']
        angles = (0, radians(p['STOP_ANGLE']), atan2(dy, dz))
        roof = max(p['PIVOT_Z']+dy*sin(a)+dz*cos(a)
                   for a in angles if 0 <= a <= radians(p['STOP_ANGLE']))
        require(roof < p['HEIGHT'], 'Moving door sweep must clear frame underside')
    require(0 < p['V1_DIVIDER_OFFSET'] < p['WIDTH']/2-p['T'], 'V1 setback must leave two interior dividers')
    require(2*p['V1_DIVIDER_OFFSET'] > p['T'], 'V1 dividers must remain separate')
    require(p['V1_RETURN_WIDTH']+2*p['T'] < p['LENGTH']
            and p['V1_RETURN_HEIGHT'] < p['HEIGHT']-p['T'], 'V1 return notch must leave wall material')
    require(2*p['MOUNT_RADIUS'] < min(p['MOUNT_WIDTH'], p['MOUNT_HEIGHT']), 'Mount blank corner radius is too large')
    require(2*p['PURCHASED_WINDOW_RADIUS'] < min(p['PURCHASED_WINDOW_WIDTH'], p['PURCHASED_WINDOW_HEIGHT']),
            'Purchased window corner radius is too large')
    require(p['PURCHASED_WINDOW_WIDTH']+2*p['T'] < wall_width
            and p['PURCHASED_WINDOW_Z']-p['PURCHASED_WINDOW_HEIGHT']/2 > p['T'],
            'Purchased window must leave wall borders')
    require(p['PURCHASED_WINDOW_Z']+p['PURCHASED_WINDOW_HEIGHT']/2
            < p['PURCHASED_HOLE_Z']-p['PURCHASED_HOLE_D']/2-p['T'],
            'Purchased window must not break into mounting holes')
    require(p['PURCHASED_HOLE_Z']+p['PURCHASED_HOLE_D']/2 < p['HEIGHT']-p['T']
            and p['PURCHASED_HOLE_SPACING']+p['PURCHASED_HOLE_D']+2*p['T'] < wall_width,
            'Purchased mounting holes must leave wall borders')
    require(p['PROXY_HOLE_TOOL_DEPTH'] > p['PROXY_T'], 'Proxy hole tool must cut through proxy flange')
    return p


_CHECKED = validate_dimensions()
FIXED_X = _CHECKED['FIXED_X']
V1_DIVIDER_OFFSET = _CHECKED['V1_DIVIDER_OFFSET']

REGISTER_FIELDS = ('parameter', 'value', 'unit', 'datum', 'source', 'uncertainty', 'status')


def _register_value(value):
    if isinstance(value, (tuple, list)):
        return json.dumps(value, separators=(',', ':'))
    return str(value)


def _register_unit(name):
    if name.endswith('_DEG') or name.endswith('_ANGLES_DEG'):
        return 'deg'
    if name.endswith('_S'):
        return 's'
    if 'SCALE' in name:
        return 'ratio X/Y'
    if 'OUTLINE' in name or 'CENTERLINE' in name:
        return 'mm XY/XYZ coordinates'
    if isinstance(P4_NOMINALS.get(name), tuple) or isinstance(P4_PAN_PROXY.get(name), tuple):
        return 'mm coordinate/size array'
    return 'mm'


def parameter_register_rows():
    """Rows for the shared nominal source; unknown installed interfaces stay blank."""
    p = validate_dimensions()
    rows = []
    for name, value in p.items():
        datum = 'Cage floor centre: X across width; Y along length; Z up; wall-local profile Y inward'
        source = 'src/design_parameters.py: provisional design selection'
        uncertainty = 'No measured vehicle correspondence or approved manufacturing tolerance'
        status = 'DESIGN_ASSUMPTION_UNVERIFIED_FIT'
        if name in ('T', 'LEAF_T'):
            source = ('research/fabrication-assets/selected-material-records.json: '
                      + ('SST-048' if name == 'T' else 'SST-030') + ' nominal')
            uncertainty = ('Supplier nominal thickness tolerance +/-0.0762 mm' if name == 'T'
                           else 'Supplier nominal thickness tolerance +/-0.0508 mm')
            status = 'SOURCE_BACKED_STOCK_NOMINAL_VERIFY_ACTUAL_LOT'
        elif name.startswith('PURCHASED_') and name != 'PURCHASED_WINDOW_RADIUS':
            source = 'research/fabrication-assets/improved-racing-trap-door-mounting.pdf: EMR-200 mounting diagram 2013-10-01'
            uncertainty = 'Drawing nominal; actual purchased revision and vehicle datum correspondence unknown'
            status = 'SOURCE_BACKED_SUPPLIER_NOMINAL_UNVERIFIED_INSTALLED_DATUM'
        elif name == 'PIN_D':
            source = 'Design-selected nominal 1/8 inch rod; research/fabrication.md'
            uncertainty = 'Actual pin supplier grade diameter tolerance and retention process unknown'
            status = 'SELECTED_STANDARD_NOMINAL_NOT_PURCHASED_SPECIFICATION'
        elif name.startswith('PROXY_'):
            source = 'Provisional display envelope in src/v2_purchased_doors.py; not supplier hardware CAD'
            uncertainty = 'Unmeasured purchased geometry; excluded from custom cut parts and fit approval'
            status = 'DISPLAY_PROXY_ASSUMPTION'
        elif name in _CALIBRATED_HINGE:
            status = 'CALIBRATED_FIXED_CONTOUR_REQUALIFY_BEFORE_CHANGING'
        elif name in ('FIXED_X', 'V1_DIVIDER_OFFSET'):
            source = ('MOVING_X + T + CHEEK_GAP' if name == 'FIXED_X'
                      else 'WIDTH/2 - V1_FRAME_SETBACK; preserves nominal +/-50 mm')
            status = 'DERIVED_FROM_DESIGN_ASSUMPTIONS'
        rows.append(dict(zip(REGISTER_FIELDS, (name, str(value), 'deg' if name == 'STOP_ANGLE' else 'mm',
                                               datum, source, uncertainty, status))))
    for group, values in (('P4', P4_NOMINALS), ('PAN_PROXY', P4_PAN_PROXY)):
        for name, value in values.items():
            key = f'{group}_{name}'
            unit = _register_unit(name)
            datum = ('P4 nominal cage dimensions and named local features; no measured vehicle transform'
                     if group == 'P4' else
                     'Pan-proxy XYZ frame; cage is transformed by CAGE_ORIGIN_XYZ and CAGE_ROTATION_DEG')
            source_name = 'P4_NOMINALS' if group == 'P4' else 'P4_PAN_PROXY'
            source = f'src/design_parameters.py:{source_name}[{name}]'
            uncertainty = 'Nominal digital input; no measured installed correspondence or manufacturing tolerance'
            status = 'DESIGN_ASSUMPTION_UNVERIFIED_FIT'
            if group == 'PAN_PROXY':
                status = 'DISPLAY_PROXY_ASSUMPTION'
                uncertainty = 'Illustrative context only; not recovered OEM interior, cover, pickup or tube geometry'
                if name in ('PAN_LENGTH', 'PAN_WIDTH', 'PAN_DEPTH'):
                    source = 'Official GM12601240 product specification; overall maximum envelope only (concepts/p4/PAN_CONTEXT.md)'
                    uncertainty = 'Published overall maximum; internal sections and datum correspondence remain unknown'
                    status = 'SOURCE_BACKED_OVERALL_ENVELOPE_INTERIOR_UNKNOWN'
            elif name == 'DEMO_DURATION_S':
                uncertainty = 'Arbitrary presentation timing; it does not represent physical opening time'
                status = 'DISPLAY_ONLY_ANIMATION_SETTING'
            rows.append(dict(zip(REGISTER_FIELDS, (key, _register_value(value), unit, datum,
                                                   source, uncertainty, status))))
    lower_gap = P4_PAN_PROXY['CAGE_ORIGIN_XYZ'][2] - P4_PAN_PROXY['PAN_FLOOR_Z']
    for name, value in P5_TOOL_ACCESS.items():
        rows.append(dict(zip(REGISTER_FIELDS, (
            'TOOL_ACCESS_'+name, _register_value(value), 'mm',
            'Saved captive-pin outer face; approach outward along its signed axis',
            f'src/design_parameters.py:P5_TOOL_ACCESS[{name}]; research/pin-tool-access.md',
            'Cylindrical nose sweep only; actual heading die, body, jaws and forming process unknown',
            'DESIGN_TOOL_ENVELOPE_ASSUMPTION'))))
    rows.append(dict(zip(REGISTER_FIELDS, (
        'PAN_PROXY_DERIVED_LOWER_WALL_TO_FLOOR_GAP', _register_value(lower_gap), 'mm',
        'Pan-proxy Z frame; insert lower wall relative to assumed floor',
        'P4_PAN_PROXY[CAGE_ORIGIN_XYZ][2] - P4_PAN_PROXY[PAN_FLOOR_Z]',
        'Nominal display gap only; not a flow, retention or operating-clearance limit',
        'DERIVED_FROM_DISPLAY_PROXY_ASSUMPTIONS'))))
    for name in ('ACTUAL_PAN_FLOOR_PROFILE', 'ACTUAL_PICKUP_KEEP_OUT', 'ACTUAL_COVER_UNDERSIDE',
                 'ACTUAL_BOSS_COORDINATES_AND_SEATS', 'ACTUAL_THREADS_AND_ENGAGEMENT',
                 'ACTUAL_INSTALLED_ATTITUDE', 'ACTUAL_OIL_LEVEL_AND_RETURN_PATHS'):
        rows.append(dict(zip(REGISTER_FIELDS, (name, '', 'measurement required',
                    'Actual installed datum not established', 'delivery/MEASUREMENTS_REQUIRED.csv',
                    'Unknown: measure actual configuration with stated method and uncertainty', 'UNKNOWN_RELEASE_BLOCKER'))))
    return rows
