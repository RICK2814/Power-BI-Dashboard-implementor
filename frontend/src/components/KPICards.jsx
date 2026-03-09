import React from 'react';
import { TrendingUp, TrendingDown, Minus, DollarSign, Users, Clock, Package, Activity, Target } from 'lucide-react';

const icons = {
    revenue: <DollarSign className="w-5 h-5" />,
    users: <Users className="w-5 h-5" />,
    growth: <TrendingUp className="w-5 h-5" />,
    time: <Clock className="w-5 h-5" />,
    quality: <Target className="w-5 h-5" />,
    risk: <Activity className="w-5 h-5" />,
    inventory: <Package className="w-5 h-5" />,
    conversion: <Target className="w-5 h-5" />
};

export default function KPICards({ stats }) {
    if (!stats || stats.length === 0) return null;

    return (
        <div className="flex gap-4 overflow-x-auto pb-4 hide-scrollbar snap-x">
            {stats.map((stat, idx) => (
                <div
                    key={stat.id || idx}
                    className="snap-start min-w-[240px] flex-1 bg-slate-800/60 backdrop-blur-sm border border-slate-700 p-5 rounded-2xl relative overflow-hidden group hover:border-slate-600 transition-colors"
                >
                    <div className="absolute -right-4 -top-4 text-slate-700/30 opacity-20 transform scale-150 group-hover:scale-110 transition-transform duration-500">
                        {icons[stat.icon] || <Activity className="w-20 h-20" />}
                    </div>

                    <div className="flex justify-between items-start mb-4 relative z-10">
                        <span className="text-sm font-medium text-slate-400">{stat.label}</span>
                        <div className={`p-1.5 rounded-lg ${stat.trend === 'up' ? 'bg-emerald-500/10 text-emerald-400' :
                                stat.trend === 'down' ? 'bg-rose-500/10 text-rose-400' :
                                    'bg-slate-700 text-slate-400'
                            }`}>
                            {stat.trend === 'up' ? <TrendingUp className="w-4 h-4" /> :
                                stat.trend === 'down' ? <TrendingDown className="w-4 h-4" /> :
                                    <Minus className="w-4 h-4" />}
                        </div>
                    </div>

                    <div className="relative z-10">
                        <h3 className="text-3xl font-bold text-white tracking-tight">{stat.value}</h3>
                        {stat.delta && (
                            <div className="mt-2 text-xs font-semibold flex items-center gap-1">
                                <span className={
                                    stat.trend === 'up' ? 'text-emerald-400' :
                                        stat.trend === 'down' ? 'text-rose-400' : 'text-slate-400'
                                }>
                                    {stat.delta}
                                </span>
                            </div>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
}
