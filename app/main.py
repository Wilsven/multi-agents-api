import asyncio
import logging
import os
from contextlib import asynccontextmanager

import uvicorn
from azure.core.exceptions import ResourceNotFoundError
from azure.identity.aio import (
    AzureDeveloperCliCredential,
    ChainedTokenCredential,
    DefaultAzureCredential,
)
from azure.keyvault.secrets.aio import SecretClient as AsyncSecretClient
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from app.database.cosmos_client import PyMongoCosmosDBClient
from app.middleware.audit import audit_middleware
from app.routers import authentication, booking, clinic, record, user, vaccine, transcription
from app.services.speech.speech_to_text import SpeechToText

logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


def create_app(test: bool = False) -> FastAPI:

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logger.info("Starting up...")
        azure_credential = (
            None  # Define credential outside try block for finally access
        )
        try:
            # Replace these with your own values, either in environment variables or directly here

            # Azure Cosmos DB
            AUDIT_DATABASE_ID = os.getenv("AZURE_AUDIT_DATABASE")
            AUDIT_COLLECTION_ID = AUDIT_DATABASE_ID

            # Azure Key Vault
            AZURE_KEYVAULT_NAME = os.getenv("AZURE_KEYVAULT_NAME")

            # Use ChainedTokenCredential if as require both AZD CLI and Service Principal/Managed Identity
            azure_credential = ChainedTokenCredential(
                AzureDeveloperCliCredential(),
                # exclude_shared_token_cache_credential=True is good practice for DefaultAzureCredential in services
                DefaultAzureCredential(exclude_shared_token_cache_credential=True),
            )

            keyvault_client = AsyncSecretClient(
                vault_url=f"https://{AZURE_KEYVAULT_NAME}.vault.azure.net/",
                credential=azure_credential,
            )
            # Attach it to app.state
            app.state.keyvault_client = keyvault_client

            secret_key = None
            cosmos_connection_string = None

            async with keyvault_client:
                logger.info(
                    f"Attempting to connect to Key Vault: {AZURE_KEYVAULT_NAME}"
                )
                # Get secret key from key vault
                try:
                    retrieved_secret = await keyvault_client.get_secret("secretKey")
                    secret_key = retrieved_secret.value
                    logger.info("Retrieved 'secretKey' from Key Vault.")
                except ResourceNotFoundError:
                    logger.warning(
                        "Secret 'secretKey' not found in Key Vault. Trying environment variable."
                    )
                    secret_key = os.getenv("SECRET_KEY", None)

                # Get Cosmos DB connection string
                try:
                    retrieved_secret = await keyvault_client.get_secret(
                        "cosmosdbConnectionString"
                    )
                    cosmos_connection_string = retrieved_secret.value
                    logger.info("Retrieved 'cosmosdbConnectionString' from Key Vault.")
                except ResourceNotFoundError:
                    logger.warning(
                        "Secret 'cosmosdbConnectionString' not found in Key Vault. Trying environment variable."
                    )
                    cosmos_connection_string = os.getenv(
                        "AZURE_COSMOSDB_CONNECTION_STRING", None
                    )

            # Check if secrets were successfully obtained
            if secret_key is None:
                logger.warning(
                    "Secret 'secretKey' was not found in Key Vault or environment."
                )
            else:
                logger.info("🔑 Secret 'secretKey' has been set.")
            # Store on app.state
            app.state.secret_key = secret_key

            if cosmos_connection_string is None:
                logger.error(
                    "Secret 'cosmosdbConnectionString' was not found in Key Vault or environment. Audit client cannot be initialized."
                )
                # Ensure state reflects failure
                app.state.audit_client = None
                # Raise an exception here if the DB client is critical for startup
                raise RuntimeError("Failed to initialize database connection.")
            else:
                logger.info("🔑 Secret 'cosmosdbConnectionString' has been set.")
                # Initialize DB Client
                logger.info("Initializing Audit DB client...")
                app.state.audit_client = PyMongoCosmosDBClient(
                    database_id=AUDIT_DATABASE_ID,
                    collection_id=AUDIT_COLLECTION_ID,
                    connection_string=cosmos_connection_string,
                )
                logger.info("Audit DB client initialized.")

            logger.info("Initializing Speech-to-Text service...")
            
            # initialize Speech-to-Text service
            stt_service = SpeechToText()
            await stt_service.initialize()
            app.state.speech_to_text_service = stt_service

            logger.info("Startup complete. Handing over to FastAPI application.")

            # Hand over control to FastAPI
            yield

        except Exception as e:
            logger.error(
                f"Critical error during application startup: {e}", exc_info=True
            )
            # Depending on the error, you might want to prevent yield or handle differently
            # For now, we let it proceed to finally for cleanup attempt
            yield  # Ensure yield happens even on startup error to allow proper shutdown signalling

        finally:
            # Cleanup: Runs on shutdown, regardless of success or failure during startup/runtime
            logger.info("Shutting down...")
            if azure_credential:
                logger.info("Closing Azure credential client session...")
                await azure_credential.close()  # <--- Explicitly close the credential
                logger.info("Azure credential closed.")
            else:
                logger.info("Azure credential was not initialized. Skipping close.")

            # Add any other cleanup (e.g., explicitly closing DB client if needed)
            if hasattr(app.state, "audit_client") and app.state.audit_client:
                # Check if your DB client has a close method
                # if hasattr(app.state.audit_client, 'close'):
                #    await app.state.audit_client.close() # If async close
                #    # app.state.audit_client.close() # If sync close
                logger.info("Audit client resources released (if applicable).")

            logger.info("Shutdown complete.")

    if not test:
        app = FastAPI(lifespan=lifespan)
        app.middleware("http")(audit_middleware)
    else:
        app = FastAPI()

    # Enable CORS
    origins = [
        "http://localhost:3000",
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
    app.include_router(transcription.router)

    @app.get("/")
    async def root():
        return JSONResponse(content={"detail": "Hello World!"})

    @app.get("/health")
    async def health():
        return JSONResponse(content={"detail": "Healthy"})

    return app


app = create_app()


async def run_app():
    config = uvicorn.Config(
        "main:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=["."]
    )

    server = uvicorn.Server(config)

    # Run both servers concurrently
    await asyncio.gather(server.serve())


# main function to run the app
if __name__ == "__main__":
    asyncio.run(run_app())
