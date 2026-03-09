import React from 'react';
import { Target, Search, BarChart2, TrendingUp, AlertCircle, Eye } from 'lucide-react';

const icons = {
    drill_down: <Search className="w-3.5 h-3.5" />,
    filter: <Target className="w-3.5 h-3.5" />,
    compare: <BarChart2 className="w-3.5 h-3.5" />,
    forecast: <TrendingUp className="w-3.5 h-3.5" />
};

export default function FollowUpButtons({ suggestions, onSelect }) {
    if (!suggestions || suggestions.length === 0) return null;

    return (
        <div className="flex flex-wrap gap-3 mt-6">
            {suggestions.map((s) => (
                <button
                    key={s.id}
                    onClick={() => onSelect(s.query)}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-800/80 hover:bg-slate-700/80 text-blue-300 border border-slate-700 hover:border-blue-500/50 rounded-full text-sm font-medium transition-all shadow-[0_0_15px_-5px_rgba(0,0,0,0.5)]"
                >
                    {icons[s.category] || <Eye className="w-3.5 h-3.5" />}
                    {s.label}
                </button>
            ))}
        </div>
    );
}
