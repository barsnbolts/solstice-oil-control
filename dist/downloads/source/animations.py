"""Presentation motion only; no oil forces or physical closing times are solved."""
import json
from math import cos, sin, radians
from parts import GATES, PIVOT_IN, PIVOT_Z, STOP_ANGLE
from design_parameters import PROXY_HINGE_R, PROXY_HINGE_Z

FIXED = r"""
export const clips = {demo: {
  label: "Exploded assembly — fixed dividers", duration: 6, loop: true,
  update(t,m) {
    const s=(1-Math.cos(2*Math.PI*t/6))/2;
    m.get("top_frame").translate([0,0,35*s]);
    m.get("right_fixed_divider").translate([25*s,0,0]);
    m.get("left_fixed_divider").translate([-25*s,0,0]);
  }
}};
"""

def gates_animation(proxy=False):
    targets=[]
    for name,theta,xyz in GATES:
        a=radians(theta)
        inward,z=(PROXY_HINGE_R,PROXY_HINGE_Z) if proxy else (PIVOT_IN,PIVOT_Z)
        labels=[f'PROXY_{name}_EMR201_leaf'] if proxy else [
            f'{name}_leaf',f'{name}_moving_cheek_0',f'{name}_moving_cheek_1']
        targets.append({'labels':labels,'axis':[cos(a),sin(a),0],
                        'pivot':[xyz[0]-sin(a)*inward,xyz[1]+cos(a)*inward,z]})
    title='Illustrative purchased-door proxies' if proxy else f'Custom gates — nominal 0 to {STOP_ANGLE:g} degrees'
    return ('const gates='+json.dumps(targets)+';\nexport const clips={demo:{label:'+
            json.dumps(title)+',duration:6,loop:true,update(t,m){\n'+
            f'const angle={STOP_ANGLE/2:g}*(1-Math.cos(2*Math.PI*t/6));\n'+
            'for(const g of gates) for(const label of g.labels) '+
            'm.get(label).rotate(g.axis,angle,g.pivot);\n}}};')
