#!/usr/bin/env python3
"""Minimal ParaViewWeb server using VTK and wslink."""

import argparse
from pathlib import Path

from wslink import server
from vtkmodules.web import protocols as vtkprotocols
from vtkmodules.web import wslink as vtk_wslink

import vtkmodules.all as vtk


def build_view(path: str) -> vtk.vtkRenderWindow:
    """Create a render window with the data from ``path``."""
    ext = Path(path).suffix.lower()
    if ext == '.stl':
        reader = vtk.vtkSTLReader()
    elif ext == '.obj':
        reader = vtk.vtkOBJReader()
    elif ext in {'.vtp', '.vtk'}:
        reader = vtk.vtkGenericDataObjectReader()
    else:
        reader = vtk.vtkGenericDataObjectReader()
    reader.SetFileName(path)
    reader.Update()
    mapper = vtk.vtkDataSetMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    renderer = vtk.vtkRenderer()
    renderer.AddActor(actor)
    view = vtk.vtkRenderWindow()
    view.AddRenderer(renderer)
    return view


class PVWServer(vtk_wslink.ServerProtocol):
    """Server protocol exposing a simple remote view."""

    view = None

    def initialize(self):
        self.registerVtkWebProtocol(vtkprotocols.vtkWebMouseHandler())
        self.registerVtkWebProtocol(vtkprotocols.vtkWebViewPort())
        self.registerVtkWebProtocol(vtkprotocols.vtkWebViewPortImageDelivery())
        if PVWServer.view:
            self.getApplication().GetObjectIdMap().SetActiveObject("VIEW", PVWServer.view)
        super().initialize()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch vtk.js visualizer")
    parser.add_argument("--data", required=True, help="Mesh file to display")
    server.add_arguments(parser)
    args = parser.parse_args()

    PVWServer.view = build_view(args.data)
    server.start_webserver(options=args, protocol=PVWServer)
