import numpy as np
from typing import List, Dict, Any

class VectorMechanics:
    """
    Solves 2D and 3D vector statics and particle equilibrium.
    (Beer & Johnston Chapter 2 & 3)
    """

    @staticmethod
    def calculate_resultant(forces: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        forces: list of dicts with 'fx', 'fy', and optional 'fz'
        """
        Rx, Ry, Rz = 0.0, 0.0, 0.0
        for f in forces:
            Rx += float(f.get('fx', 0.0))
            Ry += float(f.get('fy', 0.0))
            Rz += float(f.get('fz', 0.0))

        mag = float(np.sqrt(Rx**2 + Ry**2 + Rz**2))
        
        # Coordinate direction angles (in degrees)
        theta_x = float(np.degrees(np.arccos(Rx / mag))) if mag > 1e-9 else 0.0
        theta_y = float(np.degrees(np.arccos(Ry / mag))) if mag > 1e-9 else 0.0
        theta_z = float(np.degrees(np.arccos(Rz / mag))) if mag > 1e-9 else 0.0

        # In 2D plane: angle with +X axis
        angle_2d = float(np.degrees(np.arctan2(Ry, Rx)))

        return {
            'Rx': round(Rx, 4),
            'Ry': round(Ry, 4),
            'Rz': round(Rz, 4),
            'magnitude': round(mag, 4),
            'angle_2d_deg': round(angle_2d, 2),
            'theta_x_deg': round(theta_x, 2),
            'theta_y_deg': round(theta_y, 2),
            'theta_z_deg': round(theta_z, 2),
            'unit_vector': {
                'ux': round(Rx / mag, 4) if mag > 1e-9 else 0.0,
                'uy': round(Ry / mag, 4) if mag > 1e-9 else 0.0,
                'uz': round(Rz / mag, 4) if mag > 1e-9 else 0.0,
            }
        }

    @staticmethod
    def dot_cross_product(v1: Dict[str, float], v2: Dict[str, float]) -> Dict[str, Any]:
        a = np.array([float(v1.get('x', 0)), float(v1.get('y', 0)), float(v1.get('z', 0))])
        b = np.array([float(v2.get('x', 0)), float(v2.get('y', 0)), float(v2.get('z', 0))])

        mag_a = float(np.linalg.norm(a))
        mag_b = float(np.linalg.norm(b))

        dot = float(np.dot(a, b))
        cross = np.cross(a, b)
        cross_mag = float(np.linalg.norm(cross))

        # Angle between
        cos_theta = dot / (mag_a * mag_b) if (mag_a * mag_b) > 1e-9 else 1.0
        cos_theta = np.clip(cos_theta, -1.0, 1.0)
        theta_deg = float(np.degrees(np.arccos(cos_theta)))

        # Projection of a onto b
        proj_a_on_b = dot / mag_b if mag_b > 1e-9 else 0.0

        return {
            'dot_product': round(dot, 4),
            'cross_product': {
                'x': round(float(cross[0]), 4),
                'y': round(float(cross[1]), 4),
                'z': round(float(cross[2]), 4),
                'magnitude': round(cross_mag, 4)
            },
            'angle_deg': round(theta_deg, 2),
            'projection_a_on_b': round(proj_a_on_b, 4)
        }

    @staticmethod
    def solve_particle_equilibrium(cables: List[Dict[str, Any]], applied_load: Dict[str, float]) -> Dict[str, Any]:
        """
        Solves equilibrium of a particle/ring where cables or struts meet.
        cables: list of dicts with:
           'name': str,
           'origin': [x0, y0, z0] (usually ring at (0,0,0)),
           'target': [x, y, z] (anchor point)
        applied_load: {'fx': float, 'fy': float, 'fz': float} (e.g. suspended weight)

        System: Sum(T_i * u_i) + F_ext = 0  => A * T = -F_ext
        """
        n_cables = len(cables)
        if n_cables not in [2, 3]:
            raise ValueError("Equilibrium solver requires 2 unknown cables (2D) or 3 unknown cables (3D).")

        unit_vectors = []
        for c in cables:
            orig = np.array(c.get('origin', [0.0, 0.0, 0.0]), dtype=float)
            targ = np.array(c['target'], dtype=float)
            vec = targ - orig
            norm = np.linalg.norm(vec)
            if norm <= 1e-9:
                raise ValueError(f"Cable {c.get('name', '')} has zero length.")
            u = vec / norm
            unit_vectors.append(u)

        if n_cables == 2:
            # 2D case
            A = np.array([
                [unit_vectors[0][0], unit_vectors[1][0]],
                [unit_vectors[0][1], unit_vectors[1][1]]
            ])
            b = np.array([
                -float(applied_load.get('fx', 0.0)),
                -float(applied_load.get('fy', 0.0))
            ])
        else:
            # 3D case
            A = np.array([
                [unit_vectors[0][0], unit_vectors[1][0], unit_vectors[2][0]],
                [unit_vectors[0][1], unit_vectors[1][1], unit_vectors[2][1]],
                [unit_vectors[0][2], unit_vectors[1][2], unit_vectors[2][2]]
            ])
            b = np.array([
                -float(applied_load.get('fx', 0.0)),
                -float(applied_load.get('fy', 0.0)),
                -float(applied_load.get('fz', 0.0))
            ])

        try:
            T = np.linalg.solve(A, b)
        except np.linalg.LinAlgError:
            raise ValueError("Lines of action are linearly dependent or coplanar in 3D. System cannot be solved.")

        results = []
        for i, c in enumerate(cables):
            tension_val = float(T[i])
            results.append({
                'name': c.get('name', f'Cable {i+1}'),
                'tension': round(tension_val, 4),
                'state': 'Tension' if tension_val >= 0 else 'Compression (Strut)',
                'unit_vector': [round(float(k), 4) for k in unit_vectors[i]]
            })

        return {
            'success': True,
            'results': results,
            'equilibrium_check': {
                'sum_fx': round(float(np.sum(T * np.array([u[0] for u in unit_vectors])) + applied_load.get('fx', 0)), 6),
                'sum_fy': round(float(np.sum(T * np.array([u[1] for u in unit_vectors])) + applied_load.get('fy', 0)), 6),
                'sum_fz': round(float(np.sum(T * np.array([u[2] for u in unit_vectors])) + applied_load.get('fz', 0)), 6) if n_cables == 3 else 0.0
            }
        }
