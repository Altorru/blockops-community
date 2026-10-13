"""Creates disposable local QA users in a FRESH fixture installation only."""

import hashlib, json, pathlib, secrets

p = pathlib.Path("secrets")
if (p / "users.json").exists():
    raise SystemExit(
        "Existing users preserved. Use a fresh extracted fixture directory."
    )
p.mkdir(mode=0o700, exist_ok=True)
salt = secrets.token_bytes(16)
password = secrets.token_urlsafe(24)
digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 300000).hex()
(p / "users.json").write_text(
    json.dumps(
        {
            name: {"salt": salt.hex(), "hash": digest, "role": role}
            for name, role in [("qa", "admin"), ("viewer", "viewer")]
        }
    )
)
(p / "qa-password").write_text(password)
(p / "agent-token").write_text(secrets.token_urlsafe(48))
for f in p.iterdir():
    f.chmod(0o600)
for folder in ["world", "backups", "evidence"]:
    pathlib.Path(folder).mkdir(exist_ok=True)
print(
    "Disposable users qa / viewer created. Password: local secrets/qa-password. Do not use for production."
)
