'use client'

interface CardProgressBarProps {
  progressPct: number
}

export default function CardProgressBar({ progressPct }: CardProgressBarProps) {
  return (
    <div className="h-1 w-full bg-slate-800">
      <div
        className="h-full bg-gradient-to-r from-accent-dim via-accent to-accent-light progress-glow transition-all duration-700"
        style={{ width: `${progressPct}%` }}
      />
    </div>
  )
}
