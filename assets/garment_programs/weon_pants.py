
from copy import deepcopy
import numpy as np

import pygarment as pyg
from assets.garment_programs.base_classes import BaseBottoms
from assets.garment_programs import bands


class PantPanel(pyg.Panel):
    def __init__(
            self,
            name: str,
            body: dict,
            design: dict,
            rise: float,
            mid_rise: float,
            waist: float,
            hips: float,
            crotch_extension: float,
            hips_crotch_diff: float,
            body_crotch_height: float,
            crotch_hip_diff: float,
            dart_position: float,
            match_top_int_to: float | None = None,
            hipline_ext: float = 1,
            double_dart: bool = False) -> None:
        """
            Basic pant panel with option to be fitted (with darts)
        """

        super().__init__(name)

        dart_depth = design['length_waist_to_hip']['v'] * hipline_ext * 0.8 
        dart_width = (hips - waist) / 2

        # --- Edges definition ---
        # Right
        right_5 = pyg.CurveEdgeFactory.curve_from_tangents(
            start=[-hips, hips_crotch_diff + design['length_1']['v'] + design['length_2']['v'] + design['length_3']['v']],
            end=[-waist, mid_rise + design['length_1']['v'] + design['length_2']['v'] + design['length_3']['v']],
            target_tan0=np.array([0, 1]),
        )
        ext_point_thigh = right_5.evaluate_at_length(-hips_crotch_diff)

        right_4 = pyg.CurveEdgeFactory.curve_from_tangents(
            start=ext_point_thigh,
            end=right_5.start,
            target_tan1=np.array([0, 1]),
        )

        x_grainline = ext_point_thigh[0] + (design['width_1']['v'] + crotch_extension) / 2

        right_3 = pyg.CurveEdgeFactory.interpolate_with_tangents(
            start=[x_grainline - design['width_2']['v'] / 2, (design['length_2']['v'] + design['length_3']['v'])],
            end=right_4.start,
            target_tan1=[right_4.as_curve().unit_tangent(0.0).real, right_4.as_curve().unit_tangent(0.0).imag],
            pre_start=[x_grainline - design['width_3']['v'] / 2, design['length_3']['v']],
            initial_guess=[0.1, 0]
        )

        right_2 = pyg.CurveEdgeFactory.interpolate_with_tangents(
            start=[x_grainline - design['width_3']['v'] / 2, design['length_3']['v']],
            end=right_3.start,
            pre_start=[x_grainline - design['width_4']['v'] / 2, 0],
            post_end=right_3.end,
            initial_guess=[0.5, 0]
        )

        right_1 = pyg.CurveEdgeFactory.interpolate_with_tangents(
            start=[x_grainline - design['width_4']['v'] / 2, 0],
            end=right_2.start,
            post_end=right_2.end,
            initial_guess=[0.5, 0]
        )
       
        top = pyg.Edge(
            start=right_5.end, 
            end=[0, (rise + design['length_1']['v'] + design['length_2']['v'] + design['length_3']['v'])], 
        )

        crotch_top = pyg.Edge(
            start=top.end,
            end=[0,
            crotch_hip_diff + design['length_1']['v'] + design['length_2']['v'] + design['length_3']['v']],
        )
        crotch_bottom = pyg.CurveEdgeFactory.curve_from_tangents(
            start=crotch_top.end,
            end=[ext_point_thigh[0] + hips + crotch_extension,
            design['length_1']['v'] + design['length_2']['v'] + design['length_3']['v']], 
            target_tan0=np.array([0, -1]),
            target_tan1=np.array([1, 0]),
            initial_guess=[0.5, -0.5] 
        )

        left_top = pyg.CurveEdgeFactory.interpolate_with_tangents(
            start=crotch_bottom.end,
            end=[right_2.end[0] + design['width_2']['v'], design['length_2']['v'] + design['length_3']['v']], 
            post_end=[x_grainline + design['width_3']['v'] / 2, design['length_3']['v']],
            initial_guess=[0.3, 0]
        )

        left_middle = pyg.CurveEdgeFactory.interpolate_with_tangents(
            start=left_top.end,
            end=[x_grainline + design['width_3']['v'] / 2, design['length_3']['v']],
            post_end=[x_grainline + design['width_4']['v'] / 2, 0],
            initial_guess=[0.5, 0]
        )

        left_bottom = pyg.CurveEdgeFactory.interpolate_with_tangents(
            start=left_middle.end,
            end=[x_grainline + design['width_4']['v'] / 2, 0],
            pre_start=left_middle.start,
            initial_guess=[0.5, 0]
        )
        self.edges = pyg.EdgeSequence(
            right_1, right_2, right_3, right_4, right_5, top, crotch_top, crotch_bottom, left_top, left_middle, left_bottom
            ).close_loop()
        bottom = self.edges[-1]

        # Default placement
        self.set_pivot(crotch_bottom.end)
        self.translation = [-0.5, - body_crotch_height + 5, 0] 

        # Out interfaces (easier to define before adding a dart)
        self.interfaces = {
            'outside': pyg.Interface(
                self, 
                pyg.EdgeSequence(right_1, right_2, right_3, right_4, right_5)),
            'crotch': pyg.Interface(self, pyg.EdgeSequence(crotch_top, crotch_bottom)),
            'inside': pyg.Interface(self, pyg.EdgeSequence(left_top, left_middle, left_bottom)),
            'bottom': pyg.Interface(self, bottom)
        }

        # Add top dart
        # NOTE: Ruffle indicator to match to waistline proportion for correct balance line matching
        if dart_width > 0:
            top_edges, int_edges = self.add_darts(
                top, dart_width, dart_depth, dart_position, double_dart=double_dart)
            self.interfaces['top'] = pyg.Interface(
                self, int_edges, 
                ruffle=waist / match_top_int_to if match_top_int_to is not None else 1.
            ) 
            self.edges.substitute(top, top_edges)
        else:
            self.interfaces['top'] = pyg.Interface(
                self, top, 
                ruffle=waist / match_top_int_to if match_top_int_to is not None else 1.
        ) 

    def add_darts(self, top, dart_width, dart_depth, dart_position, double_dart=False):
        
        if double_dart:
            # TODOLOW Avoid hardcoding for matching with the top?
            dist = dart_position * 0.5  # Dist between darts -> dist between centers
            offsets_mid = [
                - (dart_position + dist / 2 + dart_width / 2 + dart_width / 4),   
                - (dart_position - dist / 2) - dart_width / 4,
            ]

            darts = [
                pyg.EdgeSeqFactory.dart_shape(dart_width / 2, dart_depth * 0.9), # smaller
                pyg.EdgeSeqFactory.dart_shape(dart_width / 2, dart_depth)
            ]
        else:
            offsets_mid = [
                - dart_position - dart_width / 2,
            ]
            darts = [
                pyg.EdgeSeqFactory.dart_shape(dart_width, dart_depth)
            ]
        top_edges, int_edges = pyg.EdgeSequence(top), pyg.EdgeSequence(top)

        for off, dart in zip(offsets_mid, darts):
            left_edge_len = top_edges[-1].length()
            top_edges, int_edges = self.add_dart(
                dart,
                top_edges[-1],
                offset=left_edge_len + off,
                edge_seq=top_edges, 
                int_edge_seq=int_edges
            )

        return top_edges, int_edges
        

