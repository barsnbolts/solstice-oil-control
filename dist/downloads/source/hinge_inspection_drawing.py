"""Nominal prototype inspection sheets, derived from STEP; not released drawings."""
from pathlib import Path
from cadgen import read_step
from cadgen.eng_drawing import Sheet,eng_drawing
from parts import PARTS,BORE_D,PIVOT_IN,PIVOT_Z
ROOT=Path(__file__).resolve().parents[1]

@eng_drawing(out='../PDF/hinge_inspection_drawing.pdf')
def hinge_inspection_drawing():
    sheets=[]
    for name in ['side_wall','door_leaf','fixed_cheek','moving_cheek']:
        shape=read_step(ROOT/'STEP'/f'{name}.step')
        t=PARTS[name][0]
        sheet=Sheet('A3',scale=2 if 'cheek' in name else 1,
            title=name.replace('_',' ').upper()+' - NOMINAL INSPECTION',
            part_number=name,revision='P1',material=f'304 stainless / nominal {t} mm',
            notes=['PROTOTYPE - NOT A PRODUCTION RELEASE.',
                   'Dimensions nominal; tolerances not qualified.',
                   'Use matching DXF for the complete cut profile.',
                   'Deburr and inspect after welding; see coupon plan.'])
        top,front,right,iso=sheet.three_views(shape,iso=True,gap=32)
        top.overall()
        if 'cheek' in name:
            top.hole((PIVOT_IN,PIVOT_Z,t),BORE_D,thru=True,angle=45)
        sheets.append(sheet)
    assembly=read_step(ROOT/'STEP/v3_hinge_coupon.step')
    sheet=Sheet('A3',scale=1,title='V3 GATE COUPON - NOMINAL ASSEMBLY',
        part_number='V3-COUPON',revision='P1',material='Mixed; see COUPON_BOM.csv',
        notes=['BENCH PROCESS ARTICLE - NOT AN ENGINE PART.',
               'Six cut pieces plus one owner-finished pin.',
               'Clamp fixed wall; keep the moving leaf free.',
               'Fixture, weld process and final fits need qualification.'])
    top,front,right,iso=sheet.three_views(assembly,iso=True,gap=32)
    front.overall()
    return [*sheets,sheet]

if __name__=='__main__':hinge_inspection_drawing()
