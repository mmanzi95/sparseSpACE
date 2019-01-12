from spatiallyAdaptiveBase import *


class SpatiallyAdaptiveExtendScheme(SpatiallyAdaptivBase):
    def __init__(self, a, b, number_of_refinements_before_extend=1, grid=None, no_initial_splitting=False,
                 version=0, dim_adaptive=False, automatic_extend_split=False):
        # there are three different version that coarsen grids slightly different
        # version 0 coarsen as much as possible while extending and adding only new points in regions where it is supposed to
        # version 1 coarsens less and also adds moderately many points in non refined regions which might result in a more balanced configuration
        # version 2 coarsen fewest and adds a bit more points in non refinded regions but very similar to version 1
        assert 2 >= version >= 0
        self.version = version
        SpatiallyAdaptivBase.__init__(self, a, b, grid)
        self.noInitialSplitting = no_initial_splitting
        self.numberOfRefinementsBeforeExtend = number_of_refinements_before_extend
        self.refinements_for_recalculate = 100
        self.dim_adaptive = dim_adaptive
        self.automatic_extend_split = automatic_extend_split

    # draw a visual representation of refinement tree
    def draw_refinement(self, filename=None):
        plt.rcParams.update({'font.size': 32})
        dim = self.dim
        if dim > 2:
            print("Refinement can only be printed in 2D")
            return
        fig = plt.figure(figsize=(20, 20))
        ax2 = fig.add_subplot(111, aspect='equal')
        for i in self.refinement.get_objects():
            startx = i.start[0]
            starty = i.start[1]
            endx = i.end[0]
            endy = i.end[1]
            ax2.add_patch(
                patches.Rectangle(
                    (startx, starty),
                    endx - startx,
                    endy - starty,
                    fill=False  # remove background
                )
            )
        if filename is not None:
            plt.savefig(filename, bbox_inches='tight')
        plt.show()
        return fig

    # returns the points of a single component grid with refinement
    def get_points_component_grid(self, levelvec, numSubDiagonal):
        assert (numSubDiagonal < self.dim)
        points_array = []
        for area in self.refinement.get_objects():
            start = area.start
            end = area.end
            level_interval, is_null = self.coarsen_grid(levelvec, area, numSubDiagonal)
            self.grid.setCurrentArea(start, end, level_interval)
            points = self.grid.getPoints()
            points_array.extend(points)
        return points_array

    def get_points_and_weights_component_grid(self, levelvec, numSubDiagonal):
        assert (numSubDiagonal < self.dim)
        points_array = []
        weights_array = []
        for area in self.refinement.get_objects():
            start = area.start
            end = area.end
            level_interval, is_null = self.coarsen_grid(levelvec, area, numSubDiagonal)
            self.grid.setCurrentArea(start, end, level_interval)
            points, weights = self.grid.get_points_and_weights()
            points_array.extend(points)
            weights_array.extend(weights)
        return points_array, weights_array

    # returns the points of a single component grid with refinement
    def get_points_component_grid_not_null(self, levelvec, numSubDiagonal):
        assert (numSubDiagonal < self.dim)
        array2 = []
        for area in self.refinement.get_objects():
            start = area.start
            end = area.end
            level_interval, is_null = self.coarsen_grid(levelvec, area, numSubDiagonal)
            if not is_null:
                self.grid.setCurrentArea(start, end, level_interval)
                points = self.grid.getPoints()
                array2.extend(points)
                # print("considered", levelvec, level_interval, area.start, area.end, area.coarseningValue)
            # else:
            # print("not considered", levelvec, level_interval, area.start, area.end, area.coarseningValue)
        return array2

    # optimized adaptive refinement refine multiple cells in close range around max variance (here set to 10%)
    def coarsen_grid(self, levelvector, area, num_sub_diagonal, print_point=None):
        start = area.start
        end = area.end
        coarsening = area.coarseningValue
        temp = list(levelvector)
        coarsening_save = coarsening
        area_is_null = False
        if self.version == 0:

            maxLevel = max(temp)
            temp2 = list(reversed(sorted(list(temp))))
            if temp2[0] - temp2[1] < coarsening:
                while coarsening > 0:
                    maxLevel = max(temp)
                    if maxLevel == self.lmin[0]:  # we assume here that lmin is equal everywhere
                        break
                    for d in range(self.dim):
                        if temp[d] == maxLevel:
                            temp[d] -= 1
                            coarsening -= 1
                            break
                area_is_null = True
            else:
                for d in range(self.dim):
                    if temp[d] == maxLevel:
                        temp[d] -= coarsening
                        break
                if area.is_already_calculated(tuple(temp), tuple(levelvector)):
                    area_is_null = True
                else:
                    area.add_level(tuple(temp), tuple(levelvector))
        else:
            while coarsening > 0:
                maxLevel = max(temp)
                if maxLevel == self.lmin[0]:  # we assume here that lmin is equal everywhere
                    break
                occurences_of_max = 0
                for i in temp:
                    if i == maxLevel:
                        occurences_of_max += 1
                is_top_diag = num_sub_diagonal == 0
                if self.version == 1:
                    no_forward_problem = coarsening_save >= self.lmax[0] + self.dim - 1 - maxLevel - (
                            self.dim - 2) - maxLevel + 1
                    do_coarsen = no_forward_problem and coarsening >= occurences_of_max - is_top_diag
                else:
                    no_forward_problem = coarsening_save >= self.lmax[0] + self.dim - 1 - maxLevel - (
                            self.dim - 2) - maxLevel + 2
                    do_coarsen = no_forward_problem and coarsening >= occurences_of_max
                if do_coarsen:
                    for d in range(self.dim):
                        if temp[d] == maxLevel:
                            temp[d] -= 1
                            coarsening -= 1
                else:
                    break
        level_coarse = [temp[d] - self.lmin[d] + int(self.noInitialSplitting) for d in range(len(temp))]
        if print_point is not None:
            if all([start[d] <= print_point[d] and end[d] >= print_point[d] for d in range(self.dim)]):
                print("Level: ", levelvector, "Coarsened level:", level_coarse, coarsening_save, start, end)
        return level_coarse, area_is_null

    def initialize_refinement(self):
        if self.dim_adaptive:
            self.combischeme.init_adaptive_combi_scheme(self.lmax, self.lmin)
        if self.noInitialSplitting:
            assert False
            new_refinement_object = RefinementObjectExtendSplit(np.array(self.a), np.array(self.b), self.grid,
                                                                self.numberOfRefinementsBeforeExtend, 0, 0, automatic_extend_split=self.automatic_extend_split)
            self.refinement = RefinementContainer([new_refinement_object], self.dim, self.errorEstimator)
        else:
            parent_integral = self.grid.integrate(self.f, np.zeros(self.dim, dtype=int), self.a, self.b)
            parent = RefinementObjectExtendSplit(np.array(self.a), np.array(self.b), self.grid,
                                                                 self.numberOfRefinementsBeforeExtend, None, 0,
                                                                 0, automatic_extend_split=self.automatic_extend_split)
            parent.set_integral(parent_integral)
            new_refinement_objects = parent.split_area_arbitrary_dim()
            self.refinement = RefinementContainer(new_refinement_objects, self.dim, self.errorEstimator)
        if self.errorEstimator is None:
            self.errorEstimator = ErrorCalculatorExtendSplit()

    def evaluate_area(self, f, area, levelvec):
        num_sub_diagonal = (self.lmax[0] + self.dim - 1) - np.sum(levelvec)
        level_for_evaluation, is_null = self.coarsen_grid(levelvec, area, num_sub_diagonal)
        #print(level_for_evaluation, area.coarseningValue)
        if is_null:
            return 0, None, 0
        else:
            return self.grid.integrate(f, level_for_evaluation, area.start, area.end), None, np.prod(
                self.grid.levelToNumPoints(level_for_evaluation))

    def do_refinement(self, area, position):
        if self.automatic_extend_split:
            if area.extend_parent_integral is None:
                area.extend_parent_integral = self.get_parent_extend_integral(area)
            if area.split_parent_integral is None:
                area.split_parent_integral = self.get_parent_split_integral2(area)

        lmax_change = self.refinement.refine(position)
        if lmax_change != None:
            self.lmax = [self.lmax[d] + lmax_change[d] for d in range(self.dim)]
            print("New scheme")
            self.scheme = self.combischeme.getCombiScheme(self.lmin[0], self.lmax[0], self.dim)
            return True
        return False

    def calc_error(self, objectID, f):
        area = self.refinement.getObject(objectID)
        #print(area.parent.integral)
        if area.parent_integral is None:
            #integral1 = self.get_parent_split_integral(area, True)
            integral2 = self.get_parent_split_integral2(area,True)
            #if integral1 is not None and abs(integral1 - area.integral) < abs(integral2 - area.integral):
            #    area.parent_integral = integral1
            #else:
            #    area.parent_integral = integral2
            area.parent_integral = integral2
        if area.switch_to_parent_estimation:
            area.sum_siblings = 0.0
            i = 0
            for child in area.parent.children:
                if child.integral is not None:
                    area.sum_siblings += child.integral
                    i += 1
            # print(i)
            assert i == 2 ** self.dim  # we always have 2**dim children
            # self.error_split = abs(self.split_parent_integral - sum_siblings) / (
            #            2 ** (self.dim) / 2 * 2 ** (self.depth))  # 2**self.dim)
        self.refinement.calc_error(objectID, f)
        #print("Area points and error:",area.num_points, area.error)

    def get_parent_split_integral2(self, area, only_one_extend=False):
        area_parent = area.parent
        parent_integral = 0
        area_parent.coarseningValue = area.coarseningValue
        area_parent.levelvec_dict = {}
        complete_integral = 0.0
        area.num_points_split_parent = 0.0
        if not area.switch_to_parent_estimation:
            lmax = self.lmax[0] - 1
            lmin = self.lmin[0]
            while True:
                area_parent = area.parent
                parent_integral = 0
                area_parent.coarseningValue = area.coarseningValue
                area_parent.levelvec_dict = {}
                complete_integral = 0.0
                area.num_points_split_parent = 0.0
                lmax += 1
                scheme = self.combischeme.getCombiScheme(lmin,lmax,self.dim,do_print=False)
                for ss in scheme:
                    if self.grid.isNested():
                        factor = ss[1]
                    else:
                        factor = 1
                    num_sub_diagonal = (self.lmax[0] + self.dim - 1) - np.sum(ss[0])
                    level_for_evaluation, is_null = self.coarsen_grid(ss[0], area_parent, num_sub_diagonal)
                    if not is_null:
                        self.grid.setCurrentArea(area_parent.start, area_parent.end, level_for_evaluation)
                        points, weights = self.grid.get_points_and_weights()
                        #print(points, weights, area.start, area.end, area.parent.start, area.parent.end)
                        for i, p in enumerate(points):
                            if self.point_in_area(p,area):
                                #print("point:", p, "f_value", self.f(p),"weight", weights[i], "value", self.f(p) * weights[i] * self.get_point_factor(p, area, area_parent) * ss[1], "area" ,area.start, area.end, self.get_point_factor(p, area, area_parent))
                                parent_integral += self.f(p) * weights[i] * self.get_point_factor(p, area, area_parent) * ss[1]
                                area.num_points_split_parent += factor #* self.get_point_factor(p,area,area_parent)
                            #complete_integral += self.f(p) * weights[i] * ss[1]

                #print(parent_integral, complete_integral / 2**self.dim)
                area_parent.coarseningValue = area.coarseningValue + 1
                area_parent.levelvec_dict = {}
                area.num_points_reference = 0.0
                for ss in self.scheme:
                    if self.grid.isNested():
                        factor = ss[1]
                    else:
                        factor = 1
                    num_sub_diagonal = (self.lmax[0] + self.dim - 1) - np.sum(ss[0])
                    level_for_evaluation, is_null = self.coarsen_grid(ss[0], area_parent, num_sub_diagonal)
                    if not is_null:
                        self.grid.setCurrentArea(area_parent.start, area_parent.end, level_for_evaluation)
                        points, weights = self.grid.get_points_and_weights()
                        #print(points)
                        for p in points:
                            if self.point_in_area(p,area):
                                #print(p)
                                area.num_points_reference += factor #* self.get_point_factor(p,area,area_parent)
                                #print(area.num_points_split_parent)
                if only_one_extend or 3*area.num_points_split_parent > area.num_points_extend_parent:
                    break

        else:
            for ss in self.scheme:
                if self.grid.isNested():
                    factor = ss[1]
                else:
                    factor = 1
                area_integral, partial_integrals, evaluations = self.evaluate_area(self.f, area_parent, ss[0])
                complete_integral += area_integral * ss[1]
                area.num_points_split_parent += evaluations * factor

            parent_integral = complete_integral #/ 2**self.dim

            area_parent.coarseningValue = area.coarseningValue + 1
            area_parent.levelvec_dict = {}
            area.num_points_reference = 0.0

            for ss in self.scheme:
                if self.grid.isNested():
                    factor = ss[1]
                else:
                    factor = 1
                area_integral, partial_integrals, evaluations = self.evaluate_area(self.f, area_parent, ss[0])
                area.num_points_reference += evaluations * factor

        #if area.num_points_split_parent == 0:
        #    area.switch_to_parent_estimation = True
        #print("Parent integral:", parent_integral, area.integral, complete_integral, complete_integral - parent_integral)
        return parent_integral

    def get_parent_split_integral(self, area, only_one_extend=False):
        area_parent = area.parent
        parent_integral = 0
        area_parent.coarseningValue = area.coarseningValue
        area_parent.levelvec_dict = {}
        complete_integral = 0.0
        if area.switch_to_parent_estimation:
            return self.get_parent_split_integral2(area)
            """
            for ss in self.scheme:
                if self.grid.isNested():
                    factor = ss[1]
                else:
                    factor = 1
                area_integral, partial_integrals, evaluations = self.evaluate_area(self.f, area_parent, ss[0])
                complete_integral += area_integral * ss[1]
                area.num_points_split_parent += evaluations * factor

            parent_integral = complete_integral

            area_parent.coarseningValue = area.coarseningValue + 1
            area_parent.levelvec_dict = {}
            area.num_points_reference = 0.0

            for ss in self.scheme:
                if self.grid.isNested():
                    factor = ss[1]
                else:
                    factor = 1
                area_integral, partial_integrals, evaluations = self.evaluate_area(self.f, area_parent, ss[0])
                area.num_points_reference += evaluations * factor
            """
        else:
            area.num_points_split_parent = 0.0
            lmax = self.lmax[0] - 1
            lmin = self.lmin[0]
            i=0
            while True:
                area.num_points_split_parent = 0.0
                area_parent = area.parent
                parent_integral = 0
                area_parent.coarseningValue = area.coarseningValue
                area_parent.levelvec_dict = {}
                complete_integral = 0.0
                lmax += 1
                i += 1
                scheme = self.combischeme.getCombiScheme(lmin,lmax,self.dim,do_print=False)
                for ss in scheme:
                    if self.grid.isNested():
                        factor = ss[1]
                    else:
                        factor = 1
                    num_sub_diagonal = (lmax + self.dim - 1) - np.sum(ss[0])
                    level_for_evaluation, is_null = self.coarsen_grid(ss[0], area_parent, num_sub_diagonal)
                    if not is_null:
                        boundary_save = self.grid.get_boundaries()
                        self.grid.set_boundaries([True]*self.dim)
                        self.grid.setCurrentArea(area_parent.start, area_parent.end, level_for_evaluation)
                        self.grid.set_boundaries(boundary_save)
                        corner_points = list(
                            zip(*[g.ravel() for g in np.meshgrid(*[self.grid.coordinate_array[d] for d in range(self.dim)])]))
                        values = np.array([self.f(p) if self.grid.point_not_zero(p) else 0.0 for p in corner_points])
                        values = values.reshape(*[self.grid.numPointsWithBoundary[d] for d in reversed(range(self.dim))])
                        values = np.transpose(values)
                        corner_points_grid = [self.grid.coordinate_array[d] for d in range(self.dim)]
                        self.grid.setCurrentArea(area.start, area.end, level_for_evaluation)
                        points, weights = self.grid.get_points_and_weights()
                        interpolated_values = interpn(corner_points_grid, values, points, method='linear')
                        #print(area.start, area.end, points,interpolated_values, weights)
                        parent_integral += sum([interpolated_values[i] * weights[i] for i in range(len(interpolated_values))]) * ss[1]
                        #print(corner_points)
                        for p in corner_points:
                            if self.point_in_area(p,area) and self.grid.point_not_zero(p):
                                area.num_points_split_parent += factor #* self.get_point_factor(p,area,area_parent)
                print("Current estimate:", parent_integral, "with number of points:", area.num_points_split_parent, "Analytic Solution:", self.f.getAnalyticSolutionIntegral(area.start,area.end))
                if only_one_extend or i > 3 and area.num_points_split_parent > 0:
                    break

            area_parent.coarseningValue = area.coarseningValue + 1
            area_parent.levelvec_dict = {}
            area.num_points_reference = 0.0
            for ss in self.scheme:
                if self.grid.isNested():
                    factor = ss[1]
                else:
                    factor = 1
                num_sub_diagonal = (self.lmax[0] + self.dim - 1) - np.sum(ss[0])
                level_for_evaluation, is_null = self.coarsen_grid(ss[0], area_parent, num_sub_diagonal)
                if not is_null:
                    self.grid.setCurrentArea(area_parent.start, area_parent.end, level_for_evaluation)
                    points, weights = self.grid.get_points_and_weights()
                    for p in points:
                        if self.point_in_area(p,area):
                            area.num_points_reference += factor #* self.get_point_factor(p, area, area_parent)
            '''
            area_parent.levelvec_dict = {}
            area_parent.coarseningValue = area.coarseningValue + 1
            area.refinement_reference = 0.0
            for ss in self.scheme:
                area_integral, partial_integrals, evaluations = self.evaluate_area(self.f, area_parent, ss[0])
                area.refinement_reference += area_integral * ss[1]
            '''
            #print("Parent integral:", parent_integral, area.integral, complete_integral, complete_integral - parent_integral)
            #parent_integral2 = self.get_parent_split_integral2(area)
        return parent_integral


    def point_in_area(self, point, area):
        for d in range(self.dim):
            if point[d] < area.start[d] or point[d] > area.end[d]:
                return False
        return True

    def get_point_factor(self, point, area, area_parent):
        factor = 1.0
        for d in range(self.dim):
            if (point[d] == area.start[d] or point[d] == area.end[d]) and not(point[d] == area_parent.start[d] or point[d] == area_parent.end[d]):
                factor /= 2.0
        return factor

    def get_parent_extend_integral(self, area):

        if area.switch_to_parent_estimation:
            area.num_points_extend_parent = 0.0
            extend_parent_integral = 0.0
            i = 0
            for area_eval in area.parent.children:
                area_eval.levelvec_dict = {}
                area_eval.coarseningValue += 1
                i += 1
                for ss in self.scheme:
                    if self.grid.isNested():
                        factor = ss[1]
                    else:
                        factor = 1
                    area_integral, partial_integrals, evaluations = self.evaluate_area(self.f, area_eval, ss[0])
                    #print(area_integral, partial_integrals, evaluations, area_eval.start, area_eval.end, ss[0])
                    area.num_points_extend_parent += evaluations * factor
                    extend_parent_integral += area_integral * ss[1]
                area_eval.coarseningValue -= 1
            assert i == 2**self.dim
        else:
            area_eval = area
            extend_parent_integral = 0.0
            area_eval.levelvec_dict = {}
            area_eval.coarseningValue +=  1
            area_eval.num_points_extend_parent = 0.0
            for ss in self.scheme:
                if self.grid.isNested():
                    factor = ss[1]
                else:
                    factor = 1
                area_integral, partial_integrals, evaluations = self.evaluate_area(self.f, area_eval, ss[0])
                #print(area_integral, partial_integrals, evaluations, area_eval.start, area_eval.end, ss[0])
                area.num_points_extend_parent += evaluations * factor
                extend_parent_integral += area_integral * ss[1]
            area_eval.coarseningValue -= 1
        return extend_parent_integral

    def get_parent_extend_integral2(self, area):
        lmax = self.lmax[0] - 1
        area.num_points_extend_parent = 0
        print(area.num_points_split_parent, area.split_parent_integral)
        while area.num_points_extend_parent <= area.num_points_split_parent:
            lmax += 1
            scheme = self.combischeme.getCombiScheme(self.lmin[0], lmax, self.dim, do_print=False)
            if area.switch_to_parent_estimation:
                area.num_points_extend_parent = 0.0
                extend_parent_integral = 0.0
                i = 0
                for area_eval in area.parent.children:
                    area_eval.levelvec_dict = {}
                    area_eval.coarseningValue += 1
                    i += 1
                    for ss in scheme:
                        if self.grid.isNested():
                            factor = ss[1]
                        else:
                            factor = 1
                        area_integral, partial_integrals, evaluations = self.evaluate_area(self.f, area_eval, ss[0])
                        #print(area_integral, partial_integrals, evaluations, area_eval.start, area_eval.end, ss[0])
                        area.num_points_extend_parent += evaluations * factor
                        extend_parent_integral += area_integral * ss[1]
                    area_eval.coarseningValue -= 1
                assert i == 2**self.dim
            else:
                area_eval = area
                extend_parent_integral = 0.0
                area_eval.levelvec_dict = {}
                area_eval.coarseningValue += 1
                area_eval.num_points_extend_parent = 0.0
                for ss in scheme:
                    if self.grid.isNested():
                        factor = ss[1]
                    else:
                        factor = 1
                    area_integral, partial_integrals, evaluations = self.evaluate_area(self.f, area_eval, ss[0])
                    #print(area_integral, partial_integrals, evaluations, area_eval.start, area_eval.end, ss[0])
                    area.num_points_extend_parent += evaluations * factor
                    extend_parent_integral += area_integral * ss[1]
                area_eval.coarseningValue -= 1
        return extend_parent_integral