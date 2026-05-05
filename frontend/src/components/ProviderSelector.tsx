import { ChevronDown, DollarSign } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { apiService } from '../services/api';
import type { ModelInfo, Provider } from '../types/chat';

interface ProviderSelectorProps {
    selectedProvider: string;
    selectedModel: string;
    onProviderChange: (provider: string) => void;
    onModelChange: (model: string) => void;
    disabled?: boolean;
    variant?: 'full' | 'compact' | 'list';
    onModelSelect?: (modelId: string) => void;
}

export const ProviderSelector: React.FC<ProviderSelectorProps> = ({
    selectedProvider,
    selectedModel,
    onProviderChange,
    onModelChange,
    disabled = false,
    variant = 'full'
}) => {
    const [providers, setProviders] = useState<Provider[]>([]);
    const [models, setModels] = useState<ModelInfo[]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        loadProviders();
    }, []);

    useEffect(() => {
        if (selectedProvider) {
            loadModels(selectedProvider);
        }
    }, [selectedProvider]);

    const loadProviders = async () => {
        try {
            const data = await apiService.listProviders();
            setProviders(data);
            if (data.length > 0 && !selectedProvider) {
                onProviderChange(data[0].name);
            }
        } catch (error) {
            console.error('Failed to load providers:', error);
        }
    };

    const loadModels = async (provider: string) => {
        setLoading(true);
        try {
            const data = await apiService.listModels(provider);
            setModels(data);
            if (data.length > 0 && !selectedModel) {
                onModelChange(data[0].id);
            }
        } catch (error) {
            console.error('Failed to load models:', error);
        } finally {
            setLoading(false);
        }
    };

    const currentModel = models.find((m) => m.id === selectedModel);

    // Common select styles to keep code clean
    const selectStyles = "w-full bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-2 pr-10 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-500/50 disabled:opacity-50 appearance-none transition-all";

    if (variant === 'list') {
        return (
            <div className="flex flex-col gap-1 max-h-60 overflow-y-auto custom-scrollbar">
                {loading ? (
                    <div className="p-2 text-xs text-gray-500 animate-pulse text-center">Loading models...</div>
                ) : (
                    models.map((model) => (
                        <button
                            key={model.id}
                            onClick={() => onModelChange(model.id)}
                            className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${selectedModel === model.id
                                    ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 font-medium'
                                    : 'hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300'
                                }`}
                        >
                            {model.name}
                        </button>
                    ))
                )}
            </div>
        );
    }

    if (variant === 'compact') {
        return (
            <div className="relative w-full">
                <select
                    value={selectedModel}
                    onChange={(e) => onModelChange(e.target.value)}
                    disabled={disabled || loading}
                    className={selectStyles}
                >
                    {loading ? (
                        <option>Loading models...</option>
                    ) : (
                        models.map((model) => (
                            <option key={model.id} value={model.id}>
                                {model.name}
                            </option>
                        ))
                    )}
                </select>
                <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none text-gray-400" />
            </div>
        );
    }

    return (
        <div className="flex flex-wrap gap-4 items-center">
            {/* Provider Selector */}
            <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Provider:</label>
                <div className="relative">
                    <select
                        value={selectedProvider}
                        onChange={(e) => onProviderChange(e.target.value)}
                        disabled={disabled}
                        className={selectStyles}
                    >
                        {providers.map((provider) => (
                            <option key={provider.name} value={provider.name} className="bg-white dark:bg-gray-800">
                                {provider.display_name}
                                {!provider.has_api_key && provider.requires_api_key && ' (⚠️ No API key)'}
                            </option>
                        ))}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none text-gray-400" />
                </div>
            </div>

            {/* Model Selector */}
            <div className="flex items-center gap-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">Model:</label>
                <div className="relative">
                    <select
                        value={selectedModel}
                        onChange={(e) => onModelChange(e.target.value)}
                        disabled={disabled || loading}
                        className={selectStyles}
                    >
                        {loading ? (
                            <option>Loading...</option>
                        ) : (
                            models.map((model) => (
                                <option key={model.id} value={model.id} className="bg-white dark:bg-gray-800">
                                    {model.name}
                                </option>
                            ))
                        )}
                    </select>
                    <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 pointer-events-none text-gray-400" />
                </div>
            </div>

            {/* Cost Info */}
            {currentModel && (currentModel.cost_per_1k_input || currentModel.cost_per_1k_output) && (
                <div className="flex items-center gap-1 text-xs font-mono text-gray-600 dark:text-gray-400 bg-gray-100 dark:bg-gray-800 px-3 py-1 rounded-full border border-gray-200 dark:border-gray-700">
                    <DollarSign className="w-3 h-3 text-green-500" />
                    <span>
                        ${currentModel.cost_per_1k_input?.toFixed(4) || '0'}/1K in
                    </span>
                </div>
            )}
        </div>
    );
};