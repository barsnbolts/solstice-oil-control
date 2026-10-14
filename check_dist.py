"""Validate the portable GitHub Pages bundle without the private CAD workspace."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import csv
import hashlib
import io
import json
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


def validate_dist(dist):
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
    edition_match = re.search(r'<meta name="project-edition" content="([^"]+)"', index)
    if not edition_match or edition_match.group(1) != version.get('edition'):
        raise ValueError('Page edition does not match version.json')
    candidate = version.get('candidate_sha256')
    if not re.fullmatch(r'[0-9a-f]{64}', candidate or '') or catalog.get('candidate_sha256') != candidate:
        raise ValueError('Catalog and published version do not bind the same candidate')
    if catalog.get('schema_version') != 1 or set(catalog.get('concepts', {})) != set(CURRENT):
        raise ValueError('Unexpected current-concept catalog')

    selector = re.search(r'<select id="pan-concept">(.*?)</select>', index, re.S)
    values = set(re.findall(r'<option value="([^"]+)"', selector.group(1))) if selector else set()
    if values != set(CURRENT):
        raise ValueError(f'Concept selector and catalog differ: {values}')
    view_selector = re.search(r'<select id="pan-view">(.*?)</select>', index, re.S)
    view_values = set(re.findall(r'<option value="([^"]+)"', view_selector.group(1))) if view_selector else set()
    if view_values != VIEWS:
        raise ValueError(f'View selector and catalog differ: {view_values}')

    cards = {key: (well, envelope, gates, cuts, pins, card)
             for key, well, envelope, gates, cuts, pins, card in re.findall(
                 r'<article class="concept" data-concept="([^"]+)" data-well-mm="([^"]+)" '
                 r'data-envelope-mm="([^"]+)" data-gates="([^"]+)" '
                 r'data-cut-plates="([^"]+)" data-pins="([^"]+)"(.*?)</article>', index, re.S)}
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
        well, envelope, gates, cuts, pins, card = cards[key]
        if (well != dimension(concept['well_mm']) or envelope != dimension(concept['envelope_mm'])
                or int(gates) != concept['gates'] or int(cuts) != concept['cut_plates']
                or int(pins) != concept['pins']):
            raise ValueError(f'Website card disagrees with shared catalog: {key}')
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
            'candidate_sha256': candidate, 'zip_members': len(members),
            'current_profiles': len(current_profiles), 'download_profiles': total_profiles,
            'download_profile_paths': len(dxf_members)}


if __name__ == '__main__':
    print(json.dumps(validate_dist(SITE/'dist'), sort_keys=True))
