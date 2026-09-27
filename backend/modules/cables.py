import numpy as np
from typing import List, Dict, Any

class CableSolver:
    """
    Solves cables under concentrated loads, parabolic cables (uniform horizontal load),
    and catenary cables.
    (Beer & Johnston Chapter 7)
    """

    @staticmethod
    def solve_parabolic_cable(span_L: float, sag_h: float, w_per_m: float) -> Dict[str, Any]:
        """
        Cable with supports at same elevation, subject to uniform load w per horizontal meter.
        """
        L = float(span_L)
        h = float(sag_h)
        w = float(w_per_m)

        if L <= 0 or h <= 0 or w <= 0:
            raise ValueError("Span, sag, and load must be positive.")

        # Minimum tension at center
        T0 = (w * L**2) / (8.0 * h)
        # Maximum vertical reaction at supports
        Vy = w * L / 2.0
        # Maximum tension at support
        T_max = float(np.sqrt(T0**2 + Vy**2))

        # Cable length approximation (Beer & Johnston formula)
        # s = L * (1 + (8/3)*(h/L)^2 - (32/5)*(h/L)^4)
        ratio = h / L
        length_s = L * (1.0 + (8.0 / 3.0) * (ratio**2) - (32.0 / 5.0) * (ratio**4))

        # Profile curve points for visualization
        x_pts = np.linspace(0, L, 100)
        # y measured downward from support line: y = (4*h / L^2) * x * (L - x)
        y_pts = (4.0 * h / (L**2)) * x_pts * (L - x_pts)

        return {
            'success': True,
            'type': 'parabolic',
            'span': L,
            'sag': h,
            'distributed_load': w,
            'min_tension_T0': round(T0, 4),
            'max_vertical_reaction': round(Vy, 4),
            'max_tension_Tmax': round(T_max, 4),
            'cable_length': round(length_s, 4),
            'profile': {
                'x': [round(float(xi), 3) for xi in x_pts],
                'y_sag': [round(float(yi), 4) for yi in y_pts]
            }
        }

    @staticmethod
    def solve_concentrated_loads(span_L: float, loads: List[Dict[str, float]], known_sag: Dict[str, float]) -> Dict[str, Any]:
        """
        Cable spanning from x=0, y=0 to x=L, y=0 supporting vertical concentrated loads.
        known_sag: {'point_index': int, 'sag': float} specifies the sag at one of the load points.
        loads: [{'x': float, 'p': float}, ...] where p is downward force.
        """
        L = float(span_L)
        sorted_loads = sorted(loads, key=lambda item: float(item['x']))
        num_loads = len(sorted_loads)

        if num_loads == 0:
            raise ValueError("At least one concentrated load is required.")

        k_idx = int(known_sag['point_index'])
        y_k = float(known_sag['sag']) # sag at point k

        # Overall equilibrium to find vertical reactions at A (x=0) and B (x=L):
        # Taking moment about A: By * L - Sum(P_i * x_i) = 0 => By = Sum(P_i * x_i) / L
        total_moment_A = sum(float(ld['p']) * float(ld['x']) for ld in sorted_loads)
        total_load = sum(float(ld['p']) for ld in sorted_loads)
        
        By = total_moment_A / L
        Ay = total_load - By

        # Now, cut at the known sag point k:
        # Sum of moments about point k for the left portion must equal zero:
        # Ay * x_k - T0 * y_k - Sum_{i < k}( P_i * (x_k - x_i) ) = 0
        x_k = float(sorted_loads[k_idx]['x'])
        m_left_loads = sum(float(ld['p']) * (x_k - float(ld['x'])) for ld in sorted_loads[:k_idx])
        
        # T0 * y_k = Ay * x_k - m_left_loads
        m_net_k = Ay * x_k - m_left_loads
        if abs(y_k) <= 1e-9:
            raise ValueError("Sag at reference point cannot be zero.")
        T0 = m_net_k / y_k

        if T0 <= 0:
            raise ValueError("Calculated horizontal tension is non-positive. Check loads and sag configuration.")

        # Compute sag y_i at all load points
        sags = []
        for i, ld in enumerate(sorted_loads):
            xi = float(ld['x'])
            m_left = sum(float(sorted_loads[j]['p']) * (xi - float(sorted_loads[j]['x'])) for j in range(i))
            yi = (Ay * xi - m_left) / T0
            sags.append({'point_index': i, 'x': xi, 'sag': round(float(yi), 4), 'load': float(ld['p'])})

        # Calculate tension in each segment
        # Segment 0: from A(0,0) to Point 0(x0, y0)
        all_pts = [{'x': 0.0, 'y': 0.0}] + [{'x': s['x'], 'y': s['sag']} for s in sags] + [{'x': L, 'y': 0.0}]
        segments = []
        max_T = T0

        for i in range(len(all_pts) - 1):
            p1 = all_pts[i]
            p2 = all_pts[i+1]
            dx = p2['x'] - p1['x']
            dy = p2['y'] - p1['y']
            theta_rad = np.arctan2(dy, dx)
            seg_T = T0 / np.cos(theta_rad)
            if seg_T > max_T:
                max_T = seg_T
            seg_len = np.sqrt(dx**2 + dy**2)
            segments.append({
                'segment_id': i + 1,
                'from': [round(p1['x'], 3), round(p1['y'], 3)],
                'to': [round(p2['x'], 3), round(p2['y'], 3)],
                'tension': round(float(seg_T), 4),
                'angle_deg': round(float(np.degrees(theta_rad)), 2),
                'length': round(float(seg_len), 4)
            })

        total_length = sum(s['length'] for s in segments)

        return {
            'success': True,
            'type': 'concentrated',
            'span': L,
            'horizontal_tension_T0': round(float(T0), 4),
            'reaction_Ay': round(float(Ay), 4),
            'reaction_By': round(float(By), 4),
            'max_tension': round(float(max_T), 4),
            'total_cable_length': round(float(total_length), 4),
            'load_points': sags,
            'segments': segments
        }
