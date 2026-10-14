from cadgen import dxf,flatten
from nested_rim_bridge import nested_rim_bridge

@dxf(out='../DXF/nested_rim_bridge_cut.dxf')
def nested_rim_bridge_cut():
    return flatten.flat_pattern(nested_rim_bridge(),coordinate=1.2192,kerf=0)

if __name__=='__main__':nested_rim_bridge_cut()
