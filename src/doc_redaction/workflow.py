from typing import Any

import typer
from loguru import logger
from strands import Agent
from strands.agent.agent_result import AgentResult
from strands_tools import file_read, file_write

from doc_redaction.agent import create_agent
from doc_redaction.output import SensitiveData
from doc_redaction.promt import (
    DETECTION_SYSTEM_PROMPT,
    MULTIMODAL_SYSTEM_PROMPT,
    REDACTED_SYSTEM_PROMPT,
)
from doc_redaction.tool.detect_sensitive_data import detect_sensitive_data
from doc_redaction.tool.redact_sensitive_data import redact_sensitive_data
from doc_redaction.tool.tool_utils import omit_empty_keys
from doc_redaction.utils.commons import InvalidDocumentKeyError, save_as_json
from doc_redaction.utils.token_tracker import summarize_token_usage, token_usage

DIR: str = "data/"
PREFIX: dict[str, str] = {"confidential": "confidential/", "contract": "contract/", "markdown": "markdown/", "redact": "redact/", "token": "token/"}
FORMAT: dict[str, str] = {
    "json": ".json",
    "md": ".md",
    "pdf": ".pdf",
}


def run_doc_processing_wf(key: str = "spielbank_rocketbase_vertrag"):
    if not isinstance(key, str) or not key:
        raise InvalidDocumentKeyError()

    # Step 1: Convert input contract from PDF to markdwon format
    multimodal_agent: Agent = create_agent(
        name="MultimodalAgent",
        system_prompt=MULTIMODAL_SYSTEM_PROMPT,
        tools=[file_read, file_write],
    )
    CONVERT_IN: str = f"{DIR}{PREFIX['contract']}{key}{FORMAT['pdf']}"
    CONVERT_OUT: str = f"{DIR}{PREFIX['markdown']}{key}{FORMAT['md']}"
    CONVERT_USER_PROMPT: str = f"""
    Convert the following document to markdown: {CONVERT_IN}. Save the result to {CONVERT_OUT}.
    """

    convert_result: AgentResult = multimodal_agent(CONVERT_USER_PROMPT)
    convert_result_token_usage = token_usage(
        content=convert_result.metrics.accumulated_usage,
        model=multimodal_agent.model.get_config()["model_id"],
    )
    logger.info(f"Conversion stopping reason: {convert_result.stop_reason}")
    logger.info(f"{multimodal_agent.name} token usage: {convert_result_token_usage}")
    logger.info(f"Saved conversion result in {CONVERT_OUT}")

    # Step 2: Detect sensitve information
    DETECT_OUT: str = f"{DIR}{PREFIX['confidential']}{key}{FORMAT['json']}"
    DETECT_USER_PROMPT: str = f"""
    Analyze the following document: {convert_result.metrics.tool_metrics["file_write"].tool["input"]["content"]}.
    Detect sensitive data. Save the result to {DETECT_OUT}.

    IMPORTANT:
    - Only include information you find in the text.
    - Do not add any information on your own.
    - If you do not find any information for a specific field, return an empty list for that field.
    """

    detector_agent: Agent = create_agent(
        name="DetectorAgent",
        system_prompt=DETECTION_SYSTEM_PROMPT,
        tools=[detect_sensitive_data, omit_empty_keys, file_write],
    )

    detector_result: str = detector_agent.structured_output(
        output_model=SensitiveData,
        prompt=DETECT_USER_PROMPT,
    ).model_dump_json(indent=2)

    detector_result_token_usage = token_usage(content=DETECT_USER_PROMPT)
    save_as_json(data=detector_result, filename=DETECT_OUT)

    logger.info(f"{detector_agent.name} token usage: {detector_result_token_usage}")
    logger.info(f"Saved detection result in {DETECT_OUT}")

    # Step 3: Redact sensitive information
    REDACT_OUT: str = f"{DIR}{PREFIX['redact']}{key}{FORMAT['md']}"

    REDACTED_USER_PROMPT: str = f"""
    Analyze the following document: {convert_result.metrics.tool_metrics["file_write"].tool["input"]["content"]}.
    Redact all information provided in {detector_result} except for the document_analysis field.
    Save the result to {REDACT_OUT}.
    """

    redact_agent: Agent = create_agent(
        name="RedactAgent",
        system_prompt=REDACTED_SYSTEM_PROMPT,
        tools=[file_write, redact_sensitive_data],
    )

    res_redacted: AgentResult = redact_agent(REDACTED_USER_PROMPT)
    redacted_result_token_usage = token_usage(
        content=res_redacted.metrics.accumulated_usage,
        model=redact_agent.model.get_config()["model_id"],
    )
    logger.info(f"Conversion stopping reason: {res_redacted.stop_reason}")
    logger.info(f"{redact_agent.name} token usage: {redacted_result_token_usage}")
    logger.info(f"Saved redaction result in {REDACT_OUT}")

    # Summarize token usage
    all_agents_tokens: dict[str, dict[str, Any]] = {
        "multimodal_agent": detector_result_token_usage,
        "detector_agent": convert_result_token_usage,
        "redact_agent": redacted_result_token_usage,
    }
    token_summary: str = summarize_token_usage(all_agents_tokens)
    TOKEN_SUMMARY_OUT: str = f"{DIR}{PREFIX['token']}{key}{FORMAT['json']}"
    save_as_json(data=token_summary, filename=TOKEN_SUMMARY_OUT)

    return res_redacted


if __name__ == "__main__":
    typer.run(run_doc_processing_wf)
