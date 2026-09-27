import numpy as np
from typing import List, Dict, Any

class RigidBodyMechanics:
    """
    Solves moments, couples, equivalent force-couple systems, wrenches,
    and general 2D rigid body equilibrium.
    (Beer & Johnston Chapter 3 & 4)
    """

    @staticmethod
    def moment_about_point(point_o: List[float], point_a: List[float], force: List[float]) -> Dict[str, Any]:
        """
        Calculates moment of force F applied at point A about point O: M_O = r_{A/O} x F
        """
        o = np.array(point_o, dtype=float)
        a = np.array(point_a, dtype=float)
        f = np.array(force, dtype=float)

        r = a - o
        m = np.cross(r, f)
        mag = float(np.linalg.norm(m))

        return {
            'r_vector': [round(float(x), 4) for x in r],
            'moment_vector': {
                'Mx': round(float(m[0]), 4),
                'My': round(float(m[1]), 4),
                'Mz': round(float(m[2]), 4),
                'magnitude': round(mag, 4)
            }
        }

    @staticmethod
    def moment_about_axis(axis_point: List[float], axis_dir: List[float], force_point: List[float], force: List[float]) -> Dict[str, Any]:
        """
        Moment of force F about an axis defined by axis_point and direction axis_dir.
        M_axis = lambda_axis . (r x F)
        """
        p_axis = np.array(axis_point, dtype=float)
        dir_axis = np.array(axis_dir, dtype=float)
        norm_dir = np.linalg.norm(dir_axis)
        if norm_dir <= 1e-9:
            raise ValueError("Axis direction vector cannot be zero.")
        lam = dir_axis / norm_dir

        p_force = np.array(force_point, dtype=float)
        f = np.array(force, dtype=float)

        r = p_force - p_axis
        m_vec = np.cross(r, f)
        m_scalar = float(np.dot(lam, m_vec))

        return {
            'unit_axis': [round(float(k), 4) for k in lam],
            'moment_scalar': round(m_scalar, 4),
            'moment_vector': [round(float(k * m_scalar), 4) for k in lam]
        }

    @staticmethod
    def equivalent_system(reduction_point: List[float], forces: List[Dict[str, Any]], couples: List[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Reduces a system of forces and couples to an equivalent force-couple system at reduction_point.
        Also calculates the central axis of the wrench (Wrench / پیچ‌واره).
        """
        o = np.array(reduction_point, dtype=float)
        R = np.zeros(3)
        M_O = np.zeros(3)

        # Add applied couples
        if couples:
            for c in couples:
                M_O += np.array([float(c.get('mx', 0)), float(c.get('my', 0)), float(c.get('mz', 0))])

        # Add forces and their moments
        for item in forces:
            pos = np.array(item['point'], dtype=float)
            f = np.array([float(item.get('fx', 0)), float(item.get('fy', 0)), float(item.get('fz', 0))])
            R += f
            r = pos - o
            M_O += np.cross(r, f)

        R_mag = float(np.linalg.norm(R))
        M_mag = float(np.linalg.norm(M_O))

        wrench_info = {}
        if R_mag > 1e-9:
            # Pitch p = (R . M_O) / |R|^2
            pitch = float(np.dot(R, M_O) / (R_mag**2))
            # Point on central axis closest to reduction_point O: r0 = (R x M_O) / |R|^2
            r0 = np.cross(R, M_O) / (R_mag**2)
            wrench_axis_point = o + r0
            wrench_info = {
                'has_wrench': True,
                'pitch_p': round(pitch, 4),
                'axis_point': [round(float(k), 4) for k in wrench_axis_point],
                'axis_direction': [round(float(k / R_mag), 4) for k in R],
                'minimum_moment': round(abs(pitch * R_mag), 4)
            }
        else:
            wrench_info = {
                'has_wrench': False,
                'is_pure_couple': True
            }

        return {
            'reduction_point': [round(float(k), 4) for k in o],
            'resultant_force': {
                'Rx': round(float(R[0]), 4),
                'Ry': round(float(R[1]), 4),
                'Rz': round(float(R[2]), 4),
                'magnitude': round(R_mag, 4)
            },
            'resultant_moment': {
                'Mx': round(float(M_O[0]), 4),
                'My': round(float(M_O[1]), 4),
                'Mz': round(float(M_O[2]), 4),
                'magnitude': round(M_mag, 4)
            },
            'wrench': wrench_info
        }
