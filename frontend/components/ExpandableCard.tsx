"use client";

import { useState, ReactNode } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

interface ExpandableCardProps {
  title: string;
  icon?: ReactNode;
  children: ReactNode;
  expandedContent?: ReactNode;
  defaultExpanded?: boolean;
  className?: string;
}

export default function ExpandableCard({
  title,
  icon,
  children,
  expandedContent,
  defaultExpanded = false,
  className = "",
}: ExpandableCardProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const hasExpandableContent = expandedContent !== undefined;

  return (
    <div
      className={`glass-card rounded-2xl overflow-hidden transition-all duration-300 ${className}`}
    >
      {/* Header - always visible */}
      <div
        className={`flex items-center justify-between px-5 py-3 border-b border-slate-700/40 ${
          hasExpandableContent ? "cursor-pointer hover:bg-slate-800/30" : ""
        } transition-colors duration-200`}
        onClick={() => hasExpandableContent && setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center gap-2">
          {icon}
          <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">
            {title}
          </span>
        </div>
        {hasExpandableContent && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(!isExpanded);
            }}
            className="text-slate-500 hover:text-accent-light transition-colors duration-200"
            aria-label={isExpanded ? "Collapse" : "Expand"}
          >
            {isExpanded ? (
              <ChevronUp className="w-4 h-4" />
            ) : (
              <ChevronDown className="w-4 h-4" />
            )}
          </button>
        )}
      </div>

      {/* Main content - always visible */}
      <div className={!hasExpandableContent ? "" : ""}>{children}</div>

      {/* Expanded content - conditionally rendered with animation */}
      {hasExpandableContent && (
        <div
          className={`overflow-hidden transition-all duration-300 ease-in-out ${
            isExpanded ? "max-h-[2000px] opacity-100" : "max-h-0 opacity-0"
          }`}
        >
          <div className="border-t border-slate-700/30 bg-slate-800/20 p-5">
            {expandedContent}
          </div>
        </div>
      )}
    </div>
  );
}
