"""Check public packet paths and reject broken/local website links."""
from pathlib import Path
import csv,io,json,os,shutil,tempfile,zipfile
from build import SITE
from check_dist import edition_identity, validate_dist

dist=SITE/'dist'
result=validate_dist(dist,allow_preview=True)
assert result['status']=='passed' and result['concepts']==3 and result['views']==9
assert result['fit_scenarios']==5
assert result['installation_path_concepts']==3 and result['installation_paths']==6
assert result['installation_path_context_checks']==30
assert result['gravity_gate_cases']==91
version=json.loads((dist/'version.json').read_text())
if version.get('preview'):
    try:
        validate_dist(dist)
    except ValueError as error:
        assert 'Local preview editions' in str(error)
    else:
        raise AssertionError('Local preview passed the public bundle gate')
else:
    assert validate_dist(dist)['status']=='passed'
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
    asset=root/'versioned-asset.js'
    asset.write_text('original')
    edition=edition_identity(root)
    asset.write_text('edited after review')
    assert edition_identity(root)!=edition
with tempfile.TemporaryDirectory() as directory:
    bundle=Path(directory)/'dist'
    shutil.copytree(dist,bundle,copy_function=os.link)
    css=bundle/'style.css'
    content=css.read_text()
    css.unlink()
    css.write_text(content+'\n/* post-review edit */')
    try:
        validate_dist(bundle,allow_preview=version.get('preview',False))
    except ValueError as error:
        assert 'Site files changed after the edition was built' in str(error)
    else:
        raise AssertionError('A post-review site asset edit passed the edition check')
print('Public links, no-local-path guard, archive CRC, source/sidecars and both BOM path sets passed.')
