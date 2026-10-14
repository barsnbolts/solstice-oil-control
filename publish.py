"""Publish the exact static edition accepted with the frozen CAD candidate."""
from pathlib import Path
import json
import subprocess
import sys

SITE=Path(__file__).resolve().parent
ROOT=SITE.parent
sys.path.insert(0,str(ROOT/'checks'))
sys.path.insert(0,str(SITE))
from workflow import sha,verify_candidate
from check_dist import validate_dist


def verify_reviewed_edition():
    verify_candidate(ROOT)
    candidate_sha=sha(ROOT/'review/candidate.json')
    approval=json.loads((ROOT/'review/retro-fix-approval.json').read_text())
    package=json.loads((ROOT/'review/delivery-validation.json').read_text())
    version=json.loads((SITE/'dist/version.json').read_text())
    if approval.get('status')!='accepted' or approval.get('candidate_sha256')!=candidate_sha:
        raise ValueError('The CAD candidate is not accepted for publication')
    if package.get('candidate_sha256')!=candidate_sha:
        raise ValueError('The accepted CAD candidate has not been packaged')
    if (approval.get('site_edition')!=version.get('edition') or
            version.get('candidate_sha256')!=candidate_sha):
        raise ValueError('The static site is not the exact edition accepted with this candidate')
    page=(SITE/'dist/index.html').read_text()
    if 'LOCAL PREVIEW / REVIEW PENDING' in page or 'DIGITAL REVIEW COMPLETE' not in page:
        raise ValueError('The reviewed bundle does not carry its production status')
    validate_dist(SITE/'dist')
    return version['edition']


def publish():
    edition=verify_reviewed_edition()
    print(f'Publishing accepted site edition {edition}')
    subprocess.run(['git','add','dist','index.template.html','style.css','app.js','icon.svg','build.py','publish.py','test_site.py','check_dist.py','README.md','vendor','.github','.gitignore'],cwd=SITE,check=True)
    changed=subprocess.run(['git','diff','--cached','--quiet'],cwd=SITE).returncode
    if changed==1:subprocess.run(['git','commit','-m','Update accepted Solstice project edition'],cwd=SITE,check=True)
    elif changed!=0:raise RuntimeError('Could not inspect staged site changes')
    subprocess.run(['git','push','origin','main'],cwd=SITE,check=True)


if __name__=='__main__':
    publish()
