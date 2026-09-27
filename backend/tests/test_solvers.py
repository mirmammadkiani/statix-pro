import unittest
import numpy as np

from backend.modules.beams import BeamSolver
from backend.modules.trusses import TrussSolver
from backend.modules.vectors import VectorMechanics
from backend.modules.rigid_body import RigidBodyMechanics
from backend.modules.centroids import CentroidSolver
from backend.modules.inertia import InertiaSolver
from backend.modules.cables import CableSolver
from backend.modules.friction import FrictionSolver
from backend.modules.virtual_work import VirtualWorkSolver

class TestStaticsSolvers(unittest.TestCase):

    def test_beam_simply_supported(self):
        # Beam L=10 with P=100 kN at center x=5
        b = BeamSolver(10.0)
        b.add_support(0.0, 'pin')
        b.add_support(10.0, 'roller')
        b.add_point_load(5.0, -100.0)
        res = b.solve()
        self.assertTrue(res['success'])
        self.assertAlmostEqual(res['supports'][0]['Ry'], 50.0, places=1)
        self.assertAlmostEqual(res['supports'][1]['Ry'], 50.0, places=1)
        self.assertAlmostEqual(res['max_moment'], 250.0, places=1)

    def test_truss_solver(self):
        t = TrussSolver()
        t.add_node(0, 0)
        t.add_node(4, 0)
        t.add_node(2, 3)
        t.add_element(0, 1)
        t.add_element(0, 2)
        t.add_element(1, 2)
        t.add_support(0, 'pin')
        t.add_support(1, 'roller')
        t.add_load(2, 0, -10000)
        res = t.solve()
        self.assertTrue(res['success'])
        self.assertEqual(res['determinacy'], 'determinate')
        self.assertAlmostEqual(res['supports'][0]['Ry'], 5000.0, places=1)
        self.assertAlmostEqual(res['supports'][1]['Ry'], 5000.0, places=1)

    def test_vector_mechanics(self):
        forces = [{'fx': 30, 'fy': 40, 'fz': 0}]
        res = VectorMechanics.calculate_resultant(forces)
        self.assertAlmostEqual(res['magnitude'], 50.0, places=2)
        self.assertAlmostEqual(res['angle_2d_deg'], 53.13, places=1)

    def test_rigid_body_moment(self):
        res = RigidBodyMechanics.moment_about_point([0, 0, 0], [2, 0, 0], [0, 50, 0])
        self.assertAlmostEqual(res['moment_vector']['Mz'], 100.0, places=2)

    def test_centroid_solver(self):
        # 10x20 rectangle at (0,0)
        shapes = [{'type': 'rectangle', 'x': 0, 'y': 0, 'w': 10, 'h': 20, 'subtract': False}]
        res = CentroidSolver.solve_composite(shapes)
        self.assertAlmostEqual(res['x_bar'], 5.0, places=2)
        self.assertAlmostEqual(res['y_bar'], 10.0, places=2)
        self.assertAlmostEqual(res['total_area'], 200.0, places=2)

    def test_inertia_solver(self):
        # 10x20 rectangle
        shapes = [{'type': 'rectangle', 'x': 0, 'y': 0, 'w': 10, 'h': 20, 'subtract': False}]
        res = InertiaSolver.solve_composite_inertia(shapes)
        # Ix_bar = (b*h^3)/12 = 10 * 8000 / 12 = 6666.67
        self.assertAlmostEqual(res['centroidal_moments']['I_x_bar'], 6666.6667, places=1)

    def test_friction_slip_tip(self):
        # W=100, b=2, h=4, force at y=1.5, mu=0.5
        # slipping P = 0.5 * 100 = 50
        # tipping: P * 1.5 = 100 * 1 => P = 66.67
        res = FrictionSolver.block_slip_vs_tip(100, 2, 4, 1.5, 0, 0, 0.5)
        self.assertTrue(res['success'])
        self.assertAlmostEqual(res['P_slip_critical'], 50.0, places=1)
        self.assertAlmostEqual(res['P_tip_critical'], 66.6667, places=1)
        self.assertIn("لغزش", res['governing_mode'])

    def test_cables_parabolic(self):
        # L=100, h=10, w=20
        res = CableSolver.solve_parabolic_cable(100, 10, 20)
        # T0 = w*L^2 / (8*h) = 20 * 10000 / 80 = 2500
        self.assertAlmostEqual(res['min_tension_T0'], 2500.0, places=1)

if __name__ == '__main__':
    unittest.main()
