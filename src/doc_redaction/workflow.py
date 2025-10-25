from typing import Any

import typer
from loguru import logger
from strands import Agent
from strands.agent.agent_result import AgentResult
from strands_tools import current_time, image_reader

from doc_redaction.agent import MODEL_IDS, create_agent
from doc_redaction.output import SensitiveData
from doc_redaction.promt import (
    CONVERTER_SYSTEM_PROMPT,
    DETECTION_SYSTEM_PROMPT,
    REDACTED_SYSTEM_PROMPT,
)
from doc_redaction.tool.detect_sensitive_data import detect_sensitive_data
from doc_redaction.tool.redact_sensitive_data import redact_sensitive_data
from doc_redaction.tool.tool_utils import omit_empty_keys, remove_temp_files, save_file
from doc_redaction.utils.commons import InvalidDocumentKeyError, save_as_json
from doc_redaction.utils.doc_assessment import assess_doc_quality
from doc_redaction.utils.doc_reader import merge_markdown_strings, pdf_to_png
from doc_redaction.utils.token_tracker import summarize_token_usage, token_usage

DIR: str = "data/"
PREFIX: dict[str, str] = {
    "confidential": "confidential/",
    "contract": "contract/",
    "markdown": "markdown/",
    "quality": "quality/",
    "redact": "redact/",
    "temp": "temp/img/",
    "token": "token/",
}
FORMAT: dict[str, str] = {
    "json": ".json",
    "md": ".md",
    "pdf": ".pdf",
}


# key = "GRB_mit_Niessbrauchrecht"
def run_doc_processing_wf(key: str = "spielbank_rocketbase_vertrag"):
    if not isinstance(key, str) or not key:
        raise InvalidDocumentKeyError()

    # Step 0: Assess document quality
    DOC_QUALITY_IN: str = f"{DIR}{PREFIX['contract']}{key}{FORMAT['pdf']}"
    DOC_QUALITY_OUT: str = f"{DIR}{PREFIX['quality']}{key}{FORMAT['json']}"
    doc_quality: dict[str, Any] = assess_doc_quality(
        file_path=DOC_QUALITY_IN,
        output_path=DOC_QUALITY_OUT,
    )

    # Step 1: Convert input contract from PDF to markdwon format using vision model
    multimodal_agent: Agent = create_agent(
        name="multimodal_agent",
        system_prompt=CONVERTER_SYSTEM_PROMPT,
        tools=[
            # file_write,
            image_reader,
            merge_markdown_strings,
            save_file,
            remove_temp_files,
        ],
    )
    CONVERT_IN: list[str] = pdf_to_png(
        pdf_path=f"{DIR}{PREFIX['contract']}{key}{FORMAT['pdf']}",
        output_dir=f"{DIR}{PREFIX['temp']}",
    )
    CONVERT_OUT: str = f"{DIR}{PREFIX['markdown']}{key}{FORMAT['md']}"
    CONVERT_USER_PROMPT: str = f"""
    Convert the following document to markdown: {CONVERT_IN}.
    Save the result to {CONVERT_OUT}.
    Finally, clean up temporary files using remove_temp_files tool.
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
    Analyze the following document: {convert_result!s}.
    Detect sensitive data.
    """

    detector_agent: Agent = create_agent(
        name="detector_agent",
        system_prompt=DETECTION_SYSTEM_PROMPT,
        tools=[
            current_time,
            detect_sensitive_data,
            omit_empty_keys,
        ],
    )
    detector_agent.model.update_config(
        model_id=MODEL_IDS["haiku"],
        max_tokens=64000,
    )

    detector_result: str = detector_agent.structured_output(
        output_model=SensitiveData,
        prompt=DETECT_USER_PROMPT,
    ).model_dump_json(indent=2)

    save_as_json(data=detector_result, filename=DETECT_OUT)

    detector_result_token_usage: dict[str, dict[str, Any]] = {
        token_type: token_usage(
            content=content,
            token_type=token_type,
            model=detector_agent.model.get_config()["model_id"],
        )
        for token_type, content in {
            "inputTokens": DETECT_USER_PROMPT,
            "outputTokens": detector_result,
        }.items()
    }

    logger.info(f"{detector_agent.name} token usage: {detector_result_token_usage}")
    logger.info(f"Saved detection result in {DETECT_OUT}")

    # Step 3: Redact sensitive information
    REDACT_OUT: str = f"{DIR}{PREFIX['redact']}{key}{FORMAT['md']}"

    REDACTED_USER_PROMPT: str = f"""
    Analyze the following document: {convert_result!s}.
    Redact all information provided in {detector_result!s} except for the document_analysis field.
    Save the result to {REDACT_OUT}.
    """

    redact_agent: Agent = create_agent(
        name="redact_agent",
        system_prompt=REDACTED_SYSTEM_PROMPT,
        tools=[save_file, redact_sensitive_data],
    )
    redact_agent.model.update_config(
        model_id=MODEL_IDS["haiku"],
        max_tokens=64000,
    )

    result_redacted: AgentResult = redact_agent(REDACTED_USER_PROMPT)
    redacted_result_token_usage = token_usage(
        content=result_redacted.metrics.accumulated_usage,
        model=redact_agent.model.get_config()["model_id"],
    )
    logger.info(f"Conversion stopping reason: {result_redacted.stop_reason}")
    logger.info(f"{redact_agent.name} token usage: {redacted_result_token_usage}")
    logger.info(f"Saved redaction result in {REDACT_OUT}")

    # Step 4: Summarize token usage
    all_agents_tokens: dict[str, dict[str, Any]] = {
        "multimodal_agent": detector_result_token_usage,
        "detector_agent": convert_result_token_usage,
        "redact_agent": redacted_result_token_usage,
    }
    token_summary: str = summarize_token_usage(all_agents_tokens)
    TOKEN_SUMMARY_OUT: str = f"{DIR}{PREFIX['token']}{key}{FORMAT['json']}"
    save_as_json(data=token_summary, filename=TOKEN_SUMMARY_OUT)

    return doc_quality, detector_result, token_summary


if __name__ == "__main__":
    typer.run(run_doc_processing_wf)
