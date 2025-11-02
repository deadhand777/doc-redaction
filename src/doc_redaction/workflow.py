from typing import Any

import typer
from loguru import logger
from strands import Agent
from strands.multiagent import GraphBuilder
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


def process_and_summarize_tokens(agents: list[Agent], result) -> Any:
    """
    Process token usage for all agents and return a summarized token usage string.

    Args:
        agents: List of Agent objects used in the workflow
        result: Graph execution result containing accumulated usage data

    Returns:
        str: JSON string with summarized token usage across all agents
    """
    all_agents_tokens: dict[str, dict[str, Any]] = {
        agent.model.get_config()["model_id"]: token_usage(content=result.results[node_name].accumulated_usage, model=agent.model.get_config()["model_id"])
        for agent, node_name in [(agents[0], "convert_result"), (agents[1], "detector_result"), (agents[2], "redact_result")]
    }

    result: str = summarize_token_usage(all_agents_tokens)

    return result


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


def run_doc_processing_wf(key: str = "spielbank_rocketbase_vertrag"):
    """
    Run the document processing workflow for a given document key.

    Parameters:
        key (str): The document key to process.

    Returns:
        dict[str, Any]: Document quality assessment results.
        Any: Workflow execution result.
    """
    if not isinstance(key, str) or not key:
        raise InvalidDocumentKeyError()

    # Step 0: Assess document quality
    DOC_QUALITY_IN: str = f"{DIR}{PREFIX['contract']}{key}{FORMAT['pdf']}"
    DOC_QUALITY_OUT: str = f"{DIR}{PREFIX['quality']}{key}{FORMAT['json']}"
    doc_quality: dict[str, Any] = assess_doc_quality(
        file_path=DOC_QUALITY_IN,
        output_path=DOC_QUALITY_OUT,
    )

    # Step 1: Convert input contract from PDF to markdwon format using vision model Agent
    multimodal_agent: Agent = create_agent(
        name="multimodal_agent",
        system_prompt=CONVERTER_SYSTEM_PROMPT,
        tools=[
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

    # Step 2: Detect sensitve information Agent
    DETECT_OUT: str = f"{DIR}{PREFIX['confidential']}{key}{FORMAT['json']}"
    detector_agent: Agent = create_agent(
        name="detector_agent",
        system_prompt=DETECTION_SYSTEM_PROMPT,
        tools=[
            current_time,
            detect_sensitive_data,
            omit_empty_keys,
        ],
    )
    detector_agent.model.update_config(model_id=MODEL_IDS["haiku"])

    # Step 3: Redact sensitive information Agent
    REDACT_OUT: str = f"{DIR}{PREFIX['redact']}{key}{FORMAT['md']}"

    redact_agent: Agent = create_agent(
        name="redact_agent",
        system_prompt=REDACTED_SYSTEM_PROMPT,
        tools=[save_file, redact_sensitive_data],
    )
    redact_agent.model.update_config(model_id=MODEL_IDS["haiku"])

    # Step 4: Build and run workflow graph
    builder = GraphBuilder()

    builder.add_node(multimodal_agent, "convert_result")
    builder.add_node(detector_agent, "detector_result")
    builder.add_node(redact_agent, "redact_result")

    builder.add_edge("convert_result", "detector_result")
    builder.add_edge("convert_result", "redact_result")
    builder.add_edge("detector_result", "redact_result")

    builder.set_entry_point("convert_result")
    builder.set_execution_timeout(300)
    graph = builder.build()

    user_prompt: str = f"""
    1. Convert the following list of images to a single markdown: {CONVERT_IN}. Save the result to {CONVERT_OUT}.
    2. Detect sensitive data. Return the results as structured_output as defined in {SensitiveData} schema. Save the result to {DETECT_OUT}.
    3. Redact all information provided in detector_result except for the document_analysis field. Save the result to {REDACT_OUT}.
    """

    result = graph(user_prompt)

    logger.info(f"Workflow status: {result.status.value}")
    logger.info(f"{multimodal_agent.name} token usage: {result.accumulated_usage}")

    # Step 5: Summarize token usage
    agents: list[Agent] = [multimodal_agent, detector_agent, redact_agent]
    token_summary: dict[str, Any] = process_and_summarize_tokens(agents, result)
    TOKEN_SUMMARY_OUT: str = f"{DIR}{PREFIX['token']}{key}{FORMAT['json']}"
    save_as_json(data=token_summary, filename=TOKEN_SUMMARY_OUT)

    return doc_quality, result, token_summary


if __name__ == "__main__":
    typer.run(run_doc_processing_wf)
