"""Off-screen VTK renderer for crab_v2.py's preview (shaded, smooth normals with crisp feature edges)."""
import numpy as np

PURPLE = (0.478, 0.310, 0.702)      # purple PLA, #7a4fb3
DARK = (0.16, 0.16, 0.17)
HORN = (0.85, 0.85, 0.82)
BODY = (0.80, 0.62, 0.28)
LID = (0.478, 0.310, 0.702)


def _poly(m):
    import vtk
    import trimesh
    v, f = trimesh.remesh.subdivide_to_size(m.vertices, m.faces, max_edge=3.0, max_iter=8)
    m = trimesh.Trimesh(v, f, process=False)
    from vtk.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray
    pts = vtk.vtkPoints()
    pts.SetData(numpy_to_vtk(np.ascontiguousarray(m.vertices, dtype=np.float64), deep=True))
    f = np.hstack([np.full((len(m.faces), 1), 3), m.faces]).astype(np.int64).ravel()
    cells = vtk.vtkCellArray()
    cells.SetCells(len(m.faces), numpy_to_vtkIdTypeArray(f, deep=True))
    pd = vtk.vtkPolyData()
    pd.SetPoints(pts)
    pd.SetPolys(cells)
    n = vtk.vtkPolyDataNormals()
    n.SetInputData(pd)
    n.SetFeatureAngle(32)
    n.SplittingOn()
    n.ConsistencyOn()
    n.Update()
    return n.GetOutput()


def render(scene, cam, size=(900, 760), ssao=True):
    """scene: list of (trimesh, rgb[, specular]); cam: dict(pos, focal, up, angle). Returns an HxWx3 uint8 image."""
    import vtk
    from vtk.util.numpy_support import vtk_to_numpy
    r = vtk.vtkRenderer()
    r.SetBackground(1, 1, 1)
    for item in scene:
        m, c = item[0], item[1]
        mp = vtk.vtkPolyDataMapper()
        mp.SetInputData(_poly(m))
        a = vtk.vtkActor()
        a.SetMapper(mp)
        p = a.GetProperty()
        p.SetColor(*c)
        p.SetAmbient(0.18)
        p.SetDiffuse(0.82)
        p.SetSpecular(item[2] if len(item) > 2 else 0.12)
        p.SetSpecularPower(25)
        r.AddActor(a)
    kit = vtk.vtkLightKit()
    kit.SetKeyLightIntensity(0.95)
    kit.AddLightsToRenderer(r)
    cm = r.GetActiveCamera()
    cm.SetPosition(*cam["pos"])
    cm.SetFocalPoint(*cam["focal"])
    cm.SetViewUp(*cam.get("up", (0, 0, 1)))
    cm.SetViewAngle(cam.get("angle", 30))
    r.ResetCameraClippingRange()
    if ssao:
        try:
            r.UseSSAOOn()
            r.SetSSAORadius(6.0)
            r.SetSSAOKernelSize(128)
            r.SetSSAOBias(0.05)
        except AttributeError:
            pass
    w = vtk.vtkRenderWindow()
    w.SetOffScreenRendering(1)
    w.SetMultiSamples(8)
    w.AddRenderer(r)
    w.SetSize(*size)
    w.Render()
    f = vtk.vtkWindowToImageFilter()
    f.SetInput(w)
    f.ReadFrontBufferOff()
    f.Update()
    img = f.GetOutput()
    x, y, _ = img.GetDimensions()
    a = vtk_to_numpy(img.GetPointData().GetScalars()).reshape(y, x, -1)[::-1, :, :3]
    w.Finalize()
    return a


def _cam(az, el, dist, focal, angle=28):
    az, el = np.radians(az), np.radians(el)
    d = np.array([np.cos(el) * np.cos(az), np.cos(el) * np.sin(az), np.sin(el)])
    return dict(pos=tuple(np.asarray(focal) + d * dist), focal=tuple(focal), up=(0, 0, 1), angle=angle)


def world(meshes, dummies, ch, keep=None):
    out = []
    for n, (m, fr) in {**meshes, **dummies}.items():
        if keep and not keep(n, fr):
            continue
        w = m.copy()
        w.apply_transform(ch[fr])
        out.append((w, HORN if "horn" in n else DARK if "case" in n else PURPLE))
    return out


def preview(meshes, dummies, lid, body, poses, chain, path, extra=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    views = [("home", "home (upright, forearm forward)", _cam(140, 20, 640, (0, 60, 105))),
             ("pick on the lid", "pick on the lid, claw down", _cam(35, 18, 640, (0, 50, 75))),
             ("reaching out, side view", "reach forward", _cam(180, 6, 860, (0, 150, 80), 26)),
             ("claw, half open", None, _cam(-35, 28, 340, (5, 215, 66), 26))]
    fig, axs = plt.subplots(2, 2, figsize=(18, 15.2))
    for ax, (title, pn, cam) in zip(axs.ravel(), views):
        if pn:
            scene = [(body, BODY), (lid, PURPLE)] + world(meshes, dummies, chain(poses[pn]))
        else:
            scene = world(meshes, dummies, chain((0, 0, 0, 0, 30)), keep=lambda n, fr: fr in "CDF" and "j3" not in n)
        ax.imshow(render(scene, cam))
        ax.set_title(title, fontsize=17)
        ax.set_axis_off()
    plt.tight_layout()
    plt.savefig(path, dpi=60)
    plt.close(fig)
