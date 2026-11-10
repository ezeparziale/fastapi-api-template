from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.api.default_responses import default_responses
from app.api.deps import CurrentUser
from app.db.database import get_db
from app.models import UserCreditCard
from app.schemas import MessageDetail, UserCreditCardIn, UserCreditCardOut

router = APIRouter()


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=UserCreditCardOut,
    responses={
        **default_responses,
        200: {
            "description": "Credit card info",
            "model": UserCreditCardOut,
        },
        404: {
            "description": "Credit card not found",
            "model": MessageDetail,
            "content": {
                "application/json": {"example": {"detail": "Credit card not found"}}
            },
        },
    },
)
def get_credit_card(
    current_user: CurrentUser,
) -> UserCreditCardOut:
    """
    ### Get credit card from current user
    This endpoint allows the current user to retrieve their credit card information.
    """
    credit_card = current_user.credit_card

    if not credit_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit card not found",
        )

    return UserCreditCardOut.model_validate(credit_card.credit_card)


@router.put(
    "/",
    status_code=status.HTTP_200_OK,
    response_model=MessageDetail,
    responses={
        **default_responses,
        200: {
            "description": "Credit card updated",
            "model": MessageDetail,
            "content": {
                "application/json": {"example": {"detail": "Credit card updated"}}
            },
        },
    },
)
def update_credit_card(
    credit_card: UserCreditCardIn,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> MessageDetail:
    """
    ### Update credit card from current user
    This endpoint allows the current user to update their credit card information.
    """
    stmt_upsert = (
        insert(UserCreditCard)
        .values(user_id=current_user.id, credit_card=credit_card.model_dump())
        .on_conflict_do_update(
            index_elements=[UserCreditCard.user_id],
            set_={"credit_card": credit_card.model_dump()},
        )
    )
    db.execute(stmt_upsert)
    db.commit()

    return MessageDetail(detail="Credit card updated")


@router.delete(
    "/",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    responses={
        **default_responses,
        204: {
            "description": "Credit card deleted",
        },
        404: {
            "description": "Credit card not found",
            "model": MessageDetail,
            "content": {
                "application/json": {"example": {"detail": "Credit card not found"}}
            },
        },
    },
)
def delete_credit_card(
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> Response:
    """
    ### Delete credit card from current user
    This endpoint allows the current user to delete their credit card information.
    """
    stmt_select = select(UserCreditCard).filter_by(user_id=current_user.id)
    existing_credit_card = db.execute(stmt_select).scalars().first()

    if not existing_credit_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit card not found",
        )

    db.delete(existing_credit_card)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
