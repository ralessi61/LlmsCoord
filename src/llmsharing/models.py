from datetime import datetime
from enum import Enum
from typing import Self
from uuid import UUID, uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    PrivateAttr,
    field_validator,
    model_validator,
)


class TaskType(Enum):
    """ Possible task types for LLM requests. """
    SUMMARY = "summary"
    EXTRACTION = "extraction"
    QUESTION_ANSWERING = "question_answering"
    TRANSLATION = "translation"
    DETECTION = "detection"
    CLASSIFICATION = "classification"
    GENERATION = "generation"


class LLMRequest(BaseModel):
    doc_id: str = Field(..., description='Parsed doc Id')
    tasktype: TaskType = Field(..., description='LLM task')
    request_id: UUID = Field(default_factory=uuid4, description='request Id')
    provider: str = Field(default="fast",   description='LLM provider')
    fields: list[str] | None = Field(default=None, description='Fields to extract if tasktype is extraction')
    prompt: str = Field(..., description="LLM Prompt")

    @field_validator("prompt")
    @classmethod
    def validate_prompt(cls, v:str) -> str:
        stripped = v.strip() 
        if len(stripped) < 3:
            raise ValueError("Prompt cannot be empty or less than 3 characters long")
        return stripped

    @model_validator(mode="after")
    def validate_after(self) -> Self:
        if self.tasktype == TaskType.EXTRACTION and not self.fields:
            raise ValueError("Fields must be provided for extraction task")
        return self


class LLMResponse(BaseModel):
    response_id: UUID = Field(default_factory=uuid4, description='response Id')
    request_id: UUID = Field(..., description='Unique request Id')
    response: str | None = Field(default=None, description='LLM response')


class OrchestratorConfig(BaseModel):
    max_concurrency: int = Field(..., description='Max concurrent requests', ge=1)
    max_tokens: int = Field(..., description='Max tokens per request', gt=0)
    temperature: float = Field(..., description='Temperature for LLM', ge=0.0, le=1.0)
    model_config = ConfigDict(extra='allow')
    orchestrator_id: UUID = Field(default_factory=uuid4, description='Unique orchestrator Id')
   

class BatchResult(BaseModel):
    batch_id: UUID = Field(default_factory=uuid4, description='batch Id')
    total_requests: int = Field(..., description='Total number of requests in the batch', ge=1)
    successful_requests: int = Field(..., description='Number of successful requests', ge=0)
    failed_requests: int = Field(..., description='Number of failed requests', ge=0)
    total_tokens_used: int = Field(..., description='Tokens used in the batch', ge=0)
    total_latency: float = Field(..., description='Time taken for the batch in seconds', ge=0.0)
    total_retries: int = Field(..., description='Number of retries in the batch', ge=0)
    _created_at: datetime = PrivateAttr(default_factory=datetime.now)


class TaskResult(BaseModel):
    task_id: UUID = Field(default_factory=uuid4, description='task Id')
    success: bool = Field(..., description='Task success status')
    error_code: int | None = Field(default=None, description='Error code if task failed')
    error_message: str | None = Field(default=None, description='Error message if task failed')
    output: str | None = Field(default=None, description='Task output if successful')
    tasktype: TaskType = Field(..., description='Task type')    
    llmrequest_id: UUID = Field(..., description='request Id')
    status: str = Field(..., description='Task status')
    response: str | None = Field(default=None, description='LLM response')
    latency: float = Field(..., description='Time taken for the task in seconds', ge=0.0)
    retries: int = Field(..., description='Number of retries for the task', ge=0)
    tokens_estimated: int = Field(..., description='Tokens used for the task', ge=0)
    _created_at: datetime = PrivateAttr(default_factory=datetime.now)

    @model_validator(mode="after")
    def validate_result(self) -> Self:
        """ Validate that the result is coherent """
        if not self.success and not self.error_message:
            raise ValueError("If the task failed, the error message is required")
        if self.success and not self.output:
            raise ValueError("If the task succeeded, the output is required")
        if self.success and not self.tokens_estimated:
            raise ValueError("If the task succeeded, the estimated tokens are required")
        return self