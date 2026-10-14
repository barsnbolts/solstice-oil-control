"""Check public packet paths and reject broken/local website links."""
from pathlib import Path
import csv,io,tempfile,zipfile
from build import SITE
from check_dist import validate_dist

dist=SITE/'dist'
result=validate_dist(dist)
assert result['status']=='passed' and result['concepts']==3 and result['views']==9
with zipfile.ZipFile(dist/'downloads/Solstice_prototype_files.zip') as z:
    assert z.testzip() is None
    for name in ('delivery/BOM.csv','delivery/COUPON_BOM.csv','concepts/p4/BOM.csv'):
        for row in csv.DictReader(io.StringIO(z.read(name).decode())):
            if row['cut_file']:
                target=(str(Path(name).parent/row['cut_file']) if name.startswith('concepts/') else row['cut_file'])
                assert target in z.namelist(),target
    assert 'src/design_parameters.py' in z.namelist()
    assert 'STEP/solstice_baffle.step.json' in z.namelist()
    assert not any(name.startswith(('review/','history/','research/')) for name in z.namelist())
    assert 'concepts/p4/src/advanced_geometry.py' in z.namelist()
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory);page=root/'index.html'
    for fixture in ('<a href="missing.pdf">missing</a>','<p>/Users/private/file</p>','<a href="../outside.html">escape</a>'):
        page.write_text(fixture)
        try:validate_dist(root)
        except ValueError:pass
        else:raise AssertionError('Unsafe or broken fixture accepted')
print('Public links, no-local-path guard, archive CRC, source/sidecars and both BOM path sets passed.')
