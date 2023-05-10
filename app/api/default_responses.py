from app.schemas import MessageDetail

default_responses = {
    401: {
        "description": "Unauthorized",
        "model": MessageDetail,
        "content": {
            "application/json": {"example": {"detail": "Authorization required"}}
        },
    },
    500: {
        "description": "Internal Server Error",
        "model": MessageDetail,
        "content": {
            "application/json": {"example": {"detail": "Internal Server Error"}}
        },
    },
}
