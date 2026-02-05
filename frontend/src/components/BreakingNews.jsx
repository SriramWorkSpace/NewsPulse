import { useState, useEffect } from 'react'
import PropTypes from 'prop-types'

const BreakingNews = ({ apiBase = 'http://localhost:8000' }) => {
    const [breakingStories, setBreakingStories] = useState([])
    const [visible, setVisible] = useState(false)
    const [dismissed, setDismissed] = useState(new Set())

    useEffect(() => {
        const fetchBreakingNews = async () => {
            try {
                const response = await fetch(`${apiBase}/breaking?threshold=60`)

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`)
                }

                const data = await response.json()
                const stories = data.breaking || []

                // Filter out dismissed stories
                const activeStories = stories.filter(
                    story => !dismissed.has(story.url)
                )

                setBreakingStories(activeStories)
                setVisible(activeStories.length > 0)
            } catch (err) {
                console.error('Breaking news error:', err)
            }
        }

        // Initial fetch
        fetchBreakingNews()

        // Auto-refresh every 5 minutes
        const interval = setInterval(fetchBreakingNews, 5 * 60 * 1000)

        return () => clearInterval(interval)
    }, [apiBase, dismissed])

    const handleDismiss = (storyUrl) => {
        setDismissed(prev => new Set([...prev, storyUrl]))
        setBreakingStories(prev => prev.filter(s => s.url !== storyUrl))

        // Hide banner if no stories left
        if (breakingStories.length <= 1) {
            setVisible(false)
        }
    }

    const getUrgencyColor = (score) => {
        if (score >= 80) return 'bg-red-600 border-red-700'
        if (score >= 60) return 'bg-orange-600 border-orange-700'
        return 'bg-yellow-600 border-yellow-700'
    }

    const getUrgencyBadge = (score) => {
        if (score >= 80) return 'URGENT'
        if (score >= 60) return 'BREAKING'
        return 'DEVELOPING'
    }

    const getTimeAgo = (detectedAt) => {
        if (!detectedAt) return ''

        const now = new Date()
        const detected = new Date(detectedAt)
        const diffMinutes = Math.floor((now - detected) / 60000)

        if (diffMinutes < 1) return 'just now'
        if (diffMinutes === 1) return '1 min ago'
        if (diffMinutes < 60) return `${diffMinutes} min ago`

        const diffHours = Math.floor(diffMinutes / 60)
        if (diffHours === 1) return '1 hour ago'
        return `${diffHours} hours ago`
    }

    if (!visible || breakingStories.length === 0) {
        return null
    }

    return (
        <div className="fixed top-0 left-0 right-0 z-50 animate-slideDown">
            {breakingStories.map((story, idx) => (
                <div
                    key={story.url || idx}
                    className={`${getUrgencyColor(story.score)} border-b-2 text-white shadow-2xl`}
                >
                    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3">
                        <div className="flex items-center justify-between gap-4">
                            {/* Left: Breaking indicator */}
                            <div className="flex items-center gap-3 flex-shrink-0">
                                <div className="flex items-center gap-2">
                                    <span className="relative flex h-3 w-3">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                                        <span className="relative inline-flex rounded-full h-3 w-3 bg-white"></span>
                                    </span>
                                    <span className="text-sm font-black uppercase tracking-wider">
                                        {getUrgencyBadge(story.score)}
                                    </span>
                                </div>
                                <div className="hidden sm:flex items-center gap-1 text-xs bg-white/20 px-2 py-1 rounded-full">
                                    <span className="font-bold">{story.score}</span>
                                    <span className="opacity-90">•</span>
                                    <span>{story.article_count} articles</span>
                                </div>
                            </div>

                            {/* Center: Story title */}
                            <div className="flex-1 min-w-0">
                                <a
                                    href={story.url}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="hover:underline"
                                >
                                    <p className="font-semibold text-sm sm:text-base line-clamp-1">
                                        {story.title}
                                    </p>
                                </a>
                                <div className="flex items-center gap-3 mt-1">
                                    <p className="text-xs opacity-90">
                                        {story.source} • {getTimeAgo(story.detected_at)}
                                    </p>
                                    {story.novel_entities && story.novel_entities.length > 0 && (
                                        <div className="hidden md:flex items-center gap-1 text-xs">
                                            <span className="opacity-75">New:</span>
                                            <span className="font-semibold">
                                                {story.novel_entities.slice(0, 3).join(', ')}
                                            </span>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Right: Dismiss button */}
                            <button
                                onClick={() => handleDismiss(story.url)}
                                className="flex-shrink-0 p-2 hover:bg-white/20 rounded-lg transition-colors"
                                aria-label="Dismiss"
                            >
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                                </svg>
                            </button>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    )
}

BreakingNews.propTypes = {
    apiBase: PropTypes.string,
}

export default BreakingNews
