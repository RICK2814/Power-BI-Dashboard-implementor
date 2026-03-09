import React from 'react';
import { History, MessageSquare, ChevronRight } from 'lucide-react';

export default function QueryHistory({ history }) {
    if (!history || history.length === 0) return null;

    return (
        <div className="bg-slate-800/50 backdrop-blur-md border border-slate-700 rounded-2xl p-5 mb-6">
            <div className="flex items-center gap-2 text-slate-300 font-semibold mb-4">
                <History className="w-4 h-4 text-blue-400" />
                <h3>Session History</h3>
            </div>

            <div className="space-y-3 max-h-[300px] overflow-y-auto pr-2 custom-scrollbar">
                {history.slice().reverse().map((item, idx) => (
                    <div key={idx} className="group flex items-start gap-3 p-3 rounded-xl hover:bg-slate-700/50 transition-colors text-sm cursor-pointer">
                        <div className="text-slate-500 mt-0.5">
                            <MessageSquare className="w-4 h-4 group-hover:text-blue-400 transition-colors" />
                        </div>
                        <div className="flex-1">
                            <p className="text-slate-300 font-medium line-clamp-2">{item.query}</p>
                            <p className="text-slate-500 text-xs mt-1 truncate">{item.dashboard_title}</p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-600 group-hover:text-slate-400 transition-colors" />
                    </div>
                ))}
            </div>
        </div>
    );
}
