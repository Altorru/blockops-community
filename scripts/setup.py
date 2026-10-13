import getpass, hashlib, json, os, pathlib, secrets

p = pathlib.Path("secrets")
p.mkdir(mode=0o700, exist_ok=True)
users = p / "users.json"
data = json.loads(users.read_text()) if users.exists() else {}
name = input("Local username: ").strip()
if not name or len(name) > 40:
    raise SystemExit("Username required (max 40 characters)")
role = input("Role [admin/viewer] (admin): ").strip() or "admin"
if role not in ("admin", "viewer"):
    raise SystemExit("Invalid role")
password = getpass.getpass("Password (at least 12 characters): ")
if len(password) < 12:
    raise SystemExit("Password too short")
salt = secrets.token_bytes(16)
data[name] = {
    "salt": salt.hex(),
    "hash": hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 300000).hex(),
    "role": role,
}
users.write_text(json.dumps(data))
users.chmod(0o600)
token = p / "agent-token"
if not token.exists():
    token.write_text(secrets.token_urlsafe(48))
    token.chmod(0o600)
print("Local credentials saved. Restart console to load user changes.")
