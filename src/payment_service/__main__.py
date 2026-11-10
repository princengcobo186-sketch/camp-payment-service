"""Entrypoint: python -m payment_service"""

import os

import uvicorn

from payment_service.main import create_app

if __name__ == "__main__":
    # Bind all interfaces: the container's network namespace is the isolation boundary.
    uvicorn.run(create_app(), host="0.0.0.0", port=int(os.environ.get("PORT", "8080")))  # noqa: S104
