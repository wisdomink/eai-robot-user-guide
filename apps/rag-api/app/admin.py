"""Account administration is isolated from the existing business API."""

from functools import lru_cache
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from app.core.config import PUBLIC_BASE_URL
from app.services.admin_service import AdminStorage, SESSION_TTL


COOKIE_NAME = "eai_admin_session"
COOKIE_PATH = "/api/admin"


@lru_cache(maxsize=1)
def get_admin_storage() -> AdminStorage:
    return AdminStorage.from_config()


def _origin(url: str) -> tuple[str, str, int] | None:
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username is not None:
            return None
        port = parsed.port if parsed.port is not None else (443 if parsed.scheme == "https" else 80)
        return parsed.scheme, parsed.hostname, port
    except ValueError:
        return None


def same_origin(request: Request, response: Response):
    response.headers["Cache-Control"] = "no-store"
    origin = request.headers.get("origin")
    source = _origin(origin) if origin is not None else None
    # Reverse proxies may replace Host with an internal ALB hostname.
    allowed = {_origin(PUBLIC_BASE_URL)}
    if source is not None:
        allowed.add(_origin(f"{source[0]}://{request.headers.get('host', '')}"))
    if request.headers.get("sec-fetch-site") in {"cross-site", "same-site"} or (
        origin is not None and (source is None or source not in allowed)
    ):
        raise HTTPException(403, "请从当前站点的管理后台操作", headers={"Cache-Control": "no-store"})


router = APIRouter(prefix="/api/admin", tags=["Admin"], dependencies=[Depends(same_origin)])


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class UserCreateRequest(LoginRequest):
    password: str = Field(min_length=8, max_length=128)


class UserUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    password: str | None = Field(default=None, min_length=8, max_length=128)
    enabled: bool | None = None


def require_session(request: Request, storage: AdminStorage = Depends(get_admin_storage)) -> dict:
    session = storage.session(request.cookies.get(COOKIE_NAME, ""))
    if session is None:
        raise HTTPException(401, "登录已失效，请重新登录", headers={"Cache-Control": "no-store"})
    return session


def require_admin(session: dict = Depends(require_session)) -> dict:
    if session["user"]["role"] != "admin":
        raise HTTPException(403, "仅管理员可以管理账号和查看登录记录", headers={"Cache-Control": "no-store"})
    return session


@router.post("/login")
def login(payload: LoginRequest, request: Request, response: Response, storage: AdminStorage = Depends(get_admin_storage)):
    result = storage.login(payload.username, payload.password, request.client.host if request.client else "")
    if result is None:
        raise HTTPException(401, "账号或密码错误，或账号已停用", headers={"Cache-Control": "no-store"})
    storage.logout(request.cookies.get(COOKIE_NAME, ""))
    secure = (
        request.url.scheme == "https"
        or urlsplit(request.headers.get("origin", "")).scheme == "https"
        or request.headers.get("x-forwarded-proto", "").split(",")[0].strip() == "https"
    )
    response.set_cookie(COOKIE_NAME, result.pop("token"), max_age=SESSION_TTL, path=COOKIE_PATH,
                        httponly=True, secure=secure, samesite="strict")
    return result


@router.post("/logout")
def logout(request: Request, response: Response, storage: AdminStorage = Depends(get_admin_storage)):
    storage.logout(request.cookies.get(COOKIE_NAME, ""))
    response.delete_cookie(COOKIE_NAME, path=COOKIE_PATH, httponly=True, samesite="strict")
    return {"ok": True}


@router.get("/me")
def me(session: dict = Depends(require_session)):
    return session


@router.get("/users", dependencies=[Depends(require_admin)])
def users(storage: AdminStorage = Depends(get_admin_storage)):
    return {"users": storage.list_users()}


@router.post("/users", status_code=201, dependencies=[Depends(require_admin)])
def create_user(payload: UserCreateRequest, storage: AdminStorage = Depends(get_admin_storage)):
    try:
        return {"user": storage.create_user(payload.username, payload.password)}
    except FileExistsError as exc:
        raise HTTPException(409, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.patch("/users/{username}", dependencies=[Depends(require_admin)])
def update_user(username: str, payload: UserUpdateRequest, storage: AdminStorage = Depends(get_admin_storage)):
    try:
        return {"user": storage.update_user(username, **payload.model_dump())}
    except KeyError as exc:
        raise HTTPException(404, "账号不存在") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc


@router.get("/login-logs", dependencies=[Depends(require_admin)])
def login_logs(limit: int = Query(25, ge=1, le=100), after: str | None = Query(None, max_length=128),
               username: str = Query("", max_length=64), storage: AdminStorage = Depends(get_admin_storage)):
    return storage.login_logs(limit=limit, after=after, username=username)
