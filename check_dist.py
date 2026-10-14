"""Validate the portable GitHub Pages bundle without the private CAD workspace."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import csv
import hashlib
import io
import json
import math
import re
import zipfile

SITE = Path(__file__).resolve().parent
CURRENT = {'baseline': 'A', 'radial': 'B', 'nested': 'C'}
VIEWS = {'detail', 'exploded', 'section'}


class Links(HTMLParser):
    def __init__(self, path, root):
        super().__init__()
        self.path = path
        self.root = root

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key not in ('href', 'src', 'poster') or not value:
                continue
            url = urlsplit(value)
            if url.scheme or not url.path:
                continue
            target = (self.path.parent/unquote(url.path)).resolve()
            if not target.is_relative_to(self.root.resolve()) or not target.is_file():
                raise ValueError(f'Broken public link: {self.path.relative_to(self.root)}: {value}')


def dimension(values):
    return ' × '.join(f'{value:g}' for value in values)


def bom_counts(archive, member, variant):
    rows = csv.DictReader(io.StringIO(archive.read(member).decode('utf-8')))
    selected = [row for row in rows if row['variant'] == variant]
    return (sum(int(row['quantity']) for row in selected if row['cut_file']),
            sum(int(row['quantity']) for row in selected if is_captive_pin(row['part'])))


def bom_profiles(archive, member, variant):
    rows = csv.DictReader(io.StringIO(archive.read(member).decode('utf-8')))
    return {Path(row['cut_file']).name for row in rows
            if row['variant'] == variant and row['cut_file']}


def is_captive_pin(value):
    normalized = re.sub(r'[^a-z0-9]', '', value.lower())
    return normalized in {'captivepin', 'captivepivotpin'}


def edition_identity(dist, edition=None):
    dist = Path(dist)
    if edition is None and (dist/'version.json').is_file():
        edition = json.loads((dist/'version.json').read_text()).get('edition')
    content_hashes = ''
    for path in sorted(dist.rglob('*')):
        if not path.is_file() or path.name == 'version.json':
            continue
        data = path.read_bytes()
        if edition and path.suffix == '.html':
            text = data.decode('utf-8')
            text = text.replace(f'<meta name="project-edition" content="{edition}">',
                                '<meta name="project-edition" content="@@EDITION@@">')
            text = text.replace(f'?v={edition}', '').replace(f'&amp;v={edition}', '')
            data = text.encode('utf-8')
        content_hashes += hashlib.sha256(data).hexdigest()
    return hashlib.sha256(content_hashes.encode()).hexdigest()[:16]


def validate_dist(dist, *, allow_preview=False):
    dist = Path(dist).resolve()
    page = dist/'index.html'
    if not page.is_file():
        raise ValueError('Published bundle is missing index.html')
    for path in dist.rglob('*'):
        if not path.is_file():
            continue
        if path.suffix in ('.html', '.csv', '.svg', '.js', '.css', '.step', '.json'):
            data = path.read_text(encoding='utf-8')
            if '/Users/' in data or '127.0.0.1' in data:
                raise ValueError(f'Private/local path in public export: {path.relative_to(dist)}')
            if path.suffix == '.html':
                if '@@' in data:
                    raise ValueError(f'Unexpanded template token: {path.relative_to(dist)}')
                parser = Links(path, dist)
                parser.feed(data)

    index = page.read_text(encoding='utf-8')
    version = json.loads((dist/'version.json').read_text())
    catalog = json.loads((dist/'catalog.json').read_text())
    preview = version.get('preview', False)
    if preview and not allow_preview:
        raise ValueError('Local preview editions cannot pass the public bundle check')
    status_text = 'LOCAL PREVIEW / REVIEW PENDING' if preview else 'DIGITAL REVIEW COMPLETE'
    if status_text not in index:
        raise ValueError('Page status does not match the bundle review state')
    edition_match = re.search(r'<meta name="project-edition" content="([^"]+)"', index)
    if not edition_match or edition_match.group(1) != version.get('edition'):
        raise ValueError('Page edition does not match version.json')
    actual_edition = edition_identity(dist, version.get('edition'))
    if actual_edition != version.get('edition'):
        raise ValueError('Site files changed after the edition was built')
    candidate = version.get('candidate_sha256')
    if not re.fullmatch(r'[0-9a-f]{64}', candidate or '') or catalog.get('candidate_sha256') != candidate:
        raise ValueError('Catalog and published version do not bind the same candidate')
    if catalog.get('schema_version') != 1 or set(catalog.get('concepts', {})) != set(CURRENT):
        raise ValueError('Unexpected current-concept catalog')

    fit_report = json.loads((dist/'assets/digital-fit-scenarios.json').read_text())
    scenarios = fit_report.get('digital_fit_scenarios', {})
    fit_section = re.search(r'<section id="fitment" class="section">(.*?)</section>', index, re.S)
    if not fit_section or not scenarios:
        raise ValueError('Digital fit scenario section or data is missing')
    scenario_cards = {name: body for name, body in re.findall(
        r'<article class="fit-scenario" data-scenario="([^"]+)">(.*?)</article>',
        fit_section.group(1), re.S)}
    if set(scenario_cards) != set(scenarios):
        raise ValueError('Digital fit scenario cards disagree with the saved geometry report')
    for name, scenario in scenarios.items():
        card = scenario_cards[name]
        outcomes = {letter: (state, label) for letter, state, label in re.findall(
            r'<div class="fit-outcome" data-fit-concept="([ABC])">.*?'
            r'<span class="fit-state (clear|intersection)">([^<]+)</span>', card, re.S)}
        if set(outcomes) != {'A', 'B', 'C'}:
            raise ValueError(f'Incomplete fit outcomes on site: {name}')
        for concept_key, letter in CURRENT.items():
            expected = scenario['concepts'][concept_key]['status']
            state = 'clear' if expected == 'clear_in_declared_proxy' else 'intersection'
            if outcomes[letter][0] != state:
                raise ValueError(f'Site fit status disagrees with CAD report: {name}/{letter}')

    nominal = scenarios.get('nominal_visual_proxy', {}).get('concepts', {})
    path_section = re.search(r'<div class="fit-path-grid">(.*?)</div></section>', index, re.S)
    if not path_section or set(nominal) != set(CURRENT):
        raise ValueError('Digital installation-path section or nominal results are missing')
    path_cards = {letter: body for letter, body in re.findall(
        r'<article class="fit-path-card" data-path-concept="([ABC])">(.*?)</article>',
        path_section.group(1), re.S)}
    if set(path_cards) != set(CURRENT.values()):
        raise ValueError('Installation-path cards do not cover A/B/C')
    route_names = {'pickup_tube_retained', 'pickup_tube_removed_as_assembly'}
    path_context_results = []
    for scenario in scenarios.values():
        for concept_key in CURRENT:
            routes = scenario['concepts'][concept_key].get('installation_paths', {})
            if set(routes) != route_names:
                raise ValueError(f'Incomplete saved installation-path results: {concept_key}')
            for route, result in routes.items():
                if result.get('sample_step_mm') != 1.0 or result.get('sampled_poses', 0) < 1:
                    raise ValueError(f'Unexpected installation-path sampling: {concept_key}/{route}')
                clear = result.get('status') == 'clear_in_sampled_vertical_path'
                if clear != (result.get('first_collision') is None):
                    raise ValueError(f'Contradictory installation-path result: {concept_key}/{route}')
                path_context_results.append((route, clear))
    retained_total = sum(route == 'pickup_tube_retained' for route, _ in path_context_results)
    retained_blocked = sum(route == 'pickup_tube_retained' and not clear
                           for route, clear in path_context_results)
    removed_total = sum(route == 'pickup_tube_removed_as_assembly'
                        for route, _ in path_context_results)
    removed_clear = sum(route == 'pickup_tube_removed_as_assembly' and clear
                        for route, clear in path_context_results)
    path_note = (f'Across five contexts, the retained pickup/tube route is blocked in '
                 f'{retained_blocked} of {retained_total} concept-context checks. '
                 f'With that proxy assembly omitted, {removed_clear} of {removed_total} checks clear; '
                 'nested C is blocked only by the narrowed-shell proxy.')
    displayed_note = re.search(
        r'<div class="fit-path-section">.*?<p class="fit-summary">(.*?)</p>',
        fit_section.group(1), re.S)
    if not displayed_note or displayed_note.group(1) != path_note:
        raise ValueError('Installation-path summary disagrees with saved scenario results')
    gravity = fit_report.get('gravity_torque_study', {})
    gravity_cases = gravity.get('gravity_vectors_m_s2', {})
    gravity_concepts = gravity.get('concepts', {})
    if (len(gravity_cases) != 7 or set(gravity_concepts) != set(CURRENT)
            or gravity.get('angle_samples_deg') != fit_report.get('sample_angles_deg')):
        raise ValueError('Saved gravity-torque coverage is incomplete')
    for case, vector in gravity_cases.items():
        if abs(sum(value*value for value in vector)**0.5 - 9.80665) > 1e-6:
            raise ValueError(f'Invalid effective-gravity vector: {case}')
    gate_counts = {'baseline': 3, 'radial': 4, 'nested': 6}
    for concept_key, gates in gravity_concepts.items():
        if len(gates) != gate_counts[concept_key]:
            raise ValueError(f'Wrong gate count in gravity-torque report: {concept_key}')
        for gate, results in gates.items():
            if set(results) != set(gravity_cases):
                raise ValueError(f'Incomplete gravity cases: {concept_key}/{gate}')
            for case, result in results.items():
                curve = result.get('curve', [])
                if [row.get('angle_deg') for row in curve] != gravity['angle_samples_deg']:
                    raise ValueError(f'Incomplete gravity angle curve: {concept_key}/{gate}/{case}')
                closed = curve[0]['torque_Nm_per_kg']
                bias = 'opens' if closed > 1e-9 else 'closes' if closed < -1e-9 else 'neutral'
                if result.get('closed_bias') != bias:
                    raise ValueError(f'Gravity bias disagrees with torque sign: {concept_key}/{gate}/{case}')
    if any(gate['level']['closed_bias'] != 'closes'
           for gates in gravity_concepts.values() for gate in gates.values()):
        raise ValueError('Level gravity result does not match the saved gate geometry')
    for concept_key, letter in CURRENT.items():
        routes = {route: (state, css_state) for route, state, css_state in re.findall(
            r'<div class="fit-route-row" data-fit-route="([^"]+)" '
            r'data-route-state="([^"]+)">.*?<strong class="fit-state (clear|intersection)">',
            path_cards[letter], re.S)}
        expected = nominal[concept_key].get('installation_paths', {})
        if set(routes) != route_names or set(expected) != route_names:
            raise ValueError(f'Incomplete installation-path routes on site: {letter}')
        for route in route_names:
            expected_status = expected[route]['status']
            expected_css = 'clear' if expected_status == 'clear_in_sampled_vertical_path' else 'intersection'
            if routes[route] != (expected_status, expected_css):
                raise ValueError(f'Site installation path disagrees with CAD report: {letter}/{route}')

    alternative = fit_report.get('digital_alternative_exit_path_study', {})
    alternative_paths = alternative.get('paths', {})
    alternative_concepts = alternative.get('concepts', {})
    if (len(alternative_paths) != 8 or set(alternative_concepts) != set(CURRENT)
            or alternative.get('continuous_motion_proven') is not False):
        raise ValueError('Saved alternative exit-path coverage or limits are incomplete')
    if 'fit-alt-path-grid' not in fit_section.group(1):
        raise ValueError('Alternative exit-path result cards are missing')
    alternative_cards = {name: body for name, body in re.findall(
        r'<article class="fit-alt-path-card" data-alt-path="([^"]+)">(.*?)</article>',
        fit_section.group(1), re.S)}
    if set(alternative_cards) != set(alternative_paths):
        raise ValueError('Alternative exit-path cards disagree with saved CAD paths')
    alternative_results = 0
    blocked_results = 0
    for path_name, path in alternative_paths.items():
        card = alternative_cards[path_name]
        heading = re.search(r'<h4>(.*?)</h4>', card, re.S)
        if not heading or heading.group(1) != path.get('label'):
            raise ValueError(f'Alternative exit-path title is not reader-facing: {path_name}')
        if 'REFERENCE_' in card or re.search(r'<h4>(?:shift|tilt)_', card):
            raise ValueError(f'Internal route identifiers are visible on the site: {path_name}')
        outcomes = {letter: (state, css_state) for letter, state, css_state in re.findall(
            r'<div class="fit-alt-outcome" data-alt-concept="([ABC])" '
            r'data-alt-state="(clear|intersection)">.*?'
            r'<strong class="fit-state (clear|intersection)">', card, re.S)}
        if set(outcomes) != set(CURRENT.values()):
            raise ValueError(f'Alternative exit path does not cover A/B/C: {path_name}')
        for concept_key, letter in CURRENT.items():
            result = alternative_concepts[concept_key].get(path_name)
            if not result:
                raise ValueError(f'Missing saved alternative exit result: {concept_key}/{path_name}')
            status = result.get('status')
            if status not in {'blocked_by_proxy_intersection', 'clear_in_sampled_exit_path'}:
                raise ValueError(f'Invalid alternative exit status: {concept_key}/{path_name}')
            css_state = 'intersection' if status == 'blocked_by_proxy_intersection' else 'clear'
            if outcomes[letter] != (css_state, css_state):
                raise ValueError(f'Site alternative exit result disagrees with CAD: {letter}/{path_name}')
            sampling = result.get('sampling', {})
            if (result.get('sampled_poses', 0) < 1
                    or sampling.get('translation_step_mm') != 1.0
                    or (path.get('mode') == 'tilt' and sampling.get('rotation_step_deg') != 1.0)):
                raise ValueError(f'Unexpected alternative exit sampling: {concept_key}/{path_name}')
            collision = result.get('first_collision')
            if (status == 'clear_in_sampled_exit_path') != (collision is None):
                raise ValueError(f'Contradictory alternative exit result: {concept_key}/{path_name}')
            alternative_results += 1
            blocked_results += status == 'blocked_by_proxy_intersection'
    expected_alt_note = (f'{blocked_results} of {alternative_results} selected concept-path checks '
                         'intersect the nominal pickup/tube or pan-shell proxy at a sampled pose. '
                         'A clear result applies only to these discrete paths.')
    displayed_alt_note = re.search(
        r'<div class="fit-alt-section">.*?<p class="fit-summary">(.*?)</p>',
        fit_section.group(1), re.S)
    if not displayed_alt_note or displayed_alt_note.group(1) != expected_alt_note:
        raise ValueError('Alternative exit-path summary disagrees with saved CAD results')

    selector = re.search(r'<select id="pan-concept">(.*?)</select>', index, re.S)
    values = set(re.findall(r'<option value="([^"]+)"', selector.group(1))) if selector else set()
    if values != set(CURRENT):
        raise ValueError(f'Concept selector and catalog differ: {values}')
    view_selector = re.search(r'<select id="pan-view">(.*?)</select>', index, re.S)
    view_values = set(re.findall(r'<option value="([^"]+)"', view_selector.group(1))) if view_selector else set()
    if view_values != VIEWS:
        raise ValueError(f'View selector and catalog differ: {view_values}')

    cards = {key: (well, envelope, gates, cuts, pins, area, mass, moving_mass, window_area, card)
             for key, well, envelope, gates, cuts, pins, area, mass, moving_mass, window_area, card in re.findall(
                 r'<article class="concept" data-concept="([^"]+)" data-well-mm="([^"]+)" '
                 r'data-envelope-mm="([^"]+)" data-gates="([^"]+)" '
                 r'data-cut-plates="([^"]+)" data-pins="([^"]+)" '
                 r'data-installed-net-cut-area-mm2="([^"]+)" '
                 r'data-estimated-metal-mass-g="([^"]+)" '
                 r'data-estimated-moving-gate-mass-g="([^"]+)" '
                 r'data-gross-gate-window-area-mm2="([^"]+)"(.*?)</article>', index, re.S)}
    if set(cards) != set(CURRENT):
        raise ValueError('Current A/B/C cards do not match the catalog')

    for key, letter in CURRENT.items():
        concept = catalog['concepts'][key]
        if concept.get('letter') != letter or set(concept.get('views', {})) != VIEWS:
            raise ValueError(f'Invalid variant/view entry: {key}')
        if not (len(concept.get('well_mm', ())) == 2 and len(concept.get('envelope_mm', ())) == 3
                and all(isinstance(value, (int, float)) and value > 0
                        for value in (*concept['well_mm'], *concept['envelope_mm']))):
            raise ValueError(f'Invalid nominal dimensions: {key}')
        well, envelope, gates, cuts, pins, area, mass, moving_mass, window_area, card = cards[key]
        if (well != dimension(concept['well_mm']) or envelope != dimension(concept['envelope_mm'])
                or int(gates) != concept['gates'] or int(cuts) != concept['cut_plates']
                or int(pins) != concept['pins']):
            raise ValueError(f'Website card disagrees with shared catalog: {key}')
        comparison = concept.get('comparison', {})
        expected_metrics = (
            ('installed_net_cut_area_mm2', area),
            ('estimated_metal_mass_g', mass),
            ('estimated_moving_gate_mass_g', moving_mass),
            ('gross_gate_window_area_mm2', window_area),
        )
        if any(name not in comparison or not math.isclose(comparison[name], float(value),
                                                          rel_tol=0, abs_tol=0.001)
               for name, value in expected_metrics):
            raise ValueError(f'Website card comparison metrics disagree with catalog: {key}')
        paths = [concept.get('overview', '')]
        for stage, entry in concept['views'].items():
            if set(entry) != {'model', 'poster', 'step'}:
                raise ValueError(f'Invalid view file map: {key}/{stage}')
            paths.extend(entry.values())
        for relative in paths:
            target = (dist/relative).resolve()
            if not target.is_relative_to(dist) or not target.is_file() or target.stat().st_size == 0:
                raise ValueError(f'Missing catalog asset: {key}: {relative}')

    default = catalog.get('default_selection', {})
    if default.get('concept') not in CURRENT or default.get('view') not in VIEWS:
        raise ValueError('Invalid default interactive view')
    default_view = catalog['concepts'][default['concept']]['views'][default['view']]
    model_match = re.search(r'<model-viewer[^>]*\bid="pan-model"[^>]*\bsrc="([^"]+)"', index)
    if not model_match or urlsplit(model_match.group(1)).path != default_view['model']:
        raise ValueError('Initial interactive viewer does not match the catalog default')

    archive_path = dist/'downloads/Solstice_prototype_files.zip'
    with zipfile.ZipFile(archive_path) as archive:
        if archive.testzip() is not None:
            raise ValueError('Public prototype ZIP failed its CRC check')
        members = set(archive.namelist())
        for key, letter in CURRENT.items():
            concept = catalog['concepts'][key]
            bom, variant = ('delivery/BOM.csv', 'V3') if key == 'baseline' else ('concepts/p4/BOM.csv', key)
            counts = bom_counts(archive, bom, variant)
            if counts != (concept['cut_plates'], concept['pins']):
                raise ValueError(f'Website catalog counts disagree with {bom}: {letter}')
        for bom in ('delivery/BOM.csv', 'concepts/p4/BOM.csv'):
            for row in csv.DictReader(io.StringIO(archive.read(bom).decode('utf-8'))):
                if row['cut_file']:
                    target = str(Path(bom).parent/row['cut_file']) if bom.startswith('concepts/') else row['cut_file']
                    if target not in members:
                        raise ValueError(f'Public ZIP BOM points to a missing cut file: {target}')
        current_profiles = bom_profiles(archive, 'delivery/BOM.csv', 'V3') | \
            bom_profiles(archive, 'concepts/p4/BOM.csv', 'radial') | \
            bom_profiles(archive, 'concepts/p4/BOM.csv', 'nested')
        dxf_members = [name for name in members if name.endswith('.dxf') and
                       (name.startswith('DXF/') or name.startswith('concepts/p4/DXF/'))]
        profile_hashes = {}
        for name in dxf_members:
            profile_name = Path(name).name
            digest = hashlib.sha256(archive.read(name)).hexdigest()
            if profile_name in profile_hashes and profile_hashes[profile_name] != digest:
                raise ValueError(f'Duplicate DXF filename has different contents: {profile_name}')
            profile_hashes[profile_name] = digest
        all_profiles = set(profile_hashes)
        if not current_profiles.issubset(all_profiles):
            raise ValueError('A/B/C BOM references a missing downloadable DXF profile')
        total_profiles = len(all_profiles)
        profile_match = re.search(
            r'<p class="small" data-profile-counts="(\d+),(\d+),(\d+),(\d+)">', index)
        expected_profile_counts = (total_profiles, len(current_profiles),
                                   total_profiles-len(current_profiles), len(dxf_members))
        if not profile_match or tuple(map(int, profile_match.groups())) != expected_profile_counts:
            raise ValueError(f'Website DXF summary disagrees with the BOM: {expected_profile_counts}')
        if any(name.startswith(('review/', 'history/', 'research/')) for name in members):
            raise ValueError('Private review/history/research files entered the public ZIP')
    return {'status': 'passed', 'concepts': len(CURRENT), 'views': len(CURRENT)*len(VIEWS),
            'fit_scenarios': len(scenarios),
            'installation_path_concepts': len(path_cards),
            'installation_paths': len(path_cards)*len(route_names),
            'installation_path_context_checks': len(path_context_results),
            'alternative_exit_paths': len(alternative_paths),
            'alternative_exit_path_checks': alternative_results,
            'gravity_gate_cases': sum(len(gates)*len(gravity_cases) for gates in gravity_concepts.values()),
            'candidate_sha256': candidate, 'zip_members': len(members),
            'current_profiles': len(current_profiles), 'download_profiles': total_profiles,
            'download_profile_paths': len(dxf_members)}


if __name__ == '__main__':
    print(json.dumps(validate_dist(SITE/'dist'), sort_keys=True))
