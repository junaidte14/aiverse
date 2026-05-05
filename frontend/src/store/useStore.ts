// src/store/useStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { apiService } from '../services/api';
import type { ChatSettings, User } from '../types/chat';

interface AppState {
    // Auth State
    user: User | null;
    isAuthenticated: boolean;
    setUser: (user: User | null) => void;
    logout: () => void;

    // Chat Settings State
    settings: ChatSettings;
    updateSettings: (newSettings: Partial<ChatSettings>) => void;

    // UI & Navigation State (New)
    theme: 'light' | 'dark';
    setTheme: (theme: 'light' | 'dark') => void;
    isSidebarOpen: boolean;
    toggleSidebar: () => void;
    activeConversationId: string | null;
    setActiveConversationId: (id: string | null) => void;

    messages: any[];
    setMessages: (messages: any[]) => void;
    addMessage: (message: any) => any;
    updateMessage: (id: string, updates: any) => void;
}

export const useStore = create<AppState>()(

    persist(
        (set) => ({
            // Auth Initial State
            user: null,
            isAuthenticated: !!localStorage.getItem('access_token'),
            setUser: (user) => set({ user, isAuthenticated: !!user }),
            logout: () => {
                apiService.clearToken();
                set({ user: null, isAuthenticated: false });
            },

            // Settings Initial State
            settings: {
                provider: 'groq',
                model: 'llama-3.3-70b-versatile',
                temperature: 0.7,
                max_tokens: 1000,
                stream: true,
            },
            updateSettings: (newSettings) =>
                set((state) => ({
                    settings: { ...state.settings, ...newSettings },
                })),

            // UI Initial State
            theme: 'light',
            setTheme: (theme) => set({ theme }),
            isSidebarOpen: true,
            toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
            activeConversationId: null,
            setActiveConversationId: (id) => set({ activeConversationId: id }),

            messages: [],

            setMessages: (messages) => set({ messages }),

            addMessage: (message) => {
                const id = message.id ?? crypto.randomUUID(); // BEST FIX
                //console.log(`[Store] addMessage id=${id} role=${message.role}`);
                const newMessage = {
                    ...message,
                    id,
                    metadata_json: message.metadata_json ?? null,
                    timestamp: new Date(),
                };

                set((state) => ({
                    messages: [...state.messages, newMessage],
                }));

                return newMessage;
            },

            updateMessage: (id, updates) =>
                set((state) => {
                    //console.log(`[Store] updateMessage id=${id} updates=`, updates);
                    const newMessages = state.messages.map((m) =>
                        m.id === id ? { ...m, ...updates } : m
                    );
                    return { messages: [...newMessages] }; // force new reference
                }),
        }),
        {
            name: 'aiverse-storage', // Key in localStorage
            partialize: (state) => ({ settings: state.settings, theme: state.theme }), // Only persist settings, not sensitive user data
        }
    )
);