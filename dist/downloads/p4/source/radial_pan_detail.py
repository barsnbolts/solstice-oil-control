from cadgen import step
from pan_reference import scene,scene_animation,scene_kinematics

@step(out='../STEP/radial_pan_detail.step',animation=scene_animation('radial'),kinematics=scene_kinematics('radial'))
def radial_pan_detail():
    return scene('radial','detail')

if __name__=='__main__':radial_pan_detail()
