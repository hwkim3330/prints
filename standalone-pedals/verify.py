"""Check the unladen mechanism geometry through its nominal 12-degree stroke."""
from math import hypot, cos, sin, radians
import model as m

def pose(part,angle):
    return part.rotate((0,0,m.PIVOT),(1,0,m.PIVOT),-angle)

def check():
    fixed=[m.base(),m.sensor_post().translate((37,45,7))]
    fixed += [m.hinge().translate((x,0,7)) for x in (-42,42)]
    for width in (84,96):
        pedal=m.pedal(width)
        for i in range(25):
            at=pose(pedal,m.TRAVEL*i/24)
            for component in fixed:
                assert at.intersect(component).val().Volume()<.01,(width,i)
    def reach(deg):
        a=radians(deg)
        y=65*cos(a)+3*sin(a)
        z=m.PIVOT-65*sin(a)+3*cos(a)
        return hypot(y-65,z-7)
    lengths=[reach(m.TRAVEL*i/100) for i in range(101)]
    assert all(a>b for a,b in zip(lengths,lengths[1:]))
    print(f"25 CAD poses per pedal; cable shortening {lengths[0]-lengths[-1]:.2f} mm")

if __name__=="__main__":check()
