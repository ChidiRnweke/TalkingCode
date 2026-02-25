"""Export backend OpenAPI schema to frontend/openapi.json."""

import json
from pathlib import Path

from talkingcode.app import create_app


def main() -> None:
    app = create_app()
    schema = app.openapi()
    output_path = Path(__file__).resolve().parent.parent / "openapi.json"
    output_path.write_text(json.dumps(schema, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
