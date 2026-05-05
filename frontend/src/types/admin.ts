export interface AdminUser {
    id: number;
    username: string;
    email: string;
    role: string;
    is_active: boolean;
    total_tokens_used: number;
    total_cost: number;
    monthly_cost: number;
    created_at: string;
    last_login: string | null;
}

export interface UserCreateRequest {
    username: string;
    email: string;
    password: string;
    role: string;
    is_active: boolean;
}

export interface UserUpdateRequest {
    email?: string;
    password?: string;
    role?: string;
    is_active?: boolean;
}

export interface AdminConversation {
    conversation_id: string;
    user_id: number;
    model: string;
    messages: Array<{ role: string; content: string }>;
    created_at: string;
    updated_at: string;
    metadata?: any;
}

export interface AnalyticsDashboard {
    overview: {
        total_users: number;
        active_users: number;
        total_conversations: number;
        period_conversations: number;
        total_tokens: number;
        total_cost: number;
    };
    top_users: Array<{
        username: string;
        total_tokens: number;
        total_cost: number;
        monthly_cost: number;
    }>;
    provider_usage: Array<{
        provider: string;
        count: number;
    }>;
    model_popularity: Array<{
        model: string;
        count: number;
    }>;
    daily_usage: Array<{
        date: string;
        conversations: number;
        tokens: number;
    }>;
    error_rates: Array<{
        provider: string;
        total_requests: number;
        errors: number;
        error_rate: number;
    }>;
    period_days: number;
}

export interface UserAPIKeys {
    [key: string]: {
        has_key: boolean;
        masked_key?: string;
    };
}