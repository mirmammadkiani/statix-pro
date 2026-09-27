from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os

from backend.modules.beams import BeamSolver
from backend.modules.trusses import TrussSolver
from backend.modules.vectors import VectorMechanics
from backend.modules.rigid_body import RigidBodyMechanics
from backend.modules.centroids import CentroidSolver
from backend.modules.inertia import InertiaSolver
from backend.modules.cables import CableSolver
from backend.modules.friction import FrictionSolver
from backend.modules.virtual_work import VirtualWorkSolver
from backend.modules.network import get_network_info
from backend.presets.beer_johnston_examples import PRESETS

app = FastAPI(
    title="Statix Pro - Beer & Johnston Engineering Statics Suite",
    description="Full-scale engineering solver for all Beer & Johnston statics problems",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Pydantic Data Models ---
class BeamRequest(BaseModel):
    length: float
    supports: List[Dict[str, Any]]
    hinges: Optional[List[float]] = []
    point_loads: Optional[List[Dict[str, Any]]] = []
    moments: Optional[List[Dict[str, Any]]] = []
    dist_loads: Optional[List[Dict[str, Any]]] = []

class TrussRequest(BaseModel):
    nodes: List[Dict[str, float]]
    elements: List[Dict[str, Any]]
    supports: List[Dict[str, Any]]
    loads: List[Dict[str, Any]]

class VectorResultantRequest(BaseModel):
    forces: List[Dict[str, float]]

class VectorDotCrossRequest(BaseModel):
    v1: Dict[str, float]
    v2: Dict[str, float]

class ParticleEquilibriumRequest(BaseModel):
    cables: List[Dict[str, Any]]
    applied_load: Dict[str, float]

class MomentPointRequest(BaseModel):
    point_o: List[float]
    point_a: List[float]
    force: List[float]

class EquivalentSystemRequest(BaseModel):
    reduction_point: List[float]
    forces: List[Dict[str, Any]]
    couples: Optional[List[Dict[str, float]]] = []

class CompositeShapeRequest(BaseModel):
    shapes: List[Dict[str, Any]]

class ParabolicCableRequest(BaseModel):
    span_L: float
    sag_h: float
    w_per_m: float

class CableConcentratedRequest(BaseModel):
    span_L: float
    loads: List[Dict[str, float]]
    known_sag: Dict[str, float]

class FrictionSlipTipRequest(BaseModel):
    weight_W: float
    width_b: float
    height_h: float
    force_height_y: float
    force_angle_deg: float = 0.0
    incline_theta_deg: float = 0.0
    mu_s: float

class FrictionBeltRequest(BaseModel):
    T1_slack: float
    mu: float
    wrap_angle_deg: float
    drum_radius: float = 0.2

class VirtualWorkRequest(BaseModel):
    expression_str: str
    var_name: str = "theta"
    interval: List[float] = [0.0, 3.14159]

# --- API Endpoints ---
@app.get("/api/presets")
def get_presets():
    return {"presets": PRESETS}

@app.get("/api/network-info")
def get_network():
    return get_network_info()

@app.post("/api/solve/beam")
def solve_beam(req: BeamRequest):
    try:
        b = BeamSolver(req.length)
        for s in req.supports:
            b.add_support(s['x'], s['type'])
        for h in req.hinges or []:
            b.add_hinge(h)
        for p in req.point_loads or []:
            b.add_point_load(p['x'], p['fy'], p.get('fx', 0.0))
        for m in req.moments or []:
            b.add_moment(m['x'], m['m'])
        for d in req.dist_loads or []:
            b.add_distributed_load(d['x1'], d['x2'], d['w1'], d['w2'])
        return b.solve()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/truss")
def solve_truss(req: TrussRequest):
    try:
        t = TrussSolver()
        for n in req.nodes:
            t.add_node(n['x'], n['y'])
        for el in req.elements:
            t.add_element(el['node1'], el['node2'], el.get('A'), el.get('E'))
        for s in req.supports:
            t.add_support(s['node'], s['type'])
        for ld in req.loads:
            t.add_load(ld['node'], ld.get('fx', 0.0), ld.get('fy', 0.0))
        return t.solve()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/vectors/resultant")
def solve_vectors_resultant(req: VectorResultantRequest):
    try:
        return VectorMechanics.calculate_resultant(req.forces)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/vectors/dot-cross")
def solve_vectors_dot_cross(req: VectorDotCrossRequest):
    try:
        return VectorMechanics.dot_cross_product(req.v1, req.v2)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/vectors/particle-equilibrium")
def solve_particle_equilibrium(req: ParticleEquilibriumRequest):
    try:
        return VectorMechanics.solve_particle_equilibrium(req.cables, req.applied_load)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/rigid-body/moment")
def solve_rigid_body_moment(req: MomentPointRequest):
    try:
        return RigidBodyMechanics.moment_about_point(req.point_o, req.point_a, req.force)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/rigid-body/equivalent")
def solve_rigid_body_equivalent(req: EquivalentSystemRequest):
    try:
        return RigidBodyMechanics.equivalent_system(req.reduction_point, req.forces, req.couples)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/centroids")
def solve_centroids(req: CompositeShapeRequest):
    try:
        return CentroidSolver.solve_composite(req.shapes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/inertia")
def solve_inertia(req: CompositeShapeRequest):
    try:
        return InertiaSolver.solve_composite_inertia(req.shapes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/cables/parabolic")
def solve_cables_parabolic(req: ParabolicCableRequest):
    try:
        return CableSolver.solve_parabolic_cable(req.span_L, req.sag_h, req.w_per_m)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/cables/concentrated")
def solve_cables_concentrated(req: CableConcentratedRequest):
    try:
        return CableSolver.solve_concentrated_loads(req.span_L, req.loads, req.known_sag)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/friction/slip-tip")
def solve_friction_slip_tip(req: FrictionSlipTipRequest):
    try:
        return FrictionSolver.block_slip_vs_tip(
            req.weight_W, req.width_b, req.height_h,
            req.force_height_y, req.force_angle_deg,
            req.incline_theta_deg, req.mu_s
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/friction/belt")
def solve_friction_belt(req: FrictionBeltRequest):
    try:
        return FrictionSolver.solve_belt_friction(
            req.T1_slack, req.mu, req.wrap_angle_deg, req.drum_radius
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/solve/virtual-work")
def solve_virtual_work(req: VirtualWorkRequest):
    try:
        return VirtualWorkSolver.analyze_potential_energy(
            req.expression_str, req.var_name, req.interval
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Mount Frontend static files
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
