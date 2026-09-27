import numpy as np
from typing import List, Dict, Any, Tuple

class TrussSolver:
    """
    Direct Stiffness Matrix FEM solver for 2D Trusses.
    Solves for:
    - Nodal displacements
    - Support reactions
    - Member axial forces (Tension: +, Compression: -)
    - Zero-force members
    - Static determinacy (m + r = 2j)
    """

    def __init__(self):
        self.nodes: List[Dict[str, float]] = []        # [{'x': float, 'y': float}, ...]
        self.elements: List[Dict[str, Any]] = []      # [{'node1': int, 'node2': int, 'A': float, 'E': float}]
        self.supports: Dict[int, List[bool]] = {}     # {node_idx: [fix_x, fix_y]}
        self.loads: Dict[int, List[float]] = {}        # {node_idx: [fx, fy]}
        self.default_E = 200e9                         # 200 GPa
        self.default_A = 0.0025                        # 25 cm^2 = 0.0025 m^2

    def add_node(self, x: float, y: float) -> int:
        idx = len(self.nodes)
        self.nodes.append({'x': float(x), 'y': float(y)})
        return idx

    def add_element(self, node1: int, node2: int, A: float = None, E: float = None) -> int:
        if node1 == node2:
            raise ValueError("Element must connect two distinct nodes.")
        idx = len(self.elements)
        self.elements.append({
            'node1': int(node1),
            'node2': int(node2),
            'A': float(A if A is not None else self.default_A),
            'E': float(E if E is not None else self.default_E)
        })
        return idx

    def add_support(self, node_idx: int, support_type: str):
        """
        support_type:
        - 'pin': fixes x and y
        - 'roller_x': fixes y (rolls in x)
        - 'roller_y': fixes x (rolls in y)
        - 'fixed': fixes x and y
        """
        st = support_type.lower()
        if st in ['pin', 'fixed']:
            self.supports[int(node_idx)] = [True, True]
        elif st in ['roller', 'roller_x']:
            self.supports[int(node_idx)] = [False, True]
        elif st == 'roller_y':
            self.supports[int(node_idx)] = [True, False]
        else:
            raise ValueError(f"Unknown support type: {support_type}")

    def add_load(self, node_idx: int, fx: float, fy: float):
        """Concentrated force applied to node. fx: right +, fy: up +"""
        node_idx = int(node_idx)
        if node_idx not in self.loads:
            self.loads[node_idx] = [0.0, 0.0]
        self.loads[node_idx][0] += float(fx)
        self.loads[node_idx][1] += float(fy)

    def solve(self) -> Dict[str, Any]:
        num_nodes = len(self.nodes)
        num_elems = len(self.elements)
        if num_nodes < 2 or num_elems < 1:
            raise ValueError("Truss must contain at least 2 nodes and 1 element.")

        total_dofs = 2 * num_nodes
        K_global = np.zeros((total_dofs, total_dofs))
        F_global = np.zeros(total_dofs)

        # Apply external nodal loads to F_global
        for node_idx, (fx, fy) in self.loads.items():
            F_global[2 * node_idx] += fx
            F_global[2 * node_idx + 1] += fy

        # Count reactions
        num_reactions = 0
        restrained_dofs = []
        for node_idx, fixes in self.supports.items():
            if fixes[0]:
                restrained_dofs.append(2 * node_idx)
                num_reactions += 1
            if fixes[1]:
                restrained_dofs.append(2 * node_idx + 1)
                num_reactions += 1

        # Check determinacy: m + r vs 2j
        m = num_elems
        r = num_reactions
        j = num_nodes
        determinacy = "determinate"
        if m + r < 2 * j:
            determinacy = "unstable_mechanism"
        elif m + r > 2 * j:
            determinacy = f"indeterminate_degree_{m + r - 2 * j}"

        # Element stiffness matrices and lengths
        elem_info = []
        for i, el in enumerate(self.elements):
            n1 = el['node1']
            n2 = el['node2']
            x1, y1 = self.nodes[n1]['x'], self.nodes[n1]['y']
            x2, y2 = self.nodes[n2]['x'], self.nodes[n2]['y']

            dx = x2 - x1
            dy = y2 - y1
            L = np.sqrt(dx**2 + dy**2)
            if L <= 1e-9:
                raise ValueError(f"Element {i} has zero length.")

            c = dx / L
            s = dy / L

            k_local = (el['E'] * el['A'] / L) * np.array([
                [ c*c,  c*s, -c*c, -c*s],
                [ c*s,  s*s, -c*s, -s*s],
                [-c*c, -c*s,  c*c,  c*s],
                [-c*s, -s*s,  c*s,  s*s]
            ])

            dofs = [2 * n1, 2 * n1 + 1, 2 * n2, 2 * n2 + 1]
            for r_idx in range(4):
                for c_idx in range(4):
                    K_global[dofs[r_idx], dofs[c_idx]] += k_local[r_idx, c_idx]

            elem_info.append({'L': L, 'c': c, 's': s, 'dofs': dofs, 'A': el['A'], 'E': el['E']})

        # Partition DOFs
        free_dofs = [d for d in range(total_dofs) if d not in restrained_dofs]
        if len(free_dofs) == 0:
            raise ValueError("All DOFs are restrained.")

        K_ff = K_global[np.ix_(free_dofs, free_dofs)]
        F_f = F_global[free_dofs]

        try:
            U_f = np.linalg.solve(K_ff, F_f)
        except np.linalg.LinAlgError:
            raise ValueError("Structure is unstable (geometric mechanism). Check supports and member configuration.")

        U_global = np.zeros(total_dofs)
        for idx, d in enumerate(free_dofs):
            U_global[d] = U_f[idx]

        # Calculate Reactions: R = K * U - F
        R_global = K_global @ U_global - F_global

        support_results = []
        for node_idx, fixes in self.supports.items():
            rx = float(R_global[2 * node_idx]) if fixes[0] else 0.0
            ry = float(R_global[2 * node_idx + 1]) if fixes[1] else 0.0
            support_results.append({
                'node': node_idx,
                'x': self.nodes[node_idx]['x'],
                'y': self.nodes[node_idx]['y'],
                'Rx': round(rx, 4),
                'Ry': round(ry, 4),
                'R_magnitude': round(float(np.sqrt(rx**2 + ry**2)), 4)
            })

        # Calculate internal forces in each member
        # Force P = (EA/L) * [-c, -s, c, s] * [u1, v1, u2, v2]^T
        # Positive = Tension, Negative = Compression
        member_results = []
        for i, info in enumerate(elem_info):
            dofs = info['dofs']
            u_elem = U_global[dofs]
            c, s, L, A, E = info['c'], info['s'], info['L'], info['A'], info['E']

            delta_L = (u_elem[2] - u_elem[0]) * c + (u_elem[3] - u_elem[1]) * s
            axial_force = (E * A / L) * delta_L
            stress = axial_force / A

            # Check zero-force member (threshold 1e-4)
            is_zero_force = abs(axial_force) < 1e-3

            if is_zero_force:
                kind = "Zero-Force"
                force_type = "ZERO"
            elif axial_force > 0:
                kind = "Tension"
                force_type = "T"
            else:
                kind = "Compression"
                force_type = "C"

            member_results.append({
                'element_id': i,
                'node1': self.elements[i]['node1'],
                'node2': self.elements[i]['node2'],
                'length': round(float(L), 4),
                'force': round(float(axial_force), 4),
                'abs_force': round(float(abs(axial_force)), 4),
                'stress_MPa': round(float(stress / 1e6), 4),
                'state': kind,
                'type': force_type
            })

        # Deformed node positions (scaled for visual clarity)
        deformed_nodes = []
        for i, n in enumerate(self.nodes):
            ux = float(U_global[2 * i])
            uy = float(U_global[2 * i + 1])
            deformed_nodes.append({
                'node_id': i,
                'x': n['x'],
                'y': n['y'],
                'ux': ux,
                'uy': uy
            })

        return {
            'success': True,
            'determinacy': determinacy,
            'num_nodes': num_nodes,
            'num_elements': num_elems,
            'num_reactions': num_reactions,
            'nodes': deformed_nodes,
            'members': member_results,
            'supports': support_results
        }
