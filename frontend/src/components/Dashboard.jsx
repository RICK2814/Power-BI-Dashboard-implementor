import React from 'react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
    LineChart, Line, AreaChart, Area, PieChart, Pie, Cell
} from 'recharts';
import { DollarSign, TrendingUp, Users, Package, Clock, Activity, AlertCircle } from 'lucide-react';

const COLORS = {
    blue: ['#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#1d4ed8'],
    green: ['#22c55e', '#4ade80', '#86efac', '#bbf7d0', '#15803d'],
    multi: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6366f1']
};

const getIcon = (iconName) => {
    switch (iconName) {
        case 'revenue': return <DollarSign className="w-5 h-5" />;
        case 'growth': return <TrendingUp className="w-5 h-5" />;
        case 'customers': return <Users className="w-5 h-5" />;
        case 'units': return <Package className="w-5 h-5" />;
        case 'time': return <Clock className="w-5 h-5" />;
        default: return <Activity className="w-5 h-5" />;
    }
};

const Dashboard = ({ data }) => {
    if (!data) return null;

    return (
        <div className="space-y-6 max-w-6xl mx-auto pb-10">
            {/* Header */}
            <div className="flex justify-between items-end">
                <div>
                    <h2 className="text-2xl font-bold text-slate-800 tracking-tight">{data.dashboardTitle}</h2>
                    <p className="text-sm text-slate-500 mt-1 flex items-center gap-2">
                        Generated just now
                        {data.dataConfidence === 'medium' && (
                            <span className="inline-flex items-center gap-1 text-amber-600 bg-amber-50 px-2 py-0.5 rounded text-xs">
                                <AlertCircle className="w-3 h-3" /> Medium Confidence
                            </span>
                        )}
                    </p>
                </div>
            </div>

            {/* KPI Cards */}
            {data.summaryStats && data.summaryStats.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {data.summaryStats.map((stat) => (
                        <div key={stat.id} className="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm relative overflow-hidden group">
                            <div className="absolute top-0 right-0 p-4 opacity-10 transform translate-x-1/4 -translate-y-1/4 group-hover:scale-110 transition-transform duration-500">
                                {getIcon(stat.icon)}
                            </div>
                            <div className="flex justify-between items-start mb-4">
                                <span className="text-sm font-semibold text-slate-500">{stat.label}</span>
                                <div className={`p-2 rounded-lg ${stat.trend === 'up' ? 'bg-emerald-50 text-emerald-600' :
                                        stat.trend === 'down' ? 'bg-rose-50 text-rose-600' :
                                            'bg-slate-50 text-slate-600'
                                    }`}>
                                    {getIcon(stat.icon)}
                                </div>
                            </div>
                            <div className="flex items-baseline gap-2">
                                <h3 className="text-3xl font-bold text-slate-800 tracking-tight">{stat.value}</h3>
                            </div>
                            {stat.delta && (
                                <div className="mt-3 text-xs font-medium">
                                    <span className={
                                        stat.trend === 'up' ? 'text-emerald-600' :
                                            stat.trend === 'down' ? 'text-rose-600' : 'text-slate-500'
                                    }>
                                        {stat.delta}
                                    </span>
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {/* Charts Area */}
            {data.charts && data.charts.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {data.charts.map((chart) => (
                        <div key={chart.id} className={`bg-white p-6 rounded-2xl border border-slate-200 shadow-sm ${chart.layout === 'full' ? 'md:col-span-2' : ''}`}>
                            <div className="mb-6">
                                <h3 className="text-lg font-bold text-slate-800">{chart.title}</h3>
                                <p className="text-sm text-slate-500">{chart.subtitle}</p>
                            </div>

                            <div className="h-[300px] w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                    {chart.chartType === 'bar' ? (
                                        <BarChart data={chart.data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                                            {chart.showGrid && <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />}
                                            <XAxis dataKey={chart.xKey} axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dy={10} />
                                            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dx={-10} />
                                            {chart.showTooltip && <Tooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />}
                                            {chart.showLegend && <Legend wrapperStyle={{ paddingTop: '20px' }} />}
                                            {chart.yKeys.map((key, index) => (
                                                <Bar
                                                    key={key}
                                                    dataKey={key}
                                                    name={chart.yLabels?.[index] || key}
                                                    fill={COLORS[chart.colorScheme || 'blue'][index % 5]}
                                                    radius={[4, 4, 0, 0]}
                                                    barSize={chart.layout === 'full' ? 40 : 20}
                                                />
                                            ))}
                                        </BarChart>
                                    ) : chart.chartType === 'line' ? (
                                        <LineChart data={chart.data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                                            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                                            <XAxis dataKey={chart.xKey} axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dy={10} />
                                            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontSize: 12 }} dx={-10} />
                                            <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)' }} />
                                            <Legend wrapperStyle={{ paddingTop: '20px' }} />
                                            {chart.yKeys.map((key, index) => (
                                                <Line type="monotone" key={key} dataKey={key} name={chart.yLabels?.[index] || key} stroke={COLORS[chart.colorScheme || 'blue'][index % 5]} strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                                            ))}
                                        </LineChart>
                                    ) : (
                                        <div className="flex items-center justify-center h-full text-slate-400 bg-slate-50 rounded-lg border border-dashed border-slate-200">
                                            Chart type "{chart.chartType}" not fully implemented in this demo.
                                        </div>
                                    )}
                                </ResponsiveContainer>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* Development Debug Info */}
            <div className="mt-8">
                <details className="text-xs text-slate-400 group">
                    <summary className="cursor-pointer hover:text-slate-600 outline-none">Show Internal Details</summary>
                    <div className="mt-3 p-4 bg-slate-800 text-slate-300 rounded-lg overflow-x-auto whitespace-pre font-mono">
                        {data.sqlExecuted}
                    </div>
                </details>
            </div>
        </div>
    );
};

export default Dashboard;
