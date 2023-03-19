from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session

from app.api.deps import CommonsDep, CurrentUser
from app.db.database import get_db
from app.models import Post, Vote
from app.schemas import Post as PostSchema
from app.schemas import PostCreate, PostOut

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK)
def get_posts(
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
    commons: CommonsDep = None,
) -> list[PostOut]:
    """
    ### Get post list
    """
    stmt_select = (
        select(Post, func.count(Vote.post_id).label("votes"))
        .join(Vote, Vote.post_id == Post.id, isouter=True)
        .group_by(Post.id)
        .where(Post.title.contains(commons.search))
        .limit(commons.limit)
        .offset(commons.offset)
    )
    posts = db.execute(stmt_select).all()
    return posts  # type: ignore[return-value]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_posts(
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> PostSchema:
    """
    ### Create post
    """
    new_post = Post(owner_id=current_user.id, **post.dict())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post


@router.get("/{id}", status_code=status.HTTP_200_OK)
def get_post(
    id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> PostOut:
    """
    ### Get post by id
    """
    stmt_select = (
        select(Post, func.count(Vote.post_id).label("votes"))
        .join(Vote, Vote.post_id == Post.id, isouter=True)
        .group_by(Post.id)
        .where(Post.id == id)
        .limit(1)
    )
    post = db.execute(stmt_select).first()

    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Post with id {id} not found"
        )
    return post  # type: ignore[return-value]


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    id: int,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> None:
    """
    ### Delete post
    """
    stmt_select = select(Post).where(Post.id == id).limit(1)
    post_query = db.execute(stmt_select)

    post = post_query.scalars().first()

    if post is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {id} does not exist",
        )

    if post.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    stmt_delete = (
        delete(Post).where(Post.id == id).execution_options(synchronize_session=False)
    )
    db.execute(stmt_delete)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)  # type: ignore[return-value]


@router.put("/{id}", status_code=status.HTTP_200_OK)
def update_post(
    id: int,
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: CurrentUser = None,
) -> PostSchema:
    """
    ### Update post
    """
    stmt_select = select(Post).where(Post.id == id).limit(1)
    post_to_update = db.execute(stmt_select).scalars().first()

    if post_to_update is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {id} does not exist",
        )

    if post_to_update.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform requested action",
        )

    stmt_update = (
        update(Post)
        .where(Post.id == id)
        .values(post.dict())  # type: ignore[arg-type]
        .execution_options(synchronize_session=False)
        .returning(Post)
    )
    result = db.scalars(stmt_update)
    db.commit()
    return result.first()  # type: ignore[return-value]
