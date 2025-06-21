from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, credit_card, posts, users, votes

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authorization"])
api_router.include_router(posts.router, prefix="/posts", tags=["Posts"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(
    credit_card.router, prefix="/credit-card", tags=["Credit Card"]
)
api_router.include_router(votes.router, prefix="/votes", tags=["Votes"])
