"""Entry point: `python app.py` sobe a API da loja."""
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from src.app import create_app  # noqa: E402 — logging configurado antes da config
from src.config import settings  # noqa: E402

app = create_app()

if __name__ == "__main__":
    logging.getLogger(__name__).info("Servidor iniciado em http://%s:%s", settings.HOST, settings.PORT)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
