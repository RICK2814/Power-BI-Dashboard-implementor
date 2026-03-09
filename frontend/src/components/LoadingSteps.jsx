import React, { useEffect, useState } from 'react';
import { Search, Database, BarChart2, Sparkles } from 'lucide-react';

const steps = [
    { id: 1, text: "Understanding your question...", icon: <Search className="w-4 h-4" /> },
    { id: 2, text: "Writing optimized SQL...", icon: <Database className="w-4 h-4" /> },
    { id: 3, text: "Fetching rows from database...", icon: <Database className="w-4 h-4" /> },
    { id: 4, text: "Building visualizations...", icon: <BarChart2 className="w-4 h-4" /> }
];

export default function LoadingSteps() {
    const [activeStep, setActiveStep] = useState(1);

    useEffect(() => {
        let current = 1;
        const interval = setInterval(() => {
            current++;
            if (current > 4) current = 4;
            setActiveStep(current);
        }, 1500);
        return () => clearInterval(interval);
    }, []);

    return (
        <div className="flex flex-col items-center justify-center py-20 animate-in fade-in duration-300">
            <div className="w-16 h-16 bg-blue-500/20 rounded-full flex items-center justify-center text-blue-400 mb-8 animate-pulse shadow-[0_0_30px_-5px_rgba(59,130,246,0.3)]">
                <Sparkles className="w-8 h-8" />
            </div>

            <div className="space-y-4 max-w-sm w-full">
                {steps.map((step) => (
                    <div
                        key={step.id}
                        className={`flex items-center gap-4 transition-all duration-500 ${activeStep === step.id ? 'opacity-100 translate-x-0' :
                                activeStep > step.id ? 'opacity-40 translate-x-0 text-emerald-400' :
                                    'opacity-0 -translate-x-4'
                            }`}
                    >
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${activeStep === step.id ? 'bg-blue-500 text-white shadow-lg shadow-blue-500/30' :
                                activeStep > step.id ? 'bg-emerald-500/20 text-emerald-400' :
                                    'bg-slate-800 text-slate-500'
                            }`}>
                            {step.icon}
                        </div>
                        <span className={`font-medium ${activeStep === step.id ? 'text-white' :
                                activeStep > step.id ? 'text-slate-400 font-normal' :
                                    'text-slate-500'
                            }`}>
                            {step.text}
                        </span>
                    </div>
                ))}
            </div>
        </div>
    );
}
