"""Refresh the curated public site and push it to the existing Pages repository."""
from pathlib import Path
import subprocess
import sys
SITE=Path(__file__).resolve().parent
subprocess.run([sys.executable,str(SITE/'build.py')],check=True)
subprocess.run(['git','add','dist','index.template.html','style.css','app.js','icon.svg','build.py','publish.py','test_site.py','README.md','.github','.gitignore'],cwd=SITE,check=True)
changed=subprocess.run(['git','diff','--cached','--quiet'],cwd=SITE).returncode
if changed==1:subprocess.run(['git','commit','-m','Update accepted Solstice project edition'],cwd=SITE,check=True)
elif changed!=0:raise RuntimeError('Could not inspect staged site changes')
subprocess.run(['git','push','origin','main'],cwd=SITE,check=True)
