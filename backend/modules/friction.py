import numpy as np
from typing import Dict, Any

class FrictionSolver:
    """
    Solves Coulomb friction, tipping vs slipping on inclined plane,
    wedges, and belt friction (Capstan equation).
    (Beer & Johnston Chapter 8)
    """

    @staticmethod
    def block_slip_vs_tip(weight_W: float, width_b: float, height_h: float,
                           force_height_y: float, force_angle_deg: float,
                           incline_theta_deg: float, mu_s: float) -> Dict[str, Any]:
        """
        Analyzes a block of weight W on an inclined plane of angle theta.
        Horizontal force P applied at height y from base, inclined at force_angle_deg relative to incline.
        Determines whether the block will slip first or tip first, and calculates critical force P_crit.
        """
        W = float(weight_W)
        b = float(width_b)
        h = float(height_h)
        y = float(force_height_y)
        alpha = np.radians(float(force_angle_deg))
        theta = np.radians(float(incline_theta_deg))
        mu = float(mu_s)

        # Equilibrium equations with force P:
        # Sum F_parallel = P * cos(alpha) - W * sin(theta) - F_f = 0  => F_f = P * cos(alpha) - W * sin(theta)
        # Sum F_perpendicular = N - W * cos(theta) + P * sin(alpha) = 0 => N = W * cos(theta) - P * sin(alpha)
        # Slipping occurs when |F_f| = mu * N
        # For impending motion up the incline:
        # P * cos(alpha) - W * sin(theta) = mu * (W * cos(theta) - P * sin(alpha))
        # P * (cos(alpha) + mu * sin(alpha)) = W * (sin(theta) + mu * cos(theta))
        denom_slip = np.cos(alpha) + mu * np.sin(alpha)
        if abs(denom_slip) > 1e-6:
            P_slip_up = W * (np.sin(theta) + mu * np.cos(theta)) / denom_slip
        else:
            P_slip_up = float('inf')

        # For impending motion down the incline (minimum force to hold block):
        # W * sin(theta) - P * cos(alpha) = mu * (W * cos(theta) - P * sin(alpha))
        # P * (cos(alpha) - mu * sin(alpha)) = W * (sin(theta) - mu * cos(theta))
        denom_hold = np.cos(alpha) - mu * np.sin(alpha)
        if abs(denom_hold) > 1e-6 and (np.sin(theta) - mu * np.cos(theta)) > 0:
            P_hold_down = W * (np.sin(theta) - mu * np.cos(theta)) / denom_hold
        else:
            P_hold_down = 0.0 # block will not slide down on its own if theta <= phi_s

        # Tipping analysis:
        # Impending tipping occurs when Normal force N moves to the front edge (corner at x = +b/2):
        # Moment about front bottom corner A:
        # Clockwise moments tipping it forward = Counter-clockwise restoring moments
        # Restoring moment from weight: W * cos(theta) * (b / 2) - W * sin(theta) * (h / 2)
        # Tipping moment from P: P * cos(alpha) * y + P * sin(alpha) * (b / 2)
        restoring_M = W * np.cos(theta) * (b / 2.0) - W * np.sin(theta) * (h / 2.0)
        tipping_arm = np.cos(alpha) * y + np.sin(alpha) * (b / 2.0)

        if tipping_arm > 1e-6:
            P_tip = restoring_M / tipping_arm
        else:
            P_tip = float('inf')

        friction_angle_deg = float(np.degrees(np.arctan(mu)))
        angle_of_repose_deg = friction_angle_deg

        # Determine governing mode
        governing_mode = ""
        P_crit = 0.0

        valid_P_slip = P_slip_up if P_slip_up > 0 else float('inf')
        valid_P_tip = P_tip if P_tip > 0 else float('inf')

        if valid_P_slip < valid_P_tip:
            governing_mode = "لغزش (Slipping)"
            P_crit = valid_P_slip
            comparison_note = f"نیروی لغزش ({round(valid_P_slip, 2)}) کمتر از نیروی واژگونی ({round(valid_P_tip, 2)}) است، بنابراین جسم قبل از چپ شدن سر می‌خورد."
        else:
            governing_mode = "واژگونی (Tipping)"
            P_crit = valid_P_tip
            comparison_note = f"نیروی واژگونی ({round(valid_P_tip, 2)}) کمتر از نیروی لغزش ({round(valid_P_slip, 2)}) است، بنابراین جسم قبل از سر خوردن واژگون می‌شود."

        return {
            'success': True,
            'friction_angle_deg': round(friction_angle_deg, 2),
            'P_slip_critical': round(valid_P_slip, 4) if valid_P_slip != float('inf') else None,
            'P_tip_critical': round(valid_P_tip, 4) if valid_P_tip != float('inf') else None,
            'governing_mode': governing_mode,
            'P_critical': round(P_crit, 4),
            'comparison_note': comparison_note,
            'self_locking': theta < np.arctan(mu)
        }

    @staticmethod
    def solve_belt_friction(T1_slack: float, mu: float, wrap_angle_deg: float, drum_radius: float = 0.2) -> Dict[str, Any]:
        """
        Belt / Capstan friction: T2 / T1 = exp(mu * beta)
        """
        T1 = float(T1_slack)
        mu_val = float(mu)
        beta_rad = np.radians(float(wrap_angle_deg))
        R = float(drum_radius)

        if T1 <= 0 or mu_val <= 0 or beta_rad <= 0:
            raise ValueError("T1, mu, and wrap angle must be positive.")

        # Ratio T2 / T1
        ratio = float(np.exp(mu_val * beta_rad))
        T2 = T1 * ratio
        torque = (T2 - T1) * R

        return {
            'success': True,
            'T1_slack': round(T1, 4),
            'T2_tight': round(T2, 4),
            'tension_ratio_T2_T1': round(ratio, 4),
            'friction_torque_Nm': round(torque, 4),
            'wrap_angle_rad': round(float(beta_rad), 4),
            'total_turns': round(float(wrap_angle_deg / 360.0), 2)
        }
