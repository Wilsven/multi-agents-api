import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from azure.core.exceptions import ResourceNotFoundError
from azure.identity.aio import AzureDeveloperCliCredential
from azure.keyvault.secrets.aio import SecretClient as AsyncSecretClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.database.cosmos_client import PyMongoCosmosDBClient
from app.middleware.audit import audit_middleware
from app.routers import authentication, booking, clinic, record, user, vaccine

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


def create_app(test: bool = False) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("🚀 Starting up...")
        # Replace these with your own values, either in environment variables or directly here

        # Azure Cosmos DB
        AUDIT_DATABASE_ID = os.getenv("AZURE_AUDIT_DATABASE")
        AUDIT_COLLECTION_ID = AUDIT_DATABASE_ID

        # Azure Key Vault
        AZURE_KEYVAULT_NAME = os.getenv("AZURE_KEYVAULT_NAME")

        # Use AzureCliCredential to bypass using service principal when AZURE_CLIENT_ID
        # (along with AZURE_TENANT_ID and AZURE_CLIENT_SECRET) is set
        azure_credential = AzureDeveloperCliCredential()

        keyvault_client = AsyncSecretClient(
            vault_url=f"https://{AZURE_KEYVAULT_NAME}.vault.azure.net/",
            credential=azure_credential,
        )
        # Attach it to app.state
        app.state.keyvault_client = keyvault_client

        async with keyvault_client:
            # Get secret key from key vault
            try:
                retrieved_secret = await keyvault_client.get_secret("secretKey")
                secret_key = retrieved_secret.value
            except ResourceNotFoundError:
                secret_key = os.getenv("SECRET_KEY", None)

            # Store on app.state
            app.state.secret_key = secret_key

            try:
                retrieved_secret = await keyvault_client.get_secret(
                    "cosmosdbConnectionString"
                )
                cosmos_connection_string = retrieved_secret.value
            except ResourceNotFoundError:
                cosmos_connection_string = os.getenv(
                    "AZURE_COSMOSDB_CONNECTION_STRING", None
                )

            finally:
                logger.info(f"🔑 SECRET_KEY set: {secret_key is not None}.")
                logger.info(
                    f"🔑 AZURE_COSMOSDB_CONNECTION_STRING set: {cosmos_connection_string is not None}."
                )

        app.state.audit_client = PyMongoCosmosDBClient(
            database_id=AUDIT_DATABASE_ID,
            collection_id=AUDIT_COLLECTION_ID,
            connection_string=cosmos_connection_string,
        )

        # Hand over control to FastAPI
        yield

    if not test:
        app = FastAPI(lifespan=lifespan)
        app.middleware("http")(audit_middleware)
    else:
        app = FastAPI()

    # Enable CORS
    origins = [
        "http://localhost:4200",
        "http://localhost:8000",
        "http://localhost:8001",
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(authentication.router)
    app.include_router(booking.router)
    app.include_router(clinic.router)
    app.include_router(record.router)
    app.include_router(user.router)
    app.include_router(vaccine.router)

    @app.get("/")
    async def root():
        return JSONResponse(content={"detail": "Hello World!"})

    return app


app = create_app()


async def run_app():
    config_main = uvicorn.Config(
        "main:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=["."]
    )

    server_main = uvicorn.Server(config_main)

    # Run both servers concurrently
    await asyncio.gather(server_main.serve())


# main function to run the app
if __name__ == "__main__":
    asyncio.run(run_app())
