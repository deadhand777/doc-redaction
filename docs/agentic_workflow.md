# Agent Workflow

The service is a **agentic system** composed of a **graph-based multi-agent workflow**.

The document processing pipeline uses a **Graph Multi-Agent Pattern** to orchestrate three specialized agents that convert, analyze, and redact sensitive information from PDF contracts using AI agents powered by AWS Bedrock models. This graph-based approach enables parallel processing and efficient resource utilization through the Strands framework's `GraphBuilder`.

![Agentic Workflow](assets/agentic_workflow.png)

### Graph Node 1: PDF to Markdown Conversion (`convert_result`)

**Entry Point Agent** - Multimodal agent with AI vision capabilities:

- Reads and understands PDF content from converted PNG images
- Converts PDF structure and content to clean markdown format
- Preserves document structure, formatting, and content hierarchy
- **Tools**: `image_reader`, `merge_markdown_strings`, `save_file`, `remove_temp_files`

**Output**: Markdown file representing the original PDF document
**Graph Position**: Entry point that triggers downstream agents

### Graph Node 2: Sensitive Data Detection (`detector_result`)

**Detection Agent** - Specialized for sensitive information identification:

- **Dependencies**: Requires completion of conversion agent (`convert_result`)
- Analyzes document content using structured output with SensitiveData model
- Identifies and extracts sensitive information including:
  - Personal information (names, emails, phone numbers)
  - Company details (names, addresses, registration numbers)
  - Document metadata and analysis information
- **Tools**: `current_time`, `detect_sensitive_data`, `omit_empty_keys`
- **Model Configuration**: Uses Haiku model for efficient processing

**Output**: Structured JSON file with detected sensitive information
**Graph Position**: Parallel processing node that can execute concurrently with redaction planning

### Graph Node 3: Document Redaction (`redact_result`)

**Redaction Agent** - Focused on content sanitization:

- **Dependencies**: Requires both conversion (`convert_result`) and detection (`detector_result`) completion
- Systematically redacts all sensitive information identified by the detection agent
- Preserves document structure and non-sensitive content
- Maintains document readability while removing confidential data
- **Tools**: `save_file`, `redact_sensitive_data`
- **Model Configuration**: Uses Haiku model optimized for redaction tasks

**Output**: Redacted markdown file with sensitive information removed
**Graph Position**: Final processing node that combines results from both upstream agents

### Graph-Based Agent Architecture

The workflow implements a **Graph Multi-Agent Pattern** using the Strands framework's `GraphBuilder`:

#### Graph Structure
- **Nodes**: Three specialized agents (Conversion, Detection, Redaction)
- **Edges**: Define dependencies and data flow between agents
- **Entry Point**: Conversion agent serves as the workflow entry point
- **Parallel Execution**: Detection and redaction agents can process concurrently after conversion

#### Agent Configuration
Each agent is purpose-built with specific:
- System prompts tailored to their specialized task
- Curated tool sets for required operations
- Model configurations optimized for their workload (e.g., Haiku model for detection and redaction)

#### Workflow Execution
```python
builder = GraphBuilder()
builder.add_node(multimodal_agent, "convert_result")
builder.add_node(detector_agent, "detector_result")
builder.add_node(redact_agent, "redact_result")

# Define dependencies
builder.add_edge("convert_result", "detector_result")
builder.add_edge("convert_result", "redact_result")
builder.add_edge("detector_result", "redact_result")

builder.set_entry_point("convert_result")
builder.set_execution_timeout(300)
graph = builder.build()
```

This architecture provides:
- **Parallel Processing**: Detection and redaction can process simultaneously where dependencies allow
- **Optimized Resource Usage**: Multiple agents can work concurrently
- **Flexible Execution**: Graph structure enables dynamic workflow adaptation
- **Robust Error Handling**: Built-in timeout and status management

### Graph Workflow Benefits

The Graph Multi-Agent Pattern provides several key advantages over traditional linear workflows:

