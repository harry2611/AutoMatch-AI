from __future__ import annotations

import hashlib

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.entities import Experiment, ExperimentAssignment
from app.models.enums import ExperimentArm, ExperimentStatus


def get_active_experiment(db: Session) -> Experiment | None:
    return db.execute(
        select(Experiment).where(Experiment.status == ExperimentStatus.ACTIVE).order_by(Experiment.created_at.desc())
    ).scalar_one_or_none()


def assign_experiment_arm(db: Session, buyer_id: int, experiment: Experiment | None) -> ExperimentArm:
    if experiment is None:
        return ExperimentArm.BAYESIAN

    assignment = db.execute(
        select(ExperimentAssignment).where(
            ExperimentAssignment.experiment_id == experiment.id,
            ExperimentAssignment.buyer_id == buyer_id,
        )
    ).scalar_one_or_none()
    if assignment is not None:
        return assignment.arm

    digest = hashlib.sha256(f"{experiment.id}:{buyer_id}".encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    arm = experiment.treatment_arm if bucket < experiment.traffic_split else experiment.control_arm

    assignment = ExperimentAssignment(experiment_id=experiment.id, buyer_id=buyer_id, arm=arm)
    db.add(assignment)
    db.commit()
    return arm

