from sys import prefix
from typing import Any

import uuid
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from app.schemas import PostCreate, PostResponse, UserCreate, UserRead, UserUpdate
from app.db import Post, create_db_and_tables, get_async_session, User
from sqlalchemy import select
from app.images import imagekit
import os
import tempfile
from app.users import auth_backend,current_user,fastapi_users

############ To Create the database as soon as the application runs if the database is not created
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    print("✅ Database tables created!")
    yield

###########################

app = FastAPI(lifespan=lifespan)

# ✅ FIXED: Correct fastapi_users router syntax
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_register_router(UserRead,UserCreate),
    prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth/jwt", tags=["auth"]
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/auth/jwt", tags=["auth"]
)

@app.post("/upload")
async def upload(file: UploadFile = File(...),
                             caption: str = Form(""),
                             user: Any = Depends(current_user), # Protecting EndPoints
                             session: AsyncSession = Depends(get_async_session)  ## Dependency injection
                             ):

    try:
        content = await file.read()

        # ✅ Upload works! Just fix response handling
        upload_result = imagekit.files.upload(
            file=content,
            file_name=file.filename,
            use_unique_file_name=True,
            tags=["backend-upload"]
        )


        post = Post(
            user_id = user.id,
            caption=caption,
            url=upload_result.url,
            file_type="video" if file.content_type.startswith("video/") else "image",
            file_name=upload_result.name or file.filename
        )

        session.add(post)
        await session.commit()  ## Must commit to save
        await session.refresh(post)
        return post

    except Exception as e:
        print(f"❌ Upload error: {type(e).__name__}: {str(e)}")
        print(f"❌ Full traceback: {e}")
        raise HTTPException(status_code=400, detail=f"{type(e).__name__}: {str(e)}")
    finally:
        pass


@app.get("/feed")
async def get_feed(
        session: AsyncSession = Depends(get_async_session),
        user: Any = Depends(current_user), # Protecting EndPoints,
):
    result = await session.execute(select(Post).order_by(Post.created_at.desc()))
    posts = [row[0] for row in result.all()] #convert all into a list, looping throught the values

    result = await session.execute(select(User))
    users = [row[0] for row in result.all()]
    user_dict = {u.id: u.email for u in users}



    posts_data = []
    for post in posts:
        posts_data.append({
            "id": str(post.id),
            "user_id" : str(post.user_id),
            "caption" : post.caption,
            "url" : post.url,
            "file_type" : post.file_type,
            "file_name" : post.file_name,
            "created_at" : post.created_at,
            "is_owner":post.user_id == user.id,
            "email" : user_dict.get(post.user_id,"Unknown"),

        })

    return {"posts": posts_data}

@app.get("/debug-imagekit")
def debug_imagekit():
    return {
        "methods_with_upload": [m for m in dir(imagekit) if 'upload' in m.lower()],
        "all_methods": [m for m in dir(imagekit) if 'file' in m.lower() or 'upload' in m.lower()],
        "has_files": hasattr(imagekit, 'files'),
        "imagekit_type": str(type(imagekit))
    }


@app.delete("/posts/{post_id}")
async def delete_post(post_id: str,
                      session: AsyncSession = Depends(get_async_session),
                      user: Any = Depends(current_user)):# Protecting EndPoints
    try:
        post_uuid = uuid.UUID(post_id)
        result = await session.execute(select(Post).where(Post.id == post_uuid))
        post = result.scalars().first()


        if not post:
            raise HTTPException(status_code=404, detail="Post not found")

        if post.user_id != user.id:
            raise HTTPException(status_code=403, detail="You are not allowed to perform this action")


        await session.delete(post)
        await session.commit()

        return {"success": True,"message": "Post deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"{type(e).__name__}: {str(e)}")


























# text_post = {
#     1: {
#         "title": "Morning Coffee Vibes ☕",
#         "content": "Nothing beats starting the day with fresh brew and good music. What's your go-to morning ritual? #ProductivityHacks"
#
#     },
#     2: {
#         "title": "FastAPI + aiosqlite Victory 🚀",
#         "content": "Fixed async SQLite bottleneck! 10x query performance boost. Pro tip: use connection pooling for production. Code snippet incoming."
#
#     },
#     3: {
#         "title": "C Pointers Mastered Finally",
#         "content": "Double pointers no longer haunt my dreams! void** pptr = &ptr; draw diagrams first. Systems programming feels good today."
#
#     },
#     4: {
#         "title": "AWS Migration Complete",
#         "content": "Moved monolith to microservices on ECS + RDS PostgreSQL. Latency down 40%! Docker + Fargate = smooth sailing."
#
#     },
#     5: {
#         "title": "Java Spring Boot Optimization",
#         "content": "Profiled app with VisualVM - found @Cacheable missing indexes killing performance. Now sub-50ms endpoints! #JavaTips"
#
#     },
#     6: {
#         "title": "Algorithm Practice Streak",
#         "content": "Day 45: Sliding Window + Two Pointers combo solved 3 LeetCode Hards. Pattern recognition getting sharp. What's your daily grind?"
#
#     },
#     7: {
#         "title": "uv Package Manager Love",
#         "content": "Switched from poetry/pipenv to uv. Installs 10x faster, lockfiles instant. `uv run uvicorn main:app --reload` = perfection."
#
#     },
#     8: {
#         "title": "Weekend Coding Plans",
#         "content": "Building image upload endpoint next. S3 presigned URLs + FastAPI. Bonus: thumbnail generation with Pillow. Who's joining?"
#
#     },
#     9: {
#         "title": "Database Schema Evolution",
#         "content": "Migrated from SQLite to PostgreSQL without downtime. Alembic + Flyway combo worked perfectly. Schema versioning matters!"
#
#     },
#     10: {
#         "title": "Memory Leak Hunt Success",
#         "content": "Valgrind saved the day! Found unclosed SQLite handles in async context. aiosqlite context managers are your friends."
#
#     }
# }
#
# @app.get("/posts") # Path Parameters
# def get_all_posts(limit : int = None): # Query Parameter
#     if limit:
#         return list(text_post.values())[:limit]
#     return text_post
#
# @app.get("/posts/{id}")
# def get_post(id: int) -> PostResponse:
#     if id not in text_post:
#         raise HTTPException(status_code=404, detail="Post not found")
#     return text_post.get(id)
#
#
# @app.post("/posts")
# def create_post(post:PostCreate) -> PostResponse:
#     new_post = {"Title": post.title, "Content": post.content}
#     text_post[max(text_post.keys()) + 1] = new_post
#     return new_post

# @app.delete("/posts/{id}")
# def delete_post(id: int):
#     if id not in text_post:
#         raise HTTPException(status_code=404, detail="Post not found")
#




