import { useState, useEffect, useMemo, useCallback } from 'react';
import SearchIcon from './icons/SearchIcon';
import ArrowUpIcon from './icons/ArrowUpIcon';
import ArrowDownIcon from './icons/ArrowDownIcon';
import ArrowRightIcon from './icons/ArrowRightIcon';
import SparklesIcon from './icons/SparklesIcon';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const ARTICLES_PER_PAGE = 50;
const MAX_PAGES = 20;

export default function Search({ initialQuery = '' }) {
    const [query, setQuery] = useState(initialQuery);
    const [articles, setArticles] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);
    const [meta, setMeta] = useState(null);
    const [currentPage, setCurrentPage] = useState(1);
    const [totalPages, setTotalPages] = useState(1);
    const [summarizing, setSummarizing] = useState({});
    const [summaries, setSummaries] = useState({});
    const [relatedArticles, setRelatedArticles] = useState({});
    const [showingRelated, setShowingRelated] = useState({});

    useEffect(() => {
        if (initialQuery) {
            performSearch(initialQuery, 1);
        }
    }, [initialQuery]);

    const performSearch = useCallback(async (searchQuery, page = 1) => {
        if (!searchQuery.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const response = await fetch(`${API_BASE}/search?q=${encodeURIComponent(searchQuery)}&page=${page}&pageSize=${ARTICLES_PER_PAGE}`);
            if (!response.ok) {
                throw new Error('Search failed');
            }
            const data = await response.json();
            setArticles(data.articles || []);
            setMeta(data.meta);
            setCurrentPage(page);
            const calculatedPages = Math.ceil((data.meta?.totalResults || 0) / ARTICLES_PER_PAGE);
            setTotalPages(Math.min(calculatedPages, MAX_PAGES));
        } catch (err) {
            setError(err.message);
            setArticles([]);
        } finally {
            setLoading(false);
        }
    }, []);

    const handleSearch = useCallback((e) => {
        e.preventDefault();
        performSearch(query, 1);
    }, [query, performSearch]);

    const handlePageChange = useCallback((newPage) => {
        if (newPage >= 1 && newPage <= totalPages) {
            performSearch(query, newPage);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    }, [query, totalPages, performSearch]);

    const handleSummarize = useCallback(async (article, articleIdx) => {
        setSummarizing(prev => ({ ...prev, [articleIdx]: true }));

        try {
            const response = await fetch(`${API_BASE}/summarize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: article.title,
                    description: article.description,
                    content: article.content
                })
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                const errorMsg = errorData.detail?.message || errorData.detail || 'Summarization failed'
                throw new Error(errorMsg)
            }

            const data = await response.json();
            setSummaries(prev => ({ ...prev, [articleIdx]: data.summary }));
        } catch (err) {
            setSummaries(prev => ({ ...prev, [articleIdx]: `Error: ${err.message}` }));
        } finally {
            setSummarizing(prev => ({ ...prev, [articleIdx]: false }));
        }
    }, []);

    const handleShowRelated = useCallback(async (articleIdx) => {
        // Toggle visibility
        if (showingRelated[articleIdx]) {
            setShowingRelated(prev => ({ ...prev, [articleIdx]: false }));
            return;
        }

        // If already fetched, just show
        if (relatedArticles[articleIdx]) {
            setShowingRelated(prev => ({ ...prev, [articleIdx]: true }));
            return;
        }

        // Fetch related articles
        try {
            const response = await fetch(`${API_BASE}/related/${articleIdx}?top_k=3`);
            if (!response.ok) throw new Error('Failed to fetch related articles');

            const data = await response.json();
            setRelatedArticles(prev => ({ ...prev, [articleIdx]: data.related || [] }));
            setShowingRelated(prev => ({ ...prev, [articleIdx]: true }));
        } catch (err) {
            console.error('Related articles error:', err);
        }
    }, [relatedArticles, showingRelated]);

    const getSentimentColor = useCallback((label) => {
        switch (label?.toLowerCase()) {
            case 'positive':
                return 'bg-green-500 text-white border-green-600';
            case 'negative':
                return 'bg-red-500 text-white border-red-600';
            case 'neutral':
                return 'bg-gray-600 text-white border-gray-700';
            default:
                return 'bg-mutedBrown/20 text-charcoal border-mutedBrown/30';
        }
    }, []);

    const getSentimentIcon = useCallback((label) => {
        switch (label?.toLowerCase()) {
            case 'positive': return <ArrowUpIcon className="w-3 h-3" />;
            case 'negative': return <ArrowDownIcon className="w-3 h-3" />;
            case 'neutral': return <ArrowRightIcon className="w-3 h-3" />;
            default: return null;
        }
    }, []);

    const pageNumbers = useMemo(() => {
        return Array.from({ length: totalPages }, (_, i) => i + 1)
            .filter(page => page >= currentPage - 2 && page <= currentPage + 2);
    }, [totalPages, currentPage]);

    return (
        <div className="space-y-8">
            {/* Search Header */}
            <div className="text-center mb-8">
                <h1 className="text-4xl font-bold text-charcoal mb-3">Search Intelligence</h1>
                <p className="text-mutedBrown/70">Search news with ML-powered sentiment analysis</p>
            </div>

            {/* Search Form */}
            <form onSubmit={handleSearch} className="max-w-3xl mx-auto">
                <div className="relative">
                    <SearchIcon className="absolute left-6 top-1/2 -translate-y-1/2 w-5 h-5 text-mutedBrown/40" />
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Search for technology, business, politics..."
                        className="w-full pl-14 pr-36 py-5 text-lg bg-white/95 border-2 border-white/60 rounded-full focus:outline-none focus:bg-white focus:border-sageGreen/50 focus:shadow-lg transition-all placeholder-mutedBrown/40 text-charcoal"
                    />
                    <button
                        type="submit"
                        disabled={loading || !query.trim()}
                        className="absolute right-2 top-1/2 -translate-y-1/2 px-8 py-3 bg-sageGreen/40 border border-sageGreen/60 text-charcoal rounded-full hover:bg-sageGreen/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all font-medium shadow-sm"
                    >
                        {loading ? 'Searching...' : 'Search'}
                    </button>
                </div>
            </form>

            {/* Error Message */}
            {error && (
                <div className="max-w-3xl mx-auto p-4 bg-mutedRose/10 border-2 border-mutedRose/30 rounded-2xl text-mutedRose font-medium shadow-sm">
                    Error: {error}
                </div>
            )}

            {/* Results Meta */}
            {meta && (
                <div className="max-w-3xl mx-auto text-sm text-charcoal/80 font-medium">
                    Found <span className="text-sageGreen font-bold">{meta.totalResults.toLocaleString()}</span> results for "{meta.q}"
                    {totalPages > 1 && <span className="ml-2">• Page {currentPage} of {totalPages}</span>}
                </div>
            )}

            {/* Results List */}
            {articles.length === 0 && !loading && !error && (
                <div className="text-center py-20">
                    <div className="flex items-center justify-center w-20 h-20 bg-white/90 border border-white/60 rounded-full mx-auto mb-6 shadow-sm">
                        <SearchIcon className="w-10 h-10 text-mutedBrown/40" />
                    </div>
                    <p className="text-charcoal/70 text-lg font-medium">
                        {query ? 'No results found. Try a different search term.' : 'Enter a search term to find news articles.'}
                    </p>
                </div>
            )}

            <div className="grid md:grid-cols-2 gap-6">
                {articles.map((article, idx) => (
                    <article
                        key={article.url || idx}
                        className="bg-white/90 border border-white/60 rounded-2xl overflow-hidden hover:bg-white hover:border-sageGreen/40 transition-colors will-change-transform group"
                    >
                        {article.urlToImage && (
                            <div className="relative h-48 overflow-hidden bg-taupe">
                                <img
                                    src={article.urlToImage}
                                    alt={article.title}
                                    loading="lazy"
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 will-change-transform"
                                    onError={(e) => {
                                        e.target.parentElement.style.display = 'none';
                                    }}
                                />
                                {/* ML Sentiment Badge */}
                                {article.sentiment && (
                                    <div className="absolute top-3 right-3">
                                        <div className={`${getSentimentColor(article.sentiment.label)} px-3 py-1 rounded-full text-xs font-bold border flex items-center shadow-md`}>
                                            {getSentimentIcon(article.sentiment.label)}
                                            <span className="ml-1">{article.sentiment.label}</span>
                                        </div>
                                    </div>
                                )}
                                {/* Confidence Score */}
                                {article.sentiment?.score && (
                                    <div className="absolute bottom-3 left-3">
                                        <div className="bg-charcoal/80 backdrop-blur-sm px-3 py-1 rounded-full text-xs font-bold text-white shadow-md">
                                            {(article.sentiment.score * 100).toFixed(0)}% Confidence
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                        <div className="p-5">
                            <div className="flex items-center justify-between mb-3">
                                <span className="text-xs font-bold text-mutedRose uppercase tracking-wide">{article.source?.name || 'Unknown Source'}</span>
                                <span className="text-xs text-charcoal/60 font-medium">{new Date(article.publishedAt).toLocaleDateString()}</span>
                            </div>

                            <h3 className="font-bold text-charcoal mb-2 line-clamp-2 group-hover:text-sageGreen transition-colors text-base">
                                <a
                                    href={article.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                >
                                    {article.title}
                                </a>
                            </h3>

                            {article.description && (
                                <p className="text-sm text-charcoal/80 line-clamp-3 mb-4 leading-relaxed">
                                    {article.description}
                                </p>
                            )}

                            {/* ML Features */}
                            <div className="pt-3 border-t border-mutedBrown/10 space-y-2">
                                <div className="flex items-center justify-between">
                                    <a
                                        href={article.url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-sm font-bold text-charcoal hover:text-sageGreen flex items-center gap-1 transition-colors"
                                    >
                                        <span>Read more</span>
                                        <ArrowRightIcon className="w-3.5 h-3.5" />
                                    </a>
                                </div>

                                {/* AI Summarize Button */}
                                <button
                                    onClick={() => handleSummarize(article, idx)}
                                    disabled={summarizing[idx]}
                                    className="custom-btn w-full flex items-center justify-center gap-2"
                                >
                                    <SparklesIcon className="w-2.5 h-2.5" />
                                    <span className="text-[10px]">{summarizing[idx] ? 'Summarizing...' : 'AI Summarize'}</span>
                                </button>

                                {/* Related Stories Button */}
                                <button
                                    onClick={() => handleShowRelated(idx)}
                                    className="custom-btn custom-btn-secondary w-full flex items-center justify-center gap-2"
                                >
                                    <svg className="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                    </svg>
                                    <span className="text-[10px]">{showingRelated[idx] ? 'Hide Related' : 'Related Stories'}</span>
                                </button>

                                {/* Summary Display */}
                                {summaries[idx] && (
                                    <div className="mt-3 p-3 bg-sageGreen/10 border border-sageGreen/30 rounded-lg">
                                        <div className="flex items-start space-x-2 mb-2">
                                            <SparklesIcon className="w-4 h-4 text-sageGreen mt-0.5 flex-shrink-0" />
                                            <span className="text-xs font-bold text-charcoal">AI Summary</span>
                                        </div>
                                        <p className="text-sm text-charcoal leading-relaxed">{summaries[idx]}</p>
                                    </div>
                                )}

                                {/* Related Articles Display */}
                                {showingRelated[idx] && relatedArticles[idx] && (
                                    <div className="mt-3 p-3 bg-mutedRose/10 border border-mutedRose/30 rounded-lg">
                                        <div className="flex items-start space-x-2 mb-3">
                                            <svg className="w-4 h-4 text-mutedRose mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                                            </svg>
                                            <span className="text-xs font-semibold text-charcoal">Related Stories (ML-Clustered)</span>
                                        </div>
                                        <div className="space-y-2">
                                            {relatedArticles[idx].length === 0 ? (
                                                <p className="text-xs text-mutedBrown/60">No related articles found</p>
                                            ) : (
                                                relatedArticles[idx].map((related, i) => (
                                                    <a
                                                        key={i}
                                                        href={related.url}
                                                        target="_blank"
                                                        rel="noopener noreferrer"
                                                        className="block p-2 bg-white/50 rounded-lg hover:bg-white/80 transition-colors"
                                                    >
                                                        <div className="flex items-start justify-between gap-2">
                                                            <p className="text-xs font-medium text-charcoal line-clamp-2 flex-1">{related.title}</p>
                                                            <span className="text-xs text-sageGreen font-semibold whitespace-nowrap">
                                                                {Math.round(related.similarity * 100)}%
                                                            </span>
                                                        </div>
                                                        {related.source && (
                                                            <p className="text-xs text-mutedBrown/60 mt-1">{related.source}</p>
                                                        )}
                                                    </a>
                                                ))
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </article>
                ))}
            </div>

            {/* Pagination Controls */}
            {totalPages > 1 && articles.length > 0 && (
                <div className="flex items-center justify-center space-x-2 mt-8">
                    <button
                        onClick={() => handlePageChange(currentPage - 1)}
                        disabled={currentPage === 1}
                        className="px-4 py-2 bg-white/95 border border-white/60 text-charcoal rounded-lg hover:bg-white hover:border-sageGreen/40 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium will-change-transform"
                    >
                        Previous
                    </button>

                    <div className="flex items-center space-x-1">
                        {/* First page */}
                        {currentPage > 3 && (
                            <>
                                <button
                                    onClick={() => handlePageChange(1)}
                                    className="px-3 py-2 bg-white/95 border border-white/60 text-charcoal rounded-lg hover:bg-white hover:border-sageGreen/40 transition-colors will-change-transform"
                                >
                                    1
                                </button>
                                {currentPage > 4 && <span className="text-mutedBrown/40 px-2">...</span>}
                            </>
                        )}

                        {/* Page numbers around current */}
                        {pageNumbers.map(page => (
                            <button
                                key={page}
                                onClick={() => handlePageChange(page)}
                                className={`px-3 py-2 border rounded-lg transition-colors font-medium will-change-transform ${page === currentPage
                                    ? 'bg-sageGreen/40 border-sageGreen/60 text-charcoal shadow-md'
                                    : 'bg-white/95 border-white/60 text-charcoal hover:bg-white hover:border-sageGreen/40'
                                    }`}
                            >
                                {page}
                            </button>
                        ))}

                        {/* Last page */}
                        {currentPage < totalPages - 2 && (
                            <>
                                {currentPage < totalPages - 3 && <span className="text-mutedBrown/40 px-2">...</span>}
                                <button
                                    onClick={() => handlePageChange(totalPages)}
                                    className="px-3 py-2 bg-white/95 border border-white/60 text-charcoal rounded-lg hover:bg-white hover:border-sageGreen/40 transition-colors will-change-transform"
                                >
                                    {totalPages}
                                </button>
                            </>
                        )}
                    </div>

                    <button
                        onClick={() => handlePageChange(currentPage + 1)}
                        disabled={currentPage === totalPages}
                        className="px-4 py-2 bg-white/95 border border-white/60 text-charcoal rounded-lg hover:bg-white hover:border-sageGreen/40 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium will-change-transform"
                    >
                        Next
                    </button>
                </div>
            )}

            {/* Loading State */}
            {loading && (
                <div className="max-w-3xl mx-auto text-center py-20">
                    <div className="inline-block animate-spin rounded-full h-16 w-16 border-4 border-sageGreen border-t-transparent mb-4"></div>
                    <p className="text-mutedBrown/70 font-medium">Searching with ML analysis...</p>
                </div>
            )}
        </div>
    );
}
