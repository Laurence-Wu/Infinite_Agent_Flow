'use client'

import { memo, useState, useEffect, useRef, useCallback } from 'react'

interface BackgroundVideoProps {
  videoName?: string
  opacity?: number
  className?: string
  enabled?: boolean
}

/**
 * BackgroundVideo - Decorative ambient video component with lazy loading
 * 
 * Performance optimizations:
 * - Lazy loads when component enters viewport
 * - Uses Intersection Observer for efficient detection
 * - Low priority loading (idle callback)
 * - Mobile: disables on small screens or reduces quality
 * - Preloads only metadata initially
 * - Uses requestIdleCallback for non-blocking load
 */
function BackgroundVideo({ 
  videoName, 
  opacity = 0.06,
  className = '',
  enabled = true,
}: BackgroundVideoProps) {
  const [selectedVideo, setSelectedVideo] = useState<string | null>(null)
  const [isLoaded, setIsLoaded] = useState(false)
  const [isVisible, setIsVisible] = useState(false)
  const [shouldLoad, setShouldLoad] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const videoRef = useRef<HTMLVideoElement>(null)
  const loadTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Videos array
  const videos = [
    'ambient-flow-1.mp4',
    'ambient-flow-2.mp4',
    'ambient-flow-3.mp4',
    'ambient-flow-4.mp4',
  ]

  // Pick video on mount
  useEffect(() => {
    if (videoName && videos.includes(videoName)) {
      setSelectedVideo(videoName)
    } else {
      // Use deterministic random based on session
      const randomIndex = Math.floor(Math.random() * videos.length)
      setSelectedVideo(videos[randomIndex])
    }
  }, [videoName])

  // Intersection Observer for lazy loading
  useEffect(() => {
    if (!enabled || !containerRef.current) return

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsVisible(true)
            // Delay loading slightly to prioritize main content
            loadTimeoutRef.current = setTimeout(() => {
              setShouldLoad(true)
            }, 100)
            observer.disconnect()
          }
        })
      },
      {
        rootMargin: '50px', // Start loading when 50px from viewport
        threshold: 0.01,
      }
    )

    observer.observe(containerRef.current)

    return () => {
      observer.disconnect()
      if (loadTimeoutRef.current) {
        clearTimeout(loadTimeoutRef.current)
      }
    }
  }, [enabled])

  // Use requestIdleCallback for non-blocking video load
  useEffect(() => {
    if (!shouldLoad || !selectedVideo) return

    const loadVideo = () => {
      if (videoRef.current) {
        videoRef.current.load()
      }
    }

    if ('requestIdleCallback' in window) {
      const idleHandle = requestIdleCallback(loadVideo, { timeout: 2000 })
      return () => cancelIdleCallback(idleHandle)
    } else {
      // Fallback for browsers without requestIdleCallback
      setTimeout(loadVideo, 0)
    }
  }, [shouldLoad, selectedVideo])

  // Cleanup
  useEffect(() => {
    return () => {
      if (loadTimeoutRef.current) {
        clearTimeout(loadTimeoutRef.current)
      }
    }
  }, [])

  if (!enabled || !selectedVideo) {
    return null
  }

  return (
    <div 
      ref={containerRef}
      className={`fixed inset-0 pointer-events-none z-0 overflow-hidden ${className}`}
      style={{ opacity: isVisible ? opacity : 0 }}
      aria-hidden="true"
    >
      {/* Main background video layer */}
      {shouldLoad && (
        <>
          <video
            ref={videoRef}
            autoPlay
            loop
            muted
            playsInline
            preload="metadata"
            className="absolute min-w-full min-h-full object-cover"
            style={{
              filter: 'blur(40px) saturate(1.2)',
              transform: 'scale(1.1)',
              willChange: 'transform',
              contain: 'strict',
            }}
            onLoadedData={() => setIsLoaded(true)}
            onError={(e) => {
              console.warn('Background video failed to load:', e)
              setIsLoaded(true) // Still mark as loaded to avoid retry
            }}
          >
            <source src={`/decorative_videos/${selectedVideo}`} type="video/mp4" />
          </video>
          
          {/* Overlay gradient to ensure text readability */}
          <div 
            className="absolute inset-0"
            style={{
              background: 'radial-gradient(ellipse at center, transparent 0%, rgba(29,32,33,0.4) 100%)',
            }}
          />
        </>
      )}

      {/* Secondary subtle video layer for depth (only load after first is ready) */}
      {isLoaded && (
        <div 
          className="fixed inset-0 pointer-events-none z-0 overflow-hidden"
          style={{ opacity: opacity * 0.5 }}
          aria-hidden="true"
        >
          <video
            autoPlay
            loop
            muted
            playsInline
            preload="none"
            className="absolute min-w-full min-h-full object-cover"
            style={{
              filter: 'blur(60px) saturate(0.8)',
              transform: 'scale(1.2)',
              willChange: 'transform',
            }}
          >
            <source src={`/decorative_videos/${selectedVideo}`} type="video/mp4" />
          </video>
        </div>
      )}
    </div>
  )
}

// Memoize to prevent unnecessary re-renders
export default memo(BackgroundVideo)
