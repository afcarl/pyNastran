# coding: utf-8
from __future__ import print_function
#import os

#from six import iteritems, itervalues, string_types

#import numpy as np
import vtk

#from qtpy.compat import getsavefilename#, getopenfilename

#from pyNastran.utils import integer_types
#from pyNastran.gui.gui_objects.coord_properties import CoordProperties


class ViewActions(object):
    def __init__(self, gui):
        self.gui = gui

    def on_pan_left(self, event):
        """https://semisortedblog.wordpress.com/2014/09/04/building-vtk-user-interfaces-part-3c-vtk-interaction"""
        camera, cam, focal = self._setup_pan()

        # Create a vector that points upward, i.e. (0, 1, 0)
        up = camera.GetViewUp() # We don't want roll
        vec = [0, 0, 0]
        new_cam = [0, 0, 0]
        new_focal = [0, 0, 0]

        # Calculate the forward pointing unit-vector 'vec' again in the same way,
        # i.e. the normalized vector of focal point – camera position
        vtk.vtkMath.Subtract(focal, cam, vec)

        vec[1] = 0 #We don't want roll
        vtk.vtkMath.Normalize(vec)

        # Calculate the cross product of the forward vector by the up vector,
        # which will give us an orthogonal vector pointing right relative to
        #the camera
        vtk.vtkMath.Cross(vec, up, vec)

        # Add this to the camera position and focal point to move it right
        # new_cam = cam + vec
        vtk.vtkMath.Add(cam, vec, new_cam)

        # new_focal = focal + vec
        vtk.vtkMath.Add(focal, vec, new_focal)
        self._set_camera_position_focal_point(camera, new_cam, new_focal)

    def on_pan_right(self, event):
        """https://semisortedblog.wordpress.com/2014/09/04/building-vtk-user-interfaces-part-3c-vtk-interaction"""
        camera, cam, focal = self._setup_pan()

        # Create a vector that points upward, i.e. (0, 1, 0)
        up = camera.GetViewUp() # We don't want roll
        vec = [0, 0, 0]
        new_cam = [0, 0, 0]
        new_focal = [0, 0, 0]

        # Calculate the forward pointing unit-vector 'vec' again in the same way,
        # i.e. the normalized vector of focal point – camera position
        vtk.vtkMath.Subtract(focal, cam, vec)

        vec[1] = 0 #We don't want roll
        vtk.vtkMath.Normalize(vec)

        # Calculate the cross product of the forward vector by the up vector,
        # which will give us an orthogonal vector pointing right relative to
        #the camera
        #vec = up x vec
        vtk.vtkMath.Cross(vec, up, vec)

        # Subtract vec from the camera position and focal point to move it right
        # new_cam = cam - vec
        vtk.vtkMath.Subtract(cam, vec, new_cam)

        # new_focal = focal - vec
        vtk.vtkMath.Subtract(focal, vec, new_focal)
        self._set_camera_position_focal_point(camera, new_cam, new_focal)

    def on_pan_up(self, event):
        """not 100% on this"""
        camera, cam, focal = self._setup_pan()

        # Create a 'vec' vector that will be the direction of movement
        # (numpad 8 and 5 generate movement along the z-axis; numpad 4
        # and 6 along the x-axis; numpad 7 and 9 along the y-axis)
        vec = camera.GetViewUp() # We don't want roll
        new_cam = [0, 0, 0]
        new_focal = [0, 0, 0]

        # Add the movement to the current camera position and focal point,
        # and save these in 'new_cam' and 'new_focal' respectively
        vtk.vtkMath.Subtract(cam, vec, new_cam)

        # new_focal = focal - vec
        vtk.vtkMath.Subtract(focal, vec, new_focal)
        self._set_camera_position_focal_point(camera, new_cam, new_focal)

    def on_pan_down(self, event):
        """not 100% on this"""
        camera, cam, focal = self._setup_pan()

        # Create a 'vec' vector that will be the direction of movement
        # (numpad 8 and 5 generate movement along the z-axis; numpad 4
        # and 6 along the x-axis; numpad 7 and 9 along the y-axis)
        vec = camera.GetViewUp() # We don't want roll
        new_cam = [0, 0, 0]
        new_focal = [0, 0, 0]

        # Add the movement to the current camera position and focal point,
        # and save these in 'new_cam' and 'new_focal' respectively
        vtk.vtkMath.Add(cam, vec, new_cam)

        # new_focal = focal + vec
        vtk.vtkMath.Add(focal, vec, new_focal)
        self._set_camera_position_focal_point(camera, new_cam, new_focal)

    def _setup_pan(self):
        camera = self.rend.GetActiveCamera()
        cam = camera.GetPosition()
        focal = camera.GetFocalPoint()
        return camera, cam, focal

    def _set_camera_position_focal_point(self, camera, new_cam, new_focal):
        """Set the camera position and focal point to the new vectors"""
        camera.SetPosition(new_cam)
        camera.SetFocalPoint(new_focal)

        # Update the clipping range of the camera
        self.rend.ResetCameraClippingRange()
        self.Render()

    #---------------------------------------------------------------------------
    def on_increase_magnification(self):
        """zoom in"""
        self.zoom(1.1)

    def on_decrease_magnification(self):
        """zoom out"""
        self.zoom(1.0 / 1.1)

    def rotate(self, rotate_deg, render=True):
        """see the gui"""
        camera = self.GetCamera()
        camera.Roll(-rotate_deg)
        camera.Modified()
        if render:
            self.vtk_interactor.Render()
        self.gui.log_command('rotate(%s)' % rotate_deg)

    def zoom(self, value):
        camera = self.GetCamera()
        camera.Zoom(value)
        camera.Modified()
        self.vtk_interactor.Render()
        self.gui.log_command('zoom(%s)' % value)

    #---------------------------------------------------------------------------
    def Render(self):
        self.vtk_interactor.GetRenderWindow().Render()

    def GetCamera(self):
        return self.rend.GetActiveCamera()

    #@property
    #def settings(self):
        #return self.gui.settings

    @property
    def rend(self):
        return self.gui.rend

    @property
    def vtk_interactor(self):
        return self.gui.vtk_interactor
