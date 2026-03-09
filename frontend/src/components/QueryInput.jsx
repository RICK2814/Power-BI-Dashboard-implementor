import React, { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';

export default function QueryInput({ onSubmit, isLoading, placeholder }) {
    const [query, setQuery] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        if (!query.trim() || isLoading) return;
        onSubmit(query);
        setQuery('');
    };

    return (
        <form onSubmit={handleSubmit} className="relative max-w-4xl mx-auto w-full">
            <div className="relative flex items-center bg-slate-800/80 backdrop-blur border border-slate-700 rounded-2xl overflow-hidden focus-within:ring-2 focus-within:ring-blue-500/50 focus-within:border-blue-500 transition-all shadow-lg text-white">
                <div className="pl-4 text-blue-400">
                    <Sparkles className="w-5 h-5" />
                </div>
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder={placeholder || "Ask a question about this data in plain English..."}
                    className="flex-1 bg-transparent border-none py-4 px-4 text-[16px] focus:outline-none placeholder:text-slate-500"
                    disabled={isLoading}
                />
                <button
                    type="submit"
                    disabled={isLoading || !query.trim()}
                    className="px-6 py-4 text-slate-300 hover:text-white disabled:text-slate-600 transition-colors bg-blue-600/20 hover:bg-blue-600/40 disabled:bg-transparent"
                >
                    <Send className="w-5 h-5" />
                </button>
            </div>
        </form>
    );
}
