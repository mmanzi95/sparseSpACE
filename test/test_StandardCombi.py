import unittest
from sys import path
path.append('../src/')
from StandardCombi import *
import math
from Function import *

class TestStandardCombi(unittest.TestCase):
    def test_points(self):
        a = -3
        b = math.pi
        for d in range(2, 6):
            standardCombi = StandardCombi(np.ones(d)*a, np.ones(d)*b, grid=TrapezoidalGrid(np.ones(d)*a, np.ones(d)*b, d), print_output=False)
            for l in range(8 - d):
                for l2 in range(l+1):
                    f = FunctionLinear([10**i for i in range(d)])
                    #print(l,l2,d)
                    standardCombi.set_combi_parameters(l2, l, f)
                    standardCombi.check_combi_scheme()

    def test_integration(self):
        a = -3
        b = 7.3
        for d in range(2, 6):
            standardCombi = StandardCombi(np.ones(d)*a, np.ones(d)*b, grid=TrapezoidalGrid(np.ones(d)*a, np.ones(d)*b, d), print_output=False)
            for l in range(8 - d):
                for l2 in range(l+1):
                    f = FunctionLinear([10**i for i in range(d)])
                    scheme, error, integral  = standardCombi.perform_combi(l2, l, f, f.getAnalyticSolutionIntegral(np.ones(d)*a, np.ones(d)*b))
                    rel_error = error/f.getAnalyticSolutionIntegral(np.ones(d)*a, np.ones(d)*b)
                    self.assertAlmostEqual(rel_error, 0.0, 13)

    def test_interpolation(self):
        a = -3
        b = 7
        for d in range(2, 5):
            standardCombi = StandardCombi(np.ones(d)*a, np.ones(d)*b, grid=TrapezoidalGrid(np.ones(d)*a, np.ones(d)*b, d), print_output=False)
            for l in range(8 - d):
                for l2 in range(l+1):
                    f = FunctionLinear([10*i for i in range(d)])
                    standardCombi.set_combi_parameters(l2, l, f)
                    grid_coordinates = [np.linspace(a, b, 10) for _ in range(d)]
                    interpolated_points = standardCombi.interpolate_grid(grid_coordinates)
                    grid_points = list(get_cross_product(grid_coordinates))
                    for component_grid in standardCombi.scheme:
                        interpolated_points_grid = standardCombi.interpolate_points(grid_points, component_grid)
                        for i, p in enumerate(grid_points):
                            factor = abs(f(p)[0] if f(p)[0] != 0 else 1)
                            self.assertAlmostEqual((f(p)[0] - interpolated_points_grid[i][0]) / factor, 0, 13)
                    for i, p in enumerate(grid_points):
                        factor = abs(f(p)[0] if f(p)[0] != 0 else 1)
                        self.assertAlmostEqual((f(p)[0] - interpolated_points[i][0])/factor, 0, 13)
                    interpolated_points = standardCombi(grid_points)
                    for i, p in enumerate(grid_points):
                        factor = abs(f(p)[0] if f(p)[0] != 0 else 1)
                        self.assertAlmostEqual((f(p)[0] - interpolated_points[i][0])/factor, 0, 13)

    def test_number_of_points(self):
        a = -3
        b = 7.3
        for d in range(2, 6):
            standardCombi = StandardCombi(np.ones(d)*a, np.ones(d)*b, grid=TrapezoidalGrid(np.ones(d)*a, np.ones(d)*b, d), print_output=False)
            for l in range(8 - d):
                for l2 in range(l+1):
                    f = FunctionLinear([10**i for i in range(d)])
                    standardCombi.set_combi_parameters(l2, l, f)
                    points, weights = standardCombi.get_points_and_weights()
                    self.assertEqual(len(points), standardCombi.get_total_num_points(distinct_function_evals=False))
                    self.assertEqual(len(points), len(weights))
                    for component_grid in standardCombi.scheme:
                        points, weights = standardCombi.get_points_and_weights_component_grid(component_grid.levelvector, None)
                        self.assertEqual(len(points), np.prod(standardCombi.grid.levelToNumPoints(component_grid.levelvector)))
                        self.assertEqual(standardCombi.get_num_points_component_grid(component_grid.levelvector, False, None), np.prod(standardCombi.grid.levelToNumPoints(component_grid.levelvector)))


if __name__ == '__main__':
    unittest.main()