import { useState, useEffect, useMemo, useCallback } from 'react'
import Search from './components/Search'
import TrendingIcon from './components/icons/TrendingIcon'
import SparklesIcon from './components/icons/SparklesIcon'
import ArrowUpIcon from './components/icons/ArrowUpIcon'
import ArrowDownIcon from './components/icons/ArrowDownIcon'
import ArrowRightIcon from './components/icons/ArrowRightIcon'
import SearchIcon from './components/icons/SearchIcon'

const API_BASE = 'http://localhost:8000'

export default function App() {
    const [activeView, setActiveView] = useState('home')
    const [trends, setTrends] = useState([])
    const [entities, setEntities] = useState({})
    const [featuredArticles, setFeaturedArticles] = useState([])
    const [loading, setLoading] = useState(true)
    const [searchQuery, setSearchQuery] = useState('')
    const [summarizing, setSummarizing] = useState({})
    const [summaries, setSummaries] = useState({})
    const [relatedArticles, setRelatedArticles] = useState({})
    const [showingRelated, setShowingRelated] = useState({})

    useEffect(() => {
        // Fetch trends
        fetch(`${API_BASE}/trends`)
            .then(res => res.json())
            .then(data => {
                setTrends(data.trending || [])
            })
            .catch(err => console.error('Trends error:', err))

        // Fetch trending entities
        fetch(`${API_BASE}/entities`)
            .then(res => res.json())
            .then(data => {
                setEntities(data || {})
            })
            .catch(err => console.error('Entities error:', err))

        // Fetch featured articles (latest tech news with sentiment)
        fetch(`${API_BASE}/search?q=technology&pageSize=6`)
            .then(res => res.json())
            .then(data => {
                setFeaturedArticles(data.articles || [])
                setLoading(false)
            })
            .catch(err => {
                console.error('Featured articles error:', err)
                setLoading(false)
            })
    }, [])

    const handleSearchSubmit = useCallback((e) => {
        e.preventDefault()
        if (searchQuery.trim()) {
            setActiveView('search')
        }
    }, [searchQuery])

    const getSentimentColor = useCallback((label) => {
        switch (label?.toLowerCase()) {
            case 'positive': return 'bg-sageGreen/20 text-sageGreen border-sageGreen/30'
            case 'negative': return 'bg-mutedRose/20 text-mutedRose border-mutedRose/30'
            case 'neutral': return 'bg-mutedBrown/10 text-mutedBrown border-mutedBrown/20'
            default: return 'bg-mutedBrown/5 text-mutedBrown/50 border-mutedBrown/10'
        }
    }, [])

    const getSentimentIcon = useCallback((label) => {
        switch (label?.toLowerCase()) {
            case 'positive': return <ArrowUpIcon className="w-3 h-3" />
            case 'negative': return <ArrowDownIcon className="w-3 h-3" />
            case 'neutral': return <ArrowRightIcon className="w-3 h-3" />
            default: return null
        }
    }, [])

    const handleSummarize = useCallback(async (article) => {
        const articleId = article.url
        setSummarizing(prev => ({ ...prev, [articleId]: true }))

        try {
            const response = await fetch(`${API_BASE}/summarize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title: article.title,
                    description: article.description,
                    content: article.content
                })
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                const errorMsg = errorData.detail?.message || errorData.detail || 'Summarization failed'
                throw new Error(errorMsg)
            }

            const data = await response.json()
            setSummaries(prev => ({ ...prev, [articleId]: data.summary }))
        } catch (err) {
            console.error('Summarization error:', err)
            setSummaries(prev => ({ ...prev, [articleId]: `Error: ${err.message}` }))
        } finally {
            setSummarizing(prev => ({ ...prev, [articleId]: false }))
        }
    }, [])

    const handleShowRelated = useCallback(async (articleUrl) => {
        console.log('[Related] Toggling for URL:', articleUrl)

        // Toggle visibility
        if (showingRelated[articleUrl]) {
            console.log('[Related] Hiding related articles')
            setShowingRelated(prev => ({ ...prev, [articleUrl]: false }))
            return
        }

        // If already fetched, just show
        if (relatedArticles[articleUrl]) {
            console.log('[Related] Showing cached related articles')
            setShowingRelated(prev => ({ ...prev, [articleUrl]: true }))
            return
        }

        // Fetch related articles
        console.log('[Related] Fetching related articles...')
        try {
            const url = `${API_BASE}/related-by-url?url=${encodeURIComponent(articleUrl)}&top_k=3`
            console.log('[Related] Fetching from:', url)

            const response = await fetch(url)
            console.log('[Related] Response status:', response.status)

            if (!response.ok) {
                const errorText = await response.text()
                console.error('[Related] Error response:', errorText)
                throw new Error(`Failed to fetch related articles: ${response.status}`)
            }

            const data = await response.json()
            console.log('[Related] Received data:', data)

            setRelatedArticles(prev => ({ ...prev, [articleUrl]: data.related || [] }))
            setShowingRelated(prev => ({ ...prev, [articleUrl]: true }))
            console.log('[Related] Successfully loaded', data.related?.length || 0, 'related articles')
        } catch (err) {
            console.error('[Related] Error:', err)
            alert(`Failed to load related articles: ${err.message}`)
        }
    }, [relatedArticles, showingRelated])

    return (
        <div className="min-h-screen bg-warmBeige">
            {/* Glass Morphism Header */}
            <header className="sticky top-0 z-50 backdrop-blur-xl bg-charcoal/80 border-b border-white/10">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex items-center justify-between h-20">
                        <div className="flex items-center space-x-8">
                            <button onClick={() => setActiveView('home')} className="flex items-center group">
                                <span className="text-2xl font-bold tracking-tight text-warmBeige">NewsPulse</span>
                                <span className="ml-2 text-xs bg-sageGreen/40 text-warmBeige px-2 py-1 rounded border border-sageGreen/50 shadow-sm">AI</span>
                            </button>
                            <nav className="hidden md:flex space-x-6 text-sm">
                                <button onClick={() => setActiveView('home')} className={`transition-colors ${activeView === 'home' ? 'text-warmBeige' : 'text-warmBeige/50 hover:text-warmBeige/80'}`}>Home</button>
                                <button onClick={() => document.getElementById('footer')?.scrollIntoView({ behavior: 'smooth' })} className="text-warmBeige/50 hover:text-warmBeige/80 transition-colors">About</button>
                            </nav>
                        </div>

                        {/* Glass Search Bar */}
                        <form onSubmit={handleSearchSubmit} className="hidden lg:block">
                            <div className="relative">
                                <input
                                    type="text"
                                    value={searchQuery}
                                    onChange={(e) => setSearchQuery(e.target.value)}
                                    placeholder="Search news..."
                                    className="w-80 px-4 py-2 pl-10 bg-white/10 backdrop-blur-xl border border-white/20 rounded-full text-warmBeige placeholder-warmBeige/40 focus:outline-none focus:bg-white/15 focus:border-white/30 transition-all"
                                />
                                <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-warmBeige/40" />
                                <button
                                    type="submit"
                                    className="absolute right-1 top-1/2 -translate-y-1/2 px-4 py-1 bg-sageGreen/40 text-warmBeige rounded-full hover:bg-sageGreen/50 transition-colors text-sm border border-sageGreen/50 shadow-sm"
                                >
                                    Search
                                </button>
                            </div>
                        </form>

                        <div className="flex items-center space-x-4 text-xs text-warmBeige/50">
                            <span className="hidden sm:inline">Real-time ML</span>
                            <span className="w-2 h-2 bg-sageGreen rounded-full animate-pulse"></span>
                        </div>
                    </div>
                </div>
            </header>

            {/* Home View */}
            {activeView === 'home' && (
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                    <div className="flex gap-6">
                        {/* Trending Topics - Left Floating Sidebar - Smaller & Transparent */}
                        <aside className="w-64 flex-shrink-0">
                            <div className="sticky top-24 space-y-3">
                                <div className="flex items-center space-x-2 mb-3">
                                    <TrendingIcon className="w-5 h-5 text-mutedRose" />
                                    <h2 className="text-xl font-bold text-charcoal">Trending</h2>
                                </div>
                                {trends.length === 0 ? (
                                    <div className="bg-white/70 border border-white/60 rounded-xl p-4 text-center shadow-sm">
                                        <div className="animate-pulse mb-2">
                                            <div className="w-10 h-10 bg-sageGreen/20 rounded-full mx-auto mb-2"></div>
                                        </div>
                                        <p className="text-mutedBrown text-xs font-medium mb-1">Collecting data...</p>
                                        <p className="text-xs text-mutedBrown/60">ML needs 24h</p>
                                    </div>
                                ) : (
                                    <div className="space-y-2">
                                        {trends.slice(0, 8).map((t, i) => (
                                            <div
                                                key={t.keyword || i}
                                                onClick={() => {
                                                    setSearchQuery(t.keyword);
                                                    setActiveView('search');
                                                }}
                                                className="bg-white/75 border border-white/60 rounded-lg p-3 hover:bg-white/85 hover:border-sageGreen/50 hover:shadow-md transition-all cursor-pointer group will-change-transform"
                                            >
                                                <div className="flex items-start justify-between mb-1">
                                                    <span className="text-lg font-bold text-mutedBrown/30 group-hover:text-sageGreen/60 transition-colors">#{i + 1}</span>
                                                    {t.isNew && <span className="bg-mutedRose/20 text-mutedRose text-xs px-1.5 py-0.5 rounded-full font-medium border border-mutedRose/30">NEW</span>}
                                                </div>
                                                <h3 className="font-semibold text-charcoal text-xs mb-1 line-clamp-2">{t.keyword}</h3>
                                                <div className="flex items-center justify-between text-xs">
                                                    <span className="text-mutedBrown/60">{t.currentCount}</span>
                                                    {t.growth !== null && (
                                                        <span className={`font-medium flex items-center space-x-1 ${t.growth > 0 ? 'text-sageGreen' : 'text-mutedRose'}`}>
                                                            {t.growth > 0 ? <ArrowUpIcon className="w-2.5 h-2.5" /> : <ArrowDownIcon className="w-2.5 h-2.5" />}
                                                            <span>{Math.abs(t.growth * 100).toFixed(0)}%</span>
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                <div className="text-xs text-mutedBrown/60 text-center mt-3 p-2 bg-warmBeige/60 rounded-lg border border-sageGreen/30 shadow-sm">
                                    <span className="font-medium">ML</span> • NLP
                                </div>
                            </div>
                        </aside>

                        {/* Latest News with ML Analysis - Right Main Content */}
                        <section className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-3xl font-bold text-charcoal">Latest News</h2>
                                <span className="text-sm text-mutedBrown/60 flex items-center">
                                    <span className="w-2 h-2 bg-sageGreen rounded-full mr-2 animate-pulse"></span>
                                    Sentiment Analysis Active
                                </span>
                            </div>
                            {loading ? (
                                <div className="grid md:grid-cols-2 gap-6">
                                    {[1, 2, 3, 4, 5, 6].map(i => (
                                        <div key={i} className="bg-white/90 border border-white/60 rounded-2xl p-6 animate-pulse">
                                            <div className="h-48 bg-mutedBrown/10 rounded-xl mb-4"></div>
                                            <div className="h-4 bg-mutedBrown/10 rounded mb-2"></div>
                                            <div className="h-4 bg-mutedBrown/10 rounded w-3/4"></div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="grid md:grid-cols-2 gap-6">
                                    {featuredArticles.map((article, i) => (
                                        <article key={article.url || i} className="bg-white/80 border border-white/70 rounded-2xl overflow-hidden hover:bg-white/90 hover:border-sageGreen/50 hover:shadow-lg transition-all will-change-transform group">
                                            {article.urlToImage && (
                                                <div className="relative h-48 overflow-hidden bg-taupe">
                                                    <img
                                                        src={article.urlToImage}
                                                        alt={article.title}
                                                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300 will-change-transform"
                                                        loading="lazy"
                                                        onError={(e) => e.target.parentElement.style.display = 'none'}
                                                    />
                                                    {/* ML Sentiment Badge */}
                                                    <div className="absolute top-3 right-3">
                                                        <div className={`${getSentimentColor(article.sentiment?.label)} px-3 py-1 rounded-full text-xs font-bold flex items-center border shadow-md`}>
                                                            {getSentimentIcon(article.sentiment?.label)}
                                                            <span className="ml-1">{article.sentiment?.label || 'analyzing'}</span>
                                                        </div>
                                                    </div>
                                                </div>
                                            )}
                                            <div className="p-5">
                                                <div className="flex items-center justify-between mb-3">
                                                    <span className="text-xs font-semibold text-mutedRose uppercase tracking-wide">{article.source?.name || 'News'}</span>
                                                    <span className="text-xs text-mutedBrown/60">{new Date(article.publishedAt).toLocaleDateString()}</span>
                                                </div>
                                                <h3 className="font-bold text-charcoal mb-2 line-clamp-2 group-hover:text-sageGreen transition-colors">
                                                    <a href={article.url} target="_blank" rel="noopener noreferrer">{article.title}</a>
                                                </h3>
                                                <p className="text-sm text-mutedBrown/70 line-clamp-3 mb-4">{article.description}</p>

                                                {/* AI Summary */}
                                                {summaries[article.url] && (
                                                    <div className="mb-4 p-3 bg-sageGreen/5 border border-sageGreen/20 rounded-xl">
                                                        <p className="text-xs font-semibold text-sageGreen mb-1 flex items-center">
                                                            <SparklesIcon className="w-3 h-3 mr-1" />
                                                            AI Summary
                                                        </p>
                                                        <p className="text-sm text-charcoal/80">{summaries[article.url]}</p>
                                                    </div>
                                                )}

                                                {/* Related Stories */}
                                                {showingRelated[article.url] && relatedArticles[article.url] && (
                                                    <div className="mb-4 p-3 bg-mutedRose/5 border border-mutedRose/20 rounded-xl">
                                                        <p className="text-xs font-semibold text-mutedRose mb-2 flex items-center">
                                                            <SparklesIcon className="w-3 h-3 mr-1" />
                                                            Related Stories
                                                        </p>
                                                        <div className="space-y-2">
                                                            {relatedArticles[article.url].map((related, idx) => (
                                                                <div key={idx} className="text-xs p-2 bg-white/50 rounded-lg hover:bg-white/80 transition-colors">
                                                                    <div className="flex items-center justify-between mb-1">
                                                                        <span className="font-semibold text-mutedRose">
                                                                            {(related.similarity * 100).toFixed(0)}% similar
                                                                        </span>
                                                                        <span className="text-mutedBrown/60">{related.source}</span>
                                                                    </div>
                                                                    <a
                                                                        href={related.url}
                                                                        target="_blank"
                                                                        rel="noopener noreferrer"
                                                                        className="text-charcoal hover:text-sageGreen line-clamp-2"
                                                                    >
                                                                        {related.title}
                                                                    </a>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                )}

                                                <div className="flex items-center justify-between pt-3 border-t border-mutedBrown/10">
                                                    <div className="flex items-center gap-3">
                                                        <a href={article.url} target="_blank" rel="noopener noreferrer" className="text-sm font-medium text-sageGreen hover:text-sageGreen/80 flex items-center">
                                                            Read more <ArrowRightIcon className="ml-1 w-3 h-3" />
                                                        </a>
                                                        <button
                                                            onClick={() => handleSummarize(article)}
                                                            disabled={summarizing[article.url]}
                                                            className="text-xs px-2 py-1 bg-sageGreen/20 hover:bg-sageGreen/30 text-sageGreen rounded-full flex items-center gap-1 transition-colors disabled:opacity-50"
                                                        >
                                                            <SparklesIcon className="w-3 h-3" />
                                                            {summarizing[article.url] ? 'Summarizing...' : 'AI Summarize'}
                                                        </button>
                                                        <button
                                                            onClick={() => handleShowRelated(article.url)}
                                                            className="text-xs px-2 py-1 bg-mutedRose/20 hover:bg-mutedRose/30 text-mutedRose rounded-full flex items-center gap-1 transition-colors"
                                                        >
                                                            <SparklesIcon className="w-3 h-3" />
                                                            {showingRelated[article.url] ? 'Hide Related' : 'Related Stories'}
                                                        </button>
                                                    </div>
                                                    {article.sentiment?.score && (
                                                        <span className="text-xs text-mutedBrown/50">Confidence: {(article.sentiment.score * 100).toFixed(0)}%</span>
                                                    )}
                                                </div>
                                            </div>
                                        </article>
                                    ))}
                                </div>
                            )}
                        </section>
                    </div>

                    {/* Quick Stats */}
                    <section className="mt-12 bg-white/80 border border-white/70 rounded-3xl p-8 shadow-lg">
                        <h3 className="text-2xl font-bold mb-6 text-charcoal flex items-center">
                            <span className="w-2 h-2 bg-sageGreen rounded-full mr-3 animate-pulse"></span>
                            Real-Time Analytics
                        </h3>
                        <div className="grid md:grid-cols-4 gap-6">
                            <div className="text-center p-6 bg-sageGreen/10 rounded-2xl border border-sageGreen/30">
                                <div className="text-4xl font-bold text-sageGreen mb-2">{featuredArticles.length}</div>
                                <p className="text-sm text-mutedBrown">Latest Articles</p>
                            </div>
                            <div className="text-center p-6 bg-mutedRose/10 rounded-2xl border border-mutedRose/30">
                                <div className="text-4xl font-bold text-mutedRose mb-2">{trends.length}</div>
                                <p className="text-sm text-mutedBrown">Trending Topics</p>
                            </div>
                            <div className="text-center p-6 bg-sageGreen/10 rounded-2xl border border-sageGreen/30">
                                <div className="text-4xl font-bold text-sageGreen mb-2">
                                    {featuredArticles.filter(a => a.sentiment?.label).length}
                                </div>
                                <p className="text-sm text-mutedBrown">ML Analyzed</p>
                            </div>
                            <div className="text-center p-6 bg-charcoal/5 rounded-2xl border border-charcoal/20">
                                <div className="text-4xl font-bold text-charcoal mb-2">
                                    {featuredArticles.filter(a => a.sentiment?.score).length > 0
                                        ? Math.round(
                                            (featuredArticles
                                                .filter(a => a.sentiment?.score)
                                                .reduce((sum, a) => sum + a.sentiment.score, 0) /
                                                featuredArticles.filter(a => a.sentiment?.score).length) * 100
                                        )
                                        : 0}%
                                </div>
                                <p className="text-sm text-mutedBrown">Avg Confidence</p>
                            </div>
                        </div>

                        {/* Sentiment Breakdown */}
                        <div className="mt-8 pt-6 border-t border-charcoal/10">
                            <h4 className="text-lg font-bold text-charcoal mb-4">Sentiment Breakdown</h4>
                            <div className="grid md:grid-cols-3 gap-4">
                                <div className="flex items-center justify-between p-4 bg-sageGreen/5 rounded-xl border border-sageGreen/20">
                                    <div className="flex items-center gap-2">
                                        <ArrowUpIcon className="w-5 h-5 text-sageGreen" />
                                        <span className="font-semibold text-charcoal">Positive</span>
                                    </div>
                                    <span className="text-2xl font-bold text-sageGreen">
                                        {featuredArticles.filter(a => a.sentiment?.label?.toLowerCase() === 'positive').length}
                                    </span>
                                </div>
                                <div className="flex items-center justify-between p-4 bg-mutedBrown/5 rounded-xl border border-mutedBrown/20">
                                    <div className="flex items-center gap-2">
                                        <ArrowRightIcon className="w-5 h-5 text-mutedBrown" />
                                        <span className="font-semibold text-charcoal">Neutral</span>
                                    </div>
                                    <span className="text-2xl font-bold text-mutedBrown">
                                        {featuredArticles.filter(a => a.sentiment?.label?.toLowerCase() === 'neutral').length}
                                    </span>
                                </div>
                                <div className="flex items-center justify-between p-4 bg-mutedRose/5 rounded-xl border border-mutedRose/20">
                                    <div className="flex items-center gap-2">
                                        <ArrowDownIcon className="w-5 h-5 text-mutedRose" />
                                        <span className="font-semibold text-charcoal">Negative</span>
                                    </div>
                                    <span className="text-2xl font-bold text-mutedRose">
                                        {featuredArticles.filter(a => a.sentiment?.label?.toLowerCase() === 'negative').length}
                                    </span>
                                </div>
                            </div>
                        </div>
                    </section>

                    {/* Trending Entities Section */}
                    <section className="mt-12 bg-white/80 border border-white/70 rounded-3xl p-8 shadow-lg">
                        <h3 className="text-2xl font-bold mb-6 text-charcoal flex items-center">
                            <span className="w-2 h-2 bg-mutedRose rounded-full mr-3 animate-pulse"></span>
                            Trending Entities (ML-Powered)
                        </h3>
                        <div className="grid md:grid-cols-3 gap-6">
                            {/* People */}
                            <div>
                                <h4 className="text-sm font-bold text-mutedBrown/60 uppercase tracking-wide mb-3 flex items-center">
                                    👤 People
                                </h4>
                                <div className="space-y-2">
                                    {(entities.PERSON || []).slice(0, 5).map(([name, count], i) => (
                                        <button
                                            key={i}
                                            onClick={() => {
                                                setSearchQuery(name);
                                                setActiveView('search');
                                            }}
                                            className="w-full text-left p-2 bg-sageGreen/5 hover:bg-sageGreen/15 rounded-lg transition-colors group"
                                        >
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm font-semibold text-charcoal group-hover:text-sageGreen">{name}</span>
                                                <span className="text-xs text-mutedBrown/60 bg-white/50 px-2 py-0.5 rounded-full">{count}</span>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Organizations */}
                            <div>
                                <h4 className="text-sm font-bold text-mutedBrown/60 uppercase tracking-wide mb-3 flex items-center">
                                    🏢 Organizations
                                </h4>
                                <div className="space-y-2">
                                    {(entities.ORG || []).slice(0, 5).map(([name, count], i) => (
                                        <button
                                            key={i}
                                            onClick={() => {
                                                setSearchQuery(name);
                                                setActiveView('search');
                                            }}
                                            className="w-full text-left p-2 bg-mutedRose/5 hover:bg-mutedRose/15 rounded-lg transition-colors group"
                                        >
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm font-semibold text-charcoal group-hover:text-mutedRose">{name}</span>
                                                <span className="text-xs text-mutedBrown/60 bg-white/50 px-2 py-0.5 rounded-full">{count}</span>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Locations */}
                            <div>
                                <h4 className="text-sm font-bold text-mutedBrown/60 uppercase tracking-wide mb-3 flex items-center">
                                    🌍 Locations
                                </h4>
                                <div className="space-y-2">
                                    {(entities.GPE || []).slice(0, 5).map(([name, count], i) => (
                                        <button
                                            key={i}
                                            onClick={() => {
                                                setSearchQuery(name);
                                                setActiveView('search');
                                            }}
                                            className="w-full text-left p-2 bg-sageGreen/5 hover:bg-sageGreen/15 rounded-lg transition-colors group"
                                        >
                                            <div className="flex items-center justify-between">
                                                <span className="text-sm font-semibold text-charcoal group-hover:text-sageGreen">{name}</span>
                                                <span className="text-xs text-mutedBrown/60 bg-white/50 px-2 py-0.5 rounded-full">{count}</span>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>
                        <p className="mt-4 text-xs text-mutedBrown/50 text-center">
                            Extracted using spaCy NER • Click to search
                        </p>
                    </section>
                </main>
            )}

            {/* Search View */}
            {activeView === 'search' && (
                <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
                    <Search initialQuery={searchQuery} />
                </main>
            )}

            {/* Footer */}
            <footer id="footer" className="mt-20 bg-charcoal/95 border-t border-white/20 text-warmBeige">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
                    <div className="grid md:grid-cols-3 gap-12 mb-12">
                        {/* Sentiment Analysis */}
                        <div>
                            <div className="flex items-center justify-center w-12 h-12 bg-sageGreen/30 rounded-2xl mb-4 border border-sageGreen/40 shadow-sm">
                                <ArrowUpIcon className="w-6 h-6 text-sageGreen" />
                            </div>
                            <h4 className="text-lg font-semibold mb-3">Sentiment Analysis</h4>
                            <p className="text-sm text-warmBeige/70">ML classifies news tone as positive, negative, or neutral</p>
                        </div>

                        {/* Trend Detection */}
                        <div>
                            <div className="flex items-center justify-center w-12 h-12 bg-mutedRose/30 rounded-2xl mb-4 border border-mutedRose/40 shadow-sm">
                                <TrendingIcon className="w-6 h-6 text-mutedRose" />
                            </div>
                            <h4 className="text-lg font-semibold mb-3">Trend Detection</h4>
                            <p className="text-sm text-warmBeige/70">NLP extracts keywords and ranks emerging vs. established trends</p>
                        </div>

                        {/* AI Summarization */}
                        <div>
                            <div className="flex items-center justify-center w-12 h-12 bg-sageGreen/30 rounded-2xl mb-4 border border-sageGreen/40 shadow-sm">
                                <SearchIcon className="w-6 h-6 text-sageGreen" />
                            </div>
                            <h4 className="text-lg font-semibold mb-3">AI Summarization</h4>
                            <p className="text-sm text-warmBeige/70">Google Gemini AI generates concise article summaries</p>
                        </div>
                    </div>

                    {/* Credit */}
                    <div className="border-t border-white/10 pt-8 text-center">
                        <p className="text-warmBeige/80">Made with ❤️ by <span className="font-semibold text-sageGreen">Sriram</span></p>
                    </div>
                </div>
            </footer>
        </div>
    )
}
