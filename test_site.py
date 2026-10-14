"""Check public packet paths and reject broken/local website links."""
from pathlib import Path
import csv,io,tempfile,zipfile
from build import SITE,validate

dist=SITE/'dist'
validate(dist)
with zipfile.ZipFile(dist/'downloads/Solstice_prototype_files.zip') as z:
    assert z.testzip() is None
    for name in ('delivery/BOM.csv','delivery/COUPON_BOM.csv'):
        for row in csv.DictReader(io.StringIO(z.read(name).decode())):
            if row['cut_file']:assert row['cut_file'] in z.namelist(),row['cut_file']
    assert 'src/design_parameters.py' in z.namelist()
    assert 'STEP/solstice_baffle.step.json' in z.namelist()
    assert not any(name.startswith(('review/','history/','research/')) for name in z.namelist())
with tempfile.TemporaryDirectory() as directory:
    root=Path(directory);page=root/'index.html'
    for fixture in ('<a href="missing.pdf">missing</a>','<p>/Users/private/file</p>','<a href="../outside.html">escape</a>'):
        page.write_text(fixture)
        try:validate(root)
        except ValueError:pass
        else:raise AssertionError('Unsafe or broken fixture accepted')
print('Public links, no-local-path guard, archive CRC, source/sidecars and both BOM path sets passed.')
