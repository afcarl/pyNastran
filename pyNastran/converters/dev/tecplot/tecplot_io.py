from __future__ import print_function
from six import iteritems
from six.moves import range

import os
from numpy import arange, mean, amax, amin, array

import vtk
from vtk import vtkHexahedron, vtkQuad

from pyNastran.converters.dev.tecplot.tecplot_binary import TecplotReader, merge_tecplot_files


class TecplotIO(object):
    def __init__(self):
        pass

    def get_tecplot_wildcard_geometry_results_functions(self):
        data = ('Tecplot Binary FEBlock',
                'Tecplot Binary FEBlock (*.dat; *.plt; *.tec)', self.load_tecplot_geometry,
                None, None)
        return data

    #def removeOldGeometry(self, filename):
        #self._remove_old_cart3d_geometry(filename)

    def load_tecplot_geometry(self, tecplot_filename, dirname, plot=True):
        #key = self.caseKeys[self.iCase]
        #case = self.resultCases[key]

        skip_reading = self._remove_old_cart3d_geometry(tecplot_filename)
        if skip_reading:
            return

        if 0:
            fnames = os.listdir('time20000')
            fnames = [os.path.join('time20000', fname) for fname in fnames]
            model = merge_tecplot_files(fnames, tecplot_filename_out=None, log=self.log)
        else:
            model = TecplotReader(log=self.log, debug=False)
            model.read_tecplot(tecplot_filename)

        self.modelType = 'tecplot'
        #self.modelType = model.modelType
        self.nNodes = model.nnodes

        nodes = model.xyz
        points = vtk.vtkPoints()
        points.SetNumberOfPoints(self.nNodes)
        #self.gridResult.Allocate(self.nNodes, 1000)
        #vectorReselt.SetNumberOfComponents(3)
        #self.nidMap = {}
        #elem.SetNumberOfPoints(nNodes)

        assert nodes is not None
        nnodes = nodes.shape[0]

        nid = 0
        mmax = amax(nodes, axis=0)
        mmin = amin(nodes, axis=0)
        dim_max = (mmax - mmin).max()
        self.update_axes_length(dim_max)

        for i in range(nnodes):
            points.InsertPoint(nid, nodes[i, :])
            nid += 1

        is_surface = True
        # is_surface = False
        is_volume = not is_surface
        if is_surface:
            self.nElements = model.nelements
            free_faces = array(model.get_free_faces(), dtype='int32')# + 1
            nfaces = len(free_faces)
            elements = free_faces
            self.grid.Allocate(nfaces, 1000)

            for face in free_faces:
                elem = vtkQuad()
                epoints = elem.GetPointIds()
                epoints.SetId(0, face[0])
                epoints.SetId(1, face[1])
                epoints.SetId(2, face[2])
                epoints.SetId(3, face[3])
                self.grid.InsertNextCell(elem.GetCellType(), elem.GetPointIds())  #elem.GetCellType() = 5  # vtkTriangle

        elif is_volume:
            self.nElements = model.nelements
            elements = model.elements
            self.grid.Allocate(self.nElements, 1000)

            nelements = elements.shape[0]
            # elements -= 1
            for eid in range(nelements):
                elem = vtkHexahedron()
                node_ids = elements[eid, :]
                epoints = elem.GetPointIds()
                epoints.SetId(0, node_ids[0])
                epoints.SetId(1, node_ids[1])
                epoints.SetId(2, node_ids[2])
                epoints.SetId(3, node_ids[3])
                epoints.SetId(4, node_ids[4])
                epoints.SetId(5, node_ids[5])
                epoints.SetId(6, node_ids[6])
                epoints.SetId(7, node_ids[7])
                self.grid.InsertNextCell(elem.GetCellType(), elem.GetPointIds())  #elem.GetCellType() = 5  # vtkTriangle
        else:
            raise NotImplementedError()

        self.grid.SetPoints(points)
        #self.grid.GetPointData().SetScalars(self.gridResult)
        #print(dir(self.grid) #.SetNumberOfComponents(0))
        #self.grid.GetCellData().SetNumberOfTuples(1);
        #self.grid.GetCellData().SetScalars(self.gridResult)
        self.grid.Modified()
        if hasattr(self.grid, 'Update'):
            self.grid.Update()

        #self._create_cart3d_free_edegs(model, nodes, elements)


        # loadCart3dResults - regions/loads
        self.TurnTextOn()
        self.scalarBar.VisibilityOn()
        self.scalarBar.Modified()

        loads = []
        assert loads is not None
        if 'Mach' in loads:
            avgMach = mean(loads['Mach'])
            note = ':  avg(Mach)=%g' % avgMach
        else:
            note = ''
        self.iSubcaseNameMap = {1: ['Tecplot%s' % note, '']}
        cases = {}
        ID = 1

        form, cases = self._fill_tecplot_case(cases, ID, nodes, elements, model, is_surface)
        self._finish_results_io2(form, cases)

    def clear_tecplot(self):
        pass

    #def load_tecplot_results(self, cart3d_filename, dirname):
        #model = Cart3DReader(log=self.log, debug=False)
        #self.load_cart3d_geometry(cart3d_filename, dirname)

    def _fill_tecplot_case(self, cases, ID, nodes, elements, model, is_surface):
        #'x', 'y', 'z',
        result_names = ['rho', 'U', 'V', 'W', 'p']
        nelements = elements.shape[0]
        nnodes = nodes.shape[0]

        cases_new = []
        new = False

        #is_results = False
        is_results = True
        results_form = []

        if is_surface:
            element_id = 'FaceID'
        else:
            element_id = 'ElementID'

        geometry_form = [
            ('NodeID', 0, []),
            (element_id, 1, []),
            #('Region', 2, []),
        ]

        eids = arange(1, nelements + 1)
        nids = arange(1, nnodes + 1)


        if new:
            cases_new[0] = (ID, nids, 'NodeID', 'node', '%i')
            cases_new[1] = (ID, eids, element_id, 'centroid', '%i')
            #cases_new[2] = (ID, regions, 'Region', 'centroid', '%i')
        else:
            cases[(ID, 0, 'NodeID', 1, 'node', '%i')] = nids
            cases[(ID, 1, element_id, 1, 'centroid', '%i')] = eids
            #cases[(ID, 2, 'Region', 1, 'centroid', '%i')] = regions

        if is_results and len(model.results):
            i = 2
            for iresult, result_name in enumerate(result_names):
                nodal_data = model.results[:, iresult]
                if new:
                    cases_new[i] = (result, i, result_name, 1, 'node', '%.3f')
                else:
                    cases[(ID, i, result_name, 1, 'node', '%.3f')] = nodal_data
                results_form.append((result_name, i, []))
                i += 1
        form = [
            ('Geometry', None, geometry_form),
        ]
        if len(results_form):
            form.append(('Results', None, results_form))
        return form, cases