#!/usr/bin/python
'''
This is inspired by both the Ultrasonic Basic Obstacle Avoider 
and Ultrasonic_Servo examples. 

Essentially, the gopigo should: 
  - Move fwd until it is within 20cm of an obstacle
  - Stop
  - Scan the room
  - Find a space between obstacles big enough to fit
  - Turn in that direction
  - Move fwd until it is within 20cm of an obstacle
  - Etc.
'''

from gopigo import *
from control import *
import math

STOP_DIST=20 # Dist, in cm, before an obstacle to stop.
SAMPLES=2 # Number of sample readings to take for each reading.
INF=250 # Distance, in cm, to be considered infinity.
REPEAT=3

def main():
    for x in range(REPEAT):
        move(STOP_DIST)
        readings = scan_room()
        holes = findholes(readings)
        gaps = verify_holes(holes)
        if len(gaps) == 0:
            exit()
        ## Choose the first gap found
        turn_to(gaps[0][0])

def move(min_dist):
    fwd()
    while True:
        dist=us_dist(15)
        if dist<min_dist:
            stop()
            break
        time.sleep(.1)
    return

def turn_to(angle):
    '''
    Turn the GoPiGo to a specified angle where angle=0 is 90deg 
    the way to the left and angle=180 is 90deg to the right.
    The GoPiGo is currently pointing forward at angle==90.
    '''
    ## <0 is turn left, >0 is turn right.
    degs = angle-90
    if degs < 0:
        left_deg(degs)
    else:
        right_deg(degs)

def verify_holes(holes):
    '''
    A hole is a list of (angle,distance) tuples.
    To verify that a hole can fit the chassis,
    we need to calculate the distance between the 
    first and last tuple.
    Returns a list of (angle,gap distance) tuples.
    '''
    gaps = []
    for hole in holes:
        xy1 = calc_xy(hole[0])
        xy2 = calc_xy(hole[-1])
        gap = calc_gap(xy1,xy2)
        ang1 = hole[0][0]
        ang2 = hole[-1][0]
        middle_ang = (ang2 + ang1)/2
        if gap >= CHASS_WID:
            gaps.append((middle_ang,gap))
    return gaps

def findholes(readings):
    '''
    Each reading will be a (angle,dist) tuple giving
    the distance to an obstacle at the given angle.
    To find a hole, we want 3 consecutive INF readings.
    '''
    holes = []
    buf = []
    ## Previous non-INF reading
    prev = ()
    for (a,d) in readings:
        if d != INF:
            ## If dist is not INF, then we've hit another
            ## obstacle, so reset the buffer.
            if len(buf) > 2:
                ## If the buffer has at least 3 INF readings,
                ## then record the hole.
                holes.append(buf)
            buf = []
            continue
        ## Add reading to buffer
        buf.append((a,d))
    return holes

def scan_room():
    '''
    Start at 0 and move to 180 in increments.
    Angle required to fit chass @20cm away is:
        degrees(atan(CHASS_WID/20))
    Increments angles should be 1/2 of that.
    Looking for 3 consecutive readings of inf.
    3 misses won't guarantee a big enough hole
     because not every obstacle will be 20cm away,
     but it is a good place to start, and more
     importantly, gives us edges to use to 
     measure.
    
    Return list of (angle,dist).
    '''
    ret = []
    inc = math.degrees(math.atan(CHASS_WID/20))
    for ang in range(0,180,inc):
        servo(ang)
        buf=[]
        for i in range(SAMPLES):
            dist=us_dist(15)
            if dist<INF and dist>=0:
                buf.appen(dist)
            else:
                buf.append(INF)
        ave = math.fsum(buf)/len(buf)
        ret.append((ang,ave))
    return ret

def calc_xy(meas):
    '''
    Given an angle and distance, return (x,y) tuple.
    x = dist*cos(radians(angle))
    y = dist*sin(radians(angle))
    '''
    a = meas[0]
    d = meas[1]
    x = d*math.cos(math.radians(a))
    y = d*math.sin(math.radians(a))
    return (x,y)

def calc_gap(xy1,xy2):
    '''
    Given two points represented by (x,y) tuples, 
    calculate the distance between the two points.
    dist is the hyp of the triangle.
    
    dist = sqrt((x1-x2)^2 + (y1-y2)^2)
    '''
    dist = math.hypot(xy1[0]-xy2[0],xy1[1]-xy2[1])
    return dist

