import numpy as np
from math import *
from qiskit_metal import draw, Dict
from qiskit_metal.qlibrary.core import BaseQubit


class TurtleQubit(BaseQubit):
    """
    The base 'TurtleQubit' class

    Inherits 'BaseQubit' class

    Description:
        Metal transmon object consisting of a single capacitive island
        surrounded by ground plane. The Josephson Junction is specified to
        the south. There is a readout resonator and charge line.

    Main Body:
        *position_x / position_y = where the center of the transmon circle
                                    should be located on the chip
    """

    """
    Edits Tom:
     - Made the cpw side of the claw grounded.
     - Added a parameter res_dist, so the capacitive coupling can be tuned
       with both the width of the clamp (res_arc) and the distance.
    """

    default_options = Dict(
        rad_i = '125um', # transmon inner radius
        gap = '25um', # gap between the qubit and ground plane
        layer = '1',
        jj_w = '10um', #junction width
        #res_arc = '50um', # arclength of resonator claw
        #res_ext = '25um', #extension of readout resonator beyond transmon
        #res_angle = '90', #angle of resonator claw relative to junction pos (counter clockwise)
        #res_claw_width = '10um', #width of the claw
        #res_s = '6um', # space around coupler claw
        #res_g = False, #add ground between claw and qubit
        #res_g_s = '2um', #thickness of ground between qubit and claw if res_ground
        #cpw_width = '10um',
        #cpw_gap = '6um',
        pos_x = '1 mm',
        pos_y = '1 mm',
        rotation = '0.0', # degrees to rotate the component by
        _default_connection_pads=Dict(
            res_arc = '50um',
            res_dist = '25um',
            res_ext = '25um',
            res_angle = '90',
            res_claw_width='10um',
            res_claw_rounding = '2um', # Has to be less than half of res_claw_width!
            res_s = '6um',
            res_g = False,
            res_g_s = '2um',
            cpw_width = '12um',
            cpw_gap = '12um'
        )
    )
    """Default drawing options"""

    component_metadata = Dict(short_name='Turtle',
                              _qgeometry_table_poly='True',
                              _qgeometry_table_junction='True')

    def make(self):
        """Convert self.options in QGeometry"""
        self.make_turtle()
        for name in self.options.connection_pads:
            if self.options.connection_pads[name].res_g:
                self.make_grounded_claw(name)
            else:
                self.make_claw(name)

    def make_turtle(self):
        p = self.parse_options()

        #Create inner qubit island
        inner_pad = draw.Point(0,0).buffer(p.rad_i)
        # create the qubit pocket
        pocket = draw.Point(0,0).buffer(p.rad_i + p.gap)

        if self.design.render_mode == 'simulate':
            #Draw the JJ location
            jj_port = draw.rectangle(p.jj_w, 1e-3)#+p.gap)
            jj_p = jj_port
            # Create two small squares to launch the junction from
            jj_p1 = draw.translate(jj_p, xoff=0, yoff=(-(p.rad_i)))#+ 0.5*p.gap)))
            jj_p2 = draw.translate(jj_p, xoff=0, yoff=(-(p.rad_i+ p.gap)))
            #Join the pads on either end or remove from the pocket
            inner_pad = inner_pad.union(jj_p1)
            pocket = draw.subtract(pocket, jj_p2)
        else:
            pass
        # rect_jj = draw.LineString([(0, -(p.rad_i+0.5e-3)),
                                   # (0, -(p.rad_i+p.gap-0.5e-3))])
        rect_jj = draw.LineString([(0, -(p.rad_i+p.gap-0.5e-3)),
                                   (0, -(p.rad_i + 0.5e-3))])


        #translate and rotate all shapes

        objects = [inner_pad, pocket, rect_jj]
        objects = draw.rotate(objects, p.rotation, origin=(0,0))
        objects = draw.translate(objects, xoff=p.pos_x, yoff=p.pos_y)

        [inner_pad, pocket, rect_jj] = objects

        # Translate to Metal QGeometry
        geom_inner = {'Qubit': inner_pad}
        geom_pocket = {'Pocket': pocket}



        self.add_qgeometry('poly', geom_inner, layer=1, subtract=False)
        self.add_qgeometry('poly', geom_pocket, layer=1, subtract=True)
        self.add_qgeometry('junction', dict(rect_jj=rect_jj), width=p.jj_w)


    def make_claw(self, name):

        p = self.parse_options()
        pc = self.p.connection_pads[name]
        #Draw resonator claw
        claw_rad = draw.Point(0,0).buffer(
                            p.rad_i + \
                            pc.res_dist + \
                            0.5*pc.res_claw_width).boundary
        r = p.rad_i + pc.res_dist + pc.res_claw_width
        theta = pc.res_arc/r
        res_angle = pc.res_angle*np.pi/180
        claw_inter = draw.Polygon([(0,0),
                                   (r*np.cos(-np.pi/2 + res_angle - theta/2), r*np.sin(-np.pi/2 + res_angle - theta/2)),
                                   ((r+pc.res_ext)*np.cos(-np.pi/2 + res_angle), (r+pc.res_ext)*np.sin(np.pi/2 + res_angle)),
                                   (r*np.cos(-np.pi/2 + res_angle + theta/2), r*np.sin(-np.pi/2 + res_angle + theta/2))])
        claw_rad = claw_rad.intersection(claw_inter)
        res_claw = claw_rad.buffer(0.5*pc.res_claw_width, resolution=64, cap_style=2)

        cpw_arm = draw.rectangle(pc.cpw_width, pc.res_ext + 0.5*pc.res_claw_width)
        port_line = draw.LineString([(pc.cpw_width/2, -(pc.res_ext+pc.res_claw_width/2)/2),(-pc.cpw_width/2, -(pc.res_ext+pc.res_claw_width/2)/2)])

        polys = [cpw_arm, port_line]

        polys = draw.translate(polys, xoff=0, yoff=-(p.rad_i + pc.res_dist + 0.5*(pc.res_claw_width + pc.res_ext)))
        polys = draw.rotate(polys, pc.res_angle, origin=(0,0))

        [cpw_arm, port_line] = polys

        claw_gap = res_claw.buffer(pc.res_s, resolution=64, cap_style=2, join_style=1)
