import { create } from 'zustand';
import { apiService } from '../services/api';

interface ConversationState {
    conversations: any[];
    isLoading: boolean;

    fetchConversations: () => Promise<void>;
    addConversation: (conv: any) => void;
    upsertConversation: (conv: any) => void;
    updateConversationTitle: (id: string, title: string) => void; // ✅ NEW
    removeConversation: (id: string) => void;
}

export const useConversationStore = create<ConversationState>((set) => ({
    conversations: [],
    isLoading: false,

    fetchConversations: async () => {
        set({ isLoading: true });
        const data = await apiService.listConversations();
        set({ conversations: data, isLoading: false });
    },

    addConversation: (conv) =>
        set((state) => ({
            conversations: [conv, ...state.conversations],
        })),

    upsertConversation: (conv) =>
        set((state) => {
            const updated = state.conversations.some(c => c.id === conv.id)
                ? state.conversations.map(c =>
                    c.id === conv.id ? { ...c, ...conv } : c
                )
                : [conv, ...state.conversations];

            return {
                conversations: updated.sort(
                    (a, b) =>
                        new Date(b.updated_at).getTime() -
                        new Date(a.updated_at).getTime()
                )
            };
        }),

    updateConversationTitle: (id, title) =>
        set((state) => ({
            conversations: state.conversations.map(c =>
                c.id === id ? { ...c, title } : c
            )
        })),

    removeConversation: (id) =>
        set((state) => ({
            conversations: state.conversations.filter(c => c.id !== id)
        })),
}));