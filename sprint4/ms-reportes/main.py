import uvicorn
from fastapi import FastAPI

import views
from db import get_collection


def create_app():
    app = FastAPI(title="BITE.co - Microservicio de Reportes (Latencia)")

    @app.on_event("startup")
    def on_startup():
        # Asegura el indice (empresa, periodo). No falla el arranque si Mongo no esta listo.
        try:
            get_collection()
        except Exception:
            pass

    app.include_router(views.router)
    return app


app = create_app()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
