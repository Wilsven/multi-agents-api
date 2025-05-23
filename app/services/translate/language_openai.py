import json
from dataclasses import dataclass
from typing import Any, Awaitable, cast

from lingua import Language, LanguageDetectorBuilder
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessageParam,
    ChatCompletionReasoningEffort,
    ChatCompletionToolParam,
)
from pandas import DataFrame
from tabulate import tabulate

from app.services.approaches import settings
from app.services.approaches.promptmanager import PromptManager

from app.schemas.translate import TranslateRequest, TranslateResponse


@dataclass
class GPTReasoningModelSupport:
    streaming: bool


class LanguageOpenAI:
    # List of GPT reasoning models support
    GPT_REASONING_MODELS = {
        "o1": GPTReasoningModelSupport(streaming=False),
        "o3-mini": GPTReasoningModelSupport(streaming=True),
    }
    # Set a higher token limit for GPT reasoning models
    RESPONSE_DEFAULT_TOKEN_LIMIT = 1024
    RESPONSE_REASONING_DEFAULT_TOKEN_LIMIT = 8192

    def __init__(
        self,
        openai_client: AsyncOpenAI,
        chatgpt_model: str,
        chatgpt_deployment: str,
        prompt_manager: PromptManager,
        official_terms: DataFrame,
    ):
        self.openai_client = openai_client
        self.chatgpt_model = chatgpt_model
        self.chatgpt_deployment = chatgpt_deployment
        self.prompt_manager = prompt_manager
        self.languages = [
            Language.ENGLISH,
            Language.CHINESE,
            Language.TAMIL,
            Language.MALAY,
        ]
        self.translator_prompt = self.prompt_manager.load_prompt("translator.prompty")
        self.language_detector_prompt = self.prompt_manager.load_prompt(
            "language_detector.prompty"
        )
        self.language_detector_tool = self.prompt_manager.load_tools(
            "language_detector_tool.json"
        )
        self.official_terms = official_terms
        self.query_response_token_limit = settings.CHAT_RESPONSE_MAX_TOKENS

    async def get_language(self, query_text: str) -> str:
        detector = LanguageDetectorBuilder.from_languages(*self.languages).build()
        language = detector.detect_language_of(query_text)

        if language is None:
            print("Language not detected. Setting language to unknown.")
            language = "unknown"
        else:
            confidence_scores = detector.compute_language_confidence_values(query_text)
            if confidence_scores[0].value > settings.LANG_SCORE_THRESHOLD:
                language = str(language).split(".")[1].lower()
            else:
                query_messages = self.prompt_manager.render_prompt(
                    self.language_detector_prompt, {"user_query": query_text}
                )
                language_tool: list[ChatCompletionToolParam] = (
                    self.language_detector_tool
                )
                language_detector_completion = cast(
                    ChatCompletion,
                    await self.create_chat_completion(
                        chatgpt_model=self.chatgpt_model,
                        chatgpt_deployment=self.chatgpt_deployment,
                        messages=query_messages,
                        response_token_limit=self.get_response_token_limit(
                            self.chatgpt_model, self.query_response_token_limit
                        ),
                        temperature=settings.TEMPERATURE,
                        n=1,
                        tools=language_tool,
                        reasoning_effort="low",
                        response_format={"type": "json_object"},  # JSON mode
                        seed=settings.SEED,
                    ),
                )

                language = self.get_tool_result(
                    language_detector_completion,
                    default_response="english",
                    function_name="language_detector",
                    parameter_name="language",
                )
        return language  # { 'english', 'chinese', 'tamil', 'malay', 'unknown' }

    async def translate(self, translate_request: TranslateRequest) -> str:

        selected_language = translate_request.target_language.value.upper()
        language_detected = await self.get_language(translate_request.text)
        language_detected = language_detected.upper()

        self.terms_markdown = tabulate(
            self.official_terms[[language_detected, selected_language]],
            headers="keys",
            tablefmt="pipe",
            showindex=False,
        )

        query_messages = self.prompt_manager.render_prompt(
            self.translator_prompt,
            {
                "language": translate_request.target_language,
                "official_terms_languages": self.official_terms,
                "input": translate_request.text,
            },
        )
        chat_completion = cast(
            ChatCompletion,
            await self.create_chat_completion(
                chatgpt_model=self.chatgpt_model,
                chatgpt_deployment=self.chatgpt_deployment,
                messages=query_messages,
                response_token_limit=self.get_response_token_limit(
                    self.chatgpt_model, self.query_response_token_limit
                ),
                n=1,
                temperature=0.0,
                seed=settings.SEED,
            ),
        )

        translated_text = chat_completion.choices[0].message.content
        translate_response = TranslateResponse(
            translated_text=translated_text, language_detected=language_detected
        )

        return translate_response.model_dump()

    def create_chat_completion(
        self,
        chatgpt_model: str,
        chatgpt_deployment: str,
        messages: list[ChatCompletionMessageParam],
        response_token_limit: int,
        temperature: float | None = None,
        tools: list[ChatCompletionToolParam] | None = None,
        n: int | None = None,
        should_stream: bool = False,
        reasoning_effort: ChatCompletionReasoningEffort | None = None,
        response_format: dict | None = None,
        seed: int | None = None,
    ) -> Awaitable[ChatCompletion] | Awaitable[AsyncStream[ChatCompletionChunk]]:
        if chatgpt_model in self.GPT_REASONING_MODELS:
            params: dict[str, Any] = {
                # max_tokens is not supported
                "max_completion_tokens": response_token_limit
            }

            # Adjust parameters for reasoning models
            supported_features = self.GPT_REASONING_MODELS[chatgpt_model]
            if supported_features.streaming and should_stream:
                params["stream"] = True
                params["stream_options"] = {"include_usage": True}
            params["reasoning_effort"] = reasoning_effort

        else:
            # Include parameters that may not be supported for reasoning models
            params = {"max_tokens": response_token_limit, "temperature": temperature}

        if should_stream:
            params["stream"] = True
            params["stream_options"] = {"include_usage": True}

        if response_format:
            params["response_format"] = response_format

        if tools:
            params["tools"] = tools

        # Azure OpenAI takes the deployment name as the model name
        return self.openai_client.chat.completions.create(
            model=chatgpt_deployment if chatgpt_deployment else chatgpt_model,
            messages=messages,
            seed=seed,
            n=n or 1,
            **params,
        )

    def get_response_token_limit(self, model: str, default_limit: int) -> int:
        if model in self.GPT_REASONING_MODELS:
            return self.RESPONSE_REASONING_DEFAULT_TOKEN_LIMIT

        return default_limit

    def get_tool_result(
        self,
        chat_completion: ChatCompletion,
        default_response: str,
        function_name: str,
        parameter_name: str,
    ):
        response_message = chat_completion.choices[0].message

        if response_message.tool_calls:
            for tool in response_message.tool_calls:
                if tool.type != "function":
                    continue
                function = tool.function
                if function.name == function_name:
                    arg = json.loads(function.arguments)
                    result = arg.get(parameter_name, self.NO_RESPONSE)
                    if result != self.NO_RESPONSE:
                        return result
        elif query_text := response_message.content:
            if query_text.strip() != self.NO_RESPONSE:
                return query_text
        return default_response
