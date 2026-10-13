"""No Minecraft binaries or EULA. Honest disposable world-writing fixture."""

import pathlib, time, signal, sys, threading
from status_fixture import serve

threading.Thread(target=serve, daemon=True).start()
p = pathlib.Path("/world")
p.mkdir(exist_ok=True)
signal.signal(signal.SIGTERM, lambda *_: sys.exit(0))
print("[Fixture] No Minecraft server. Synthetic lifecycle and world data.", flush=True)
print("FixturePlayer joined the game", flush=True)
while True:
    (p / "level.dat").write_text(
        "BLOCKOPS FIXTURE WORLD\ntick=" + str(time.time()) + "\n"
    )
    print("[Fixture] World tick saved", flush=True)
    time.sleep(5)
