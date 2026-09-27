import numpy as np
from typing import List, Dict, Any

class CentroidSolver:
    """
    Solves centroids and first moments of area for composite shapes,
    polygons, and applies Pappus-Guldinus theorems.
    (Beer & Johnston Chapter 5)
    """

    @staticmethod
    def solve_composite(shapes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        shapes: list of shape dicts.
        Shape types:
        - 'rectangle': {x, y, w, h, subtract: bool} (bottom-left at (x,y))
        - 'right_triangle': {x, y, b, h, subtract: bool} (right angle at (x,y))
        - 'circle': {xc, yc, r, subtract: bool}
        - 'semicircle': {xc, yc, r, orientation: 'top'|'bottom'|'left'|'right', subtract: bool}
        - 'polygon': {vertices: [[x1, y1], [x2, y2], ...], subtract: bool}
        """
        table_rows = []
        total_A = 0.0
        total_Qx = 0.0  # Sum(y * A)
        total_Qy = 0.0  # Sum(x * A)

        for i, s in enumerate(shapes):
            stype = s['type'].lower()
            sub = s.get('subtract', False)
            sign = -1.0 if sub else 1.0

            A = 0.0
            cx = 0.0
            cy = 0.0

            if stype == 'rectangle':
                w = float(s['w'])
                h = float(s['h'])
                x = float(s['x'])
                y = float(s['y'])
                A = w * h
                cx = x + w / 2.0
                cy = y + h / 2.0

            elif stype == 'right_triangle':
                b = float(s['b'])
                h = float(s['h'])
                x = float(s['x'])
                y = float(s['y'])
                A = 0.5 * abs(b * h)
                cx = x + (b / 3.0)
                cy = y + (h / 3.0)

            elif stype == 'circle':
                r = float(s['r'])
                xc = float(s['xc'])
                yc = float(s['yc'])
                A = np.pi * (r**2)
                cx = xc
                cy = yc

            elif stype == 'semicircle':
                r = float(s['r'])
                xc = float(s['xc'])
                yc = float(s['yc'])
                A = 0.5 * np.pi * (r**2)
                d = (4.0 * r) / (3.0 * np.pi)
                orient = s.get('orientation', 'top')
                if orient == 'top':
                    cx = xc
                    cy = yc + d
                elif orient == 'bottom':
                    cx = xc
                    cy = yc - d
                elif orient == 'right':
                    cx = xc + d
                    cy = yc
                elif orient == 'left':
                    cx = xc - d
                    cy = yc

            elif stype == 'polygon':
                verts = np.array(s['vertices'], dtype=float)
                # Shoelace formula for polygon area and centroid
                x = verts[:, 0]
                y = verts[:, 1]
                # close loop if not closed
                if not (x[0] == x[-1] and y[0] == y[-1]):
                    x = np.append(x, x[0])
                    y = np.append(y, y[0])
                cross = x[:-1] * y[1:] - x[1:] * y[:-1]
                signed_A = 0.5 * np.sum(cross)
                A = abs(signed_A)
                if abs(A) > 1e-9:
                    cx = np.sum((x[:-1] + x[1:]) * cross) / (6.0 * signed_A)
                    cy = np.sum((y[:-1] + y[1:]) * cross) / (6.0 * signed_A)

            signed_A = sign * A
            Qx = signed_A * cy
            Qy = signed_A * cx

            total_A += signed_A
            total_Qx += Qx
            total_Qy += Qy

            table_rows.append({
                'part_id': i + 1,
                'type': stype,
                'is_subtracted': sub,
                'area': round(signed_A, 4),
                'x_bar': round(cx, 4),
                'y_bar': round(cy, 4),
                'Qx': round(Qx, 4),
                'Qy': round(Qy, 4)
            })

        if abs(total_A) <= 1e-9:
            raise ValueError("Total area of composite shape is zero or negative.")

        overall_x_bar = total_Qy / total_A
        overall_y_bar = total_Qx / total_A

        # Pappus-Guldinus calculations
        # Volume of revolution about x-axis (if y_bar >= 0): V = 2 * pi * y_bar * A
        vol_about_x = 2.0 * np.pi * abs(overall_y_bar) * total_A
        vol_about_y = 2.0 * np.pi * abs(overall_x_bar) * total_A

        return {
            'success': True,
            'total_area': round(total_A, 4),
            'Qx': round(total_Qx, 4),
            'Qy': round(total_Qy, 4),
            'x_bar': round(overall_x_bar, 4),
            'y_bar': round(overall_y_bar, 4),
            'pappus_guldinus': {
                'volume_revolution_x_axis': round(vol_about_x, 4),
                'volume_revolution_y_axis': round(vol_about_y, 4)
            },
            'breakdown_table': table_rows
        }
