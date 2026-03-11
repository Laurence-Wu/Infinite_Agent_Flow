'use client'

import { useState } from 'react'
import ExpandableMarkdown from '@/components/ExpandableMarkdown'

interface CardInstructionProps {
  markdown: string
}

export default function CardInstruction({ markdown }: CardInstructionProps) {
  const [showFullInstruction, setShowFullInstruction] = useState(false)

  return (
    <div>
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-semibold uppercase tracking-wider text-slate-400">
          Instruction
        </h4>
        {markdown && (
          <button
            onClick={() => setShowFullInstruction(!showFullInstruction)}
            className="text-xs text-accent-light hover:text-accent hover:underline"
          >
            {showFullInstruction ? 'Show Less' : 'Show Full'}
          </button>
        )}
      </div>
      
      {markdown ? (
        <div className={`prose prose-sm max-w-none ${
          showFullInstruction ? '' : 'max-h-60 overflow-hidden relative'
        }`}>
          <ExpandableMarkdown 
            markdown={markdown} 
            defaultExpandedSections={['h1']}
          />
          {!showFullInstruction && (
            <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-surface to-transparent pointer-events-none" />
          )}
        </div>
      ) : (
        <p className="text-slate-500 italic text-sm">Loading instruction...</p>
      )}
    </div>
  )
}
