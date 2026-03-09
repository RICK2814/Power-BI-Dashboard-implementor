import React from 'react';
import {
    BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell, ScatterChart, Scatter,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const PALETTES = {
    blue: ['#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#1d4ed8'],
    green: ['#22c55e', '#4ade80', '#86efac', '#bbf7d0', '#15803d'],
    amber: ['#f59e0b', '#fbbf24', '#fcd34d', '#fde68a', '#b45309'],
    rose: ['#f43f5e', '#fb7185', '#fda4af', '#fecdd3', '#be123c'],
    violet: ['#8b5cf6', '#a78bfa', '#c4b5fd', '#ddd6fe', '#6d28d9'],
    teal: ['#14b8a6', '#2dd4bf', '#5eead4', '#99f6e4', '#0f766e'],
    multi: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#6366f1']
};

export default function ChartRenderer({ charts }) {
    if (!charts || charts.length === 0) return null;

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {charts.map((chart) => {
                // Evaluate layout size
                const colSpan = chart.layout === 'full' ? 'md:col-span-2 lg:col-span-3' :
                    chart.layout === 'half' ? 'md:col-span-2 lg:col-span-2' :
                        'col-span-1';

                const colors = PALETTES[chart.colorScheme] || PALETTES.blue;
                // Basic data processing
                const data = chart.data || [];

                return (
                    <div key={chart.id} className={`bg-slate-800/80 backdrop-blur-sm p-6 rounded-2xl border border-slate-700 shadow-xl ${colSpan}`}>
                        <div className="mb-6">
                            <h3 className="text-xl font-bold text-white tracking-tight">{chart.title}</h3>
                            <p className="text-sm text-slate-400 mt-1">{chart.subtitle}</p>
                        </div>

                        <div className="h-[350px] w-full mt-4">
                            <ResponsiveContainer width="100%" height="100%">
                                {chart.chartType === 'bar' ? (
                                    <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                                        {chart.showGrid && <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />}
                                        <XAxis dataKey={chart.xKey} axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} dy={10} />
                                        <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} dx={-10} />
                                        <Tooltip cursor={{ fill: '#1e293b' }} contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }} />
                                        {chart.showLegend && <Legend wrapperStyle={{ paddingTop: '20px', color: '#cbd5e1' }} />}
                                        {chart.yKeys.map((key, idx) => (
                                            <Bar
                                                key={key}
                                                dataKey={key}
                                                name={chart.yLabels?.[idx] || key}
                                                fill={colors[idx % colors.length]}
                                                radius={chart.stacked ? [0, 0, 0, 0] : [4, 4, 0, 0]}
                                                stackId={chart.stacked ? "a" : undefined}
                                            />
                                        ))}
                                    </BarChart>
                                ) : chart.chartType === 'line' ? (
                                    <LineChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                                        {chart.showGrid && <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />}
                                        <XAxis dataKey={chart.xKey} axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} dy={10} />
                                        <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} dx={-10} />
                                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }} />
                                        {chart.showLegend && <Legend wrapperStyle={{ paddingTop: '20px', color: '#cbd5e1' }} />}
                                        {chart.yKeys.map((key, idx) => (
                                            <Line
                                                type="monotone"
                                                key={key}
                                                dataKey={key}
                                                name={chart.yLabels?.[idx] || key}
                                                stroke={colors[idx % colors.length]}
                                                strokeWidth={3}
                                                dot={{ r: 3, fill: '#0f172a', strokeWidth: 2 }}
                                                activeDot={{ r: 6, strokeWidth: 0 }}
                                            />
                                        ))}
                                    </LineChart>
                                ) : chart.chartType === 'area' ? (
                                    <AreaChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                                        {chart.showGrid && <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#334155" />}
                                        <XAxis dataKey={chart.xKey} axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} dy={10} />
                                        <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94a3b8', fontSize: 12 }} dx={-10} />
                                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }} />
                                        {chart.showLegend && <Legend wrapperStyle={{ paddingTop: '20px', color: '#cbd5e1' }} />}
                                        {chart.yKeys.map((key, idx) => (
                                            <Area
                                                type="monotone"
                                                key={key}
                                                dataKey={key}
                                                name={chart.yLabels?.[idx] || key}
                                                stroke={colors[idx % colors.length]}
                                                fill={colors[idx % colors.length]}
                                                fillOpacity={0.3}
                                                stackId={chart.stacked ? "a" : undefined}
                                            />
                                        ))}
                                    </AreaChart>
                                ) : chart.chartType === 'pie' || chart.chartType === 'donut' ? (
                                    <PieChart margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                                        <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px', color: '#fff' }} />
                                        {chart.showLegend && <Legend wrapperStyle={{ paddingTop: '0px', color: '#cbd5e1' }} />}
                                        <Pie
                                            data={data}
                                            dataKey={chart.yKeys[0]}
                                            nameKey={chart.xKey}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={chart.chartType === 'donut' ? '60%' : '0%'}
                                            outerRadius='80%'
                                            stroke="#0f172a"
                                            strokeWidth={2}
                                        >
                                            {data.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                                            ))}
                                        </Pie>
                                    </PieChart>
                                ) : chart.chartType === 'table' ? (
                                    <div className="overflow-auto h-full rounded-lg border border-slate-700 bg-slate-900/50">
                                        <table className="w-full text-left text-sm text-slate-300">
                                            <thead className="bg-slate-800/80 uppercase text-xs text-slate-400 sticky top-0 z-10">
                                                <tr>
                                                    {Object.keys(data[0] || {}).map(k => (
                                                        <th key={k} className="px-4 py-3 border-b border-slate-700">{k.replace(/_/g, ' ')}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {data.map((row, i) => (
                                                    <tr key={i} className="hover:bg-slate-800/40 border-b border-slate-800/50">
                                                        {Object.values(row).map((v, idx) => (
                                                            <td key={idx} className="px-4 py-3 whitespace-nowrap">{v}</td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                ) : (
                                    <div className="flex items-center justify-center h-full text-slate-500 border border-slate-700 border-dashed rounded-xl">
                                        Unsupported chart type: {chart.chartType}
                                    </div>
                                )}
                            </ResponsiveContainer>
                        </div>
                    </div>
                );
            })}
        </div>
    );
}