#        cpw_gap = cpw_arm.buffer(pc.cpw_gap, resolution=64, cap_style=2, join_style=2)
#        cpw_gap = draw.subtract(cpw_gap, draw.Point(0,0).buffer(p.rad_i + p.gap))
        cpw_gap = draw.rectangle(pc.cpw_width + 2*pc.cpw_gap, pc.res_ext +
                                 0.5*pc.res_claw_width)
        cpw_gap = draw.translate(cpw_gap, xoff=0, yoff=-(p.rad_i + pc.res_dist + 0.5*(pc.res_claw_width + pc.res_ext)))
        cpw_gap = draw.rotate(cpw_gap, pc.res_angle, origin=(0,0))

        # Round the claw
        res_claw_cutout = draw.subtract( res_claw.buffer(pc.res_claw_rounding) , res_claw )
        res_claw_cutout_buffer = res_claw_cutout.buffer( pc.res_claw_rounding )
        res_claw = res_claw.intersection(draw.subtract( res_claw.buffer(2.*pc.res_claw_rounding) , res_claw_cutout_buffer ).buffer(pc.res_claw_rounding))

        res_claw = draw.union(res_claw, cpw_arm)
        res_gap = draw.union(claw_gap, cpw_gap)

        #translate and rotate all shapes
        objects = [res_claw, res_gap, port_line]
        objects = draw.rotate(objects, p.rotation, origin=(0,0))
        objects = draw.translate(objects, xoff=p.pos_x, yoff=p.pos_y)
        [res_claw, res_gap, port_line] = objects

        # Translate to Metal QGeometry
        geom_res = {'res_claw': res_claw}
        geom_res_gap = {'poly5': res_gap}

        self.add_qgeometry('poly', geom_res, layer=1, subtract=False)
        self.add_qgeometry('poly', geom_res_gap, layer=1, subtract=True)
        self.add_pin(name, port_line.coords, pc.cpw_width)

    def make_grounded_claw(self, name):
        p = self.parse_options()
        pc = self.p.connection_pads[name]

        claw_rad = draw.Point(0,0).buffer(
                            p.rad_i + \
                            pc.res_dist + \
                            0.5*pc.res_claw_width + pc.res_s+pc.res_g_s).boundary
        r = p.rad_i + pc.res_dist + pc.res_claw_width + pc.res_s
        theta = pc.res_arc/r
        res_angle = pc.res_angle*np.pi/180
        claw_inter = draw.Polygon([(0,0),
                                   (r*np.cos(-np.pi/2 + res_angle - theta/2), r*np.sin(-np.pi/2 + res_angle - theta/2)),
                                   ((r+pc.res_ext)*np.cos(-np.pi/2 + res_angle), (r+pc.res_ext)*np.sin(np.pi/2 + res_angle)),
                                   (r*np.cos(-np.pi/2 + res_angle + theta/2), r*np.sin(-np.pi/2 + res_angle + theta/2))])
        claw_rad = claw_rad.intersection(claw_inter)
        res_claw = claw_rad.buffer(0.5*pc.res_claw_width, resolution=64, cap_style=2)

        cpw_arm = draw.rectangle(pc.cpw_width, pc.res_ext + 0.5*pc.res_claw_width)

        end_of_coupler = -(pc.res_ext + pc.res_claw_width/2)/2
        port_line = draw.LineString([(pc.cpw_width/2, end_of_coupler),(-pc.cpw_width/2, end_of_coupler)])

        polys = [cpw_arm, port_line]

        polys = draw.translate(polys, xoff=0, yoff=-(p.rad_i + pc.res_dist + 0.5*(pc.res_claw_width + pc.res_ext)+pc.res_s+pc.res_g_s))
        polys = draw.rotate(polys, pc.res_angle, origin=(0,0))

        [cpw_arm, port_line] = polys

        claw_gap = res_claw.buffer(pc.res_s, resolution=64, cap_style=2, join_style=1)
