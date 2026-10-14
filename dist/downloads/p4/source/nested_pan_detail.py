from cadgen import step
from pan_reference import scene,scene_animation,scene_kinematics

@step(out='../STEP/nested_pan_detail.step',animation=scene_animation('nested'),kinematics=scene_kinematics('nested'))
def nested_pan_detail():
    return scene('nested','detail')

if __name__=='__main__':nested_pan_detail()
