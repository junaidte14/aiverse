/**
 * API service for communicating with FastAPI backend
 */

import type { AxiosInstance } from 'axios';
import axios from 'axios';
import { EventSourcePolyfill } from 'event-source-polyfill';
import type { AdminConversation, AdminUser, AnalyticsDashboard, UserCreateRequest, UserUpdateRequest } from '../types/admin';
import type {
    AuthResponse,
    ChatRequest,
    ChatResponse,
    Conversation,
    LoginRequest,
    ModelInfo,
    Provider,
    RegisterRequest,
    StreamChunk,
    UsageStats,
    User
} from '../types/chat';
import type { GitHubSourceCreate, IngestDirectoryRequest, RAGCollection, RAGQueryRequest, RAGQueryResponse, RAGSourceModel, RAGSourceUpdate, SyncResult } from '../types/rag';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

class ApiService {
    private client: AxiosInstance;

    constructor() {
        this.client = axios.create({
            baseURL: API_BASE_URL,
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: 300000,
        });

        // Add token to requests
        this.client.interceptors.request.use((config) => {
            const token = this.getToken();
            if (token) {
                config.headers.Authorization = `Bearer ${token}`;
            }
            return config;
        });

        // Handle 401 errors
        this.client.interceptors.response.use(
            (response) => response,
            (error) => {
                if (error.response?.status === 401) {
                    this.clearToken();
                }
                return Promise.reject(error);
            }
        );
    }

    // Token management
    getToken(): string | null {
        return localStorage.getItem('access_token');
    }

    setToken(token: string): void {
        localStorage.setItem('access_token', token);
    }

    clearToken(): void {
        localStorage.removeItem('access_token');
    }

    // Auth endpoints
    async login(credentials: LoginRequest): Promise<AuthResponse> {
        const response = await this.client.post('/auth/login', credentials);
        this.setToken(response.data.access_token);
        return response.data;
    }

    async register(data: RegisterRequest): Promise<AuthResponse> {
        const response = await this.client.post('/auth/register', data);
        this.setToken(response.data.access_token);
        return response.data;
    }

    async getCurrentUser(): Promise<User> {
        const response = await this.client.get('/auth/me');
        return response.data;
    }

    logout(): void {
        this.clearToken();
    }

    ragSyncProgressStream(sourceId: number, operationId: string): EventSource {
        const token = this.getToken();
        const url = `${API_BASE_URL}/rag/sources/${sourceId}/sync/progress/${operationId}`;

        return new EventSourcePolyfill(url, {
            headers: {
                'Authorization': `Bearer ${token}`
            },
            heartbeatTimeout: 300000, // 5 minutes
            withCredentials: true
        }) as unknown as EventSource;
    }

    // Add a unified chat method that decides based on the presence of a collection
    async chat(request: ChatRequest, collectionName: string | null): Promise<ChatResponse | RAGQueryResponse> {
        if (collectionName) {
            return this.ragQuery({
                question: request.messages[request.messages.length - 1].content,
                collection_name: collectionName,
                conversation_id: request.conversation_id,
                provider: request.provider,
                model: request.model,
                temperature: request.temperature,
                max_tokens: request.max_tokens,
                include_sources: true
            });
        }
        return this.multiProviderChat(request);
    }

    // Multi-provider AI endpoints
    async listProviders(): Promise<Provider[]> {
        const response = await this.client.get('/ai/multi/providers');
        return response.data;
    }

    async listModels(provider: string): Promise<ModelInfo[]> {
        const response = await this.client.get(`/ai/multi/models/${provider}`);
        return response.data;
    }

    async getModelInfo(provider: string, modelId: string): Promise<ModelInfo> {
        const response = await this.client.get(`/ai/multi/models/${provider}/${modelId}`);
        return response.data;
    }

    async multiProviderChat(request: ChatRequest): Promise<ChatResponse> {
        const response = await this.client.post('/ai/multi/chat', request);
        return response.data;
    }

    async *streamMultiProviderChat(request: ChatRequest): AsyncGenerator<StreamChunk> {
        const token = this.getToken();
        let response: Response | undefined;
        let reader: ReadableStreamDefaultReader<Uint8Array> | undefined;

        // Create abort controller with safe fallback
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000); // 2 minutes

