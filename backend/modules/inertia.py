import numpy as np
from typing import List, Dict, Any

class InertiaSolver:
    """
    Solves Area Moments of Inertia, Parallel Axis Theorem,
    Principal Moments of Inertia, and Mohr's Circle parameters.
    (Beer & Johnston Chapter 9)
    """

    @staticmethod
    def solve_composite_inertia(shapes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates Ix, Iy, Ixy, J, and centroidal moments using parallel axis theorem.
        Supports standard civil engineering components:
        - 'rectangle': {x, y, w, h, subtract: bool}
        - 'circle': {xc, yc, r, subtract: bool}
        - 'right_triangle': {x, y, b, h, subtract: bool}
        """
        total_A = 0.0
        total_Qx = 0.0
        total_Qy = 0.0

        parts = []

        # First pass: find centroid (x_bar, y_bar)
        for s in shapes:
            stype = s['type'].lower()
            sub = s.get('subtract', False)
            sign = -1.0 if sub else 1.0

            A = 0.0
            cx, cy = 0.0, 0.0
            # Centroidal moments of the primitive itself
            I_xc, I_yc, I_xyc = 0.0, 0.0, 0.0

            if stype == 'rectangle':
                w = float(s['w'])
                h = float(s['h'])
                x = float(s['x'])
                y = float(s['y'])
                A = w * h
                cx = x + w / 2.0
                cy = y + h / 2.0
                I_xc = (w * h**3) / 12.0
                I_yc = (h * w**3) / 12.0
                I_xyc = 0.0 # symmetric about centroidal axes

            elif stype == 'circle':
                r = float(s['r'])
                xc = float(s['xc'])
                yc = float(s['yc'])
                A = np.pi * r**2
                cx = xc
                cy = yc
                I_xc = (np.pi * r**4) / 4.0
                I_yc = (np.pi * r**4) / 4.0
                I_xyc = 0.0

            elif stype == 'right_triangle':
                b = float(s['b'])
                h = float(s['h'])
                x = float(s['x'])
                y = float(s['y'])
                A = 0.5 * abs(b * h)
                cx = x + b / 3.0
                cy = y + h / 3.0
                I_xc = (abs(b) * abs(h)**3) / 36.0
                I_yc = (abs(h) * abs(b)**3) / 36.0
                # Product of inertia of right triangle about centroidal axes
                # Sign depends on orientation of b and h
                I_xyc = -(b**2 * h**2) / 72.0 if (b * h > 0) else (b**2 * h**2) / 72.0

            signed_A = sign * A
            total_A += signed_A
            total_Qx += signed_A * cy
            total_Qy += signed_A * cx

            parts.append({
                'type': stype,
                'sub': sub,
                'sign': sign,
                'A': A,
                'cx': cx,
                'cy': cy,
                'I_xc': I_xc,
                'I_yc': I_yc,
                'I_xyc': I_xyc
            })

        if abs(total_A) <= 1e-9:
            raise ValueError("Total area is zero or negative.")

        x_bar = total_Qy / total_A
        y_bar = total_Qx / total_A

        # Second pass: compute moments of inertia about global axes and centroidal axes
        Ix_origin = 0.0
        Iy_origin = 0.0
        Ixy_origin = 0.0

        I_x_bar = 0.0
        I_y_bar = 0.0
        I_xy_bar = 0.0

        for p in parts:
            sign = p['sign']
            A = p['A']
            cx = p['cx']
            cy = p['cy']

            # Parallel axis to origin
            Ix_part_orig = p['I_xc'] + A * (cy**2)
            Iy_part_orig = p['I_yc'] + A * (cx**2)
            Ixy_part_orig = p['I_xyc'] + A * cx * cy

            Ix_origin += sign * Ix_part_orig
            Iy_origin += sign * Iy_part_orig
            Ixy_origin += sign * Ixy_part_orig

            # Parallel axis to overall composite centroid (x_bar, y_bar)
            dx = cx - x_bar
            dy = cy - y_bar

            Ix_part_c = p['I_xc'] + A * (dy**2)
            Iy_part_c = p['I_yc'] + A * (dx**2)
            Ixy_part_c = p['I_xyc'] + A * dx * dy

            I_x_bar += sign * Ix_part_c
            I_y_bar += sign * Iy_part_c
            I_xy_bar += sign * Ixy_part_c

        # Polar moment of inertia
        J_c = I_x_bar + I_y_bar
        J_origin = Ix_origin + Iy_origin

        # Radii of gyration
        kx = float(np.sqrt(abs(I_x_bar / total_A))) if total_A > 0 else 0.0
        ky = float(np.sqrt(abs(I_y_bar / total_A))) if total_A > 0 else 0.0
        kO = float(np.sqrt(abs(J_c / total_A))) if total_A > 0 else 0.0

        # Principal Moments of Inertia & Mohr's Circle
        I_avg = (I_x_bar + I_y_bar) / 2.0
        R = float(np.sqrt(((I_x_bar - I_y_bar) / 2.0)**2 + (I_xy_bar)**2))
        I_max = I_avg + R
        I_min = I_avg - R

        # Principal angle theta_p (in degrees)
        # tan(2*theta_p) = -2*Ixy / (Ix - Iy)
        two_theta_rad = float(np.arctan2(-2.0 * I_xy_bar, I_x_bar - I_y_bar))
        theta_p_deg = float(np.degrees(two_theta_rad / 2.0))

        return {
            'success': True,
            'total_area': round(total_A, 4),
            'centroid': {'x_bar': round(x_bar, 4), 'y_bar': round(y_bar, 4)},
            'centroidal_moments': {
                'I_x_bar': round(I_x_bar, 4),
                'I_y_bar': round(I_y_bar, 4),
                'I_xy_bar': round(I_xy_bar, 4),
                'J_c': round(J_c, 4)
            },
            'origin_moments': {
                'Ix': round(Ix_origin, 4),
                'Iy': round(Iy_origin, 4),
                'Ixy': round(Ixy_origin, 4),
                'J_origin': round(J_origin, 4)
            },
            'radii_of_gyration': {
                'kx': round(kx, 4),
                'ky': round(ky, 4),
                'kO': round(kO, 4)
            },
            'principal_moments': {
                'I_max': round(I_max, 4),
                'I_min': round(I_min, 4),
                'theta_p_deg': round(theta_p_deg, 2)
            },
            'mohr_circle': {
                'center': round(I_avg, 4),
                'radius': round(R, 4),
                'point_X': {'I': round(I_x_bar, 4), 'Ixy': round(I_xy_bar, 4)},
                'point_Y': {'I': round(I_y_bar, 4), 'Ixy': round(-I_xy_bar, 4)}
            }
        }
