import React, { useRef } from 'react';
import { UploadCloud, X } from 'lucide-react';

export default function CSVUpload({ onUpload, onCancel }) {
    const fileInputRef = useRef(null);

    const handleFileChange = (e) => {
        const file = e.target.files?.[0];
        if (file) {
            onUpload(file);
        }
    };

    return (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-8 max-w-lg w-full relative shadow-2xl animate-in zoom-in-95 duration-200">
                <button
                    onClick={onCancel}
                    className="absolute top-6 right-6 text-slate-400 hover:text-white transition-colors"
                >
                    <X className="w-6 h-6" />
                </button>

                <div className="text-center mb-8">
                    <div className="w-20 h-20 bg-blue-500/10 rounded-full flex items-center justify-center mx-auto mb-4 text-blue-500">
                        <UploadCloud className="w-10 h-10" />
                    </div>
                    <h2 className="text-2xl font-bold text-white mb-2">Upload Custom Dataset</h2>
                    <p className="text-slate-400 text-sm">
                        We will infer the schema and prepare the data for natural language querying immediately.
                    </p>
                </div>

                <div
                    onClick={() => fileInputRef.current?.click()}
                    className="border-2 border-dashed border-slate-700 hover:border-blue-500 bg-slate-800/50 rounded-2xl p-10 cursor-pointer flex flex-col items-center justify-center transition-colors group"
                >
                    <input
                        type="file"
                        accept=".csv"
                        className="hidden"
                        ref={fileInputRef}
                        onChange={handleFileChange}
                    />
                    <span className="text-slate-300 font-medium group-hover:text-blue-400 transition-colors">
                        Click to browse files or drag and drop
                    </span>
                    <span className="text-slate-500 text-xs mt-2">Maximum file size: 10MB (CSV only)</span>
                </div>
            </div>
        </div>
    );
}
