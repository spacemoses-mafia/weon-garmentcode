""" Panels for a straight upper garment (T-shirt)
    Note that the code is very similar to Bodice. 
"""

import numpy as np
import pygarment as pyg

from assets.garment_programs.base_classes import BaseBodicePanel


class TorsoFrontHalfPanel(BaseBodicePanel):
    """Half of a simple non-fitted upper garment (e.g. T-Shirt)
    
        Fits to the bust size
    """
    def __init__(self, name, body, design) -> None:
        """ Front = True, provides the adjustments necessary for the front panel
        """
        super().__init__(name, body, design)

        # sizes   
        waist = design['width_waist']['v'] / 2
        bust = design['width_chest']['v'] / 2
        self.width = design['width_chest']['v'] / 2
        max_len = design['front_length']['v']

        bottom = pyg.Edge(
            start=[0, 0], 
            end=[-design['width_hip']['v'] / 2, 0],
        )
        right_bottom = pyg.CurveEdgeFactory.curve_from_tangents(
            start=bottom.end,
            end=[-waist, max_len - design['waist_over_bust_line_height']['v']],
            target_tan1=np.array([0, 1]),
        )
        right_middle = pyg.CurveEdgeFactory.curve_from_tangents(
            start=right_bottom.end,
            end=[-bust, max_len - design['scye_depth']['v']],
            target_tan0=np.array([0, 1]),
        )

        self.edges.append([bottom, right_bottom, right_middle])
        self.edges.append(pyg.EdgeSeqFactory.from_verts(
            right_middle.end,
            [-bust, max_len - design['shoulder_slant']['v']], 
            [0, max_len]
        ))
        self.edges.close_loop()

        # Interfaces
        self.interfaces = {
            'outside':  pyg.Interface(self, pyg.EdgeSequence(right_bottom, right_middle)),   
            'inside': pyg.Interface(self, self.edges[-1]),
            'shoulder': pyg.Interface(self, self.edges[-2]),
            'bottom': pyg.Interface(self, bottom),
            
            # Reference to the corner for sleeve and collar projections
            'shoulder_corner': pyg.Interface(self, [self.edges[-3], self.edges[-2]]),
            'collar_corner': pyg.Interface(self, [self.edges[-2], self.edges[-1]])
        }

        # default placement
        self.translate_by([0, body['height'] - body['head_l'] - max_len, 0])

    def get_width(self, level):
        return super().get_width(level) + self.width - self.neck_to_shoulder_delta_x - self.neck_width / 2


class TorsoBackHalfPanel(BaseBodicePanel):
    """Half of a simple non-fitted upper garment (e.g. T-Shirt)
    
        Fits to the bust size
    """
    def __init__(self, name, body, design, match_length_to_front=True) -> None:
        """ Front = True, provides the adjustments necessary for the front panel
        """
        super().__init__(name, body, design)

        # sizes   
        waist = design['width_waist']['v'] / 2
        bust = design['width_chest']['v'] / 2
        self.width = design['width_chest']['v'] / 2
        if not match_length_to_front:
            max_len = design['back_length']['v']
            bottom = pyg.Edge(
                start=[0, 0], 
                end=[-design['width_hip']['v'] / 2, 0],
            )
        else:
            max_len = design['front_length']['v']
            bottom = pyg.CurveEdgeFactory.curve_from_tangents(
                start=[0, max_len - design['back_length']['v']],
                end=[-design['width_hip']['v'] / 2, 0],
                target_tan0=np.array([-1, 0]),
            )

        right_bottom = pyg.CurveEdgeFactory.curve_from_tangents(
            start=bottom.end,
            end=[-waist, max_len - design['waist_over_bust_line_height']['v']],
            target_tan1=np.array([0, 1]),
        )
        right_middle = pyg.CurveEdgeFactory.curve_from_tangents(
            start=right_bottom.end,
            end=[-bust, max_len - design['scye_depth']['v']],
            target_tan0=np.array([0, 1]),
        )

        self.edges.append([bottom, right_bottom, right_middle])
        self.edges.append(pyg.EdgeSeqFactory.from_verts(
            right_middle.end,
            [-bust, max_len - design['shoulder_slant']['v']], 
            [0, max_len]
        ))
        self.edges.close_loop()

        # Interfaces
        self.interfaces = {
            'outside':  pyg.Interface(self, pyg.EdgeSequence(right_bottom, right_middle)),   
            'inside': pyg.Interface(self, self.edges[-1]),
            'shoulder': pyg.Interface(self, self.edges[-2]),
            'bottom': pyg.Interface(self, bottom),
            
            # Reference to the corner for sleeve and collar projections
            'shoulder_corner': pyg.Interface(self, [self.edges[-3], self.edges[-2]]),
            'collar_corner': pyg.Interface(self, [self.edges[-2], self.edges[-1]])
        }

        # default placement
        self.translate_by([0, body['height'] - body['head_l'] - max_len, 0])

    def get_width(self, level):
        return super().get_width(level) + self.width - self.neck_to_shoulder_delta_x - self.neck_width / 2
