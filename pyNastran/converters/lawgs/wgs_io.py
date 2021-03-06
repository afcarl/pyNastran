"""
Defines the GUI IO file for LaWGS.
"""
from __future__ import print_function
from collections import OrderedDict

import vtk
from vtk import vtkQuad
from numpy import array, arange, cross
from pyNastran.converters.lawgs.wgs_reader import read_lawgs
from pyNastran.gui.gui_objects.gui_result import GuiResult


class LaWGS_IO(object):
    def __init__(self, parent):
        self.parent = parent

    def get_lawgs_wildcard_geometry_results_functions(self):
        data = ('LaWGS',
                'LaWGS (*.inp; *.wgs)', self.load_lawgs_geometry,
                None, None)
        return data

    def load_lawgs_geometry(self, lawgs_filename, name='main', plot=True):
        #key = self.case_keys[self.icase]
        #case = self.result_cases[key]
        self.parent.eid_maps[name] = {}
        self.parent.nid_maps[name] = {}

        skip_reading = self.parent._remove_old_geometry(lawgs_filename)
        if skip_reading:
            return

        model = read_lawgs(lawgs_filename, log=self.parent.log, debug=False)
        self.parent.model_type = model.model_type

        nodes, elements, regions = model.get_points_elements_regions()
        self.parent.nnodes = len(nodes)
        self.parent.nelements = len(elements)

        nodes = array(nodes, dtype='float32')
        elements = array(elements, dtype='int32')

        #print("nNodes = ",self.nnodes)
        #print("nElements = ", self.nelements)

        self.parent.grid.Allocate(self.parent.nelements, 1000)

        points = vtk.vtkPoints()
        points.SetNumberOfPoints(self.parent.nnodes)
        self.parent.nid_map = {}

        assert len(nodes) > 0, len(nodes)
        assert len(elements) > 0, len(elements)
        for nid, node in enumerate(nodes):
            points.InsertPoint(nid, *node)

        elem = vtkQuad()
        etype = elem.GetCellType()
        for unused_eid, element in enumerate(elements):
            (p1, p2, p3, p4) = element
            elem = vtkQuad()
            pts = elem.GetPointIds()
            pts.SetId(0, p1)
            pts.SetId(1, p2)
            pts.SetId(2, p3)
            pts.SetId(3, p4)
            self.parent.grid.InsertNextCell(etype, elem.GetPointIds())

        self.parent.grid.SetPoints(points)
        self.parent.grid.Modified()
        if hasattr(self.parent.grid, 'Update'):  # pragma: no cover
            self.parent.grid.Update()

        # loadCart3dResults - regions/loads
        #self.scalarBar.VisibilityOn()
        #self.scalarBar.Modified()

        self.parent.isubcase_name_map = {1: ['LaWGS', '']}
        cases = OrderedDict()
        ID = 1

        #print("nElements = %s" % nElements)
        form, cases = self._fill_lawgs_case(cases, ID, nodes, elements, regions)
        self.parent._finish_results_io2(form, cases)

    def _fill_lawgs_case(self, cases, ID, nodes, elements, regions):
        eids = arange(1, len(elements) + 1, dtype='int32')
        nids = arange(1, len(nodes) + 1, dtype='int32')
        regions = array(regions, dtype='int32')

        icase = 0
        geometry_form = [
            ('Region', icase, []),
            ('ElementID', icase + 1, []),
            ('NodeID', icase + 2, []),
            ('X', icase + 3, []),
            ('Y', icase + 4, []),
            ('Z', icase + 5, []),
            ('NormalX', icase + 6, []),
            ('NormalY', icase + 7, []),
            ('NormalZ', icase + 8, []),
        ]
        region_res = GuiResult(ID, header='Region', title='Region',
                               location='centroid', scalar=regions)
        eid_res = GuiResult(ID, header='ElementID', title='ElementID',
                            location='centroid', scalar=eids)
        nid_res = GuiResult(ID, header='NodeID', title='NodeID',
                            location='node', scalar=nids)
        cases[icase] = (region_res, (ID, 'Region'))
        cases[icase + 1] = (eid_res, (ID, 'ElementID'))
        cases[icase + 2] = (nid_res, (ID, 'NodeID'))

        #nnids = len(nids)
        neids = len(elements)

        a = nodes[elements[:, 2], :] - nodes[elements[:, 0], :]
        b = nodes[elements[:, 3], :] - nodes[elements[:, 1], :]
        normals = cross(a, b, axis=1)

        assert normals.shape[0] == neids, normals.shape
        assert normals.shape[1] == 3, normals.shape

        x_res = GuiResult(ID, header='X', title='X',
                          location='node', scalar=nodes[:, 0])
        y_res = GuiResult(ID, header='X', title='X',
                          location='node', scalar=nodes[:, 1])
        z_res = GuiResult(ID, header='X', title='X',
                          location='node', scalar=nodes[:, 2])

        nx_res = GuiResult(ID, header='NormalX', title='NormalX',
                           location='node', scalar=normals[:, 0])
        ny_res = GuiResult(ID, header='NormalY', title='NormalY',
                           location='node', scalar=normals[:, 1])
        nz_res = GuiResult(ID, header='NormalZ', title='NormalZ',
                           location='node', scalar=normals[:, 2])

        cases[icase + 3] = (x_res, (ID, 'X'))
        cases[icase + 4] = (y_res, (ID, 'Y'))
        cases[icase + 5] = (z_res, (ID, 'Z'))

        cases[icase + 6] = (nx_res, (ID, 'NormalX'))
        cases[icase + 7] = (ny_res, (ID, 'NormalY'))
        cases[icase + 8] = (nz_res, (ID, 'NormalZ'))
        return geometry_form, cases
