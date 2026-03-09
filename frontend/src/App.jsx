import React, { useState, useEffect, useRef } from 'react';
import { Sparkles, AlertTriangle, ArrowLeft, Lightbulb, Zap, Database, MessageSquare } from 'lucide-react';
import DomainSelector from './components/DomainSelector';
import QueryInput from './components/QueryInput';
import KPICards from './components/KPICards';
import ChartRenderer from './components/ChartRenderer';
import FollowUpButtons from './components/FollowUpButtons';
import CSVUpload from './components/CSVUpload';
import LoadingSteps from './components/LoadingSteps';
import QueryHistory from './components/QueryHistory';

const API = 'http://localhost:8000';

function App() {
    const [domains, setDomains] = useState(null);
    const [sessionId, setSessionId] = useState(null);
    const [view, setView] = useState('home'); // 'home' | 'dashboard'

    const [dashboardData, setDashboardData] = useState(null);
    const [activeDomainName, setActiveDomainName] = useState(null);
    const [history, setHistory] = useState([]);
    const [isLoading, setIsLoading] = useState(false);
    const [showUpload, setShowUpload] = useState(false);
    const [errorObj, setErrorObj] = useState(null);
    const scrollRef = useRef(null);

    useEffect(() => {
        setSessionId(crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36).substring(2, 15));
        fetch(`${API}/api/domains`)
            .then(res => res.json())
            .then(data => setDomains(data))
            .catch(err => console.error("Could not fetch domains", err));
    }, []);

    // ═══════════════════════════════════════════
    // MASTER QUERY HANDLER — works for everything
    // ═══════════════════════════════════════════
    const handleQuery = async (queryText, forceDomain = null) => {
        setIsLoading(true);
        setErrorObj(null);

        try {
            let endpoint, body;

            // Use followup only if we have a real dashboard and it's not a general answer
            const isFollowUp = dashboardData &&
                dashboardData.type === 'dashboard' &&
                dashboardData.charts?.length > 0;

            if (isFollowUp && !forceDomain) {
                endpoint = `${API}/api/followup`;
                body = {
                    prompt: queryText,
                    session_id: sessionId,
                    current_dashboard: dashboardData,
                    current_sql: dashboardData.sqlExecuted,
                    domain: dashboardData.routed_domain || null
                };
            } else {
                endpoint = `${API}/api/query`;
                body = {
                    prompt: queryText,
                    session_id: sessionId,
                    domain: forceDomain || 'auto'
                };
            }

            const res = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            const data = await res.json();

            if (data.type === 'error' || data.userMessage) {
                setErrorObj(data);
            } else {
                setDashboardData(data);
                setView('dashboard');
                setActiveDomainName(data.routed_domain_name || data.domain || 'AI');
                setHistory(prev => [...prev, {
                    query: queryText,
                    dashboard_title: data.dashboardTitle || 'AI Answer',
                    domain: data.routed_domain || 'general'
                }]);
            }
        } catch (e) {
            setErrorObj({ userMessage: "Network error — make sure the backend is running on port 8000." });
        } finally {
            setIsLoading(false);
            if (scrollRef.current) scrollRef.current.scrollTo({ top: 0, behavior: 'smooth' });
        }
    };

    const handleCsvUpload = async (file) => {
        setIsLoading(true);
        setShowUpload(false);
        setErrorObj(null);

        const formData = new FormData();
        formData.append('file', file);
        if (sessionId) formData.append('session_id', sessionId);

        try {
            const res = await fetch(`${API}/api/upload`, { method: 'POST', body: formData });
            const data = await res.json();
            if (data.type === "dashboard") {
                if (data.session_id) setSessionId(data.session_id);
                setView('dashboard');
                setActiveDomainName(data.routed_domain_name || "Custom Upload");
                setDashboardData(data);
                setHistory([{ query: "Auto-Analysis", dashboard_title: data.dashboardTitle, domain: "custom" }]);
            } else {
                setErrorObj({ userMessage: data.detail || "Upload analysis failed." });
            }
        } catch (e) {
            setErrorObj({ userMessage: "Failed to process the CSV file." });
        } finally {
            setIsLoading(false);
        }
    };

    const resetToHome = () => {
        setView('home');
        setDashboardData(null);
        setErrorObj(null);
        setActiveDomainName(null);
    };

    const newQuery = () => {
        setDashboardData(null);
        setErrorObj(null);
        setActiveDomainName(null);
        setView('dashboard');
    };

    const handleAutoAnalyze = async (domain) => {
        setIsLoading(true);
        setErrorObj(null);
        try {
            const res = await fetch(`${API}/api/auto_analyze/${domain.id}`, { method: 'POST' });
            const data = await res.json();
            if (data.type === "dashboard") {
                setView('dashboard');
                setActiveDomainName(data.routed_domain_name || domain.name);
                setDashboardData(data);
                setHistory([{ query: "Auto-Analysis", dashboard_title: data.dashboardTitle, domain: domain.id }]);
            } else {
                setErrorObj({ userMessage: data.detail || "Auto-analysis failed." });
            }
        } catch (e) {
            // Fallback: try a query instead
            handleQuery(domain.queries[0]?.query || `Show me an overview of ${domain.name}`, domain.id);
        } finally {
            setIsLoading(false);
        }
    };

    // ═══════════════════════════════════════════
    // HOME VIEW — Domain cards + global search
    // ═══════════════════════════════════════════
    if (view === 'home') {
        return (
            <div className="min-h-screen bg-slate-950 font-sans overflow-y-auto w-full relative pb-32">
                {showUpload && <CSVUpload onUpload={handleCsvUpload} onCancel={() => setShowUpload(false)} />}
                {isLoading && <div className="fixed inset-0 bg-slate-950/90 backdrop-blur z-50 flex items-center justify-center"><LoadingSteps /></div>}

                {/* Error Toast */}
                {errorObj && !isLoading && (
                    <div className="fixed top-20 left-1/2 -translate-x-1/2 z-50 bg-rose-500/10 border border-rose-500/30 backdrop-blur-lg rounded-2xl p-6 max-w-lg w-full animate-in fade-in slide-in-from-top-4">
                        <AlertTriangle className="w-6 h-6 text-rose-400 mx-auto mb-2" />
                        <p className="text-white text-center font-medium">{errorObj.userMessage}</p>
                        {errorObj.suggestions?.length > 0 && (
                            <div className="mt-4 flex flex-wrap justify-center gap-2">
                                {errorObj.suggestions.map((s, i) => (
                                    <button key={i} onClick={() => { setErrorObj(null); handleQuery(s); }} className="text-xs bg-slate-800 text-blue-300 px-3 py-1.5 rounded-full hover:bg-slate-700">{s}</button>
                                ))}
                            </div>
                        )}
                        <button onClick={() => setErrorObj(null)} className="mt-3 text-xs text-slate-500 hover:text-white block mx-auto">Dismiss</button>
                    </div>
                )}

                {/* Header */}
                <div className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md sticky top-0 z-40">
                    <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <div className="bg-blue-500 w-8 h-8 rounded-lg flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
                                <Sparkles className="w-5 h-5" />
                            </div>
                            <span className="text-xl font-bold text-white tracking-tight">ConvoBI</span>
                            <span className="text-xs bg-emerald-500/10 text-emerald-400 px-2 py-0.5 rounded-full font-semibold border border-emerald-500/20">Agentic AI</span>
                        </div>
                        {history.length > 0 && (
                            <button onClick={() => setView('dashboard')} className="text-sm text-blue-400 hover:text-white transition-colors">
                                ← Back to Dashboard
                            </button>
                        )}
                    </div>
                </div>

                {/* Hero section */}
                <div className="max-w-4xl mx-auto text-center pt-16 pb-8 px-6">
                    <h1 className="text-5xl font-extrabold text-white mb-4 tracking-tight leading-tight">
                        Ask <span className="bg-gradient-to-r from-blue-400 to-violet-400 bg-clip-text text-transparent">anything</span> about your data
                    </h1>
                    <p className="text-slate-400 text-lg max-w-2xl mx-auto mb-8">
                        No SQL needed. No domain selection needed. Just ask a question in plain English — the AI figures out everything automatically.
                    </p>

                    {/* Capability pills */}
                    <div className="flex flex-wrap justify-center gap-3 mb-8">
                        <span className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-full text-sm text-slate-300">
                            <Zap className="w-4 h-4 text-amber-400" /> Auto-routes to correct dataset
                        </span>
                        <span className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-full text-sm text-slate-300">
                            <Database className="w-4 h-4 text-blue-400" /> 8 pre-loaded domains
                        </span>
                        <span className="flex items-center gap-2 px-4 py-2 bg-slate-800/50 border border-slate-700 rounded-full text-sm text-slate-300">
                            <MessageSquare className="w-4 h-4 text-emerald-400" /> Answers general questions too
                        </span>
                    </div>
                </div>

                <DomainSelector
                    domains={domains}
                    onSelectDomain={handleAutoAnalyze}
                    onUploadClick={() => setShowUpload(true)}
                />

                {/* Global Search Bar */}
                <div className="fixed bottom-0 left-0 right-0 w-full p-6 bg-gradient-to-t from-slate-950 via-slate-950/95 to-transparent z-40 pointer-events-none">
                    <div className="pointer-events-auto max-w-4xl mx-auto w-full flex justify-center pb-2">
                        <QueryInput
                            onSubmit={(q) => handleQuery(q)}
                            isLoading={isLoading}
                            placeholder="Ask anything — 'Show monthly revenue trend', 'What is the capital of France', 'Which dept has highest attrition?' ..."
                        />
                    </div>
                </div>
            </div>
        );
    }

    // ═══════════════════════════════════════════
    // DASHBOARD VIEW — Results + follow-ups
    // ═══════════════════════════════════════════
    return (
        <div className="h-screen bg-slate-950 font-sans overflow-hidden flex flex-col text-slate-200">
            {isLoading && <div className="fixed inset-0 bg-slate-950/90 backdrop-blur z-50 flex items-center justify-center"><LoadingSteps /></div>}

            {/* Navbar */}
            <div className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-md flex-shrink-0 z-40">
                <div className="flex justify-between items-center h-16 px-6">
                    <div className="flex items-center gap-4">
                        <button onClick={resetToHome} className="flex items-center gap-3 group">
                            <div className="bg-blue-500 w-8 h-8 rounded-lg flex items-center justify-center text-white shadow-lg shadow-blue-500/20 group-hover:bg-blue-600 transition-colors">
                                <Sparkles className="w-5 h-5" />
                            </div>
                            <span className="text-xl font-bold text-white tracking-tight">ConvoBI</span>
                        </button>
                        <div className="h-6 w-px bg-slate-700 mx-2"></div>
                        {activeDomainName && (
                            <div className="flex flex-col">
                                <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Auto-Routed To</span>
                                <span className="text-sm text-blue-400 font-medium">{activeDomainName}</span>
                            </div>
                        )}
                    </div>
                    <div className="flex items-center gap-3">
                        <button onClick={newQuery} className="text-xs text-slate-400 hover:text-white px-3 py-1.5 border border-slate-700 hover:border-blue-500 rounded-lg transition-colors">
                            New Query
                        </button>
                        <button onClick={resetToHome} className="text-xs text-blue-400 hover:text-white px-3 py-1.5 border border-blue-500/30 hover:border-blue-500 rounded-lg transition-colors flex items-center gap-1">
                            <ArrowLeft className="w-3 h-3" /> Home
                        </button>
                    </div>
                </div>
            </div>

            {/* Main Canvas */}
            <div className="flex flex-1 overflow-hidden relative">
                {/* Sidebar */}
                <div className="w-[300px] border-r border-slate-800 bg-slate-900/30 p-4 overflow-y-auto hidden md:block">
                    <QueryHistory history={history} />
                </div>

                {/* Content Area */}
                <div ref={scrollRef} className="flex-1 flex flex-col bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-slate-950 overflow-y-auto relative">
                    <div className="w-full max-w-7xl mx-auto p-4 md:p-8 pb-32">

                        {/* Error State */}
                        {errorObj && !isLoading && (
                            <div className="bg-rose-500/10 border border-rose-500/20 rounded-2xl p-6 mb-8 max-w-3xl mx-auto animate-in fade-in text-center">
                                <AlertTriangle className="w-10 h-10 text-rose-400 mx-auto mb-4" />
                                <h3 className="text-lg font-bold text-white mb-2">{errorObj.userMessage}</h3>
                                {errorObj.didYouMean && (
                                    <p className="text-slate-300 mb-4">Did you mean: <button onClick={() => handleQuery(errorObj.didYouMean)} className="text-blue-400 hover:underline">{errorObj.didYouMean}</button>?</p>
                                )}
                                {errorObj.suggestions?.length > 0 && (
                                    <div className="mt-6 flex flex-wrap justify-center gap-3">
                                        {errorObj.suggestions.map((s, idx) => (
                                            <button key={idx} onClick={() => { setErrorObj(null); handleQuery(s); }} className="text-sm bg-slate-800 text-slate-300 px-4 py-2 rounded-full hover:bg-slate-700">{s}</button>
                                        ))}
                                    </div>
                                )}
                            </div>
                        )}

                        {/* Empty State */}
                        {!dashboardData && !isLoading && !errorObj && (
                            <div className="h-[50vh] flex flex-col items-center justify-center text-center animate-in fade-in duration-500">
                                <h2 className="text-4xl font-extrabold text-white mb-4 tracking-tight">What do you want to know?</h2>
                                <p className="text-slate-400 text-lg max-w-2xl">
                                    Ask a follow-up question or type a completely new question — the AI will auto-detect which dataset to use.
                                </p>
                            </div>
                        )}

                        {/* Dashboard Data */}
                        {dashboardData && !isLoading && (
                            <div className="animate-in slide-in-from-bottom-8 fade-in duration-500 w-full">
                                {dashboardData.type === 'general_answer' ? (
                                    <div className="max-w-3xl mx-auto py-8">
                                        <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 shadow-2xl">
                                            <div className="flex items-center gap-3 mb-6">
                                                <div className="bg-emerald-500/20 p-2 rounded-lg">
                                                    <MessageSquare className="w-5 h-5 text-emerald-400" />
                                                </div>
                                                <h2 className="text-xl font-bold text-white">AI Response</h2>
                                            </div>
                                            <p className="text-slate-300 text-lg leading-relaxed whitespace-pre-wrap">
                                                {dashboardData.userMessage}
                                            </p>
                                            {dashboardData.followUpSuggestions?.length > 0 && (
                                                <div className="mt-8 pt-8 border-t border-slate-800">
                                                    <p className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-4">Follow-up questions</p>
                                                    <FollowUpButtons suggestions={dashboardData.followUpSuggestions} onSelect={(q) => { setDashboardData(null); handleQuery(q); }} />
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        {/* Title + Insight */}
                                        <div className="mb-8 flex flex-col gap-4">
                                            <h2 className="text-3xl font-extrabold text-white tracking-tight">{dashboardData.dashboardTitle}</h2>
                                            {dashboardData.businessInsight && (
                                                <div className="bg-blue-900/20 border-l-4 border-blue-500 p-4 rounded-r-xl">
                                                    <p className="text-blue-200 text-lg italic leading-relaxed">{dashboardData.businessInsight}</p>
                                                </div>
                                            )}
                                        </div>

                                        {/* KPI Cards */}
                                        {dashboardData.summaryStats?.length > 0 && (
                                            <div className="mb-8">
                                                <KPICards stats={dashboardData.summaryStats} />
                                            </div>
                                        )}

                                        {/* Charts */}
                                        {dashboardData.charts?.length > 0 && (
                                            <div className="w-full">
                                                <ChartRenderer charts={dashboardData.charts} />
                                            </div>
                                        )}

                                        {/* AI Insights */}
                                        {dashboardData.aiInsights?.length > 0 && (
                                            <div className="mt-8 bg-emerald-900/10 border border-emerald-500/20 rounded-2xl p-6">
                                                <h4 className="text-sm font-semibold text-emerald-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                                    <Lightbulb className="w-4 h-4" /> AI-Generated Insights
                                                </h4>
                                                <ul className="space-y-3">
                                                    {dashboardData.aiInsights.map((insight, i) => (
                                                        <li key={i} className="text-slate-300 text-sm flex items-start gap-3">
                                                            <span className="text-emerald-400 mt-0.5 font-bold">{i + 1}.</span>
                                                            {insight}
                                                        </li>
                                                    ))}
                                                </ul>
                                                {dashboardData.recommendations?.length > 0 && (
                                                    <div className="mt-4 pt-4 border-t border-emerald-500/10">
                                                        <p className="text-xs font-semibold text-amber-400 uppercase tracking-wider mb-2">💡 Recommendations</p>
                                                        {dashboardData.recommendations.map((rec, i) => (
                                                            <p key={i} className="text-slate-300 text-sm">{rec}</p>
                                                        ))}
                                                    </div>
                                                )}
                                            </div>
                                        )}

                                        {/* SQL + Follow-ups */}
                                        <div className="mt-8 flex flex-col md:flex-row gap-6 items-start">
                                            <div className="flex-1">
                                                <h4 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">Continue exploring</h4>
                                                <FollowUpButtons suggestions={dashboardData.followUpSuggestions} onSelect={(q) => { setDashboardData(null); handleQuery(q); }} />
                                            </div>
                                            {dashboardData.sqlExecuted && (
                                                <div className="w-full md:w-1/3 bg-slate-900 rounded-xl border border-slate-800 p-4 shrink-0">
                                                    <h4 className="text-xs font-semibold text-slate-500 mb-2">EXECUTED SQL</h4>
                                                    <code className="text-xs text-blue-300 font-mono break-all whitespace-pre-wrap">{dashboardData.sqlExecuted}</code>
                                                </div>
                                            )}
                                        </div>
                                    </>
                                )}
                            </div>
                        )}
                    </div>
                </div>

                {/* Floating Input */}
                <div className="absolute bottom-0 left-0 right-0 w-full p-6 bg-gradient-to-t from-slate-950 via-slate-950/95 to-transparent z-40 pointer-events-none">
                    <div className="pointer-events-auto w-full md:w-[calc(100%-300px)] md:ml-[300px] flex justify-center pb-2">
                        <QueryInput
                            onSubmit={(q) => { setErrorObj(null); handleQuery(q); }}
                            isLoading={isLoading}
                            placeholder={dashboardData ? "Ask a follow-up or any new question..." : "Ask anything..."}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}

export default App;
