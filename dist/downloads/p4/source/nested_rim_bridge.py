from cadgen import step
from advanced_geometry import cut_profiles

@step(out='../STEP/nested_rim_bridge.step')
def nested_rim_bridge():
    return cut_profiles('nested')['nested_rim_bridge'][0]

if __name__=='__main__':nested_rim_bridge()