        try {
            response = await fetch(`${API_BASE_URL}/ai/multi/chat/stream`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...(token && { Authorization: `Bearer ${token}` }),
                },
                body: JSON.stringify(request),
                signal: controller.signal,
            });

            clearTimeout(timeoutId); // Clear timeout once fetch resolves

            if (!response.ok) {
                const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
                throw new Error(error.detail || `HTTP ${response.status}`);
            }

            if (!response.body) {
                throw new Error('Response body is null');
            }

            reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunkText = decoder.decode(value, { stream: true });
                buffer += chunkText;

                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed.startsWith('data:')) continue;

                    const data = trimmed.replace(/^data:\s*/, '');

                    if (data === '[DONE]') {
                        return;
                    }

                    try {
                        const parsed = JSON.parse(data);
                        yield parsed;
                    } catch (e) {
                        console.warn("[STREAM] Failed to parse JSON:", data, e);
                    }
                }
            }
        } catch (error) {
            console.error("[STREAM] Error:", error);
            yield { error: error instanceof Error ? error.message : 'Stream connection failed' };
            throw error;
        } finally {
            clearTimeout(timeoutId);
            reader?.releaseLock();
        }
    }

    async getUsageStats(): Promise<UsageStats> {
        const response = await this.client.get('/ai/multi/usage');
        return response.data;
    }

    // Legacy endpoints (for backward compatibility)
    async getModels(): Promise<ModelInfo[]> {
        const response = await this.client.get('/ai/models');
        return response.data.models || [];
    }

    async sendMessage(request: ChatRequest): Promise<ChatResponse> {
        const response = await this.client.post('/ai/chat', request);
        return response.data;
    }

    async *streamMessage(request: ChatRequest): AsyncGenerator<StreamChunk> {
        const token = this.getToken();
        const response = await fetch(`${API_BASE_URL}/ai/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...(token && { Authorization: `Bearer ${token}` }),
            },
            body: JSON.stringify(request),
        });
        console.log(response);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Stream request failed');
        }

        if (!response.body) {
            throw new Error('Response body is null');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        try {
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const data = JSON.parse(line.slice(6));
                        yield data as StreamChunk;
                    }
                }
            }
        } finally {
            reader.releaseLock();
        }
    }

    async listConversations(skip = 0, limit = 100): Promise<Conversation[]> {
        // Ensure this is a GET request and matches the backend prefix
        const response = await this.client.get('/conversations', {
            params: { skip, limit }
        });
        return response.data;
    }

    async getMessages(conversationId: string) {
        const response = await this.client.get(`/conversations/${conversationId}/messages`);
        return response.data;
    }

    async getConversation(conversationId: string): Promise<Conversation> {
        const response = await this.client.get(`/ai/conversations/${conversationId}`);
        return response.data;
    }

    async createConversation(model: string = 'llama2'): Promise<Conversation> {
        const response = await this.client.post('/ai/conversations', null, {
            params: { model },
        });
        return response.data;
    }

    async updateConversation(conversationId: string, title: string): Promise<Conversation> {
        const response = await this.client.put(`/conversations/${conversationId}`, null, {
            params: { title }
        });
        return response.data;
    }

    async deleteConversation(conversationId: string): Promise<void> {
        await this.client.delete(`/conversations/${conversationId}`);
    }

    async checkHealth(): Promise<{ status: string; ollama_url: string }> {
        const response = await this.client.get('/ai/health');
        return response.data;
    }

    // ==================== ADMIN - USER MANAGEMENT ====================

    async adminListUsers(
        skip: number = 0,
        limit: number = 100,
        search?: string,
        role?: string,
        is_active?: boolean
    ): Promise<AdminUser[]> {
        const params = new URLSearchParams({
            skip: skip.toString(),
            limit: limit.toString(),
        });
        if (search) params.append('search', search);
        if (role) params.append('role', role);
        if (is_active !== undefined) params.append('is_active', is_active.toString());

        const response = await this.client.get(`/admin/users?${params}`);
        return response.data;
    }

    async adminGetUser(userId: number): Promise<AdminUser> {
        const response = await this.client.get(`/admin/users/${userId}`);
        return response.data;
    }

    async adminCreateUser(data: UserCreateRequest): Promise<AdminUser> {
        const response = await this.client.post('/admin/users', data);
        return response.data;
    }

    async adminUpdateUser(userId: number, data: UserUpdateRequest): Promise<AdminUser> {
        const response = await this.client.put(`/admin/users/${userId}`, data);
        return response.data;
    }

    async adminDeleteUser(userId: number): Promise<void> {
        await this.client.delete(`/admin/users/${userId}`);
    }

    // ==================== ADMIN - CONVERSATIONS ====================

    async adminListConversations(
        skip: number = 0,
        limit: number = 100,
        userId?: number,
        provider?: string
    ): Promise<AdminConversation[]> {
        const params = new URLSearchParams({
            skip: skip.toString(),
            limit: limit.toString(),
        });
        if (userId) params.append('user_id', userId.toString());
        if (provider) params.append('provider', provider);

        const response = await this.client.get(`/admin/conversations?${params}`);
        return response.data;
    }

    async adminDeleteConversation(conversationId: string): Promise<void> {
        await this.client.delete(`/admin/conversations/${conversationId}`);
    }

    // ==================== ADMIN - ANALYTICS ====================

    async adminGetDashboard(days: number = 30): Promise<AnalyticsDashboard> {
        const response = await this.client.get(`/admin/analytics/dashboard?days=${days}`);
        return response.data;
    }

    async adminGetUserStats(userId: number, days: number = 30): Promise<any> {
        const response = await this.client.get(`/admin/analytics/users/${userId}/stats?days=${days}`);
        return response.data;
    }

    // ==================== RAG COLLECTIONS ====================

    async ragQuery(request: RAGQueryRequest): Promise<RAGQueryResponse> {
        console.log(request);
        const response = await this.client.post('/rag/query', {
            question: request.question,
            collection_name: request.collection_name || 'default',
            conversation_id: request.conversation_id,
            provider: request.provider || 'groq',
            model: request.model || 'llama-3.3-70b-versatile',
            n_context_docs: request.n_context_docs || 5,
            include_sources: request.include_sources ?? true,
            temperature: request.temperature || 0.7,
            max_tokens: request.max_tokens || 1000,
        });
        return response.data;
    }

    async ragIngestFile(file: File, collectionName: string = 'default'): Promise<any> {
        const formData = new FormData();
        formData.append('file', file);

        const response = await this.client.post(
            `/rag/ingest/file?collection_name=${collectionName}`,
            formData,
            {
                headers: {
                    'Content-Type': 'multipart/form-data',
                },
            }
        );
        return response.data;
    }

    async ragIngestDirectory(request: IngestDirectoryRequest): Promise<any> {
        const response = await this.client.post('/rag/ingest/directory', request);
        return response.data;
    }

    async ragListCollections(): Promise<string[]> {
        //const response = await this.client.get('/rag/collections');
        //console.log(response.data);
        const data = [
            "versana"
        ];
        return data;
    }

    async ragGetCollectionStats(collectionName: string): Promise<RAGCollection> {
        const response = await this.client.get(`/rag/collections/${collectionName}/stats`);
        return response.data;
    }

    async ragDeleteCollection(collectionName: string): Promise<void> {
        await this.client.delete(`/rag/collections/${collectionName}`);
    }

    async ragSearchDocuments(
        query: string,
        collectionName: string = 'default',
        nResults: number = 5
    ): Promise<any> {
        const response = await this.client.post('/rag/search', null, {
            params: { query, collection_name: collectionName, n_results: nResults },
        });
        return response.data;
    }

    // ==================== RAG SOURCES ====================

    async ragAddGitHubSource(data: GitHubSourceCreate): Promise<RAGSourceModel> {
        const response = await this.client.post('/rag/sources/github', data);
        return response.data;
    }

    async ragListSources(collectionName?: string): Promise<RAGSourceModel[]> {
        const params = collectionName ? { collection_name: collectionName } : {};
        const response = await this.client.get('/rag/sources', { params });
        return response.data;
    }

    async ragGetSource(sourceId: number): Promise<RAGSourceModel> {
        const response = await this.client.get(`/rag/sources/${sourceId}`);
        return response.data;
    }

    async ragUpdateSource(sourceId: number, data: RAGSourceUpdate): Promise<RAGSourceModel> {
        const response = await this.client.put(`/rag/sources/${sourceId}`, data);
        return response.data;
    }

    async ragSyncSource(sourceId: number): Promise<SyncResult> {
        const response = await this.client.post(`/rag/sources/${sourceId}/sync`);
        return response.data;
    }

    async ragDeleteSource(sourceId: number): Promise<void> {
        await this.client.delete(`/rag/sources/${sourceId}`);
    }

    async ragAuthenticateGoogleDrive(): Promise<any> {
        const response = await this.client.post('/rag/sources/authenticate/google-drive');
        return response.data;
    }
}

export const apiService = new ApiService();