"""Three printed concept modules with six concealed service fastener paths.

No motor ear/spline or real PCB mounting interface is claimed. Roof supports,
insert sizing, wires, thermal performance and physical fit remain to validate.
"""
import math
from v3_core_layout import (lid_fasteners, cassette_fasteners, core_dimensions,
                         electronics_reserves, rounded_hex)


def _part(b, key):
    occurrence = b.component('CORE | '+key)
    return occurrence, occurrence.component


def _finish(b, occurrence, key, bed):
    b.register(occurrence, key, 1, bed=bed)
    b.color(occurrence.component, (46, 49, 54))
    occurrence.component.attributes.add('Hexapod', 'DesignStatus',
        'FORM / ARCHITECTURE CONCEPT; no selected actuator or PCB mount fit')


def _fastener(b, label, point, start, end, length):
    if hasattr(b, 'FASTENERS'):
        b.FASTENERS.append(dict(label=label+' '+str(tuple(round(v,3) for v in point)), diameter_mm=3,
            x_mm=point[0], y_mm=point[1], shaft_start_z_mm=start,
            shaft_end_z_mm=end, nominal_length_mm=length,
            status='provisional insert geometry; hardware not selected',
            quantity=1, visible_from_top=False))


def build_parts(b):
    dims = core_dimensions()
    _build_tub(b, dims)
    _build_lid(b, dims)
    _build_cassette(b, dims)


def _build_tub(b, dims):
    occurrence, component = _part(b, 'CoreTub')
    b.add(component, 'z', -32, [b.poly(rounded_hex())], 32,
          'Continuous structural body')
    b.cut(component, 'z', -29, [b.poly(rounded_hex(4.2))], 29,
          'Hollow core with 3mm floor and 1.8mm walls')
    for x, y in lid_fasteners():
        b.add(component, 'z', -29, [b.circ(x, y, 4.2)], 29,
              'Integral concealed lid screw column')
        b.cut(component, 'z', -32, [b.circ(x, y, 1.7)], 32,
              'Underside M3 clearance shaft')
        b.cut(component, 'z', -32, [b.circ(x, y, 3.1)], 2,
              'Recessed underside screw head')
        b.add(component, 'z', -5, [b.circ(x, y, 6.5)], 5, 'Integral wide insert seating collar')
        b.cut(component, 'z', -5, [b.circ(x,y,1.7)], 5, 'Keep screw shaft open through widened collar')
        b.cut(component, 'z', -4, [b.circ(x, y, 5.3)], 4,
              'Lid boss receiving pocket with radial clearance')
        _fastener(b, 'Core lid M3x30', (x, y), -30, 0, 30)
    for x, y in cassette_fasteners():
        b.add(component, 'z', -29, [b.circ(x, y, 3.5)], 14,
              'Integral cassette support column')
        b.cut(component, 'z', -20, [b.circ(x, y, 2.1)], 5,
              'Provisional M3 insert cavity, cassette')
    for x in (-23.3, 23.3):
        b.add(component, 'z', -29, [b.rect(x-.7, -9, x+.7, 9)], 2,
              'Battery side guide, foam allowance')
    for y in (-13., 13.):
        b.add(component, 'z', -29, [b.rect(-21.8, y-.7, 21.8, y+.7)], 2,
              'Battery end guide')
    b.cut(component, 'z', -32,
          [b.cap((x, -8), (x, 8), 1.3) for x in (-24., 24.)], 3,
          'Battery soft strap routing')
    for angle in (30, 90, 150, 210, 270, 330):
        rad = math.radians(angle)
        a = (35*math.cos(rad), 35*math.sin(rad))
        c = (43*math.cos(rad), 43*math.sin(rad))
        b.cut(component, 'z', -32, [b.cap(a, c, 1.1)], 3,
              'Discreet underside ventilation slot')
    for angle in (30,90,150,210,270,330):
        rad=math.radians(angle)
        points=[(x*math.cos(rad)-y*math.sin(rad),x*math.sin(rad)+y*math.cos(rad)) for x,y in ((30,-7),(53,-10),(58,0),(53,10),(30,7))]
        b.cut(component,'z',-32,[b.poly(points)],3,'Underside weight relief between actuator bays')
    _finish(b, occurrence, 'CoreTub', -32)


