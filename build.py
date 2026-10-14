"""Export an allowlisted website from the accepted project, preserving its release."""
from pathlib import Path
from html import escape
from datetime import datetime,timezone
from urllib.parse import urlsplit,urlunsplit,unquote
import csv,hashlib,json,re,shutil,sys,tempfile,zipfile

SITE=Path(__file__).resolve().parent
ROOT=SITE.parent
sys.path.insert(0,str(ROOT/'checks'))
sys.path.insert(0,str(ROOT/'src'))
from workflow import verify_candidate,sha
from check_dist import validate_dist
from design_parameters import P4_NOMINALS,P4_PAN_PROXY

DOCS=['delivery/README.md','delivery/NEXT_DECISIONS.md','delivery/INTERFACE_ASSESSMENT.md',
      'delivery/TOLERANCE_SENSITIVITY.md','delivery/COUPON_PLAN.md','delivery/CURRENT_DIMENSIONS.md',
      'delivery/TOLERANCE_BUDGET.md','delivery/SENDCUTSEND_PREFLIGHT.md','QUALITY.md',
      'research/exact-interface-followup.md','research/honda-precedents.md',
      'research/same-pan-family-visuals.md','research/pan-camera-audit.md',
      'research/pin-tool-access.md','review/pin-tool-access-assessment.md',
      'research/heading-accessory.md','review/heading-accessory-assessment.md',
      'review/digital-fit-scenario-assessment.md','concepts/p4/CONCEPTS.md','concepts/p4/PAN_CONTEXT.md']
MODELS=['v1_fixed_dividers','v2_purchased_doors','solstice_baffle']
SCENARIOS=('nominal_visual_proxy','cover_12mm_lower_stress',
           'pickup_and_tube_25pct_larger_stress','pickup_route_offset_stress',
           'narrower_shell_stress')
SENSITIVITY_STUDIES=('cover_lowering','pickup_keepout_growth',
                     'tube_diameter_growth','pan_inner_contraction')


