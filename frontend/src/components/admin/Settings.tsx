// src/components/ChatHeader.tsx
import { Cpu } from 'lucide-react';
import React, { useEffect, useState } from 'react';
import { apiService } from '../../services/api';
import { useStore } from '../../store/useStore';
import { ProviderSelector } from '../ProviderSelector';

interface AdminProps {
    isLoading?: boolean;
    isAdmin?: boolean;
    onOpenAdmin?: () => void;
}

export const Settings: React.FC<AdminProps> = ({
    isLoading = false,
}) => {
    const { settings, updateSettings } = useStore();
    const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connecting');

    useEffect(() => {
        checkConnection();
    }, []);

    const checkConnection = async () => {
        try {
            await apiService.listProviders();
            setConnectionStatus('connected');
        } catch (error) {
            setConnectionStatus('disconnected');
        }
    };

    return (
        <div className="px-6 py-4 shadow-lg bg-white dark:bg-gray-900 border-b border-gray-100 dark:border-gray-800 transition-colors duration-300">
            <div className="mt-4 space-y-5 bg-gray-50 dark:bg-gray-950 backdrop-blur-md rounded-xl p-5 border border-gray-200 dark:border-gray-800 animate-in slide-in-from-top-2 duration-200">
                {/* Status & Model Group */}
                <div className="space-y-4 pb-4 border-b border-gray-200 dark:border-gray-800">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-gray-600 dark:text-gray-400">
                            <Cpu className="w-4 h-4" />
                            <span className="text-xs font-semibold uppercase tracking-wider">System Configuration</span>
                        </div>

                        {/* Connection Status Badge */}
                        <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium uppercase tracking-tight bg-white dark:bg-gray-800 border border-gray-100 dark:border-gray-700 text-gray-600 dark:text-gray-300">
                            {connectionStatus === 'connecting' ? (
                                <><div className="w-1.5 h-1.5 rounded-full bg-gray-400 animate-pulse" /> Connecting</>
                            ) : connectionStatus === 'disconnected' ? (
                                <><div className="w-1.5 h-1.5 rounded-full bg-red-400" /> Disconnected</>
                            ) : (
                                <><div className="w-1.5 h-1.5 rounded-full bg-green-400" /> API Online</>
                            )}
                        </div>
                    </div>

                    <ProviderSelector
                        selectedProvider={settings.provider}
                        selectedModel={settings.model}
                        onProviderChange={(provider) => updateSettings({ provider })}
                        onModelChange={(model) => updateSettings({ model })}
                        disabled={isLoading}
                    />
                </div>

                {/* Temperature */}
                <div className="space-y-2">
                    <div className="flex justify-between items-center">
                        <span className="text-xs font-medium uppercase tracking-wider text-gray-600 dark:text-gray-400">Temperature</span>
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200">{settings.temperature.toFixed(1)}</span>
                    </div>
                    <input
                        type="range"
                        min="0"
                        max="2"
                        step="0.1"
                        value={settings.temperature}
                        onChange={(e) => updateSettings({ temperature: parseFloat(e.target.value) })}
                        disabled={isLoading}
                        className="w-full h-1.5 rounded-lg appearance-none cursor-pointer bg-gray-200 dark:bg-gray-700 accent-primary-500"
                    />
                </div>

                {/* Max Tokens */}
                <div className="space-y-2">
                    <div className="flex justify-between items-center">
                        <span className="text-xs font-medium uppercase tracking-wider text-gray-600 dark:text-gray-400">Max Tokens</span>
                        <span className="text-xs font-mono px-2 py-0.5 rounded bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200">{settings.max_tokens}</span>
                    </div>
                    <input
                        type="range"
                        min="100"
                        max="4000"
                        step="100"
                        value={settings.max_tokens}
                        onChange={(e) => updateSettings({ max_tokens: parseInt(e.target.value) })}
                        disabled={isLoading}
                        className="w-full h-1.5 rounded-lg appearance-none cursor-pointer bg-gray-200 dark:bg-gray-700 accent-primary-500"
                    />
                </div>

                {/* Stream Toggle */}
                <label className="flex items-center justify-between gap-2 cursor-pointer group pt-2">
                    <span className="text-xs font-medium uppercase tracking-wider text-gray-600 dark:text-gray-400">Stream responses</span>
                    <div className="relative inline-flex items-center">
                        <input
                            type="checkbox"
                            checked={settings.stream}
                            onChange={(e) => updateSettings({ stream: e.target.checked })}
                            disabled={isLoading}
                            className="sr-only peer"
                        />
                        <div className="w-10 h-5 bg-gray-200 dark:bg-gray-700 rounded-full peer peer-checked:after:translate-x-full after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:rounded-full after:h-4 after:w-4 after:transition-all peer-checked:bg-primary-500"></div>
                    </div>
                </label>
            </div>
        </div>
    );
};