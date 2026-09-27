import sympy as sp
from typing import Dict, Any, List

class VirtualWorkSolver:
    """
    Solves mechanism equilibrium and stability of equilibrium positions
    using the Principle of Virtual Work and Potential Energy.
    (Beer & Johnston Chapter 10)
    """

    @staticmethod
    def analyze_potential_energy(expression_str: str, var_name: str = 'theta', interval: List[float] = [0, 3.14159]) -> Dict[str, Any]:
        """
        Takes a potential energy function V(q) in terms of variable q (e.g. theta),
        computes dV/dq = 0 to find equilibrium positions,
        and computes d^2V/dq^2 to determine stability (stable, unstable, neutral).
        """
        q = sp.Symbol(var_name, real=True)
        # Parse expression safely
        try:
            V = sp.sympify(expression_str, locals={'sin': sp.sin, 'cos': sp.cos, 'tan': sp.tan, 'pi': sp.pi, 'sqrt': sp.sqrt})
        except Exception as e:
            raise ValueError(f"Invalid mathematical expression: {str(e)}")

        dV_dq = sp.diff(V, q)
        d2V_dq2 = sp.diff(dV_dq, q)

        # Find critical points within interval
        solutions = []
        try:
            eq_pts = sp.solve(dV_dq, q)
        except Exception:
            eq_pts = []

        q_min, q_max = interval[0], interval[1]
        valid_points = []

        for pt in eq_pts:
            try:
                val = float(pt.evalf())
                if q_min - 1e-4 <= val <= q_max + 1e-4:
                    # Evaluate d^2V/dq^2
                    second_deriv = float(d2V_dq2.subs(q, val).evalf())
                    if second_deriv > 1e-5:
                        status = "پایدار (Stable)"
                        nature = "STABLE"
                    elif second_deriv < -1e-5:
                        status = "ناپایدار (Unstable)"
                        nature = "UNSTABLE"
                    else:
                        status = "خنثی (Neutral)"
                        nature = "NEUTRAL"

                    valid_points.append({
                        'q_value': round(val, 4),
                        'q_deg': round(float(val * 180.0 / 3.14159265), 2),
                        'potential_energy': round(float(V.subs(q, val).evalf()), 4),
                        'd2V_dq2': round(second_deriv, 4),
                        'stability': status,
                        'nature': nature
                    })
            except Exception:
                continue

        return {
            'success': True,
            'variable': var_name,
            'potential_energy_function': str(V),
            'first_derivative': str(dV_dq),
            'second_derivative': str(d2V_dq2),
            'equilibrium_points': valid_points
        }

    @staticmethod
    def solve_toggle_mechanism(P_applied: float, link_length: float, angle_deg: float) -> Dict[str, Any]:
        """
        Standard toggle clamp / scissor mechanism solved via virtual work:
        P applied horizontally, clamping force Q exerted vertically (or vice versa).
        dW = P * dx + Q * dy = 0  => Q = - P * (dx / dy)
        """
        import numpy as np
        L = float(link_length)
        theta = np.radians(float(angle_deg))
        P = float(P_applied)

        # dx = 2 * L * cos(theta) * d_theta
        # dy = L * sin(theta) * d_theta
        # Clamping mechanical advantage
        mech_adv = 1.0 / np.tan(theta) if abs(np.tan(theta)) > 1e-6 else float('inf')
        clamping_force_Q = P * mech_adv

        return {
            'success': True,
            'applied_force_P': P,
            'theta_deg': float(angle_deg),
            'mechanical_advantage': round(float(mech_adv), 4),
            'clamping_force_Q': round(float(clamping_force_Q), 4)
        }
