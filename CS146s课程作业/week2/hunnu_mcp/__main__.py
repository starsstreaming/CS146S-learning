"""Entry: `python -m hunnu_mcp` (stdio server) or `python -m hunnu_mcp login`."""

from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "login":
        from hunnu_mcp.login import main as login_main

        login_main()
        return
    from hunnu_mcp.server import main as serve

    serve()


if __name__ == "__main__":
    main()
