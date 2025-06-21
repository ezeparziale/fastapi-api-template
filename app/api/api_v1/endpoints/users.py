from math import ceil
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Response, status
from loguru import logger
from sqlalchemy import String, cast, desc, func, or_, select
from sqlalchemy.orm import Session

from app.api.default_responses import default_responses
from app.api.deps import CurrentUser, FilterParams
from app.db.database import get_db
from app.models import User, UserCreditCard
from app.schemas import (
    MessageDetail,
    UserCreate,
    UserCreditCardIn,
    UserCreditCardOut,
    UserOut,
)
from app.utils import get_password_hash

router = APIRouter()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        **default_responses,
        201: {
            "description": "User created",
            "model": UserOut,
        },
        409: {
            "description": "User already exists",
            "model": MessageDetail,
            "content": {
                "application/json": {"example": {"detail": "User already exists"}}
            },
        },
    },
)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> UserOut:
    """
    ### Create user
    """
    # Check if user exists
    stmt_select = select(User).filter_by(email=user.email)
    user_exists = db.execute(stmt_select).scalars().first()

    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists",
        )

    # Create user
    hashed_password = get_password_hash(user.password)
    user.password = hashed_password
    new_user = User(**user.model_dump())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.get(
    "/me",
    status_code=status.HTTP_200_OK,
    responses={
        **default_responses,
        200: {
            "description": "User info",
            "model": UserOut,
        },
    },
)
def get_user_me(
    current_user: CurrentUser,
) -> UserOut:
    """
    ### Get current user info
    """
    return current_user


@router.get(
    "/{id}",
    status_code=status.HTTP_200_OK,
    responses={
        **default_responses,
        200: {
            "description": "User info",
            "model": UserOut,
        },
        404: {
            "description": "User not found",
            "model": MessageDetail,
            "content": {"application/json": {"example": {"detail": "User not found"}}},
        },
    },
)
def get_user(
    id: Annotated[int, Path(description="The ID of the user to get")],
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> UserOut:
    """
    ### Get user by id
    """
    # Get user
    stmt_select = select(User).where(User.id == id).limit(1)
    user = db.execute(stmt_select).scalars().first()

    # Check if user not found
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.get(
    "/",
    description="""
    Get users list

    This endpoint returns a list of users along with additional metadata in the response headers.
    The following headers are included:

    - **Total-Count**: Total number of users in the database.
    - **Total-Count-Filtered**: Total number of users after applying any filters (e.g., search).
    - **Pagination-Pages**: Total number of pages based on the limit specified in the query parameters.

    You can also sort the results by one or multiple fields using the `sort_by` query parameter.
    To sort in descending order, prepend the field with a '-' (e.g., `-id`).
    Sorting by multiple fields is supported by separating them with commas (e.g., `title,-id`).

    The response includes both the users data and these headers for pagination and filtering details.
    """,  # noqa: E501
    status_code=status.HTTP_200_OK,
    responses={
        **default_responses,
        200: {
            "description": "User info",
            "model": list[UserOut],
        },
        400: {
            "description": "Bad request",
            "model": MessageDetail,
            "content": {
                "application/json": {"example": {"detail": "Invalid sort field"}}
            },
        },
    },
)
def get_users(
    response: Response,
    filter_query: FilterParams,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
) -> list[UserOut]:
    """
    ### Get users list
    """
    # Query
    stmt_select = select(User)

    # Search
    if filter_query.search:
        stmt_select = stmt_select.where(
            or_(
                cast(User.id, String).ilike(filter_query.search),
                User.email.icontains(filter_query.search),
            )
        )

    # Total rows filtered
    total_row_filtered = (
        db.execute(select(func.count()).select_from(stmt_select.subquery()))
        .scalars()
        .one()
    )

    # Sort
    try:
        if filter_query.sort_by:
            fields = filter_query.sort_by.split(",")
            for field in fields:
                if field.startswith("-"):
                    stmt_select = stmt_select.order_by(desc(getattr(User, field[1:])))
                else:
                    stmt_select = stmt_select.order_by(getattr(User, field))
        else:
            stmt_select = stmt_select.order_by(User.id)
    except Exception as e:
        logger.warning(e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid sort field"
        ) from e

    # Pagination
    stmt_select = stmt_select.limit(filter_query.limit).offset(filter_query.offset)

    # Get data
    users = db.execute(stmt_select).scalars().all()

    # Total rows
    total_rows = db.execute(select(func.count(User.id))).scalars().one()

    # Extra headers
    response.headers["Total-Count"] = str(total_rows)
    response.headers["Total-Count-Filtered"] = str(total_row_filtered)
    response.headers["Pagination-Pages"] = str(ceil(total_rows / filter_query.limit))

    return users  # type: ignore[return-value]


@router.get(
    "/credit-card/",
    status_code=status.HTTP_200_OK,
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
    # Get credit card
    credit_card = current_user.credit_card

    # Check if credit card not found
    if not credit_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit card not found",
        )

    return UserCreditCardOut.model_validate(credit_card.credit_card)


@router.put(
    "/credit-card/",
    status_code=status.HTTP_200_OK,
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
    # Check if credit card exists
    stmt_select = select(UserCreditCard).filter_by(user_id=current_user.id)
    existing_credit_card = db.execute(stmt_select).scalars().first()

    if existing_credit_card:
        # Update credit card
        existing_credit_card.credit_card = credit_card.model_dump()
    else:
        # Insert new credit card
        current_user.credit_card = UserCreditCard(credit_card=credit_card.model_dump())

    db.commit()

    return MessageDetail(detail="Credit card updated")


@router.delete(
    "/credit-card/",
    status_code=status.HTTP_204_NO_CONTENT,
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
    # Check if credit card exists
    stmt_select = select(UserCreditCard).filter_by(user_id=current_user.id)
    existing_credit_card = db.execute(stmt_select).scalars().first()

    if not existing_credit_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit card not found",
        )

    # Delete credit card
    db.delete(existing_credit_card)
    db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)
