import { useState } from 'react';
import SparklesIcon from './icons/SparklesIcon';
import BookIcon from './icons/BookIcon';
import CloseIcon from './icons/CloseIcon';
import ArrowRightIcon from './icons/ArrowRightIcon';

const API_BASE = 'http://127.0.0.1:8000';

export default function Summarize() {
    const [content, setContent] = useState('');
    const [summary, setSummary] = useState('');
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSummarize = async (e) => {
        e.preventDefault();
        if (!content.trim()) return;

        setLoading(true);
        setError(null);
        setSummary('');

        try {
            const response = await fetch(`${API_BASE}/summarize`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ content: content.trim() }),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail?.message || errorData.detail || 'Summarization failed');
            }

            const data = await response.json();
            setSummary(data.summary || 'No summary generated');
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="text-center mb-8">
                <div className="flex items-center justify-center space-x-3 mb-3">
                    <SparklesIcon className="w-8 h-8 text-sageGreen" />
                    <h1 className="text-4xl font-bold text-charcoal">AI Summarizer</h1>
                </div>
                <p className="text-mutedBrown/70">Powered by Google Gemini AI</p>
            </div>

            {/* Summarize Form */}
            <form onSubmit={handleSummarize} className="bg-white/90 border border-white/60 rounded-3xl p-8 shadow-sm">
                <div className="space-y-4">
                    <div>
                        <label htmlFor="content" className="block text-sm font-semibold text-charcoal mb-2">
                            Paste Article Text
                        </label>
                        <textarea
                            id="content"
                            value={content}
                            onChange={(e) => setContent(e.target.value)}
                            placeholder="Paste the article content here..."
                            rows={10}
                            className="w-full px-4 py-3 bg-white border-2 border-white/60 rounded-xl focus:outline-none focus:border-sageGreen/50 focus:shadow-lg transition-all placeholder-mutedBrown/40 text-charcoal resize-y"
                        />
                    </div>
                    <button
                        type="submit"
                        disabled={loading || !content.trim()}
                        className="w-full px-6 py-4 bg-sageGreen/40 border border-sageGreen/60 text-charcoal rounded-xl hover:bg-sageGreen/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-semibold flex items-center justify-center space-x-2 shadow-sm"
                    >
                        <SparklesIcon className="w-5 h-5" />
                        <span>{loading ? 'Generating Summary...' : 'Summarize with AI'}</span>
                    </button>
                </div>
            </form>

            {/* Error Message */}
            {error && (
                <div className="p-6 bg-mutedRose/10 border-2 border-mutedRose/30 rounded-2xl shadow-sm">
                    <p className="text-mutedRose font-medium flex items-center">
                        <CloseIcon className="w-5 h-5 mr-2" />
                        <strong>Error:</strong> <span className="ml-2">{error}</span>
                    </p>
                </div>
            )}

            {/* Loading State */}
            {loading && (
                <div className="bg-sageGreen/10 border-2 border-sageGreen/30 rounded-3xl p-12 shadow-sm">
                    <div className="flex flex-col items-center justify-center space-y-4">
                        <div className="relative">
                            <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-sageGreen border-t-transparent"></div>
                            <div className="absolute inset-0 flex items-center justify-center">
                                <SparklesIcon className="w-6 h-6 text-sageGreen" />
                            </div>
                        </div>
                        <p className="text-charcoal text-center font-medium text-lg">
                            AI is analyzing the article...
                            <br />
                            <span className="text-sm text-mutedBrown/60">Powered by Google Gemini • This may take a few seconds</span>
                        </p>
                    </div>
                </div>
            )}

            {/* Summary Display */}
            {summary && !loading && (
                <div className="bg-white/90 border-2 border-sageGreen/30 rounded-3xl overflow-hidden shadow-lg">
                    <div className="backdrop-blur-xl bg-charcoal/90 border-b border-white/10 p-6">
                        <div className="flex items-center justify-between text-warmBeige">
                            <h3 className="text-2xl font-bold">AI Summary</h3>
                            <span className="text-sm backdrop-blur-sm bg-white/10 border border-white/20 px-4 py-2 rounded-full flex items-center space-x-2">
                                <SparklesIcon className="w-4 h-4" />
                                <span>Powered by Gemini</span>
                            </span>
                        </div>
                    </div>
                    <div className="p-8">
                        <div className="prose prose-lg max-w-none">
                            <p className="text-charcoal leading-relaxed whitespace-pre-wrap text-lg">
                                {summary}
                            </p>
                        </div>
                        <div className="mt-8 pt-6 border-t-2 border-mutedBrown/10">
                            <a
                                href={url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center text-sageGreen hover:text-sageGreen/80 font-semibold text-lg group"
                            >
                                Read full article
                                <ArrowRightIcon className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
                            </a>
                        </div>
                    </div>
                </div>
            )}

            {/* Instructions */}
            {!summary && !loading && !error && (
                <div className="bg-white/90 border-2 border-white/60 rounded-3xl p-8 shadow-sm">
                    <h4 className="text-xl font-bold text-charcoal mb-6 flex items-center">
                        <BookIcon className="w-6 h-6 text-mutedRose mr-3" />
                        How it works
                    </h4>
                    <div className="space-y-4">
                        <div className="flex items-start">
                            <span className="flex-shrink-0 w-8 h-8 bg-sageGreen/30 text-charcoal border border-sageGreen/40 rounded-full flex items-center justify-center font-bold mr-4">1</span>
                            <div>
                                <p className="text-charcoal font-medium">Paste the URL of any news article</p>
                                <p className="text-sm text-mutedBrown/60">Works with most major news sites and blogs</p>
                            </div>
                        </div>
                        <div className="flex items-start">
                            <span className="flex-shrink-0 w-8 h-8 bg-sageGreen/30 text-charcoal border border-sageGreen/40 rounded-full flex items-center justify-center font-bold mr-4">2</span>
                            <div>
                                <p className="text-charcoal font-medium">Click "Summarize with AI"</p>
                                <p className="text-sm text-mutedBrown/60">Our AI fetches and analyzes the content</p>
                            </div>
                        </div>
                        <div className="flex items-start">
                            <span className="flex-shrink-0 w-8 h-8 bg-sageGreen/30 text-charcoal border border-sageGreen/40 rounded-full flex items-center justify-center font-bold mr-4">3</span>
                            <div>
                                <p className="text-charcoal font-medium">Get an instant concise summary</p>
                                <p className="text-sm text-mutedBrown/60">Powered by Google's Gemini AI model</p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