class PantsHalf(BaseBottoms):

    def __init__(self, tag: str, body: dict, design: dict, rise: float | None = None) -> None:
        super().__init__(body, design, tag, rise=rise)

        design = design['pants']
        cuff_len = design['cuff']['cuff_len']['v']
        cuff_len *= body['_leg_length']
        mid_rise = (design["back_rise"]["v"] + design["front_rise"]["v"]) / 2
        hips_crotch_diff = mid_rise  - design['length_waist_to_hip']['v']

        self.front = PantPanel(
            f'pant_f_{tag}', body, design,
            rise=design['front_rise']['v'],
            mid_rise=mid_rise,
            waist=design['waist']['v'] / 2,
            hips=design['width_hips']['v'] / 2,
            hips_crotch_diff=hips_crotch_diff,
            crotch_extension=design['width_hips']['v'] / 8,
            body_crotch_height=(body['hips_line'] - body['crotch_hip_diff']) * (1 + design['crotch_shift_ratio']['v']),
            #crotch_hip_diff=design['front_rise']['v'] - design['length_waist_to_hip']['v'],
            crotch_hip_diff=mid_rise - design['length_waist_to_hip']['v'],
            dart_position=design['waist']['v'] / 4,
            match_top_int_to=design['waist']['v'] / 2
            ).translate_by([0, body['_waist_level'] - 5, 25])

        self.back = PantPanel(
            f'pant_b_{tag}', body, design,
            rise=design['back_rise']['v'],
            mid_rise=mid_rise,
            waist=design['waist']['v'] / 2,
            hips=design['width_hips']['v'] / 2,
            hips_crotch_diff=hips_crotch_diff,
            crotch_extension=design['width_hips']['v'] / 8 + 3,
            body_crotch_height=(body['hips_line'] - body['crotch_hip_diff']) * (1 + design['crotch_shift_ratio']['v']),
            #crotch_hip_diff=design['front_rise']['v'] - design['length_waist_to_hip']['v'],
            crotch_hip_diff=mid_rise - design['length_waist_to_hip']['v'],
            hipline_ext=1.1,
            dart_position=design['width_hips']['v'] / 4,
            match_top_int_to=design['waist']['v'] / 2,
            double_dart=False
            ).translate_by([0, body['_waist_level'] - 5, -20])

        self.stitching_rules = pyg.Stitches(
            (self.front.interfaces['outside'], self.back.interfaces['outside']),
            (self.front.interfaces['inside'], self.back.interfaces['inside'])
        )

        # add a cuff
        # TODOLOW This process is the same for sleeves -- make a function?
        if design['cuff']['type']['v']:
            
            pant_bottom = pyg.Interface.from_multiple(
                self.front.interfaces['bottom'],
                self.back.interfaces['bottom'])

            # Copy to avoid editing original design dict
            cdesign = deepcopy(design)
            cdesign['cuff']['b_width'] = {}
            cdesign['cuff']['b_width']['v'] = pant_bottom.edges.length() / design['cuff']['top_ruffle']['v']
            cdesign['cuff']['cuff_len']['v'] = cuff_len

            # Init
            cuff_class = getattr(bands, cdesign['cuff']['type']['v'])
            self.cuff = cuff_class(f'pant_{tag}', cdesign)

            # Position
            self.cuff.place_by_interface(
                self.cuff.interfaces['top'],
                pant_bottom,
                gap=5,
                alignment='left'
            )

            # Stitch
            self.stitching_rules.append((
                pant_bottom,
                self.cuff.interfaces['top'])
            )

        self.interfaces = {
            'crotch_f': self.front.interfaces['crotch'],
            'crotch_b': self.back.interfaces['crotch'],
            'top_f': self.front.interfaces['top'], 
            'top_b': self.back.interfaces['top'] 
        }

    def length(self):
        if self.design['pants']['cuff']['type']['v']:
            return self.front.length() + self.cuff.length()
        
        return self.front.length()


