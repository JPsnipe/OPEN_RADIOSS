#!/usr/bin/env python3
"""Minimal ParaViewWeb server using VTK and wslink."""

import argparse

import tempfile

from pathlib import Path

from wslink import server
from vtkmodules.web import protocols as vtkprotocols
from vtkmodules.web import wslink as vtk_wslink

import vtkmodules.all as vtk

from cdb2rad.mesh_convert import convert_to_vtk



def build_view(path: str) -> vtk.vtkRenderWindow:
    """Create a render window with the data from ``path``."""
    ext = Path(path).suffix.lower()

    if ext == ".stl":
        reader = vtk.vtkSTLReader()
    elif ext == ".obj":
        reader = vtk.vtkOBJReader()

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
    view.SetOffScreenRendering(True)

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

            obj_map = self.getApplication().GetObjectIdMap()
            obj_map.SetActiveObject("VIEW", PVWServer.view)

        super().initialize()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch vtk.js visualizer")
    parser.add_argument("--data", required=True, help="Mesh file to display")

    parser.add_argument(
        "--port",
        type=int,
        default=12345,
        help="WebSocket port",
    )
    server.add_arguments(parser)
    args = parser.parse_args()

    data_path = args.data
    ext = Path(data_path).suffix.lower()
    if ext not in {".vtk", ".vtp", ".stl", ".obj"}:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".vtk")
        tmp.close()
        convert_to_vtk(data_path, tmp.name)
        data_path = tmp.name

    PVWServer.view = build_view(data_path)

    server.start_webserver(options=args, protocol=PVWServer)
