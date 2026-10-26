import math
PCA_HOLES=((3.175,3.175),(3.175,22.225),(59.055,3.175),(59.055,22.225))
FEATHER_HOLES=((2.54,2.54),(2.54,20.32),(48.26,2.54),(48.26,20.32))
def battery_box():return (43,23,13)
def stack_points():return [(32*math.cos(math.radians(a)),32*math.sin(math.radians(a))) for a in range(30,360,60)]
def guard_points():return [(42*math.cos(math.radians(a)),42*math.sin(math.radians(a))) for a in range(30,360,60)]
def pca_transform(side,x,y):return (-side*(x-31.115),side*(28.7-y))
def pca_holes(side):return [pca_transform(side,x,y) for x,y in PCA_HOLES]
def feather_holes():return [(x-25.4,y-11.43) for x,y in FEATHER_HOLES]
def ellipse(rx,ry,n=48):return [(rx*math.cos(2*math.pi*i/n),ry*math.sin(2*math.pi*i/n)) for i in range(n)]
