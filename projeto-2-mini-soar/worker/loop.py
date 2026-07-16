import logging
import os
import time

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s worker %(message)s")
logger = logging.getLogger("worker")

API_URL = os.getenv("API_URL", "http://api:8002")
INTERVAL_SECONDS = int(os.getenv("PLAYBOOK_INTERVAL_SECONDS", "60"))


def run_once() -> None:
    try:
        response = httpx.post(f"{API_URL}/playbook/run-queue", timeout=10.0)
        response.raise_for_status()
        logger.info("playbook executado: %s", response.json())
    except Exception as exc:  # noqa: BLE001
        logger.warning("falha ao executar playbook agendado: %s", exc)


def main() -> None:
    logger.info(
        "worker iniciado, chamando %s/playbook/run-queue a cada %ss",
        API_URL,
        INTERVAL_SECONDS,
    )
    while True:
        run_once()
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
