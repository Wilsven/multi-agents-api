from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.schemas.translate import LanguageDetectorRequest, TranslateRequest
from app.services.translate.language_openai import LanguageOpenAI

router = APIRouter(prefix="/translate", tags=["Translate"])


@router.post("")
async def translate_endpoint(request: Request, translate_request: TranslateRequest):
    try:
        language_openai: LanguageOpenAI = request.app.state.translate_service
        response = await language_openai.translate(translate_request)

        return JSONResponse(content=response, status_code=200)
    except Exception as e:
        error_response = {"Exception in /translate: ": str(e)}
        return JSONResponse(content=error_response, status_code=500)


@router.post("/get_language")
async def detect_language_endpoint(
    request: Request, language_detect_request: LanguageDetectorRequest
):
    try:
        language_openai: LanguageOpenAI = request.app.state.translate_service
        language = await language_openai.get_language(
            language_detect_request.text
        )  # { 'english', 'chinese', 'tamil', 'malay', 'unknown' }

        return JSONResponse(content=language, status_code=200)
    except Exception as e:
        error_response = {"Exception in /translate/get_language: ": str(e)}
        return JSONResponse(content=error_response, status_code=500)
