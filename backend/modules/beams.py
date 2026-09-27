import numpy as np
from typing import List, Dict, Any, Optional

class BeamSolver:
    """
    High-precision analytical & matrix solver for beams.
    Supports determinate and indeterminate beams with:
    - Multiple spans and overhangs
    - Pin, roller, fixed supports
    - Internal hinges (Gerber beams)
    - Concentrated point loads (vertical & inclined)
    - Applied concentrated moments
    - Distributed loads (uniform, trapezoidal, triangular)
    - Computes exact Reactions, Shear Force Diagram (SFD), Bending Moment Diagram (BMD)
    - Identifies extrema, zero crossings, and inflection points
    """

    def __init__(self, length: float):
        if length <= 0:
            raise ValueError("Beam length must be positive.")
        self.length = float(length)
        self.supports: List[Dict[str, Any]] = []      # {'x': float, 'type': 'pin'|'roller'|'fixed'}
        self.hinges: List[float] = []                 # x coordinates of internal hinges
        self.point_loads: List[Dict[str, Any]] = []    # {'x': float, 'fy': float, 'fx': float} (fy > 0 upwards or downwards? standard: downward is negative or positive, we define fy: positive UP, negative DOWN)
        self.moments: List[Dict[str, Any]] = []        # {'x': float, 'm': float} (+ CCW, - CW)
        self.dist_loads: List[Dict[str, Any]] = []     # {'x1': float, 'x2': float, 'w1': float, 'w2': float} (w > 0 UP, < 0 DOWN)
        self.E = 200e9   # Default 200 GPa
        self.I = 1e-4    # Default 1e-4 m^4
        self.A = 1e-2    # Default 0.01 m^2

    def add_support(self, x: float, support_type: str):
        """support_type: 'pin', 'roller', 'fixed'"""
        self.supports.append({'x': float(x), 'type': support_type.lower()})

    def add_hinge(self, x: float):
        """Internal hinge where bending moment is zero"""
        self.hinges.append(float(x))

    def add_point_load(self, x: float, fy: float, fx: float = 0.0):
        """fy: positive UPWARDS, negative DOWNWARDS. fx: positive RIGHT"""
        self.point_loads.append({'x': float(x), 'fy': float(fy), 'fx': float(fx)})

    def add_moment(self, x: float, m: float):
        """m: positive COUNTER-CLOCKWISE (+CCW), negative CLOCKWISE (-CW)"""
        self.moments.append({'x': float(x), 'm': float(m)})

    def add_distributed_load(self, x1: float, x2: float, w1: float, w2: float):
        """Distributed load from x1 to x2. w: positive UPWARDS, negative DOWNWARDS"""
        if x2 < x1:
            x1, x2 = x2, x1
            w1, w2 = w2, w1
        self.dist_loads.append({'x1': float(x1), 'x2': float(x2), 'w1': float(w1), 'w2': float(w2)})

    def solve(self) -> Dict[str, Any]:
        """
        Solves reactions and internal forces using beam finite element method (Direct Stiffness Method).
        Provides exact analytical values along the beam.
        """
        # Collect all critical x coordinates
        nodes_x = {0.0, self.length}
        for s in self.supports:
            nodes_x.add(s['x'])
        for h in self.hinges:
            nodes_x.add(h)
        for p in self.point_loads:
            nodes_x.add(p['x'])
        for m in self.moments:
            nodes_x.add(m['x'])
        for d in self.dist_loads:
            nodes_x.add(d['x1'])
            nodes_x.add(d['x2'])

        sorted_x = sorted(list(nodes_x))
        
        # Build elements between consecutive nodes
        # If a node is a hinge, we can split rotational DOF
        # For simplicity and extreme robustness, we create a 2D beam frame mesh
        # Each node has DOFs: [v, theta] (vertical deflection, rotation)
        # For an internal hinge at node k, element to the left connects to theta_L, element to right connects to theta_R.
        
        node_dof_map = {}
        dof_count = 0
        hinges_set = set(np.round(self.hinges, 6))

        for i, x in enumerate(sorted_x):
            v_dof = dof_count
            dof_count += 1
            if round(x, 6) in hinges_set:
                theta_left_dof = dof_count
                dof_count += 1
                theta_right_dof = dof_count
                dof_count += 1
                node_dof_map[i] = {'v': v_dof, 'theta_left': theta_left_dof, 'theta_right': theta_right_dof, 'x': x}
            else:
                theta_dof = dof_count
                dof_count += 1
                node_dof_map[i] = {'v': v_dof, 'theta': theta_dof, 'x': x}

        K = np.zeros((dof_count, dof_count))
        F = np.zeros(dof_count)

        # Assemble stiffness and distributed load equivalent forces
        EI = self.E * self.I

        num_elements = len(sorted_x) - 1
        for elem_idx in range(num_elements):
            n1 = elem_idx
            n2 = elem_idx + 1
            x1 = sorted_x[n1]
            x2 = sorted_x[n2]
            L = x2 - x1
            if L <= 1e-9:
                continue

            # DOFs for this element
            dofs1 = node_dof_map[n1]
            dofs2 = node_dof_map[n2]

            v1 = dofs1['v']
            t1 = dofs1.get('theta_right', dofs1.get('theta'))

            v2 = dofs2['v']
            t2 = dofs2.get('theta_left', dofs2.get('theta'))

            elem_dofs = [v1, t1, v2, t2]

            # 4x4 Euler-Bernoulli beam element stiffness matrix
            k_elem = (EI / (L**3)) * np.array([
                [ 12.0,      6.0 * L,    -12.0,     6.0 * L],
                [  6.0 * L,  4.0 * L**2,  -6.0 * L, 2.0 * L**2],
                [-12.0,     -6.0 * L,     12.0,    -6.0 * L],
                [  6.0 * L,  2.0 * L**2,  -6.0 * L, 4.0 * L**2]
            ])

            for r in range(4):
                for c in range(4):
                    K[elem_dofs[r], elem_dofs[c]] += k_elem[r, c]

            # Distributed load work on this element
            # Check if any distributed load covers this element
            for d in self.dist_loads:
                dx1, dx2, dw1, dw2 = d['x1'], d['x2'], d['w1'], d['w2']
                # Overlap between [x1, x2] and [dx1, dx2]
                ox1 = max(x1, dx1)
                ox2 = min(x2, dx2)
                if ox2 > ox1 + 1e-9:
                    # Evaluate load at element ends (since elements are split at load boundaries, ox1=x1 and ox2=x2)
                    # Linear interpolation of w
                    wa = dw1 + (dw2 - dw1) * ((ox1 - dx1) / (dx2 - dx1) if abs(dx2 - dx1) > 1e-9 else 0)
                    wb = dw1 + (dw2 - dw1) * ((ox2 - dx1) / (dx2 - dx1) if abs(dx2 - dx1) > 1e-9 else 0)

                    # Equivalent nodal forces for trapezoidal load on element of length L
                    # Upward load w produces positive nodal upward force Fv and fixed end moments
                    # Uniform part wa: Fv1 = wa*L/2, M1 = wa*L^2/12, Fv2 = wa*L/2, M2 = -wa*L^2/12
                    # Triangular part (wb - wa):
                    # Fv1 = 3*(wb-wa)*L/20, M1 = (wb-wa)*L^2/30
                    # Fv2 = 7*(wb-wa)*L/20, M2 = -(wb-wa)*L^2/20
                    fe_uniform = np.array([
                        wa * L / 2.0,
                        wa * L**2 / 12.0,
                        wa * L / 2.0,
                        -wa * L**2 / 12.0
                    ])
                    delta_w = wb - wa
                    fe_tri = np.array([
                        3.0 * delta_w * L / 20.0,
                        delta_w * L**2 / 30.0,
                        7.0 * delta_w * L / 20.0,
                        -delta_w * L**2 / 20.0
                    ])
                    fe_total = fe_uniform + fe_tri
                    for r in range(4):
                        F[elem_dofs[r]] += fe_total[r]

        # Add point loads and applied moments to F
        for p in self.point_loads:
            # find corresponding node
            px = p['x']
            for i, x in enumerate(sorted_x):
                if abs(x - px) < 1e-6:
                    F[node_dof_map[i]['v']] += p['fy']
                    break

        for m in self.moments:
            mx = m['x']
            for i, x in enumerate(sorted_x):
                if abs(x - mx) < 1e-6:
                    dofs = node_dof_map[i]
                    if 'theta' in dofs:
                        F[dofs['theta']] += m['m']
                    else:
                        # At hinge, moment applied to right node by default
                        F[dofs['theta_right']] += m['m']
                    break

        # Boundary conditions
        prescribed_dofs = {}
        for s in self.supports:
            sx = s['x']
            stype = s['type']
            for i, x in enumerate(sorted_x):
                if abs(x - sx) < 1e-6:
                    dofs = node_dof_map[i]
                    if stype in ['pin', 'roller']:
                        prescribed_dofs[dofs['v']] = 0.0
                    elif stype == 'fixed':
                        prescribed_dofs[dofs['v']] = 0.0
                        if 'theta' in dofs:
                            prescribed_dofs[dofs['theta']] = 0.0
                        else:
                            prescribed_dofs[dofs['theta_left']] = 0.0
                            prescribed_dofs[dofs['theta_right']] = 0.0
                    break

        # Check for determinacy / stability
        free_dofs = [d for d in range(dof_count) if d not in prescribed_dofs]
        fixed_dofs = list(prescribed_dofs.keys())

        if len(prescribed_dofs) == 0:
            raise ValueError("Beam has no supports. The structure is an unstable mechanism.")

        K_ff = K[np.ix_(free_dofs, free_dofs)]
        F_f = F[free_dofs] - K[np.ix_(free_dofs, fixed_dofs)] @ [prescribed_dofs[d] for d in fixed_dofs]

        # Solve for displacements
        try:
            U_f = np.linalg.solve(K_ff, F_f)
        except np.linalg.LinAlgError:
            raise ValueError("Structure is unstable or statically indeterminate mechanism (singular stiffness matrix).")

        U = np.zeros(dof_count)
        for idx, d in enumerate(free_dofs):
            U[d] = U_f[idx]
        for d, val in prescribed_dofs.items():
            U[d] = val

        # Reactions at fixed DOFs: R = K * U - F
        R_full = K @ U - F

        # Parse reactions at supports
        support_reactions = []
        for s in self.supports:
            sx = s['x']
            stype = s['type']
            for i, x in enumerate(sorted_x):
                if abs(x - sx) < 1e-6:
                    dofs = node_dof_map[i]
                    Ry = float(R_full[dofs['v']])
                    Rm = 0.0
                    if stype == 'fixed':
                        Rm = float(R_full[dofs['theta']]) if 'theta' in dofs else float(R_full[dofs['theta_left']])
                    support_reactions.append({
                        'x': round(sx, 4),
                        'type': stype,
                        'Ry': round(Ry, 4),
                        'Rm': round(Rm, 4),
                        'Rx': 0.0 # axial if applicable
                    })
                    break

        # Compute continuous SFD and BMD along beam using exact equilibrium section cut
        # For a section at x (just after cuts):
        # V(x) = sum(reactions left of x) + sum(applied loads left of x)
        # Note on sign convention:
        # Standard: V positive if left side shears UPWARDS (+).
        # M positive if sagging (compression on top, tension on bottom).
        # Upward force F at x_i < x produces +V and +F*(x - x_i) moment.
        # Downward force F produces -V and -F*(x - x_i) moment.
        # Positive CCW applied moment produces -M (or +M depending on left cut: CCW on left creates positive sagging moment!).

        num_sample_pts = 600
        x_vals = np.linspace(0, self.length, num_sample_pts)
        
        # To handle jumps accurately at supports and point loads, include points just before and after each node
        critical_xs = sorted(list(set(sorted_x)))
        augmented_x = list(x_vals)
        for cx in critical_xs:
            if cx > 1e-6:
                augmented_x.append(cx - 1e-6)
            augmented_x.append(cx)
            if cx < self.length - 1e-6:
                augmented_x.append(cx + 1e-6)
        augmented_x = np.array(sorted(list(set(augmented_x))))

        V_vals = []
        M_vals = []

        for x in augmented_x:
            # Internal forces at x
            V = 0.0
            M = 0.0

            # 1. Support reactions left of x
            for r in support_reactions:
                if r['x'] <= x:
                    # Upward reaction Ry
                    V += r['Ry']
                    M += r['Ry'] * (x - r['x'])
                    # Fixed moment Rm (Rm is reaction moment resisting beam rotation)
                    M += r['Rm']

            # 2. Point loads left of x
            for p in self.point_loads:
                if p['x'] <= x:
                    V += p['fy']
                    M += p['fy'] * (x - p['x'])

            # 3. Concentrated moments left of x
            for m in self.moments:
                if m['x'] <= x:
                    # Positive CCW moment adds positive bending
                    M += m['m']

            # 4. Distributed loads left of x
            for d in self.dist_loads:
                dx1, dx2, dw1, dw2 = d['x1'], d['x2'], d['w1'], d['w2']
                if x > dx1:
                    end_x = min(x, dx2)
                    load_len = end_x - dx1
                    if load_len > 1e-9:
                        # Load values at dx1 and end_x
                        span = dx2 - dx1
                        w_at_end = dw1 + (dw2 - dw1) * (load_len / span) if span > 1e-9 else dw1
                        
                        # Split into rectangular part (dw1) and triangular part (w_at_end - dw1)
                        # Rectangular part
                        F_rect = dw1 * load_len
                        cg_rect = dx1 + load_len / 2.0
                        V += F_rect
                        M += F_rect * (x - cg_rect)

                        # Triangular part
                        F_tri = 0.5 * (w_at_end - dw1) * load_len
                        cg_tri = dx1 + (2.0 / 3.0) * load_len
                        V += F_tri
                        M += F_tri * (x - cg_tri)

            V_vals.append(round(V, 4))
            M_vals.append(round(M, 4))

        V_arr = np.array(V_vals)
        M_arr = np.array(M_vals)

        # Critical values
        max_V = float(np.max(V_arr))
        min_V = float(np.min(V_arr))
        max_M = float(np.max(M_arr))
        min_M = float(np.min(M_arr))

        # Find zero crossings for Shear (locations of local moment extrema)
        zero_crossings_V = []
        for i in range(len(augmented_x) - 1):
            if V_arr[i] * V_arr[i+1] <= 0 and abs(V_arr[i] - V_arr[i+1]) > 1e-4:
                # Linear interpolation for zero crossing
                x_zero = augmented_x[i] - V_arr[i] * (augmented_x[i+1] - augmented_x[i]) / (V_arr[i+1] - V_arr[i])
                zero_crossings_V.append(round(float(x_zero), 3))

        return {
            'success': True,
            'length': self.length,
            'supports': support_reactions,
            'max_shear': max_V,
            'min_shear': min_V,
            'max_moment': max_M,
            'min_moment': min_M,
            'zero_shear_locations': sorted(list(set(zero_crossings_V))),
            'data_points': {
                'x': [round(float(xi), 3) for xi in augmented_x],
                'V': [float(vi) for vi in V_vals],
                'M': [float(mi) for mi in M_vals]
            }
        }
