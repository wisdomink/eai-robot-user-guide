"""Persistent admin accounts, revocable sessions, and login history."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
import secrets
import sqlite3
import time
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError


SESSION_TTL = 8 * 60 * 60
_PASSWORD_ROUNDS = 600_000
_USERNAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,63}")


def _timestamp() -> str:
    return datetime.fromtimestamp(time.time(), timezone.utc).isoformat(timespec="microseconds")


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PASSWORD_ROUNDS)
    return f"{salt}${digest.hex()}"


def _verify_password(password: str, encoded: str) -> bool:
    salt, digest = encoded.split("$", 1)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), _PASSWORD_ROUNDS)
    return hmac.compare_digest(actual.hex(), digest)


def _public_user(user: dict) -> dict:
    return {key: user.get(key) for key in ("username", "role", "enabled", "created_at", "last_login_at")}


class AdminStorage:
    def __init__(self, path: Path | None = None, *, table=None):
        self._table = table
        self._path = path
        self._initialized = False
        if table is None:
            if path is None:
                raise ValueError("ADMIN_DB_PATH is required for SQLite storage")
            path.parent.mkdir(parents=True, exist_ok=True)
            with closing(sqlite3.connect(path)) as db, db:
                db.execute("""CREATE TABLE IF NOT EXISTS admin_records (
                    pk TEXT NOT NULL, sk TEXT NOT NULL, payload TEXT NOT NULL,
                    expires_at INTEGER, username TEXT, PRIMARY KEY (pk, sk)
                )""")
            path.chmod(0o600)

    @classmethod
    def from_config(cls):
        from app.core.config import ADMIN_BACKEND, ADMIN_DB_PATH, ADMIN_DDB_TABLE, AWS_REGION_NAME
        if ADMIN_BACKEND == "sqlite":
            return cls(ADMIN_DB_PATH)
        if ADMIN_BACKEND != "dynamodb" or not ADMIN_DDB_TABLE:
            raise ValueError("Configure ADMIN_BACKEND=sqlite or dynamodb with ADMIN_DDB_TABLE")
        import boto3
        resource = boto3.resource("dynamodb", **({"region_name": AWS_REGION_NAME} if AWS_REGION_NAME else {}))
        return cls(table=resource.Table(ADMIN_DDB_TABLE))

    def _get(self, pk: str, sk: str) -> dict | None:
        if self._table is not None:
            return self._table.get_item(Key={"pk": pk, "sk": sk}, ConsistentRead=True).get("Item")
        with closing(sqlite3.connect(self._path, timeout=10)) as db:
            row = db.execute("SELECT payload FROM admin_records WHERE pk=? AND sk=?", (pk, sk)).fetchone()
        return json.loads(row[0]) if row else None

    def _put(self, pk: str, sk: str, payload: dict, *, create_only: bool = False) -> bool:
        item = {**payload, "pk": pk, "sk": sk}
        if self._table is not None:
            try:
                self._table.put_item(Item=item, **({"ConditionExpression": "attribute_not_exists(pk)"} if create_only else {}))
            except ClientError as exc:
                if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    return False
                raise
            return True
        with closing(sqlite3.connect(self._path, timeout=10)) as db, db:
            sql = "INSERT OR IGNORE" if create_only else "INSERT OR REPLACE"
            result = db.execute(
                f"{sql} INTO admin_records (pk, sk, payload, expires_at, username) VALUES (?, ?, ?, ?, ?)",
                (pk, sk, json.dumps(item), item.get("expires_at"), item.get("username")),
            )
        return result.rowcount == 1

    def _delete(self, pk: str, sk: str) -> None:
        if self._table is not None:
            self._table.delete_item(Key={"pk": pk, "sk": sk})
        else:
            with closing(sqlite3.connect(self._path, timeout=10)) as db, db:
                db.execute("DELETE FROM admin_records WHERE pk=? AND sk=?", (pk, sk))

    def _query(self, pk: str, *, limit: int | None = None, after: str | None = None, username: str = "") -> list[dict]:
        if self._table is not None:
            condition = Key("pk").eq(pk)
            if after:
                condition &= Key("sk").lt(after)
            options = {"KeyConditionExpression": condition, "ScanIndexForward": False, "ConsistentRead": True}
            if username:
                # ponytail: one log partition; add a username index if login volume grows.
                options["FilterExpression"] = Attr("username").eq(username)
            rows = []
            while True:
                if limit is not None:
                    options["Limit"] = limit - len(rows)
                page = self._table.query(**options)
                rows.extend(page.get("Items", []))
                if (limit is not None and len(rows) >= limit) or not page.get("LastEvaluatedKey"):
                    return rows
                options["ExclusiveStartKey"] = page["LastEvaluatedKey"]
        sql, values = "SELECT payload FROM admin_records WHERE pk=?", [pk]
        if after:
            sql += " AND sk<?"
            values.append(after)
        if username:
            sql += " AND username=?"
            values.append(username)
        sql += " ORDER BY sk DESC"
        if limit is not None:
            sql += " LIMIT ?"
            values.append(limit)
        with closing(sqlite3.connect(self._path, timeout=10)) as db:
            return [json.loads(row[0]) for row in db.execute(sql, values)]

    def _update_user(self, username: str, changes: dict, *, expected_version: str | None = None) -> dict | None:
        if self._table is not None:
            names = {f"#f{i}": key for i, key in enumerate(changes)}
            values = {f":f{i}": value for i, value in enumerate(changes.values())}
            expression = ", ".join(f"#f{i}=:f{i}" for i in range(len(changes)))
            condition = Attr("pk").exists()
            if expected_version is not None:
                condition &= Attr("auth_version").eq(expected_version) & Attr("enabled").eq(True)
            try:
                return self._table.update_item(
                    Key={"pk": "USER", "sk": username}, UpdateExpression=f"SET {expression}",
                    ExpressionAttributeNames=names, ExpressionAttributeValues=values,
                    ConditionExpression=condition, ReturnValues="ALL_NEW",
                )["Attributes"]
            except ClientError as exc:
                if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    return None
                raise
        with closing(sqlite3.connect(self._path, timeout=10)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT payload FROM admin_records WHERE pk='USER' AND sk=?", (username,)).fetchone()
            if not row:
                return None
            user = json.loads(row[0])
            if expected_version is not None and (not user["enabled"] or user["auth_version"] != expected_version):
                return None
            user.update(changes)
            db.execute("UPDATE admin_records SET payload=? WHERE pk='USER' AND sk=?", (json.dumps(user), username))
            return user

    @staticmethod
    def _new_user(username: str, password: str, role: str = "user") -> dict:
        if not _USERNAME.fullmatch(username):
            raise ValueError("账号须为 3–64 位字母、数字、下划线、点或短横线，并以字母或数字开头")
        if not 8 <= len(password) <= 128:
            raise ValueError("密码须为 8–128 位字符")
        return {
            "username": username, "password_hash": _hash_password(password), "role": role,
            "enabled": True, "auth_version": secrets.token_hex(16),
            "created_at": _timestamp(), "last_login_at": None,
        }

    def _ensure_admin(self) -> None:
        if not self._initialized:
            if self._get("USER", "admin") is None:
                self._put("USER", "admin", self._new_user("admin", "root123!", "admin"), create_only=True)
            self._initialized = True

    def list_users(self) -> list[dict]:
        self._ensure_admin()
        return [_public_user(user) for user in sorted(self._query("USER"), key=lambda row: (row["role"] != "admin", row["username"]))]

    def create_user(self, username: str, password: str) -> dict:
        self._ensure_admin()
        user = self._new_user(username, password)
        if not self._put("USER", username, user, create_only=True):
            raise FileExistsError("账号已存在")
        return _public_user(user)

    def update_user(self, username: str, *, password: str | None = None, enabled: bool | None = None) -> dict:
        if username == "admin":
            raise ValueError("内置管理员账号不可修改或停用")
        changes = {"auth_version": secrets.token_hex(16)}
        if password is not None:
            if not 8 <= len(password) <= 128:
                raise ValueError("密码须为 8–128 位字符")
            changes["password_hash"] = _hash_password(password)
        if enabled is not None:
            changes["enabled"] = enabled
        if len(changes) == 1:
            raise ValueError("请提供新密码或账号状态")
        user = self._update_user(username, changes)
        if user is None:
            raise KeyError("账号不存在")
        return _public_user(user)

    def login(self, username: str, password: str, ip: str) -> dict | None:
        self._ensure_admin()
        user = self._get("USER", username)
        # Unknown accounts still perform the same password work.
        password_hash = (user or self._get("USER", "admin"))["password_hash"]
        valid_password = _verify_password(password, password_hash)
        if user and valid_password and user["enabled"]:
            user = self._update_user(username, {"last_login_at": _timestamp()}, expected_version=user["auth_version"])
        else:
            user = None
        log = {"username": username, "timestamp": _timestamp(), "ip": ip, "success": user is not None}
        self._put("LOGIN", f"{log['timestamp']}#{secrets.token_hex(8)}", log)
        if user is None:
            return None
        token = secrets.token_urlsafe(32)
        expires_at = int(time.time()) + SESSION_TTL
        if self._table is None:
            with closing(sqlite3.connect(self._path, timeout=10)) as db, db:
                db.execute("DELETE FROM admin_records WHERE pk='SESSION' AND expires_at<=?", (int(time.time()),))
        self._put("SESSION", hashlib.sha256(token.encode()).hexdigest(), {
            "username": username, "auth_version": user["auth_version"], "expires_at": expires_at,
        })
        return {"token": token, "user": _public_user(user), "expires_at": expires_at}

    def session(self, token: str) -> dict | None:
        if not token or len(token) > 128:
            return None
        key = hashlib.sha256(token.encode()).hexdigest()
        session = self._get("SESSION", key)
        if session is None:
            return None
        user = self._get("USER", session["username"])
        if int(session["expires_at"]) <= time.time() or not user or not user["enabled"] or user["auth_version"] != session["auth_version"]:
            self._delete("SESSION", key)
            return None
        return {"user": _public_user(user), "expires_at": int(session["expires_at"])}

    def logout(self, token: str) -> None:
        if token and len(token) <= 128:
            self._delete("SESSION", hashlib.sha256(token.encode()).hexdigest())

    def login_logs(self, *, limit: int = 25, after: str | None = None, username: str = "") -> dict:
        rows = self._query("LOGIN", limit=limit + 1, after=after, username=username)
        return {
            "logs": [{key: row[key] for key in ("username", "timestamp", "ip", "success")} for row in rows[:limit]],
            "after": rows[limit - 1]["sk"] if len(rows) > limit else None,
        }
