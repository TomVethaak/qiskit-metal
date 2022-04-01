# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2017, 2021.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

#  This a launch structure used on BlueJayV2, used for wire bonding
#  There is no CPW tee attached to this p#

# Imports required for drawing

# import numpy as np # (currently not used, may be needed later for component customization)
from qiskit_metal import draw
from qiskit_metal.toolbox_python.attr_dict import Dict
from qiskit_metal.qlibrary.core import QComponent

# Define class and options for the launch geometry


class XYTip(QComponent):
    """Tapered and rouned tip to terminate capacitively couples lines.

    Inherits 'QComponent' class.

    Creates a tip with a narrowed gap.
    Limited but expandable parameters to control the XY tip polygons.
    The (0,0) point is the center of the necking of the launch tip.
    The pin attaches directly to the built-in lead length at its midpoint

    Pocket and tip:
        Pocket and tip geometries are currently fixed.
        (0,0) point is the midpoint of the necking of the launch tip.
        Pocket is a negative shape that is cut out of the ground plane

    Values (unless noted) are strings with units included, (e.g., '30um')

    Sketch:
        Below is a sketch of the tip
        ::

            -----
                 \_______
            ------------\\
            0            ||    (0,0) pin at midpoint of necking, before the lead
            ------------//
                   _____
                  /
            ------

            y
            ^
            |
            |------> x

    Default Options:
        * trace_width: 'cpw_width' -- Width of the transmission line attached to the launch pad
        * trace_gap: 'cpw_gap' -- Gap of the transmission line
        * lead_length: '25um' -- Length of the transmission line attached to the launch pad
        * tip_width: '80um' -- Width of the launch pad
        * tip_height: '80um' -- Height of the launch pad
        * tip_gap: '58um' -- Gap of the launch pad
        * taper_height: '122um' -- Height of the taper from the launch pad to the transmission line
    """

    default_options = Dict(trace_width='cpw_width',
                           trace_gap='cpw_gap',
                           lead_length='10um',
                           tip_width='5um',
                           tip_height='100um',
                           tip_gap='3um',
                           taper_height='50um',
                           tip_fillet='1um')
    """Default options"""

    TOOLTIP = """Launch pad to feed/read signals to/from the chip."""

    def make(self):
        """This is executed by the user to generate the qgeometry for the
        component."""

        p = self.p

        tip_width = p.tip_width
        tip_height = p.tip_height
        tip_gap = p.tip_gap
        trace_width = p.trace_width
        trace_width_half = trace_width / 2.
        tip_width_half = tip_width / 2.
        lead_length = p.lead_length
        taper_height = p.taper_height
        trace_gap = p.trace_gap

        tip_fillet = p.tip_fillet
        #########################################################

        # Geometry of main launch structure
        # The shape is a polygon and we prepare this point as orientation is 0 degree
        xy_tip = draw.Polygon([
            (0, trace_width_half),
            (-taper_height, tip_width_half),
            (-(tip_height + taper_height), tip_width_half),
            (-(tip_height + taper_height), -tip_width_half),
            (-taper_height, -tip_width_half),
            (0, -trace_width_half),
            (lead_length, -trace_width_half),
            (lead_length, trace_width_half),
            (0, trace_width_half)
        ])

        round_tip_circle_top        = draw.Point(-(tip_height + taper_height - tip_fillet), tip_width_half - tip_fillet).buffer(tip_fillet)
        round_tip_negative_top      = draw.subtract( draw.Polygon( [ (-(tip_height + taper_height - tip_fillet), tip_width_half ),
                                            (-(tip_height + taper_height ), tip_width_half ),
                                            (-(tip_height + taper_height ), tip_width_half - tip_fillet ),
                                            (-(tip_height + taper_height - tip_fillet), tip_width_half - tip_fillet ) ] ),
                                            round_tip_circle_top )
        round_tip_circle_bottom     = draw.Point(-(tip_height + taper_height - tip_fillet), - (tip_width_half - tip_fillet) ).buffer(tip_fillet)
        round_tip_negative_bottom   = draw.subtract( draw.Polygon( [ (-(tip_height + taper_height - tip_fillet), -tip_width_half ),
                                            (-(tip_height + taper_height ), -tip_width_half ),
                                            (-(tip_height + taper_height ), -(tip_width_half - tip_fillet) ),
                                            (-(tip_height + taper_height - tip_fillet), -(tip_width_half - tip_fillet) ) ] ),
                                            round_tip_circle_bottom )
        round_tip_negative = round_tip_negative_top.union(round_tip_negative_bottom)
        xy_tip = draw.subtract( xy_tip, round_tip_negative )

        # Geometry pocket (gap)
        # Same way applied for pocket
        pocket = draw.Polygon([(0, trace_width_half + trace_gap),
                               (-taper_height, tip_width_half + tip_gap),
                               (-(tip_height + taper_height + tip_gap),
                                tip_width_half + tip_gap),
                               (-(tip_height + taper_height + tip_gap),
                                -(tip_width_half + tip_gap)),
                               (-taper_height, -(tip_width_half + tip_gap)),
                               (0, -(trace_width_half + trace_gap)),
                               (lead_length, -(trace_width_half + trace_gap)),
                               (lead_length, trace_width_half + trace_gap),
                               (0, trace_width_half + trace_gap)])



        # These variables are used to graphically locate the pin locations
        main_pin_line = draw.LineString([(lead_length, trace_width_half),
                                         (lead_length, -trace_width_half)])

        # Create polygon object list
        polys1 = [main_pin_line, xy_tip, pocket]

        # Rotates and translates all the objects as requested. Uses package functions in
        # 'draw_utility' for easy rotation/translation
        polys1 = draw.rotate(polys1, p.orientation, origin=(0, 0))
        polys1 = draw.translate(polys1, xoff=p.pos_x, yoff=p.pos_y)
        [main_pin_line, xy_tip, pocket] = polys1

        # Adds the object to the qgeometry table
        self.add_qgeometry('poly', dict(xy_tip=xy_tip), layer=p.layer)

        # Subtracts out ground plane on the layer its on
        self.add_qgeometry('poly',
                           dict(pocket=pocket),
                           subtract=True,
                           layer=p.layer)

        # Generates the pins
        self.add_pin('tie', main_pin_line.coords, trace_width)
