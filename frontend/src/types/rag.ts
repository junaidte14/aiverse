export interface RAGQueryRequest {
    question: string;
    collection_name?: string;
    conversation_id?: string;
    provider?: string;
    model?: string;
    n_context_docs?: number;
    include_sources?: boolean;
    temperature?: number;
    max_tokens?: number;
    guest_allowed?: boolean;
}

export interface RAGSource {
    source_number: number;
    filename: string;
    source: string;
    chunk_index: number;
    distance: number;
}

export interface RAGQueryResponse {
    answer: string;
    context_used: boolean;
    conversation_id?: string;
    sources?: RAGSource[];
    tokens_used?: number;
    cost?: number;
}

export interface RAGCollection {
    collection_name: string;
    document_count: number;
    status: string;
}

export interface RAGSearchResult {
    content: string;
    metadata: {
        source: string;
        filename: string;
        extension: string;
        chunk_index: number;
        total_chunks: number;
        tokens: number;
        [key: string]: any;
    };
    distance: number;
}

export interface IngestDirectoryRequest {
    directory_path: string;
    collection_name?: string;
    file_extensions?: string[];
    exclude_patterns?: string[];
    metadata?: Record<string, any>;
}

// Source types
export enum SourceType {
    MANUAL = 'manual',
    GITHUB = 'github',
    GOOGLE_DRIVE = 'google_drive',
}

export enum SyncStatus {
    PENDING = 'pending',
    IN_PROGRESS = 'in_progress',
    COMPLETED = 'completed',
    FAILED = 'failed',
}

export interface RAGSourceModel {
    id: number;
    user_id: number;
    collection_name: string;
    source_type: SourceType;
    source_identifier: string;
    display_name: string;
    auto_sync: boolean;
    sync_interval_hours: number;
    last_sync_at: string | null;
    last_sync_status: SyncStatus;
    last_sync_error: string | null;
    total_files: number;
    total_chunks: number;
    last_commit_sha: string | null;
    config: Record<string, any> | null;
    created_at: string;
    updated_at: string;
}

export interface GitHubSourceCreate {
    repo_url: string;
    collection_name: string;
    display_name: string;
    branch?: string;
    file_extensions?: string[];
    auto_sync?: boolean;
    sync_interval_hours?: number;
}
export interface SyncResult {
    source_id: number;
    status: string;
    files_processed?: number;
    chunks_created?: number;
    commit_sha?: string;
    error?: string;
}

export interface RAGSourceUpdate {
    display_name?: string;
    auto_sync?: boolean;
    sync_interval_hours?: number;
}