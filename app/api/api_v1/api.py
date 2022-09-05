from fastapi import APIRouter

from app.api.api_v1.endpoints import items, posts, users, votes

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(posts.router, prefix="/posts", tags=["posts"])
api_router.include_router(votes.router, prefix="/votes", tags=["votes"])
