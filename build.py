"""Export an allowlisted website from the accepted project, preserving its release."""
from pathlib import Path
from html import escape
from html.parser import HTMLParser
from datetime import datetime,timezone
from urllib.parse import urlsplit,unquote
import csv,hashlib,json,re,shutil,sys,tempfile,zipfile

SITE=Path(__file__).resolve().parent
ROOT=SITE.parent
sys.path.insert(0,str(ROOT/'checks'))
from workflow import verify_candidate,sha

DOCS=['delivery/README.md','delivery/NEXT_DECISIONS.md','delivery/INTERFACE_ASSESSMENT.md',
      'delivery/TOLERANCE_SENSITIVITY.md','delivery/COUPON_PLAN.md','delivery/CURRENT_DIMENSIONS.md',
      'delivery/TOLERANCE_BUDGET.md','delivery/SENDCUTSEND_PREFLIGHT.md','QUALITY.md',
      'research/exact-interface-followup.md']
MODELS=['v1_fixed_dividers','v2_purchased_doors','solstice_baffle']


def build():
    candidate=verify_candidate()
    identity=sha(ROOT/'review/candidate.json')
    approval=json.loads((ROOT/'review/retro-fix-approval.json').read_text())
    report=json.loads((ROOT/'review/delivery-validation.json').read_text())
    if approval.get('status')!='accepted' or approval.get('candidate_sha256')!=identity or report.get('candidate_sha256')!=identity:
        raise ValueError('Publish only an accepted, packaged project candidate')
    dist=Path(tempfile.mkdtemp(prefix='.site-build-',dir=SITE))
    revision=re.search(r'status — ([^,]+)',(ROOT/'STATUS.md').read_text()).group(1)
    for name in ('assets','downloads','notes'):(dist/name).mkdir(exist_ok=True)
    public={}
    def copy(source,target):
        path=ROOT/source
        if candidate['files'].get(source)!=sha(path):raise ValueError(f'Unreviewed export: {source}')
        (dist/target).parent.mkdir(exist_ok=True,parents=True)
        shutil.copy2(path,dist/target);public[source]=target
    for folder in ('STEP','DXF','GLB','ANIMATION'):
        for path in (ROOT/folder).iterdir():
            if path.suffix in ('.step','.dxf','.glb','.mp4','.json'):
                copy(str(path.relative_to(ROOT)),f'downloads/{path.name}')
    for path in (ROOT/'src').glob('*.py'):copy(str(path.relative_to(ROOT)),f'downloads/source/{path.name}')
    for name in ['BOM.csv','COUPON_BOM.csv','COUPON_RESULTS.csv','MEASUREMENTS_REQUIRED.csv','MEASUREMENT_PRIORITY.csv','DIMENSION_REGISTER.csv','FIT_TEMPLATE.svg']:
        copy('delivery/'+name,'downloads/'+name)
    copy('PDF/hinge_inspection_drawing.pdf','downloads/hinge_inspection_drawing.pdf')
    for name in MODELS+['v3_hinge_coupon_open']:copy(f'review/{name}.png',f'assets/{name}.png')
    for name in MODELS:copy(f'ANIMATION/{name}.mp4',f'assets/{name}.mp4')
    for name in ('style.css','app.js','icon.svg'):shutil.copy2(SITE/name,dist/name)

    def link_target(url,source):
        if urlsplit(url).scheme in ('https','http'):return url
        target=(ROOT/source).parent/unquote(url.split('#')[0])
        try:key=str(target.resolve().relative_to(ROOT))
        except ValueError:return None
        if key in public:return '../'+public[key]
        if key in DOCS:return Path(key).stem+'.html'
        return None
    def inline(raw,source):
        value=escape(raw)
        def link(match):
            label,url=match.groups();target=link_target(url,source)
            return f'<a href="{escape(target,quote=True)}">{label}</a>' if target else label
        value=re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,value)
        value=re.sub(r'`([^`]+)`',r'<code>\1</code>',value)
        return re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',value)
    def document(source):
        # Deliberately limited to the Markdown constructs used in this reviewed packet.
        text=(ROOT/source).read_text()
        if source=='research/exact-interface-followup.md':
            text=re.sub(r'## Bounded local search and negative scope.*?(?=## What this pass can change)', '', text, flags=re.S)
        lines=text.splitlines();out=[];paragraph=[];listing=None;i=0
        def flush():
            if paragraph:out.append('<p>'+inline(' '.join(paragraph),source)+'</p>');paragraph.clear()
        def close_list():
            nonlocal listing
            if listing:out.append(f'</{listing}>');listing=None
        while i<len(lines):
            line=lines[i];i+=1
            if not line.strip():flush();close_list();continue
            if line.startswith('```'):
                flush();close_list();code=[]
                while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
                i+=1;out.append('<pre><code>'+escape('\n'.join(code))+'</code></pre>');continue
            if line.startswith('|'):
                flush();close_list();table=[line]
                while i<len(lines) and lines[i].startswith('|'):table.append(lines[i]);i+=1
                out.append('<div class="table-wrap"><table>')
                for n,row in enumerate(table):
                    cells=[c.strip() for c in row.strip().strip('|').split('|')]
                    if all(re.fullmatch(r':?-+:?',c) for c in cells):continue
                    tag='th' if n==0 else 'td'
                    out.append('<tr>'+''.join(f'<{tag}>'+inline(c,source)+f'</{tag}>' for c in cells)+'</tr>')
                out.append('</table></div>');continue
            heading=re.match(r'^(#{1,6}) (.*)',line)
            item=re.match(r'^(?:([-*])|\d+\.) (.*)',line)
            if heading:
                flush();close_list();level=len(heading[1]);out.append(f'<h{level}>'+inline(heading[2],source)+f'</h{level}>')
            elif item:
                flush();kind='ul' if item[1] else 'ol'
                if listing!=kind:close_list();listing=kind;out.append(f'<{kind}>')
                out.append('<li>'+inline(item[2],source)+'</li>')
            else:paragraph.append(line)
        flush();close_list()
        title=next((l[2:] for l in lines if l.startswith('# ')),Path(source).stem)
        return '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+escape(title)+' · Solstice GXP</title><link rel="stylesheet" href="../style.css"></head><body><header class="topbar"><a class="brand" href="../index.html#files">← SOLSTICE <span>PROJECT NOTES</span></a></header><main class="document">'+''.join(out)+'</main></body></html>'
    for source in DOCS:(dist/'notes'/f'{Path(source).stem}.html').write_text(document(source))

    facts=json.loads((ROOT/'review/design-summary.json').read_text())
    tolerance=json.loads((ROOT/'review/tolerance-analysis.json').read_text())
    rows=list(csv.DictReader((ROOT/'delivery/MEASUREMENTS_REQUIRED.csv').open()))
    priorities={row['worksheet_item']:row['rank'] for row in csv.DictReader((ROOT/'delivery/MEASUREMENT_PRIORITY.csv').open())}
    references=json.loads((ROOT/'research/examples-simple.json').read_text())+json.loads((ROOT/'research/examples-trapdoors.json').read_text())
    descriptions=[('Fixed dividers','Fewest parts. Two fences beneath the retained cover, with permanent return paths.','No hinges to qualify; directional retention still needs comparison.'),
      ('Purchased metal gates','A compact cage with three Improved Racing EMR-201 doors.','Real hardware must be measured. Gold parts here are simplified proxies.'),
      ('Custom metal gates','Three thin leaves, welded hinge cheeks, captive pins and 60° stops.','Most owner fabrication. Joining, alignment and retention need coupon evidence.')]
    concepts=[]
    for n,(model,(title,description,note)) in enumerate(zip(MODELS,descriptions),1):
        concepts.append(f'<article class="concept"><div class="concept-head"><p class="number">0{n} / CONCEPT</p><h3>{title}</h3></div><video controls playsinline preload="none" poster="assets/{model}.png" aria-label="{title} illustrative animation"><source src="assets/{model}.mp4" type="video/mp4"><a href="assets/{model}.mp4">Download animation</a></video><div class="concept-body"><p>{description}</p><strong class="part-count">{facts["cut_counts"][f"V{n}"]} custom cut pieces</strong><p>{note}</p><div class="concept-links"><a href="downloads/{model}.step" download>STEP ↓</a><a href="downloads/{model}.glb" download>Animated GLB ↓</a><a href="downloads/BOM.csv">BOM ↗</a></div></div></article>')
    measurements=''.join(f'<li><span class="tag">Priority {priorities[r["item"]]} · {escape(r["status"])}</span><strong>{escape(r["item"])}</strong><p>{escape(r["method"])}</p></li>' for r in sorted(rows,key=lambda r:int(priorities[r['item']])))
    refs=''.join(f'<article class="reference" data-level="{escape(r["complexity"])}"><p class="eyebrow">{escape(r["complexity"])} / {escape(r["engine"])}</p><h3>{escape(r["name"])}</h3><p>{escape(r["mechanism"])}</p><p><strong>Construction lesson:</strong> {escape(r["lesson"])}</p><a href="{escape(r["url"],quote=True)}" target="_blank" rel="noopener">Manufacturer source ↗</a></article>' for r in references)
    resources=[('NEXT_DECISIONS','Measurement & bench plan','What to measure first, and which decision it unlocks.'),('INTERFACE_ASSESSMENT','Evidence & uncertainty','Exact-pan sources, supported identities and hidden fit gaps.'),('TOLERANCE_SENSITIVITY','Tolerance sensitivity','Reproducible conditional budgets for the hinge and mounting stack.'),('README','Fabrication & fit notes','Stock, quantities, assembly intent and unresolved release holds.'),('SENDCUTSEND_PREFLIGHT','SendCutSend preparation','Cut-file review and supplier/process boundaries.'),('QUALITY','Design & production standards','The project criteria for each development stage.')]
    cards=''.join(f'<a class="resource" href="notes/{name}.html"><h3>{title} ↗</h3><p>{description}</p></a>' for name,title,description in resources)
    dxfs=''.join(f'<a href="downloads/{p.name}" download>{p.stem.replace("_"," ")} ↓</a>' for p in sorted((ROOT/'DXF').glob('*.dxf')))
    now=datetime.now(timezone.utc)
    template=(SITE/'index.template.html').read_text()
    values={'REVISION':revision,'DATE':now.isoformat(),'DATE_LABEL':now.strftime('%d %b %Y, %H:%M UTC'),
      'PROFILES':str(len(list((ROOT/'DXF').glob('*.dxf')))), 'UNKNOWN':str(sum(r['status']=='UNKNOWN' for r in rows)),
      'CONCEPTS':''.join(concepts),'MEASUREMENTS':measurements,'REFERENCES':refs,'RESOURCES':cards,'DXFS':dxfs,
      'CHEEK':f'{tolerance["cheek_gap"]["thickness_only_range_mm"][0]:.4f}',
      'ROOF':f'{tolerance["continuous_roof"]["gap_mm"]:.3f}',
      'STACK':f'{tolerance["mounting_stack"]["conditional_added_SST048_sheet_cases"][0]["nominal_insertion_loss_mm"]:.4f}'}
    for key,value in values.items():template=template.replace('@@'+key+'@@',value)
    (dist/'index.html').write_text(template)
    # Public download is curated; private review logs and third-party source archives stay local.
    with zipfile.ZipFile(dist/'downloads/Solstice_prototype_files.zip','w',zipfile.ZIP_DEFLATED) as z:
        for source,target in sorted(public.items()):
            if target.startswith('downloads/'):z.write(dist/target,source)
        for source in DOCS:
            if source.startswith('delivery/') or source=='QUALITY.md':z.write(ROOT/source,source)
        z.writestr('READ_ME_FIRST.txt',f'Solstice GXP nominal prototype exports, {revision}. Fit and engine-use release held.\nUse delivery/BOM.csv for variant quantities and DXF paths; do not order all profiles.\nSource CAD is under src/ and uses pinned cadgen==0.7.21. Native animation sidecars accompany STEP files.\nThis curated public export is not the complete local validation/evidence workspace.\nRead the fabrication, uncertainty and measurement notes before bench work.\n')
    (dist/'.nojekyll').touch()
    edition=hashlib.sha256(''.join(sha(p) for p in sorted(dist.rglob('*')) if p.is_file() and p.name!='version.json').encode()).hexdigest()[:16]
    (dist/'index.html').write_text(template.replace('@@EDITION@@',edition))
    (dist/'version.json').write_text(json.dumps({'edition':edition,'updated_at':now.isoformat(),'candidate_sha256':identity})+'\n')
    validate(dist)
    previous=SITE/'.previous-dist'
    if previous.exists():shutil.rmtree(previous)
    if (SITE/'dist').exists():(SITE/'dist').rename(previous)
    dist.rename(SITE/'dist');dist=SITE/'dist'
    print(json.dumps({'site_files':len([p for p in dist.rglob('*') if p.is_file()]),'edition':edition,'source_candidate':identity}))


def validate(dist):
    class Links(HTMLParser):
        def handle_starttag(self,tag,attrs):
            for key,value in attrs:
                if key in ('href','src','poster') and value and not urlsplit(value).scheme and not value.startswith('#'):
                    target=(self.path.parent/unquote(urlsplit(value).path)).resolve()
                    if not target.is_relative_to(dist.resolve()) or not target.is_file():raise ValueError(f'Broken public link: {self.path.name}: {value}')
    for path in dist.rglob('*'):
        if path.is_file() and path.suffix in ('.html','.csv','.svg','.js','.css','.step'):
            data=path.read_text()
            if '/Users/' in data or '127.0.0.1' in data:raise ValueError(f'Private/local path in public export: {path.name}')
            if path.suffix=='.html':
                if '@@' in data:raise ValueError('Unexpanded template token')
                parser=Links();parser.path=path;parser.feed(data)


if __name__=='__main__':build()
