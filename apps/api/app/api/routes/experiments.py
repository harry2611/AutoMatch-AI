from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import require_roles
from app.db.session import get_db
from app.models.entities import Experiment
from app.models.enums import ExperimentArm, ExperimentStatus, UserRole
from app.schemas.domain import ExperimentCreate, ExperimentDashboardResponse, ExperimentResponse
from app.services.experiments import get_active_experiment


router = APIRouter(prefix="/experiments", tags=["experiments"])


@router.get("", response_model=list[ExperimentResponse])
def list_experiments(db: Session = Depends(get_db)) -> list[ExperimentResponse]:
    experiments = db.execute(select(Experiment).order_by(Experiment.created_at.desc())).scalars().all()
    return [ExperimentResponse.model_validate(experiment) for experiment in experiments]


@router.post("", response_model=ExperimentResponse)
def create_experiment(
    payload: ExperimentCreate,
    _: object = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ExperimentResponse:
    experiment = Experiment(
        name=payload.name,
        description=payload.description,
        status=ExperimentStatus.ACTIVE,
        control_arm=ExperimentArm.HEURISTIC,
        treatment_arm=ExperimentArm.BAYESIAN,
        traffic_split=payload.traffic_split,
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return ExperimentResponse.model_validate(experiment)


@router.get("/dashboard", response_model=ExperimentDashboardResponse)
def experiment_dashboard(
    _: object = Depends(require_roles(UserRole.ADMIN)),
    db: Session = Depends(get_db),
) -> ExperimentDashboardResponse:
    experiments = db.execute(select(Experiment).order_by(Experiment.created_at.desc())).scalars().all()
    active = get_active_experiment(db)
    return ExperimentDashboardResponse(
        experiments=[ExperimentResponse.model_validate(experiment) for experiment in experiments],
        active_experiment=ExperimentResponse.model_validate(active) if active else None,
    )