#### Performance Enhancements
- **Parallel Execution**: Detection and initial redaction planning can start simultaneously after conversion
- **Resource Optimization**: Multiple agents utilize available compute resources concurrently
- **Reduced Latency**: Overall processing time decreased through concurrent operations

#### Scalability & Flexibility
- **Dynamic Adaptation**: Graph structure allows for easy addition of new processing nodes
- **Conditional Routing**: Future enhancements can implement branching logic based on document characteristics
- **Modular Design**: Individual agents can be updated or replaced without affecting the entire workflow

#### Reliability & Monitoring
- **Execution Status**: Built-in workflow status tracking and timeout management
- **Granular Metrics**: Individual agent performance metrics for detailed analysis
- **Error Isolation**: Failures in one agent don't immediately cascade to others

### Output Artifacts

- **Converted Document**: Clean markdown representation of the original PDF
- **Sensitive Data Catalog**: Structured JSON with all detected sensitive information
- **Redacted Document**: Sanitized version safe for broader distribution
- **Process Metrics**: Detailed logging, token usage, and execution statistics for each agent
- **Workflow Status**: Graph execution status and accumulated usage metrics

This graph-based workflow enables automated, AI-powered document redaction with enhanced performance, parallel processing capabilities, and full traceability. The structured output and execution metrics make it suitable for compliance and audit requirements while providing superior efficiency through multi-agent coordination.

## Example Input and Output

Sample input and output artifacts can be found in the [data directory](https://github.com/deadhand777/doc-redaction/data/) of this repository.

Raw Contract | Converted Document | Sensitive Data Catalog | Redacted Document
------------ | ------------------ | ---------------------- | -----------------
[Raw spielbank_rocketbase_dienstleistungsvertrag](https://github.com/deadhand777/doc-redaction/blob/main/data/contract/spielbank_rocketbase_dienstleistungsvertrag.pdf) | [Converted spielbank_rocketbase_dienstleistungsvertrag](https://github.com/deadhand777/doc-redaction/blob/main/data/markdown/spielbank_rocketbase_dienstleistungsvertrag.md) | [Extracted spielbank_rocketbase_dienstleistungsvertrag](https://github.com/deadhand777/doc-redaction/blob/main/data/confidential/spielbank_rocketbase_dienstleistungsvertrag.json) | [Redacted spielbank_rocketbase_dienstleistungsvertrag](https://github.com/deadhand777/doc-redaction/blob/main/data/redact/spielbank_rocketbase_dienstleistungsvertrag_redacted.md)
[Raw rocketbase_aws_agreement](https://github.com/deadhand777/doc-redaction/blob/main/data/contract/rocketbase_aws_agreement.pdf) | [Converted rocketbase_aws_agreement](https://github.com/deadhand777/doc-redaction/blob/main/data/markdown/rocketbase_aws_agreement.md) | [Extracted rocketbase_aws_agreement](https://github.com/deadhand777/doc-redaction/blob/main/data/confidential/rocketbase_aws_agreement.json) | [Redacted rocketbase_aws_agreement](https://github.com/deadhand777/doc-redaction/blob/main/data/redact/rocketbase_aws_agreement_redacted.md)
[Raw spielbank_rocketbase_vertrag](https://github.com/deadhand777/doc-redaction/blob/main/data/contract/spielbank_rocketbase_vertrag.pdf) | [Converted spielbank_rocketbase_vertrag](https://github.com/deadhand777/doc-redaction/blob/main/data/markdown/spielbank_rocketbase_vertrag.md) | [Extracted spielbank_rocketbase_vertrag](https://github.com/deadhand777/doc-redaction/blob/main/data/confidential/spielbank_rocketbase_vertrag.json) | [Redacted spielbank_rocketbase_vertrag](https://github.com/deadhand777/doc-redaction/blob/main/data/redact/spielbank_rocketbase_vertrag_redacted.md)
