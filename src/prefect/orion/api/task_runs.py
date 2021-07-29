from uuid import UUID
from typing import List

import sqlalchemy as sa
from fastapi import Depends, HTTPException, Path, Body, Response, status

from prefect.orion import models, schemas
from prefect.orion.api import dependencies
from prefect.orion.utilities.server import OrionRouter

router = OrionRouter(prefix="/task_runs", tags=["Task Runs"])


@router.post("/")
async def create_task_run(
    task_run: schemas.actions.TaskRunCreate,
    session: sa.orm.Session = Depends(dependencies.get_session),
) -> schemas.core.TaskRun:
    """
    Create a task run
    """
    return await models.task_runs.create_task_run(session=session, task_run=task_run)


@router.get("/{id}")
async def read_task_run(
    task_run_id: UUID = Path(..., description="The task run id", alias="id"),
    session: sa.orm.Session = Depends(dependencies.get_session),
) -> schemas.core.TaskRun:
    """
    Get a task run by id
    """
    task_run = await models.task_runs.read_task_run(
        session=session, task_run_id=task_run_id
    )
    if not task_run:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_run


@router.get("/")
async def read_task_runs(
    flow_run_id: UUID,
    session: sa.orm.Session = Depends(dependencies.get_session),
) -> List[schemas.core.TaskRun]:
    """
    Query for task runs
    """
    return await models.task_runs.read_task_runs(
        session=session, flow_run_id=flow_run_id
    )


@router.delete("/{id}", status_code=204)
async def delete_task_run(
    task_run_id: UUID = Path(..., description="The task run id", alias="id"),
    session: sa.orm.Session = Depends(dependencies.get_session),
):
    """
    Delete a task run by id
    """
    result = await models.task_runs.delete_task_run(
        session=session, task_run_id=task_run_id
    )
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
    return result


@router.post("/{id}/set_state")
async def set_task_run_state(
    task_run_id: UUID = Path(..., description="The task run id", alias="id"),
    state: schemas.actions.StateCreate = Body(..., description="The intended state."),
    session: sa.orm.Session = Depends(dependencies.get_session),
    response: Response = None,
) -> schemas.responses.SetStateResponse:
    """Set a task run state, invoking any orchestration rules."""

    # create the state
    await models.task_run_states.create_task_run_state(
        session=session, task_run_id=task_run_id, state=state
    )
    # set the 201 because a new state was created
    response.status_code = status.HTTP_201_CREATED

    # indicate the state was accepted
    return schemas.responses.SetStateResponse(
        status=schemas.responses.SetStateStatus.ACCEPT,
        new_state=None,
    )