export default function LoadingScreen() {
    return (
        <div className="fixed inset-0 bg-cream flex items-center justify-center z-50">
            <div className="flex flex-col items-center gap-6">
                {/* Newton's Cradle Animation */}
                <div className="newtons-cradle">
                    <div className="newtons-cradle__dot"></div>
                    <div className="newtons-cradle__dot"></div>
                    <div className="newtons-cradle__dot"></div>
                    <div className="newtons-cradle__dot"></div>
                </div>

                {/* Brand Name */}
                <div className="text-2xl font-bold">
                    <span className="text-charcoal">News</span>
                    <span className="text-mutedRose">Pulse</span>
                </div>

                <p className="text-charcoal/70 text-sm font-medium">Loading your personalized news...</p>
            </div>
        </div>
    )
}
