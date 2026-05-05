"""
AI-related Pydantic models

Request and response models for AI endpoints
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from datetime import datetime


# ============================================
# MESSAGE MODELS
# ============================================


class ChatMessage(BaseModel):
    """
    Individual chat message

    Represents a single message in a conversation
    """

    role: Literal["user", "assistant", "system"] = Field(
        ..., description="Message role (user, assistant, or system)"
    )
    content: str = Field(..., min_length=1, description="Message content")
    timestamp: Optional[datetime] = Field(
        default=None, description="When the message was created"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "What is FastAPI?",
                "timestamp": "2024-01-15T10:30:00",
            }
        }


# ============================================
# CHAT REQUEST/RESPONSE
# ============================================


class ChatRequest(BaseModel):
    """
    Chat completion request

    Send a message and get AI response
    """

    message: str = Field(..., min_length=1, max_length=4000, description="User message")
    model: str = Field(default="llama2", description="AI model to use")
    conversation_id: Optional[str] = Field(
        None, description="Conversation ID for context (optional)"
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature (0.0-2.0). Higher = more creative",
    )
    max_tokens: Optional[int] = Field(
        None, ge=1, le=4096, description="Maximum tokens to generate"
    )
    stream: bool = Field(default=False, description="Stream response in real-time")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Explain FastAPI in simple terms",
                "model": "llama2",
                "temperature": 0.7,
                "stream": False,
            }
        }


class ChatResponse(BaseModel):
    """
    Chat completion response

    AI model's response to user message
    """

    message: str = Field(..., description="AI response")
    model: str = Field(..., description="Model used")
    conversation_id: str = Field(..., description="Conversation ID")
    created_at: datetime = Field(default_factory=datetime.now)
    finish_reason: Optional[str] = Field(None, description="Why generation stopped")

    # Token usage (if available)
    prompt_tokens: Optional[int] = Field(None, description="Tokens in prompt")
    completion_tokens: Optional[int] = Field(None, description="Tokens in completion")
    total_tokens: Optional[int] = Field(None, description="Total tokens used")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "FastAPI is a modern Python web framework...",
                "model": "llama2",
                "conversation_id": "conv_123",
                "created_at": "2024-01-15T10:30:00",
                "total_tokens": 150,
            }
        }


# ============================================
# CONVERSATION MODELS
# ============================================


class Conversation(BaseModel):
    """
    Conversation with message history

    Maintains context across multiple messages
    """

    conversation_id: str = Field(..., description="Unique conversation ID")
    model: str = Field(..., description="AI model being used")
    messages: List[ChatMessage] = Field(default=[], description="Message history")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default={}, description="Additional conversation metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_abc123",
                "model": "llama2",
                "messages": [
                    {"role": "user", "content": "Hello!"},
                    {"role": "assistant", "content": "Hi! How can I help?"},
                ],
                "created_at": "2024-01-15T10:30:00",
            }
        }


# ============================================
# MODEL INFORMATION
# ============================================


class ModelInfo(BaseModel):
    """
    Information about an AI model
    """

    name: str = Field(..., description="Model name")
    size: Optional[str] = Field(None, description="Model size (e.g., '7B', '13B')")
    family: Optional[str] = Field(None, description="Model family")
    parameter_size: Optional[str] = Field(None, description="Number of parameters")
    quantization: Optional[str] = Field(None, description="Quantization level")
    modified_at: Optional[datetime] = Field(None, description="Last modified date")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "llama2:latest",
                "size": "3.8GB",
                "family": "llama",
                "parameter_size": "7B",
            }
        }


class ModelListResponse(BaseModel):
    """List of available models"""

    models: List[ModelInfo] = Field(..., description="Available models")
    count: int = Field(..., description="Number of models")


# ============================================
# GENERATION OPTIONS
# ============================================


class GenerationOptions(BaseModel):
    """
    Options for text generation

    Controls how the AI generates responses
    """

    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Randomness (0=deterministic, 2=very random)",
    )
    top_p: float = Field(
        default=0.9, ge=0.0, le=1.0, description="Nucleus sampling threshold"
    )
    top_k: int = Field(default=40, ge=1, description="Top-k sampling parameter")
    repeat_penalty: float = Field(
        default=1.1, ge=0.0, description="Penalty for repeating tokens"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "temperature": 0.7,
                "top_p": 0.9,
                "top_k": 40,
                "repeat_penalty": 1.1,
            }
        }