def build(preview=False):
    candidate=verify_candidate()
    identity=sha(ROOT/'review/candidate.json')
    approval=json.loads((ROOT/'review/retro-fix-approval.json').read_text())
    report=json.loads((ROOT/'review/delivery-validation.json').read_text())
    fit_report=json.loads((ROOT/'concepts/p4/review/validation.json').read_text())
    fit_scenarios=fit_report.get('digital_fit_scenarios',{})
    if tuple(fit_scenarios)!=SCENARIOS:
        raise ValueError('Saved CAD report has an unexpected digital-fit scenario set')
    for name,scenario in fit_scenarios.items():
        if set(scenario.get('concepts',{}))!={'baseline','radial','nested'}:
            raise ValueError(f'Incomplete A/B/C fit results: {name}')
    sensitivity=fit_report.get('single_variable_proxy_sensitivity',{})
    sensitivity_parameters=sensitivity.get('parameters',{})
    if set(sensitivity_parameters)!=set(SENSITIVITY_STUDIES):
        raise ValueError('Saved CAD report lacks the complete single-variable proxy sensitivity study')
    for name,study in sensitivity_parameters.items():
        if set(study.get('concepts',{}))!={'baseline','radial','nested'}:
            raise ValueError(f'Incomplete A/B/C proxy sensitivity results: {name}')
    if not preview and (approval.get('status')!='accepted' or approval.get('candidate_sha256')!=identity or report.get('candidate_sha256')!=identity):
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

    for folder in ('STEP','DXF','src'):
        for path in (ROOT/'concepts/p4'/folder).iterdir():
            if path.suffix in ('.step','.json','.dxf','.py'):
                target=f'downloads/p4/{"source/" if folder=="src" else ""}{path.name}'
                copy(str(path.relative_to(ROOT)),target)
    copy('concepts/p4/BOM.csv','downloads/P4_BOM.csv')
    copy('concepts/p4/review/validation.json','assets/digital-fit-scenarios.json')
    p4_render=json.loads((ROOT/'concepts/p4/review/render-receipt.json').read_text())
    for job in p4_render['jobs'].values():
        for source in job['outputs']:copy(source,'assets/p4/'+Path(source).name)
    copy('research/oil-pan-evidence/gm-pan-alt1.jpg','assets/gm-pan-interior.jpg')
    copy('research/pan-family-illustrations/same-pan-interior.gif','assets/gm-pan-family-inspection.gif')
    copy('research/pan-family-illustrations/same-pan-assembly.gif','assets/gm-pan-family-assembly.gif')
    for source in (SITE/'vendor').iterdir():
        if source.is_file():shutil.copy2(source,dist/'assets'/source.name)

    def link_target(url,source):
        if urlsplit(url).scheme in ('https','http'):return url
        target=(ROOT/source).parent/unquote(url.split('#')[0])
        try:key=str(target.resolve().relative_to(ROOT))
        except ValueError:return None
        if key in public:return '../'+public[key]
        if key in DOCS:return Path(key).stem+'.html'
        return None
    def inline(raw,source):
        links=[]
        def link(match):
            label,url=match.groups();target=link_target(url,source)
            if not target:return label
            links.append(f'<a href="{escape(target,quote=True)}">{escape(label)}</a>')
            return f'__INLINE_LINK_{len(links)-1}__'
        value=escape(re.sub(r'\[([^\]]+)\]\(([^)]+)\)',link,raw))
        value=re.sub(r'`([^`]+)`',r'<code>\1</code>',value)
        value=re.sub(r'\*\*([^*]+)\*\*',r'<strong>\1</strong>',value)
        for index,html in enumerate(links):value=value.replace(f'__INLINE_LINK_{index}__',html)
        return value
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
    legacy_bom=list(csv.DictReader((ROOT/'delivery/BOM.csv').open()))
    p4_bom=list(csv.DictReader((ROOT/'concepts/p4/BOM.csv').open()))
    profile_sources=list((ROOT/'DXF').glob('*.dxf'))+list((ROOT/'concepts/p4/DXF').glob('*.dxf'))
    profile_hashes={}
    for path in profile_sources:
        digest=sha(path)
        if path.name in profile_hashes and profile_hashes[path.name]!=digest:
            raise ValueError(f'Duplicate DXF filename has different contents: {path.name}')
        profile_hashes[path.name]=digest
    all_profile_names=set(profile_hashes)
    active_profile_names={Path(row['cut_file']).name for row in legacy_bom
                          if row['variant']=='V3' and row['cut_file']} | {
        Path(row['cut_file']).name for row in p4_bom
        if row['variant'] in ('radial','nested') and row['cut_file']}
    if not active_profile_names.issubset(all_profile_names):
        raise ValueError('Current A/B/C BOM references a missing profile name')
    references=json.loads((ROOT/'research/examples-simple.json').read_text())+json.loads((ROOT/'research/examples-trapdoors.json').read_text())
    descriptions=[('Fixed dividers','Fewest parts. Two fences beneath the retained cover, with permanent return paths.','No hinges to qualify; directional retention still needs comparison.'),
      ('Purchased metal gates','A compact cage with three Improved Racing EMR-201 doors.','Real hardware must be measured. Gold parts here are simplified proxies.'),
      ('Custom metal gates','Three thin leaves, welded hinge cheeks, captive pins and 60° stops.','Most owner fabrication. Joining, alignment and retention need coupon evidence.')]
    concepts=[]
    for n,(model,(title,description,note)) in enumerate(zip(MODELS,descriptions),1):
        concepts.append(f'<article class="concept"><div class="concept-head"><p class="number">0{n} / CONCEPT</p><h3>{title}</h3></div><video controls playsinline preload="none" poster="assets/{model}.png" aria-label="{title} illustrative animation"><source src="assets/{model}.mp4" type="video/mp4"><a href="assets/{model}.mp4">Download animation</a></video><div class="concept-body"><p>{description}</p><strong class="part-count">{facts["cut_counts"][f"V{n}"]} custom cut pieces</strong><p>{note}</p><div class="concept-links"><a href="downloads/{model}.step" download>STEP ↓</a><a href="downloads/{model}.glb" download>Animated GLB ↓</a><a href="downloads/BOM.csv">BOM ↗</a></div></div></article>')
    legacy=''.join(concepts[:2])
    current=[('A','baseline','Simple gated well','solstice_baffle','assets/solstice_baffle',
              'downloads/solstice_baffle.step','downloads/solstice_baffle.glb',
              'Three custom leaves form the simplest current gated baseline around the pickup region.',
              f"{facts['concepts']['A']['loose_mount_blanks']} loose mounting blanks are undrilled; actual attachment is unresolved."),
             ('B','radial','Radial collector','radial_collector','assets/p4/radial_collector',
              'downloads/p4/radial_collector.step','assets/p4/radial_collector.glb',
              'Four diagonal gates in an octagonal well, with five joined, open-ended guide vanes.',
              'Guide vanes extend beyond the well; mounts and corner access are unresolved.'),
             ('C','nested','Nested reservoir','nested_collector','assets/p4/nested_collector',
              'downloads/p4/nested_collector.step','assets/p4/nested_collector.glb',
              'An outer reservoir feeds an inner well through six staggered gates.',
              'Staged buffering is a hypothesis; two gate stages may also restrict refill. Mounts are unresolved.')]
    concepts=[]
    pan_catalog={}
    for letter,key,title,model,asset,step,glb,description,note in current:
        dimensions=facts['concepts'][letter]
        well=' × '.join(f'{value:g}' for value in dimensions['well_mm'])
        envelope=' × '.join(f'{value:g}' for value in dimensions['envelope_mm'])
        metrics={
            'installed_net_cut_area_mm2':dimensions['installed_cut_profile_area_mm2'],
            'estimated_metal_mass_g':dimensions['estimated_stainless_mass_g'],
            'estimated_moving_gate_mass_g':dimensions['estimated_moving_gate_mass_g'],
            'gross_gate_window_area_mm2':dimensions['gross_gate_window_area_mm2'],
        }
        bom='downloads/BOM.csv' if letter=='A' else 'downloads/P4_BOM.csv'
        outer_note=(f" Outer footprint: {P4_NOMINALS['OUTER_WIDTH']:g} × {P4_NOMINALS['OUTER_LENGTH']:g} mm."
                    if letter=='C' else '')
        concepts.append(f'<article class="concept" data-concept="{key}" data-well-mm="{well}" data-envelope-mm="{envelope}" data-gates="{dimensions["gates"]}" data-cut-plates="{dimensions["cut_plates"]}" data-pins="{dimensions["pins"]}" data-installed-net-cut-area-mm2="{metrics["installed_net_cut_area_mm2"]:.3f}" data-estimated-metal-mass-g="{metrics["estimated_metal_mass_g"]:.3f}" data-estimated-moving-gate-mass-g="{metrics["estimated_moving_gate_mass_g"]:.3f}" data-gross-gate-window-area-mm2="{metrics["gross_gate_window_area_mm2"]:.3f}"><div class="concept-head"><p class="number">{letter} / CURRENT CONCEPT</p><h3>{title}</h3></div><video controls playsinline preload="none" poster="{asset}.png" aria-label="{title} illustrative animation"><source src="{asset}.mp4" type="video/mp4"><a href="{asset}.mp4">Download animation</a></video><div class="concept-body"><p>{description}</p><p class="dimension-summary"><strong>{"Inner well" if letter=="C" else "Well"}:</strong> {well} mm · <strong>Full CAD envelope:</strong> {envelope} mm.{outer_note}<br><strong>Installed net cut area:</strong> {metrics["installed_net_cut_area_mm2"]/100:.1f} cm² · <strong>Metal estimate:</strong> {metrics["estimated_metal_mass_g"]:.0f} g<br><strong>Moving gates:</strong> {metrics["estimated_moving_gate_mass_g"]:.0f} g · <strong>Gross window area:</strong> {metrics["gross_gate_window_area_mm2"]/100:.2f} cm²</p><strong class="part-count">{dimensions["cut_plates"]} cut plates + {dimensions["pins"]} pins</strong><p>{note}</p><div class="concept-links"><a href="{step}" download>STEP ↓</a><a href="{glb}" download>Animated GLB ↓</a><a href="{bom}">BOM ↗</a></div></div></article>')
        pan_catalog[key]={
            'letter':letter,'title':title,'well_mm':dimensions['well_mm'],
            'envelope_mm':dimensions['envelope_mm'],'gates':dimensions['gates'],
            'cut_plates':dimensions['cut_plates'],'pins':dimensions['pins'],
            'comparison':metrics,
            'overview':f'assets/p4/{key}_pan_cutaway.png',
            'views':{stage:{'model':f'assets/p4/{key}_pan_{stage}.glb',
                            'poster':f'assets/p4/{key}_pan_{stage}.png',
                            'step':f'downloads/p4/{key}_pan_{stage}.step'}
                     for stage in ('detail','exploded','section')},
        }
    measurements=''.join(f'<li><span class="tag">Priority {priorities[r["item"]]} · {escape(r["status"])}</span><strong>{escape(r["item"])}</strong><p>{escape(r["method"])}</p></li>' for r in sorted(rows,key=lambda r:int(priorities[r['item']])))
    refs=''.join(f'<article class="reference" data-level="{escape(r["complexity"])}"><p class="eyebrow">{escape(r["complexity"])} / {escape(r["engine"])}</p><h3>{escape(r["name"])}</h3><p>{escape(r["mechanism"])}</p><p><strong>Construction lesson:</strong> {escape(r["lesson"])}</p><a href="{escape(r["url"],quote=True)}" target="_blank" rel="noopener">Manufacturer source ↗</a></article>' for r in references)
    outcome_labels={'baseline':'A / Simple gated well','radial':'B / Radial collector','nested':'C / Nested reservoir'}
    def geometry_label(name):
        labels={
            'REFERENCE_tube_route_UNKNOWN':'tube-route proxy',
            'REFERENCE_pan_shell_ASSUMED_INTERIOR':'pan-shell proxy',
            'REFERENCE_pickup_design_test_case':'pickup test envelope',
            'REFERENCE_OEM_cover_shape_and_height_UNKNOWN':'assumed cover proxy',
            'REFERENCE_raised_pickup_relief_UNKNOWN':'raised cover-relief proxy'}
        if name in labels:return labels[name]
        return name.replace('_',' ')
    def sensitivity_value(name, value, study):
        nominal=study['nominal_value']
        if name=='cover_lowering':return f'{nominal-value:g} mm lower'
        if name in ('pickup_keepout_growth','tube_diameter_growth'):
            return f'+{value-nominal:g} mm'
        return f'Δscale {value:g}'
    def interior_scales(delta):
        sx,sy=P4_PAN_PROXY['PAN_INNER_SCALE_XY']
        return f'{sx-delta:.5f}/{sy-delta:.5f}'
    sensitivity_cards=[]
    for name in SENSITIVITY_STUDIES:
        study=sensitivity_parameters[name]
        outcomes=[]
        for key in ('baseline','radial','nested'):
            result=study['concepts'][key]
            letter={'baseline':'A','radial':'B','nested':'C'}[key]
            if result['status']=='intersection_bracketed':
                clear=sensitivity_value(name,result['last_clear_value'],study)
                hit=sensitivity_value(name,result['first_hit_value'],study)
                collision=result['first_collision']
                if 'gate' in collision:
                    part=f"{geometry_label(collision['gate'])} at {collision['angle_deg']:g}°"
                else:
                    part=geometry_label(collision['insert_part'])
                detail=(f"Clear through {clear}; first sampled hit between {clear} and {hit}. "
                        f"Intersecting pair: {part} ↔ {geometry_label(collision['proxy'])}.")
                if name=='pan_inner_contraction':
                    detail+=f' Inner X/Y scales at hit: {interior_scales(result["first_hit_value"])}.'
                status='First sampled hit bracket'
                state='intersection'
                last_clear=result['last_clear_value']
                first_hit=result['first_hit_value']
            elif result['status']=='no_intersection_within_scan':
                limit=sensitivity_value(name,result['scan_limit'],study)
                detail=f'No sampled hit through {limit}.'
                if name=='pan_inner_contraction':
                    detail+=f' End-scan inner X/Y scales: {interior_scales(result["scan_limit"])}.'
                status='No hit in scan'
                state='clear'
                last_clear=result['last_clear_value']
                first_hit=''
            else:
                raise ValueError(f'Unexpected proxy sensitivity status: {name}/{key}')
            outcomes.append(
                f'<div class="fit-sensitivity-outcome" data-sensitivity-concept="{letter}" '
                f'data-status="{result["status"]}" data-last-clear-value="{last_clear}" '
                f'data-first-hit-value="{first_hit}" data-scan-limit="{result.get("scan_limit", "")}">'
                f'<strong>{letter} · {outcome_labels[key]}</strong>'
                f'<span class="fit-state {state}">{status}</span><p>{escape(detail)}</p></div>')
        scale_range=(f' · initial X/Y scales {interior_scales(0)}, '
                     f'end {interior_scales(study["scan_end_value"])}'
                     if name=='pan_inner_contraction' else '')
        sensitivity_cards.append(
            f'<article class="fit-sensitivity" data-sensitivity="{name}" '
            f'data-nominal-value="{study["nominal_value"]}" data-scan-end-value="{study["scan_end_value"]}" '
            f'data-coarse-step="{study["coarse_step"]}" data-resolution="{study["resolution"]}" '
            f'data-unit="{escape(study["unit"],quote=True)}">'
            f'<h4>{escape(study["label"])}</h4>'
            f'<p class="fit-sensitivity-range">Nominal {study["nominal_value"]:g} {escape(study["unit"])} '
            f'→ tested {study["scan_end_value"]:g} {escape(study["unit"])} · '
            f'coarse {study["coarse_step"]:g}, refined to {study["resolution"]:g}'
            f'{scale_range}</p>'
            f'<div class="fit-sensitivity-outcomes">{"".join(outcomes)}</div></article>')
    fit_cards=[]
    for scenario_id,scenario in fit_scenarios.items():
        outcomes=[]
        for key in ('baseline','radial','nested'):
            result=scenario['concepts'][key]
            letter={'baseline':'A','radial':'B','nested':'C'}[key]
            if not result['collisions']:
                detail='No exact Boolean intersection at the checked poses.'
                status='Clear in modeled context'
                state='clear'
            else:
                groups=[]
                for collision in result['collisions']:
                    poses=collision['sampled_poses']
                    degrees=sorted({pose[key_name] for pose in poses
                                    for key_name in pose if pose[key_name] is not None})
                    suffix=(f" at {', '.join(f'{angle:g}°' for angle in degrees)}"
                            if degrees else '')
                    groups.append(f"{collision['first']} ↔ {collision['second']}{suffix}")
                detail=f"{sum(item['pose_count'] for item in result['collisions'])} sampled intersections: {'; '.join(groups)}"
                status='Intersection found'
                state='intersection'
            extra=(f'<details class="fit-collision-detail"><summary>See intersecting parts and poses</summary><p>{escape(detail)}</p></details>'
                   if result['collisions'] else f'<p>{escape(detail)}</p>')
            outcomes.append(f'<div class="fit-outcome" data-fit-concept="{letter}"><strong>{outcome_labels[key]}</strong><span class="fit-state {state}">{status}</span>{extra}</div>')
        fit_cards.append(f'<article class="fit-scenario" data-scenario="{escape(scenario_id)}"><h3>{escape(scenario["label"])}</h3><p>{escape(scenario["description"])}</p><div class="fit-outcomes">{"".join(outcomes)}</div></article>')
    path_cards=[]
    for key in ('baseline','radial','nested'):
        letter={'baseline':'A','radial':'B','nested':'C'}[key]
        title={'baseline':'Simple gated well','radial':'Radial collector','nested':'Nested reservoir'}[key]
        paths=fit_scenarios['nominal_visual_proxy']['concepts'][key]['installation_paths']
        route_rows=[]
        for route,label in (('pickup_tube_retained','Pickup/tube proxy retained'),
                            ('pickup_tube_removed_as_assembly','Pickup/tube proxy omitted')):
            result=paths[route]
            hit=result.get('first_collision')
            if hit:
                state='intersection'
                status=f'Blocked at {hit["lift_mm"]:g} mm lift'
                detail=f'{geometry_label(hit["insert_part"])} ↔ {geometry_label(hit["obstacle"])}'
            else:
                state='clear'
                status='Clear in sampled path'
                detail=f'{result["sampled_poses"]} poses at {result["sample_step_mm"]:g} mm steps'
            route_rows.append(f'<div class="fit-route-row" data-fit-route="{route}" data-route-state="{result["status"]}"><span>{label}</span><strong class="fit-state {state}">{escape(status)}</strong><small>{escape(detail)}</small></div>')
        path_cards.append(f'<article class="fit-path-card" data-path-concept="{letter}"><h3>{letter} · {title}</h3>{"".join(route_rows)}</article>')
    removed_results=[scenario['concepts'][key]['installation_paths']['pickup_tube_removed_as_assembly']
                     for scenario in fit_scenarios.values() for key in ('baseline','radial','nested')]
    retained_results=[scenario['concepts'][key]['installation_paths']['pickup_tube_retained']
                      for scenario in fit_scenarios.values() for key in ('baseline','radial','nested')]
    path_note=(f'Across five contexts, the retained pickup/tube route is blocked in '
               f'{sum(result["status"]!="clear_in_sampled_vertical_path" for result in retained_results)} of 15 concept-context checks. '
               f'With that proxy assembly omitted, {sum(result["status"]=="clear_in_sampled_vertical_path" for result in removed_results)} of 15 checks clear; '
               'nested C is blocked only by the narrowed-shell proxy.')
    alternative_study=fit_report.get('digital_alternative_exit_path_study',{})
    alternative_paths=alternative_study.get('paths',{})
    alternative_concepts=alternative_study.get('concepts',{})
    if len(alternative_paths)!=8 or set(alternative_concepts)!={'baseline','radial','nested'}:
        raise ValueError('Saved CAD report lacks the complete 8-path A/B/C exit study')
    alternative_cards=[]
    alternative_blocked=0
    for path_name,path in alternative_paths.items():
        outcomes=[]
        for key in ('baseline','radial','nested'):
            result=alternative_concepts[key].get(path_name)
            if not result:
                raise ValueError(f'Missing alternative exit result: {key}/{path_name}')
            letter={'baseline':'A','radial':'B','nested':'C'}[key]
            hit=result.get('first_collision')
            if hit:
                alternative_blocked+=1
                state='intersection'
                status='Proxy hit'
                if hit['stage']=='shift':
                    x,y=hit['offset_xy_mm']
                    position=f"shift {x:+g} / {y:+g} mm XY"
                elif hit['stage']=='tilt':
                    position=f"tilt {hit['angle_deg']:+g}°"
                else:
                    x,y=hit.get('offset_xy_mm',(0,0))
                    position=(f"shift {x:+g} / {y:+g} mm XY" if 'offset_xy_mm' in hit
                              else f"tilt {hit.get('angle_deg',0):+g}°")
                    position+=f", then lift {hit['lift_mm']:g} mm"
                detail=(f"{position}: {geometry_label(hit['insert_part'])} ↔ "
                        f"{geometry_label(hit['obstacle'])}")
            else:
                state='clear'
                status='Clear in sampled path'
                detail=f"{result['sampled_poses']} poses; terminal lift {result['exit_lift_mm']:g} mm"
            outcomes.append(
                f'<div class="fit-alt-outcome" data-alt-concept="{letter}" '
                f'data-alt-state="{state}"><span>{letter}</span>'
                f'<strong class="fit-state {state}">{status}</strong>'
                f'<small>{escape(detail)}</small></div>')
        alternative_cards.append(
            f'<article class="fit-alt-path-card" data-alt-path="{escape(path_name)}">'
            f'<h4>{escape(path.get("label",path_name))}</h4>'
            f'<div class="fit-alt-outcomes">{"".join(outcomes)}</div></article>')
    alternative_summary=(f'{alternative_blocked} of {len(alternative_paths)*3} selected concept-path checks '
                         'intersect the nominal pickup/tube or pan-shell proxy at a sampled pose. '
                         'A clear result applies only to these discrete paths.')
    access=fit_report['pin_tool_access']
    access_labels={'isolated_hinge_before_wall_attachment':'Hinge only, before wall',
                   'isolated_wall_gate_module':'Wall / gate module',
                   'completed_insert_on_bench':'Complete cage on bench',
                   'installed_proxy_cover_removed':'Nominal pan, cover removed'}
    access_titles={'baseline':'A · Simple gated well','radial':'B · Radial collector',
                   'nested':'C · Nested reservoir'}
    access_gates={'baseline':'rear pin','radial':'front-right pin','nested':'inner rear pin'}
    access_cards=[]
    access_checks=sum(len(row['contexts']) for result in access['concepts'].values()
                      for row in result['results'])
    for key,letter in (('baseline','A'),('radial','B'),('nested','C')):
        summary=access['concepts'][key]['summary']
        access_rows=[]
        for context,label in access_labels.items():
            cells=[]
            for diameter in access['probe_diameters_mm']:
                cell=summary[context][str(diameter)]
                cells.append(f'<td data-access-context="{context}" data-access-diameter="{diameter:g}">'
                             f'{cell["clear_pin_ends"]}/{cell["total_pin_ends"]}</td>')
            access_rows.append(f'<tr><th scope="row">{label}</th>{"".join(cells)}</tr>')
        headings=''.join(f'<th scope="col">Ø{diameter:g}<br>mm</th>'
                         for diameter in access['probe_diameters_mm'])
        access_cards.append(f'<article class="fit-path-card" data-access-concept="{letter}">'
            f'<h3>{access_titles[key]}</h3><img src="assets/p4/{key}_pin_access_top.png" '
            f'width="1000" height="1000" loading="lazy" '
            f'alt="Top view of {access_titles[key]} with two assumed 12.7 mm coaxial approach cylinders at its {access_gates[key]}">'
            f'<p class="small">Amber: representative Ø12.7 mm nose sweeps at the {access_gates[key]}. '
            'The table covers every gate end.</p><table class="access-table">'
            f'<caption>Clear pin ends / tested ends</caption><thead><tr><th scope="col">Stage</th>{headings}'
            f'</tr></thead><tbody>{"".join(access_rows)}</tbody></table>'
            f'<a class="text-link" href="downloads/p4/{key}_pin_access.step" download>Download access scene (STEP) ↓</a></article>')
    clear_all=[outcome_labels[key] for key in ('baseline','radial','nested')
               if all(scenario['concepts'][key]['status']=='clear_in_declared_proxy'
                      for scenario in fit_scenarios.values())]
    sensitive=[outcome_labels[key] for key in ('baseline','radial','nested')
               if any(scenario['concepts'][key]['collisions'] for name,scenario in fit_scenarios.items()
                      if name!='nominal_visual_proxy')]
    clear_text=', '.join(clear_all) if clear_all else 'None'
    sensitive_text=', '.join(sensitive) if sensitive else 'None'
    fit_summary=(f'Clear in all {len(fit_scenarios)} modeled contexts: {clear_text}. '
                 f'Stress-case intersections: {sensitive_text}. '
                 'These cases are not measured bounds or predictions of the actual pan.')
    resources=[('CONCEPTS','Creative gated designs','New radial and nested architectures, cut quantities and tradeoffs.'),('PAN_CONTEXT','Pan assumptions','Which dimensions are sourced and which are design test cases.'),('NEXT_DECISIONS','Digital fitment plan','Current scenario work and the next digital checks.'),('INTERFACE_ASSESSMENT','Evidence & uncertainty','Exact-pan sources, supported identities and hidden fit gaps.'),('same-pan-family-visuals','GM and Vue pan references','Exact-part GM photos and qualified Vue service illustrations.'),('TOLERANCE_SENSITIVITY','Tolerance sensitivity','Reproducible conditional budgets for the hinge and mounting stack.'),('README','Fabrication & fit notes','Stock, quantities, assembly intent and unresolved release holds.'),('SENDCUTSEND_PREFLIGHT','SendCutSend preparation','Cut-file review and supplier/process boundaries.'),('QUALITY','Design & production standards','The project criteria for each development stage.'),('honda-precedents','Honda precedents','OEM, aftermarket, catalog and patent architecture notes.')]
    cards=''.join(f'<a class="resource" href="notes/{name}.html"><h3>{title} ↗</h3><p>{description}</p></a>' for name,title,description in resources)
    dxfs=''.join(f'<a href="downloads/{p.name}" download>{p.stem.replace("_"," ")} ↓</a>' for p in sorted((ROOT/'DXF').glob('*.dxf')))
    now=datetime.now(timezone.utc)
    template=(SITE/'index.template.html').read_text()
    concepts_note=('<p class="small">Comparison values come from saved CAD solids and net DXF profiles; installed cut area excludes A’s five loose mounting blanks. Mass assumes 7.9 kg/dm³ stainless and excludes weld filler; pin grade is unresolved. Window area is gross wall cutout area, not effective open area, flow capacity, or oil-control evidence.</p>')
    heading=fit_report['heading_accessory_study']
    heading_outcomes=[outcome for result in heading['concepts'].values()
                      for row in result['results'] for outcome in row['contexts'].values()]
    heading_states=('clear_in_declared_rigid_clock_bound','blocked_by_fixture_geometry',
                    'blocked_at_sampled_rigid_clock','unresolved_between_samples_or_bound_excess')
    heading_counts=[sum(o['status']==state for o in heading_outcomes) for state in heading_states]
    heading_bounds=sum(o['rigid_clock_bound']['status']!='not_evaluated_fixture_obstructed'
                       for o in heading_outcomes)
    heading_samples=sum(len(o['sampled_clock_angles_deg']) for o in heading_outcomes)
    heading_cards=[]
    for name,title,detail in (
        ('heading_hinge_setup','Before wall attachment','A rear hinge: sourced accessory and proposed saddle around isolated hardware.'),
        ('heading_wall_setup','Wall-attached module','The same A rear hinge: its attached wall intersects this saddle.'),
        ('heading_cage_setup','Completed cage example','C inner rear hinge: later cage structure also obstructs this setup.')):
        heading_cards.append(f'<article class="fit-path-card" data-heading-scene="{name}">'
            f'<h4>{title}</h4><img src="assets/p4/{name}.png" width="1200" height="900" loading="lazy" '
            f'alt="{escape(detail)} Gray marks the source body, gold the terminal blank and gate leaf, and purple the assumed saddle.">'
            f'<p class="small">{detail}</p><a class="text-link" href="downloads/p4/{name}.step" download>'
            'Download static setup (STEP) ↓</a></article>')
    heading_block=(f'<div id="heading-study" data-heading-cases="{len(heading_outcomes)}" '
        f'data-heading-clock-bounds="{heading_bounds}" data-heading-native-samples="{heading_samples}" '
        f'data-heading-state-counts="{",".join(map(str,heading_counts))}">'
        '<h3>Source geometry and a support saddle.</h3>'
        f'<p>{len(heading_outcomes)} combined stage assessments cover both ends of every A/B/C pin. '
        f'{heading_counts[0]} clear the declared rigid-clock bound; {heading_counts[1]} are blocked by this fixture, '
        f'{heading_counts[2]} by a sampled native pose, and {heading_counts[3]} remain unresolved. '
        'Accessory checks stop after a confirmed fixture obstruction.</p>'
        f'<p class="small">Static manufacturer geometry at a {heading["parameters"]["TIP_STANDOFF_MM"]:g} mm terminal-plane standoff. '
        'Purple pieces are proposed support geometry; clamping and loads are unresolved. Whole-accessory clocking is a '
        'declared clearance assumption, not the internal machine mechanism, forming contact or an axial approach.</p>'
        '<details id="heading-scenes" class="study-group"><summary>View the three fixture stages · static CAD scenes</summary>'
        f'<div class="fit-path-grid access-grid heading-grid">{"".join(heading_cards)}</div></details>'
        '<p class="small">Reference assemblies, not extra oil-pan kit parts or order items. '
        '<a href="notes/heading-accessory-assessment.html">Read stage/contact results ↗</a> · '
        '<a href="notes/heading-accessory.html">Source dimensions and assumptions ↗</a> · '
        '<a href="https://www.orbitform.com/standard-products/orbital-heads/long-reach">Manufacturer PDF/STEP source ↗</a></p></div>')
    template=template.replace('<div class="concept-grid">@@CONCEPTS@@</div>',
                              '<div class="concept-grid">@@CONCEPTS@@</div>'+concepts_note)
    catalog={'schema_version':1,'candidate_sha256':identity,'default_selection':{'concept':'nested','view':'detail'},
             'concepts':pan_catalog}
    (dist/'catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
    values={'REVISION':revision,'DATE':now.isoformat(),'DATE_LABEL':now.strftime('%d %b %Y, %H:%M UTC'),
      'PROFILES':str(len(all_profile_names)), 'CURRENT_PROFILES':str(len(active_profile_names)),
      'LEGACY_PROFILES':str(len(all_profile_names-active_profile_names)),
      'PROFILE_PATHS':str(len(profile_sources)),
      'UNKNOWN':str(sum(r['status']=='UNKNOWN' for r in rows)),
      'CONCEPTS':''.join(concepts),'LEGACY':legacy,'MEASUREMENTS':measurements,'REFERENCES':refs,'RESOURCES':cards,'DXFS':dxfs,
      'PICKUP_DIAMETER':f"{P4_PAN_PROXY['PICKUP_KEEP_OUT_DIAMETER']:g}",
      'PROXY_FLOOR_GAP':f"{facts['proxy_floor_gap_mm']:g}",
      'CHEEK':f'{tolerance["cheek_gap"]["thickness_only_range_mm"][0]:.4f}',
      'ROOF':f'{tolerance["continuous_roof"]["gap_mm"]:.3f}',
      'STACK':f'{tolerance["mounting_stack"]["conditional_added_SST048_sheet_cases"][0]["nominal_insertion_loss_mm"]:.4f}',
      'EDITION_STATUS':'LOCAL PREVIEW / REVIEW PENDING' if preview else 'DIGITAL REVIEW COMPLETE',
      'FIT_SCENARIOS':''.join(fit_cards),'FIT_SUMMARY':escape(fit_summary),
      'FIT_SENSITIVITY':''.join(sensitivity_cards),
      'FIT_PATHS':''.join(path_cards),'FIT_PATH_NOTE':escape(path_note),
      'ALT_EXIT_PATHS':''.join(alternative_cards),
      'ALT_EXIT_NOTE':escape(alternative_summary),
      'TOOL_ACCESS_CARDS':''.join(access_cards),'TOOL_ACCESS_CHECKS':str(access_checks),
      'HEADING_STUDY':heading_block,
      'SCENARIO_COUNT':str(len(fit_scenarios))}
    for key,value in values.items():template=template.replace('@@'+key+'@@',value)
    p4_dxfs=''.join(f'<a href="downloads/p4/{path.name}" download>P4 / {path.stem.replace("_"," ")} ↓</a>' for path in sorted((ROOT/'concepts/p4/DXF').glob('*.dxf')))
    template=template.replace('@@P4_DXFS@@',p4_dxfs)
    (dist/'index.html').write_text(template)
    # Public download is curated; private review logs and third-party source archives stay local.
    with zipfile.ZipFile(dist/'downloads/Solstice_prototype_files.zip','w',zipfile.ZIP_DEFLATED) as z:
        for source,target in sorted(public.items()):
            if target.startswith('downloads/'):z.write(dist/target,source)
        for source in DOCS:
            if source.startswith(('delivery/','concepts/')) or source=='QUALITY.md':z.write(ROOT/source,source)
        z.writestr('READ_ME_FIRST.txt',f'Solstice GXP nominal prototype exports, {revision}. Fit and engine-use release held.\nUse delivery/BOM.csv for variant quantities and DXF paths; do not order all profiles.\nSource CAD is under src/ and uses pinned cadgen==0.7.21. Native animation sidecars accompany STEP files.\nThis curated public export is not the complete local validation/evidence workspace.\nRead the fabrication, uncertainty and measurement notes before bench work.\n')
    (dist/'.nojekyll').touch()
    edition=hashlib.sha256(''.join(sha(p) for p in sorted(dist.rglob('*')) if p.is_file() and p.name!='version.json').encode()).hexdigest()[:16]
    def version_link(match):
        attr,url=match.groups();parts=urlsplit(url)
        if parts.scheme or not parts.path:return match.group(0)
        separator='&amp;' if parts.query else ''
        return f'{attr}="'+urlunsplit(parts._replace(query=parts.query+separator+'v='+edition))+'"'
    for page in dist.rglob('*.html'):
        html=page.read_text().replace('@@EDITION@@',edition)
        page.write_text(re.sub(r'(href|src|poster)="([^"]+)"',version_link,html))
    (dist/'version.json').write_text(json.dumps({'edition':edition,'updated_at':now.isoformat(),
                                                  'candidate_sha256':identity,'preview':preview})+'\n')
    validate(dist,allow_preview=preview)
    previous=SITE/'.previous-dist'
    if previous.exists():shutil.rmtree(previous)
    if (SITE/'dist').exists():(SITE/'dist').rename(previous)
    dist.rename(SITE/'dist');dist=SITE/'dist'
    print(json.dumps({'site_files':len([p for p in dist.rglob('*') if p.is_file()]),'edition':edition,'source_candidate':identity}))


def validate(dist,allow_preview=False):
    validate_dist(dist,allow_preview=allow_preview)


if __name__=='__main__':build(preview='--preview' in sys.argv)
