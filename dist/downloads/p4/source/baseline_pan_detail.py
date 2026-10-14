from cadgen import step
from pan_reference import scene,scene_animation,scene_kinematics

@step(out='../STEP/baseline_pan_detail.step',animation=scene_animation('baseline'),kinematics=scene_kinematics('baseline'))
def baseline_pan_detail():
    return scene('baseline','detail')

if __name__=='__main__':baseline_pan_detail()
