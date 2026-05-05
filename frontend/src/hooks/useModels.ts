/**
 * Custom hook for managing AI models
 */

import { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import type { ModelInfo } from '../types/chat';

export interface UseModelsReturn {
    models: ModelInfo[];
    isLoading: boolean;
    error: string | null;
    refetch: () => Promise<void>;
}

export const useModels = (): UseModelsReturn => {
    const [models, setModels] = useState<ModelInfo[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchModels = async () => {
        setIsLoading(true);
        setError(null);

        try {
            const data = await apiService.getModels();
            setModels(data);
        } catch (err) {
            const errorMessage = err instanceof Error ? err.message : 'Failed to load models';
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => {
        fetchModels();
    }, []);

    return {
        models,
        isLoading,
        error,
        refetch: fetchModels,
    };
};