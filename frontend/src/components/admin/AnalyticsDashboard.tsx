import {
    DollarSign,
    MessageSquare,
    Users,
    Zap
} from 'lucide-react';
import React, { useEffect, useState } from 'react';
import {
    Bar,
    BarChart,
    CartesianGrid,
    Legend,
    Line,
    LineChart,
    ResponsiveContainer,
    Tooltip,
    XAxis,
    YAxis,
} from 'recharts';
import { apiService } from '../../services/api';
import type { AnalyticsDashboard } from '../../types/admin';

export const AnalyticsDashboardComp: React.FC = () => {
    const [data, setData] = useState<AnalyticsDashboard | null>(null);
    const [loading, setLoading] = useState(false);
    const [days, setDays] = useState(30);

    useEffect(() => {
        loadData();
    }, [days]);

    const loadData = async () => {
        setLoading(true);
        try {
            const dashboard = await apiService.adminGetDashboard(days);
            setData(dashboard);
        } catch (error) {
            console.error('Failed to load analytics:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading || !data) {
        return <div className="p-8 text-center">Loading analytics...</div>;
    }

    return (
        <div>
            <br></br>
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-2xl font-bold text-gray-900">Analytics Dashboard</h1>
                <select
                    value={days}
                    onChange={(e) => setDays(parseInt(e.target.value))}
                    className="input"
                >
                    <option value={7}>Last 7 days</option>
                    <option value={30}>Last 30 days</option>
                    <option value={90}>Last 90 days</option>
                    <option value={365}>Last year</option>
                </select>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                <StatCard
                    title="Total Users"
                    value={data.overview.total_users}
                    icon={Users}
                    color="blue"
                    subtitle={`${data.overview.active_users} active`}
                />
                <StatCard
                    title="Conversations"
                    value={data.overview.total_conversations}
                    icon={MessageSquare}
                    color="green"
                    subtitle={`${data.overview.period_conversations} in period`}
                />
                <StatCard
                    title="Total Tokens"
                    value={data.overview.total_tokens.toLocaleString()}
                    icon={Zap}
                    color="purple"
                />
                <StatCard
                    title="Total Cost"
                    value={`$${data.overview.total_cost.toFixed(2)}`}
                    icon={DollarSign}
                    color="orange"
                />
            </div>

            {/* Charts Row 1 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">

                {/* Model Popularity */}
                <div className="card p-6">
                    <h3 className="text-lg font-semibold mb-4">Top Models</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <BarChart data={data.model_popularity}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis dataKey="model" angle={-45} textAnchor="end" height={100} />
                            <YAxis />
                            <Tooltip />
                            <Bar dataKey="count" fill="#3b82f6" />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Daily Usage Trend */}
            <div className="card p-6 mb-6">
                <h3 className="text-lg font-semibold mb-4">Daily Usage Trend</h3>
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={data.daily_usage}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="date" />
                        <YAxis yAxisId="left" />
                        <YAxis yAxisId="right" orientation="right" />
                        <Tooltip />
                        <Legend />
                        <Line
                            yAxisId="left"
                            type="monotone"
                            dataKey="conversations"
                            stroke="#3b82f6"
                            name="Conversations"
                        />
                        <Line
                            yAxisId="right"
                            type="monotone"
                            dataKey="tokens"
                            stroke="#10b981"
                            name="Tokens"
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Top Users */}
            <div className="card p-6 mb-6">
                <h3 className="text-lg font-semibold mb-4">Top Users by Cost</h3>
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">
                                    Username
                                </th>
                                <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">
                                    Total Tokens
                                </th>
                                <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">
                                    Total Cost
                                </th>
                                <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">
                                    Monthly Cost
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                            {data.top_users.map((user, idx) => (
                                <tr key={idx}>
                                    <td className="px-4 py-3 text-sm">{user.username}</td>
                                    <td className="px-4 py-3 text-sm">
                                        {user.total_tokens.toLocaleString()}
                                    </td>
                                    <td className="px-4 py-3 text-sm">
                                        ${user.total_cost.toFixed(4)}
                                    </td>
                                    <td className="px-4 py-3 text-sm">
                                        ${user.monthly_cost.toFixed(4)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

        </div>
    );
};

const StatCard: React.FC<{
    title: string;
    value: string | number;
    icon: any;
    color: string;
    subtitle?: string;
}> = ({ title, value, icon: Icon, color, subtitle }) => {
    const colors = {
        blue: 'bg-blue-50 text-blue-600',
        green: 'bg-green-50 text-green-600',
        purple: 'bg-purple-50 text-purple-600',
        orange: 'bg-orange-50 text-orange-600',
    };

    return (
        <div className="card p-6">
            <div className="flex items-start justify-between mb-3">
                <div className={`p-2 rounded-lg ${colors[color as keyof typeof colors]}`}>
                    <Icon className="w-5 h-5" />
                </div>
            </div>
            <div className="text-2xl font-bold text-gray-900 mb-1">{value}</div>
            <div className="text-sm text-gray-600">{title}</div>
            {subtitle && <div className="text-xs text-gray-500 mt-1">{subtitle}</div>}
        </div>
    );
};