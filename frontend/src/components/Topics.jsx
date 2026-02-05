import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'
import SparklesIcon from './icons/SparklesIcon'

const Topics = ({ apiBase = 'http://localhost:8000' }) => {
    const [topics, setTopics] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)
    const [totalArticles, setTotalArticles] = useState(0)
    const [uncategorized, setUncategorized] = useState(0)

    useEffect(() => {
        const fetchTopics = async () => {
            try {
                setLoading(true)
                const response = await fetch(`${apiBase}/topics?lookback_hours=24&min_articles=15`)

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`)
                }

                const data = await response.json()
                setTopics(data.topics || [])
                setTotalArticles(data.total_articles || 0)
                setUncategorized(data.uncategorized_count || 0)
                setError(null)
            } catch (err) {
                console.error('Topics error:', err)
                setError(err.message)
            } finally {
                setLoading(false)
            }
        }

        fetchTopics()
    }, [apiBase])

    if (loading) {
        return (
            <section className="mt-12">
                <h3 className="text-2xl font-bold mb-6 text-charcoal flex items-center">
                    <SparklesIcon className="w-6 h-6 mr-3 text-sageGreen" />
                    Discovering Topics...
                </h3>
                <div className="grid md:grid-cols-3 gap-6">
                    {[1, 2, 3].map(i => (
                        <div key={i} className="bg-white/80 border border-white/70 rounded-2xl p-6 animate-pulse">
                            <div className="h-6 bg-mutedBrown/10 rounded mb-4 w-3/4"></div>
                            <div className="h-4 bg-mutedBrown/10 rounded mb-2"></div>
                            <div className="h-4 bg-mutedBrown/10 rounded mb-2 w-5/6"></div>
                            <div className="h-4 bg-mutedBrown/10 rounded w-2/3"></div>
                        </div>
                    ))}
                </div>
            </section>
        )
    }

    if (error) {
        return (
            <section className="mt-12">
                <div className="bg-mutedRose/10 border border-mutedRose/30 rounded-2xl p-6 text-center">
                    <p className="text-mutedRose">Unable to load topics: {error}</p>
                </div>
            </section>
        )
    }

    if (topics.length === 0) {
        return (
            <section className="mt-12">
                <h3 className="text-2xl font-bold mb-6 text-charcoal flex items-center">
                    <SparklesIcon className="w-6 h-6 mr-3 text-sageGreen" />
                    Discovered Topics
                </h3>
                <div className="bg-white/80 border border-white/70 rounded-2xl p-8 text-center">
                    <SparklesIcon className="w-12 h-12 mx-auto mb-4 text-mutedBrown/30" />
                    <p className="text-mutedBrown/70 mb-2">Not enough articles yet to detect topics</p>
                    <p className="text-sm text-mutedBrown/50">
                        Need at least 15 recent articles. Currently: {totalArticles}
                    </p>
                </div>
            </section>
        )
    }

    return (
        <section className="mt-12 scroll-reveal scroll-reveal-delay-2">
            <div className="flex items-center justify-between mb-6">
                <h3 className="text-2xl font-bold text-charcoal flex items-center">
                    <SparklesIcon className="w-6 h-6 mr-3 text-sageGreen" />
                    Discovered Topics
                    <span className="ml-3 text-sm font-normal text-mutedBrown/60">
                        (Last 24 hours)
                    </span>
                </h3>
                <div className="text-sm text-mutedBrown/60">
                    {topics.length} {topics.length === 1 ? 'topic' : 'topics'} • {totalArticles} articles
                </div>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
                {topics.map((topic) => (
                    <div
                        key={topic.topic_id}
                        className="bg-white/95 border border-white/70 rounded-2xl p-6 hover:border-sageGreen/40 hover:shadow-md transition-shadow group"
                    >
                        {/* Topic Header */}
                        <div className="flex items-start justify-between mb-4">
                            <h4 className="text-lg font-bold text-charcoal group-hover:text-sageGreen transition-colors line-clamp-2">
                                {topic.label}
                            </h4>
                            <span className="ml-2 px-2 py-1 bg-sageGreen/20 text-sageGreen rounded-full text-xs font-bold whitespace-nowrap">
                                {topic.article_count} {topic.article_count === 1 ? 'article' : 'articles'}
                            </span>
                        </div>

                        {/* Keywords */}
                        <div className="flex flex-wrap gap-2 mb-4">
                            {topic.keywords.slice(0, 5).map((keyword, idx) => (
                                <span
                                    key={idx}
                                    className="px-2 py-1 bg-mutedBrown/10 text-mutedBrown text-xs rounded-full"
                                >
                                    {keyword}
                                </span>
                            ))}
                        </div>

                        {/* Sample Articles */}
                        <div className="space-y-2 pt-4 border-t border-mutedBrown/10">
                            <p className="text-xs font-semibold text-mutedBrown/60 uppercase tracking-wide mb-2">
                                Sample Articles
                            </p>
                            {topic.sample_articles.slice(0, 2).map((article, idx) => (
                                <a
                                    key={idx}
                                    href={article.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="block group/article"
                                >
                                    <p className="text-sm text-charcoal group-hover/article:text-sageGreen line-clamp-2 transition-colors">
                                        {article.title}
                                    </p>
                                    <p className="text-xs text-mutedBrown/50 mt-1">
                                        {article.source}
                                    </p>
                                </a>
                            ))}
                        </div>
                    </div>
                ))}
            </div>

            {/* Uncategorized Notice */}
            {uncategorized > 0 && (
                <div className="mt-6 p-4 bg-mutedBrown/5 border border-mutedBrown/20 rounded-xl text-center">
                    <p className="text-sm text-mutedBrown/70">
                        {uncategorized} {uncategorized === 1 ? 'article' : 'articles'} didn't fit into any topic
                    </p>
                </div>
            )}
        </section>
    )
}

Topics.propTypes = {
    apiBase: PropTypes.string,
}

export default Topics
