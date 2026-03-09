import React from 'react';
import { ShoppingBag, Users, Building2, Package, Search, Navigation, PieChart, Activity, UploadCloud } from 'lucide-react';

const icons = {
    retail: <ShoppingBag className="w-8 h-8" />,
    hr: <Users className="w-8 h-8" />,
    finance: <Building2 className="w-8 h-8" />,
    healthcare: <Activity className="w-8 h-8" />,
    supply_chain: <Package className="w-8 h-8" />,
    restaurant: <PieChart className="w-8 h-8" />,
    real_estate: <Navigation className="w-8 h-8" />,
    marketing: <Search className="w-8 h-8" />
};

export default function DomainSelector({ domains, onSelectDomain, onUploadClick }) {
    if (!domains) return <div className="p-8 text-center animate-pulse text-slate-400">Loading domains...</div>;

    return (
        <div className="max-w-7xl mx-auto p-8">
            <div className="text-center mb-12">
                <h1 className="text-4xl font-extrabold text-white mb-4 tracking-tight">Select your Business Domain</h1>
                <p className="text-slate-400 max-w-2xl mx-auto text-lg">
                    Choose a pre-loaded dataset to explore universal Business Intelligence capabilities, or upload your own CSV data.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {domains.map((domain) => (
                    <div
                        key={domain.id}
                        onClick={() => onSelectDomain(domain)}
                        className="bg-slate-800/50 backdrop-blur-md border border-slate-700/50 hover:border-blue-500/50 rounded-2xl p-6 cursor-pointer group transition-all duration-300 hover:shadow-[0_0_30px_-5px_rgba(59,130,246,0.3)] hover:-translate-y-1"
                    >
                        <div className="bg-blue-500/10 w-16 h-16 rounded-xl flex items-center justify-center text-blue-400 mb-6 group-hover:bg-blue-500 group-hover:text-white transition-colors duration-300">
                            {icons[domain.id] || <Activity className="w-8 h-8" />}
                        </div>

                        <h3 className="text-xl font-bold text-white mb-2">{domain.name}</h3>

                        <div className="flex flex-wrap gap-2 mb-6">
                            {domain.metrics.slice(0, 3).map(m => (
                                <span key={m} className="px-2 py-1 bg-slate-700/50 text-slate-300 text-xs rounded-md">
                                    {m}
                                </span>
                            ))}
                        </div>

                        <div className="space-y-3">
                            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Example Queries:</p>
                            {domain.queries.slice(0, 2).map((q, i) => (
                                <div key={i} className="text-sm text-slate-400 line-clamp-2 pl-3 border-l-2 border-slate-700 group-hover:border-blue-500/50 transition-colors">
                                    "{q.query}"
                                </div>
                            ))}
                        </div>
                    </div>
                ))}

                {/* Upload Custom CSV Card */}
                <div
                    onClick={onUploadClick}
                    className="bg-gradient-to-br from-blue-900/40 to-slate-900/40 border border-blue-500/30 border-dashed hover:border-blue-400 rounded-2xl p-6 cursor-pointer group transition-all duration-300 hover:shadow-[0_0_30px_-5px_rgba(59,130,246,0.2)] flex flex-col items-center justify-center text-center min-h-[320px]"
                >
                    <div className="bg-blue-500/20 w-20 h-20 rounded-full flex items-center justify-center text-blue-400 mb-6 group-hover:scale-110 transition-transform duration-300">
                        <UploadCloud className="w-10 h-10" />
                    </div>
                    <h3 className="text-xl font-bold text-white mb-2">Upload Your Own Data</h3>
                    <p className="text-slate-400 text-sm mb-6">
                        Drag and drop a CSV file to instantly generate AI-powered analytics for your custom dataset.
                    </p>
                    <span className="px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium group-hover:bg-blue-500 transition-colors">
                        Choose CSV File
                    </span>
                </div>

            </div>
        </div>
    );
}
