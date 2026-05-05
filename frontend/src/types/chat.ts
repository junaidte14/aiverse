/**
 * TypeScript interfaces for chat application
 */

export interface Message {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    metadata_json?: {
        sources?: any[];
        [key: string]: any;
    } | null;
    timestamp: Date;
    isStreaming?: boolean;
    sources?: { source_number: number; filename: string, source: string, chunk_index: number, distance: number }[];
}

export interface ChatRequest {
    provider: string;
    model: string;
    messages: { role: string; content: string }[];
    message: string;
    conversation_id?: string;
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
}

export interface ChatResponse {
    content: string;
    model: string;
    provider: string;
    conversation_id: string;
    tokens_used?: number;
    cost?: number;
    created_at: string;
    finish_reason?: string;
}

export interface Conversation {
    conversation_id: string;
    model: string;
    messages: Message[];
    created_at: string;
    updated_at: string;
    metadata?: Record<string, any>;
}

export interface ModelInfo {
    id: string;
    name: string;
    provider: string;
    context_length?: number;
    cost_per_1k_input?: number;
    cost_per_1k_output?: number;
    supports_streaming?: boolean;
}

export interface Provider {
    name: string;
    display_name: string;
    requires_api_key: boolean;
    has_api_key: boolean;
    models_count: number;
}

export interface UsageStats {
    total_tokens: number;
    total_cost: number;
    monthly_cost: number;
    monthly_limit: number;
    remaining_budget: number;
}

export interface APIKeyStatus {
    provider: string;
    has_key: boolean;
    masked_key?: string;
}

export interface StreamChunk {
    content?: string;
    done?: boolean;
    conversation_id?: string;
    error?: string;
}

export interface ChatSettings {
    provider: string;
    model: string;
    temperature: number;
    max_tokens: number;
    stream: boolean;
    guest_allowed?: string;
}

export interface User {
    id: number;
    username: string;
    email: string;
    is_active: boolean;
    created_at: string;
}

export interface LoginRequest {
    username: string;
    password: string;
}

export interface RegisterRequest {
    username: string;
    email: string;
    password: string;
    confirm_password: string;
    full_name: string;
    age: number;
    tags: string[];
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    user: User;
}