def _build_lid(b, dims):
    occurrence, component = _part(b, 'CoreLid')
    b.add(component, 'z', .5, [b.poly(rounded_hex())], 2,
          'Low peripheral top skin')
    b.add(component, 'z', 2.5, [b.circ(0, 0, 31.6)], 7.9,
          'Compact central enclosure island')
    # Short crown bevel keeps the large ESP32 envelope below Z8 clear.
    b.loft(component, 'z', [(10.4, b.circ(0, 0, 31.6)),
                           (12.4, b.circ(0, 0, 30.6))],
           b.F.JoinFeatureOperation, 'Soft crown edge')
    b.cut(component, 'z', .5, [b.circ(0, 0, 29.2)], 9.5,
          'Open underside cavity; 2.4mm roof')
    for index in range(6):
        angle = index*math.pi/3
        x, y = 49*math.cos(angle), 49*math.sin(angle)
        b.cut(component, 'z', .5, [b.circ(x, y, 16.8)], 2,
              'Yaw rotating hub peripheral clearance')
    for x, y in lid_fasteners():
        b.add(component, 'z', -4, [b.circ(x, y, 5)], 4.5,
              'Concealed integral lid insert boss')
        b.cut(component, 'z', -4, [b.circ(x, y, 2.1)], 4.3,
              'Blind provisional M3 insert cavity')
    component.attributes.add('Hexapod', 'PrintCaution',
        'Upright roof needs localized support/bridge validation. '
        'Do not claim supportless or final print-ready.')
    _finish(b, occurrence, 'CoreLid', -4)


def _build_cassette(b,dims):
    occurrence,component=_part(b,'ElectronicsCassette')
    b.add(component,'z',-15,[b.circ(0,0,28.8)],2,'Low removable electronics carrier')
    for index in range(6):
        a=index*math.pi/3
        points=[(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a)) for x,y in ((26.6,-6.9),(59.4,-6.9),(59.4,6.9),(26.6,6.9))]
        b.cut(component,'z',-15,[b.poly(points)],2,'Yaw bay clearance with 0.4mm allowance')
    for x,y in cassette_fasteners():
        b.cut(component,'z',-15,[b.circ(x,y,1.7)],2,'Two hidden carrier fastener paths')
        _fastener(b,'Cassette M3x6',(x,y),-19,-13,6)
    a=math.pi/6
    for x in (-15,15):
        for y in (-20,20):
            b.add(component,'z',-13,[b.circ(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),2)],1,'Rotated regulator insulating support')
    for x in (-25,25):
        for y in (-4,4):
            b.add(component,'z',-13,[b.rect(x-.8,y-.8,x+.8,y+.8)],13,'Controller support outside regulator reserve')
    b.cut(component,'z',-15,[b.cap((-7,y),(7,y),1.2) for y in (-25,25)],2,'Reserved harness route at carrier edge')
    component.attributes.add('Hexapod','MountStatus','Reserved electronics only; exact boards, connectors, thermal design and wire bends not selected or verified')
    _finish(b,occurrence,'ElectronicsCassette',-15)


def assemble_reserves(b):
    for reserve in electronics_reserves():
        key = reserve['key']
        occurrence, component = _part(b, key)
        b.PARTS[key] = occurrence
        width, depth = reserve['width'], reserve['depth']
        b.add(component, 'z', reserve['z'],
              [b.rect(-width/2, -depth/2, width/2, depth/2)],
              reserve['height'], 'Reserved component keep-out envelope')
        component.attributes.add('Hexapod', 'ReservedEnvelope', reserve['status'])
        b.color(component, (108, 118, 130))
        occurrence.transform2=b.matrix(reserve['angle'],0,(0,0,0))
        if b.DESIGN.snapshots.hasPendingSnapshot:b.DESIGN.snapshots.add()
        parent = b.PARTS['CoreTub'] if key == 'BatteryReserve' else b.PARTS['ElectronicsCassette']
        b.rigid(parent, occurrence, key+' concept allocation')
