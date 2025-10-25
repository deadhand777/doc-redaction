from pydantic import BaseModel, Field


class DocumentAnalysis(BaseModel):
    """Metadata about the analyzed document."""

    document_name: str = Field(..., description="The name of the document.")
    document_type: str = Field(..., description="The type of the document.")
    # analysis_date: str = Field(..., description="The current timestamp. Determined at analysis time by the current_time tool.")
    sensitive_data_detected: bool = Field(..., description="Whether sensitive data was detected.")


class Representative(BaseModel):
    """Information about the representatives of the parties."""

    people_names: str = Field(..., description="The full name of the representative.")
    email_addresses: str = Field(..., description="The email address of the representative.")
    phone_numbers: str = Field(..., description="The phone number of the representative.")
    job_title: str = Field(..., description="The job title of the representative.")


class Party(BaseModel):
    """Information about the parties involved in the contract."""

    company_name: str = Field(..., description="The official name of the company.")
    address: str = Field(..., description="The full business address of the company.")
    company_registration_numbers: list[str] = Field(..., description="List of detected company registration numbers.")
    # jurisdiction: str = Field(..., description="The jurisdiction governing the company.")


class ContractTerms(BaseModel):
    """Key terms and conditions of the contract."""

    initial_term: str = Field(..., description="The initial term of the contract.")
    renewal_period: str = Field(..., description="The renewal period of the contract.")
    auto_renewal: bool = Field(..., description="Whether the contract has an auto-renewal clause.")
    notice_period: str = Field(..., description="The notice period for termination of the contract.")
    termination_notice: str = Field(..., description="The termination notice period for the contract.")
    payment_terms: str = Field(..., description="The payment terms of the contract.")
    payments: str = Field(..., description="The payment schedule of the contract.")
    iban_numbers: list[str] = Field(..., description="List of detected IBAN numbers.")
    credit_card_numbers: list[str] = Field(..., description="List of detected credit card numbers.")
    account_numbers: list[str] = Field(..., description="List of detected account numbers.")
    currency_amounts: list[str] = Field(..., description="List of detected currency amounts. E.g. 1000 EUR, 10.000€, 500 USD, zehntausend Euro.")
    number_words: list[str] = Field(..., description="List of detected number words, e.g. tausend, two, three, zehn, hundert.")
    percentages: list[str] = Field(..., description="List of detected percentages., e.g. 10%, 3 Prozent, 5 percent.")
    # confidentiality_clause: bool = Field(..., description="Whether the contract includes a confidentiality clause.")
    # governing_law: str
    # jurisdiction: str


class DataProtectionCompliance(BaseModel):
    """Data protection compliance details."""

    mentioned: bool
    # data_processing_agreement: str


class RiskAssessment(BaseModel):
    """Risk assessment of the contract."""

    contains_personal_data: bool = Field(..., description="Whether the contract contains personal data.")
    contains_business_sensitive_info: bool = Field(..., description="Whether the contract contains business sensitive information.")
    contains_financial_terms: bool = Field(..., description="Whether the contract contains financial terms.")
    contains_legal_obligations: bool = Field(..., description="Whether the contract contains legal obligations.")


class SensitiveData(BaseModel):
    """Represents sensitive data detected in a document."""

    document_analysis: DocumentAnalysis = Field(..., description="Metadata about the analyzed document.")
    parties: list[Party] = Field(..., description="Information about the parties involved in the contract.")
    representative: list[Representative] = Field(..., description="Information about the representatives of the parties.")
    contract_terms: ContractTerms = Field(..., description="Key terms and conditions of the contract.")
    risk_assessment: RiskAssessment = Field(..., description="Risk assessment of the contract.")
    data_protection_compliance: DataProtectionCompliance = Field(..., description="Data protection compliance details.")
