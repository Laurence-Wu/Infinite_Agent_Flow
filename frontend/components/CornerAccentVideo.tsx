'use client'

import { memo } from 'react'

interface CornerAccentVideoProps {
  position?: 'top-left' | 'top-right' | 'bottom-left' | 'bottom-right'
  size?: 'small' | 'medium' | 'large'
  videoName?: string
  opacity?: number
}

/**
 * CornerAccentVideo - Small decorative video accent for page corners
 * Used to add subtle visual interest without blocking content
 * 
 * Positions:
 * - top-left: Dashboard header area
 * - top-right: Settings/workflows area
 * - bottom-left: Footer area
 * - bottom-right: Log terminal area
 */
function CornerAccentVideo({
  position = 'top-right',
  size = 'medium',
  videoName,
  opacity = 0.12,
}: CornerAccentVideoProps) {
  const videos = [
    'ambient-flow-1.mp4',
    'ambient-flow-2.mp4',
    'ambient-flow-3.mp4',
    'ambient-flow-4.mp4',
  ]

  const selectedVideo = videoName && videos.includes(videoName)
    ? videoName
    : videos[Math.floor(Math.random() * videos.length)]

  // Size configuration
  const sizeConfig = {
    small: { width: '150px', height: '150px' },
    medium: { width: '250px', height: '250px' },
    large: { width: '350px', height: '350px' },
  }

  // Position classes
  const positionClasses = {
    'top-left': 'top-0 left-0 origin-top-left',
    'top-right': 'top-0 right-0 origin-top-right',
    'bottom-left': 'bottom-0 left-0 origin-bottom-left',
    'bottom-right': 'bottom-0 right-0 origin-bottom-right',
  }

  return (
    <div
      className={`fixed ${positionClasses[position]} pointer-events-none z-0`}
      style={{
        width: sizeConfig[size].width,
        height: sizeConfig[size].height,
        opacity,
      }}
    >
      <video
        autoPlay
        loop
        muted
        playsInline
        preload="auto"
        className="absolute w-full h-full object-cover"
        style={{
          filter: 'blur(20px) saturate(1.5) hue-rotate(15deg)',
          maskImage: 'radial-gradient(circle at center, black 0%, transparent 70%)',
          WebkitMaskImage: 'radial-gradient(circle at center, black 0%, transparent 70%)',
        }}
      >
        <source src={`/decorative_videos/${selectedVideo}`} type="video/mp4" />
      </video>
    </div>
  )
}

export default memo(CornerAccentVideo)