#        cpw_gap = cpw_arm.buffer(pc.cpw_gap, resolution=64, cap_style=2, join_style=2)
#        cpw_gap = draw.subtract(cpw_gap, draw.Point(0,0).buffer(p.rad_i + p.gap + pc.res_g_s))
        cpw_gap = draw.rectangle(pc.cpw_width + 2*pc.cpw_gap, pc.res_ext +
                                 0.5*pc.res_claw_width)
        cpw_gap = draw.translate(cpw_gap, xoff=0, yoff=-(p.rad_i + pc.res_dist + 0.5*(pc.res_claw_width + pc.res_ext)+pc.res_s+pc.res_g_s))
        cpw_gap = draw.rotate(cpw_gap, pc.res_angle, origin=(0,0))

        res_claw = draw.union(res_claw, cpw_arm)
        res_gap = draw.union(claw_gap, cpw_gap)

        #translate and rotate all shapes
        objects = [res_claw, res_gap, port_line]
        objects = draw.rotate(objects, p.rotation, origin=(0,0))
        objects = draw.translate(objects, xoff=p.pos_x, yoff=p.pos_y)
        [res_claw, res_gap, port_line] = objects

        # Translate to Metal QGeometry
        geom_res = {'res_claw': res_claw}
        geom_res_gap = {'poly5': res_gap}

        self.add_qgeometry('poly', geom_res, layer=1, subtract=False)
        self.add_qgeometry('poly', geom_res_gap, layer=1, subtract=True)
        self.add_pin(name, port_line.coords, pc.cpw_width)
