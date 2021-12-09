#  ___________________________________________________________________________
#
#  Pyomo: Python Optimization Modeling Objects
#  Copyright 2017 National Technology and Engineering Solutions of Sandia, LLC
#  Under the terms of Contract DE-NA0003525 with National Technology and 
#  Engineering Solutions of Sandia, LLC, the U.S. Government retains certain 
#  rights in this software.
#  This software is distributed under the 3-clause BSD License.
#  ___________________________________________________________________________

import logging

import pyomo.common.unittest as unittest
from pyomo.common.dependencies import numpy_available
from pyomo.common.modeling import unique_component_name
from pyomo.environ import (
    Var, ConcreteModel, Reals, ExternalFunction,
    Objective, Constraint, sqrt, sin, SolverFactory, Block
    )
from pyomo.contrib.trustregion.interface import TRFInterface
from pyomo.contrib.trustregion.TRF import _trf_config

logger = logging.getLogger('pyomo.contrib.trustregion')


@unittest.skipIf(not numpy_available,
                 "Cannot test the trustregion solver without numpy")
class TestEFReplacement(unittest.TestCase):

    def setUp(self):
        self.m = ConcreteModel()
        self.m.z = Var(range(3), domain=Reals, initialize=2.)
        self.m.x = Var(range(2), initialize=2.)
        self.m.x[1] = 1.0

        def blackbox1(a, b):
            return sin(a - b)
        self.m.bb1 = ExternalFunction(blackbox1)

        def blackbox2(a, b):
            return a**2 + b**2
        self.m.bb2 = ExternalFunction(blackbox2)

        self.m.obj = Objective(
            expr=(self.m.z[0]-1.0)**2 + (self.m.z[0]-self.m.z[1])**2
            + (self.m.z[2]-1.0)**2 + (self.m.x[0]-1.0)**4
            + (self.m.x[1]-1.0)**6
        )
        self.m.c1 = Constraint(
            expr=(self.m.x[0] * self.m.z[0]**2
                  + self.m.bb1(self.m.x[0], self.m.x[1])
                  == 2*sqrt(2.0))
            )
        self.m.c2 = Constraint(
            expr=(self.m.z[2]**4 * self.m.z[1]**2
                  + self.m.bb2(self.m.z[1], self.m.z[2])
                  == 8+sqrt(2.0))
            )

    def test_EFReplacement(self):
        data = Block()
        self.m.add_component(unique_component_name(self.m, 'trf_data'), data)


@unittest.skipIf(not numpy_available,
                 "Cannot test the trustregion solver without numpy")
class TestTrustRegionInterface(unittest.TestCase):

    def setUp(self):
        self.m = ConcreteModel()
        self.m.z = Var(range(3), domain=Reals, initialize=2.)
        self.m.x = Var(range(2), initialize=2.)
        self.m.x[1] = 1.0

        def blackbox(a,b):
            return sin(a-b)

        self.m.bb = ExternalFunction(blackbox)

        self.m.obj = Objective(
            expr=(self.m.z[0]-1.0)**2 + (self.m.z[0]-self.m.z[1])**2
            + (self.m.z[2]-1.0)**2 + (self.m.x[0]-1.0)**4
            + (self.m.x[1]-1.0)**6
        )
        self.m.c1 = Constraint(
            expr=(self.m.x[0] * self.m.z[0]**2
                  + self.m.bb(self.m.x[0], self.m.x[1])
                  == 2*sqrt(2.0))
            )
        self.m.c2 = Constraint(
            expr=self.m.z[2]**4 * self.m.z[1]**2 + self.m.z[1] == 8+sqrt(2.0))
        self.config = _trf_config()
        self.ext_fcn_surrogate_map_rule = lambda comp,ef: 0
        self.interface = TRFInterface(self.m, self.ext_fcn_surrogate_map_rule,
                                      self.config)

    def test_initializeInterface(self):
        self.assertEqual(self.m, self.interface.original_model)
        self.assertEqual(self.config, self.interface.config)
        self.assertEqual(self.interface.basis_expression_rule,
                         self.ext_fcn_surrogate_map_rule)
        self.assertEqual('ipopt', self.interface.solver.name)

    def test_remove_ef_from_expr(self):
        model = self.m.clone()

    def test_replaceExternalFunctionsWithVariables(self):
        self.interface.replaceExternalFunctionsWithVariables()
        self.assertTrue(False)

    def test_execute_TRF(self):
        model = self.m.clone()
        #SolverFactory('trustregion').solve(model)



if __name__ == '__main__':
    unittest.main()