class Pants(BaseBottoms):

    def __init__(self, body: dict, design: dict, rise: float | None = None) -> None:
        super().__init__(body, design)

        self.right = PantsHalf('r', body, design, rise)
        self.left = PantsHalf('l', body, design, rise).mirror()

        self.stitching_rules = pyg.Stitches(
            (self.right.interfaces['crotch_f'], self.left.interfaces['crotch_f']),
            (self.right.interfaces['crotch_b'], self.left.interfaces['crotch_b']),
        )

        self.interfaces = {
            'top_f': pyg.Interface.from_multiple(
                self.right.interfaces['top_f'], self.left.interfaces['top_f']),
            'top_b': pyg.Interface.from_multiple(
                self.right.interfaces['top_b'], self.left.interfaces['top_b']),
            # Some are reversed for correct connection
            'top': pyg.Interface.from_multiple(   # around the body starting from front right
                self.right.interfaces['top_f'].flip_edges(),
                self.left.interfaces['top_f'].reverse(with_edge_dir_reverse=True),
                self.left.interfaces['top_b'].flip_edges(),
                self.right.interfaces['top_b'].reverse(with_edge_dir_reverse=True), # Flips the edges and restores the direction
            )
        }

    def get_rise(self):
        return self.right.get_rise()
    
    def length(self):
        return self.right.length()
