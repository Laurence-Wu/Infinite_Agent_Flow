"use client";

import React, { useState, ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeHighlight from "rehype-highlight";
import { ChevronDown, ChevronUp, Code, List, Table, Quote, FileText } from "lucide-react";

interface ExpandableSectionProps {
  title: string;
  icon?: ReactNode;
  children: ReactNode;
  defaultExpanded?: boolean;
  level?: number;
}

function ExpandableSection({
  title,
  icon,
  children,
  defaultExpanded = false,
  level = 0,
}: ExpandableSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const indentClass = level > 0 ? `ml-${level * 4}` : "";

  return (
    <div className={`my-2 ${indentClass}`}>
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 w-full text-left hover:bg-slate-800/30 rounded-lg px-2 py-1.5 transition-colors duration-200 group"
      >
        <span className="text-slate-500 group-hover:text-accent-light transition-colors">
          {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronUp className="w-4 h-4" />}
        </span>
        {icon && <span className="text-slate-500 group-hover:text-accent-light">{icon}</span>}
        <span className="flex-1 font-medium text-slate-300">{title}</span>
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isExpanded ? "max-h-[5000px] opacity-100 mt-2" : "max-h-0 opacity-0"
        }`}
      >
        <div className="pl-6 border-l-2 border-slate-700/50">{children}</div>
      </div>
    </div>
  );
}

interface CodeBlockProps {
  language?: string;
  children: string;
}

function ExpandableCodeBlock({ language = "text", children }: CodeBlockProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const lines = children.trim().split("\n").length;
  const isLarge = lines > 10;

  return (
    <div className="my-3 rounded-xl overflow-hidden border border-slate-700/50 bg-[#1d2021]">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full px-3 py-2 bg-slate-800/50 hover:bg-slate-800 transition-colors gap-2"
      >
        <div className="flex items-center gap-2">
          <Code className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs font-mono text-slate-400">{language}</span>
          {isLarge && (
            <span className="text-xs text-slate-600">({lines} lines)</span>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={(e) => {
              e.stopPropagation();
              navigator.clipboard.writeText(children);
            }}
            className="text-xs px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
          >
            Copy
          </button>
          {isExpanded ? (
            <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
          )}
        </div>
      </button>
      <div
        className={`overflow-auto transition-all duration-300 ease-in-out ${
          isExpanded ? "max-h-[2000px] opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <pre className="p-3 m-0 overflow-x-auto">
          <code className={`language-${language} text-sm`}>{children}</code>
        </pre>
      </div>
    </div>
  );
}

interface ExpandableListProps {
  items: ReactNode[];
  ordered?: boolean;
  depth?: number;
}

function ExpandableList({ items, ordered = false, depth = 0 }: ExpandableListProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const itemCount = items.length;

  if (depth > 2) {
    // Render nested lists normally without expandable wrapper
    const ListTag = ordered ? "ol" : "ul";
    return (
      <ListTag className={`${ordered ? "list-decimal" : "list-disc"} pl-4 my-2`}>
        {items.map((item, i) => (
          <li key={i} className="my-1 text-slate-300">
            {item}
          </li>
        ))}
      </ListTag>
    );
  }

  return (
    <div className="my-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-left hover:bg-slate-800/30 rounded-lg px-2 py-1.5 transition-colors duration-200 w-full"
      >
        <span className="text-slate-500">
          {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
        </span>
        <List className="w-3.5 h-3.5 text-slate-500" />
        <span className="text-xs text-slate-400">
          {itemCount} {ordered ? "numbered" : "bullet"} {itemCount === 1 ? "item" : "items"}
        </span>
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isExpanded ? "max-h-[3000px] opacity-100 mt-2" : "max-h-0 opacity-0"
        }`}
      >
        <div className="pl-6 border-l-2 border-slate-700/50">
          {items.map((item, i) => (
            <div key={i} className="my-1.5 text-slate-300">
              {item}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

interface ExpandableTableProps {
  headers: string[];
  rows: string[][];
}

function ExpandableTable({ headers, rows }: ExpandableTableProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="my-3 rounded-xl overflow-hidden border border-slate-700/50">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center justify-between w-full px-3 py-2 bg-slate-800/50 hover:bg-slate-800 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Table className="w-3.5 h-3.5 text-slate-400" />
          <span className="text-xs text-slate-400">
            Table ({rows.length} {rows.length === 1 ? "row" : "rows"})
          </span>
        </div>
        {isExpanded ? (
          <ChevronUp className="w-3.5 h-3.5 text-slate-400" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
        )}
      </button>
      <div
        className={`overflow-auto transition-all duration-300 ease-in-out ${
          isExpanded ? "max-h-[1500px] opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <div className="p-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-700">
                {headers.map((header, i) => (
                  <th
                    key={i}
                    className="text-left py-2 px-3 text-slate-300 font-semibold bg-slate-800/30"
                  >
                    {header}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, rowIndex) => (
                <tr
                  key={rowIndex}
                  className="border-b border-slate-800 hover:bg-slate-800/20 transition-colors"
                >
                  {row.map((cell, cellIndex) => (
                    <td key={cellIndex} className="py-2 px-3 text-slate-400">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>{cell}</ReactMarkdown>
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

interface ExpandableBlockquoteProps {
  children: ReactNode;
}

function ExpandableBlockquote({ children }: ExpandableBlockquoteProps) {
  const [isExpanded, setIsExpanded] = useState(true);

  return (
    <div className="my-3 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 w-full px-3 py-2 bg-amber-500/5 hover:bg-amber-500/10 transition-colors border-l-4 border-amber-500"
      >
        <Quote className="w-3.5 h-3.5 text-amber-500" />
        <span className="text-xs text-amber-400/80">Note</span>
        {isExpanded ? (
          <ChevronUp className="w-3.5 h-3.5 text-slate-400 ml-auto" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-auto" />
        )}
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isExpanded ? "max-h-[1000px] opacity-100" : "max-h-0 opacity-0"
        }`}
      >
        <blockquote className="pl-4 pr-3 py-2 text-slate-400 bg-amber-500/5 border-l-4 border-amber-500">
          {children}
        </blockquote>
      </div>
    </div>
  );
}

interface ExpandableParagraphProps {
  children: ReactNode;
  isLong?: boolean;
}

function ExpandableParagraph({ children, isLong = false }: ExpandableParagraphProps) {
  const [isExpanded, setIsExpanded] = useState(!isLong);
  const content = typeof children === "string" ? children : "";
  const wordCount = content.split(/\s+/).length;
  const shouldExpand = wordCount > 50;

  if (!shouldExpand) {
    return <p className="my-2 text-slate-300 leading-relaxed">{children}</p>;
  }

  return (
    <div className="my-2">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-2 text-left hover:bg-slate-800/30 rounded-lg px-2 py-1.5 transition-colors duration-200 w-full mb-1"
      >
        <FileText className="w-3.5 h-3.5 text-slate-500" />
        <span className="text-xs text-slate-500">
          {wordCount} words
        </span>
        {isExpanded ? (
          <ChevronUp className="w-3.5 h-3.5 text-slate-400 ml-auto" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 ml-auto" />
        )}
      </button>
      <div
        className={`overflow-hidden transition-all duration-300 ease-in-out ${
          isExpanded ? "max-h-[2000px] opacity-100" : "max-h-20 opacity-80"
        }`}
      >
        <p className="text-slate-300 leading-relaxed">{children}</p>
      </div>
    </div>
  );
}

interface ExpandableMarkdownProps {
  markdown: string;
  defaultExpandedSections?: string[];
}

export default function ExpandableMarkdown({
  markdown,
  defaultExpandedSections = [],
}: ExpandableMarkdownProps) {
  if (!markdown) {
    return (
      <div className="prose p-6">
        <p className="text-slate-500 italic text-sm">No content to display.</p>
      </div>
    );
  }

  return (
    <div className="prose p-6 max-h-[600px] overflow-y-auto custom-scrollbar">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={{
          h1: ({ node, children, ...props }) => (
            <ExpandableSection
              title={String(children)}
              icon={<FileText className="w-4 h-4" />}
              defaultExpanded={defaultExpandedSections.includes("h1")}
              level={0}
            >
              <h1 className="text-xl font-bold text-slate-100 mt-0" {...props}>
                {children}
              </h1>
            </ExpandableSection>
          ),
          h2: ({ node, children, ...props }) => (
            <ExpandableSection
              title={String(children)}
              icon={<FileText className="w-4 h-4" />}
              defaultExpanded={defaultExpandedSections.includes("h2")}
              level={1}
            >
              <h2 className="text-lg font-semibold text-slate-200 mt-0" {...props}>
                {children}
              </h2>
            </ExpandableSection>
          ),
          h3: ({ node, children, ...props }) => (
            <ExpandableSection
              title={String(children)}
              defaultExpanded={defaultExpandedSections.includes("h3")}
              level={2}
            >
              <h3 className="text-base font-medium text-slate-300 mt-0" {...props}>
                {children}
              </h3>
            </ExpandableSection>
          ),
          h4: ({ node, children, ...props }) => (
            <ExpandableSection
              title={String(children)}
              defaultExpanded={defaultExpandedSections.includes("h4")}
              level={3}
            >
              <h4 className="text-sm font-medium text-slate-300 mt-0" {...props}>
                {children}
              </h4>
            </ExpandableSection>
          ),
          h5: ({ node, children, ...props }) => (
            <ExpandableSection
              title={String(children)}
              defaultExpanded={defaultExpandedSections.includes("h5")}
              level={4}
            >
              <h5 className="text-sm font-medium text-slate-400 mt-0" {...props}>
                {children}
              </h5>
            </ExpandableSection>
          ),
          h6: ({ node, children, ...props }) => (
            <ExpandableSection
              title={String(children)}
              defaultExpanded={defaultExpandedSections.includes("h6")}
              level={5}
            >
              <h6 className="text-xs font-medium text-slate-500 mt-0" {...props}>
                {children}
              </h6>
            </ExpandableSection>
          ),
          code({ node, inline, className, children, ...props }: any) {
            const match = /language-(\w+)/.exec(className || "");
            const content = String(children).replace(/\n$/, "");

            if (!inline && match) {
              return (
                <ExpandableCodeBlock language={match[1]}>{content}</ExpandableCodeBlock>
              );
            }

            if (!inline) {
              return <ExpandableCodeBlock language="text">{content}</ExpandableCodeBlock>;
            }

            return (
              <code
                className="px-1.5 py-0.5 bg-slate-800/50 rounded text-amber-300 text-sm font-mono border border-slate-700/30"
                {...props}
              >
                {children}
              </code>
            );
          },
          ul({ node, children, ...props }: any) {
            const items = React.Children.toArray(children);
            return (
              <ExpandableList items={items as ReactNode[]} ordered={false} />
            );
          },
          ol({ node, children, ...props }: any) {
            const items = React.Children.toArray(children);
            return (
              <ExpandableList items={items as ReactNode[]} ordered={true} />
            );
          },
          li({ children, ...props }: any) {
            return (
              <li className="my-1 text-slate-300" {...props}>
                {children}
              </li>
            );
          },
          table({ node, children, ...props }: any) {
            // Parse table structure from children
            const headers: string[] = [];
            const rows: string[][] = [];

            React.Children.forEach(children, (child: any) => {
              if (child?.type === "thead") {
                React.Children.forEach(child.props.children, (row: any) => {
                  if (row?.type === "tr") {
                    React.Children.forEach(row.props.children, (cell: any) => {
                      if (cell?.type === "th") {
                        headers.push(String(cell.props.children));
                      }
                    });
                  }
                });
              }
              if (child?.type === "tbody") {
                React.Children.forEach(child.props.children, (row: any) => {
                  if (row?.type === "tr") {
                    const rowData: string[] = [];
                    React.Children.forEach(row.props.children, (cell: any) => {
                      if (cell?.type === "td") {
                        rowData.push(String(cell.props.children || ""));
                      }
                    });
                    rows.push(rowData);
                  }
                });
              }
            });

            if (headers.length > 0 || rows.length > 0) {
              return (
                <ExpandableTable headers={headers} rows={rows} />
              );
            }

            return <table {...props}>{children}</table>;
          },
          blockquote({ children, ...props }: any) {
            return (
              <ExpandableBlockquote>
                <span {...props}>{children}</span>
              </ExpandableBlockquote>
            );
          },
          p({ children, ...props }: any) {
            const content = String(children || "");
            const wordCount = content.split(/\s+/).length;
            return (
              <ExpandableParagraph isLong={wordCount > 50}>
                <span {...props}>{children}</span>
              </ExpandableParagraph>
            );
          },
          hr() {
            return <hr className="my-4 border-slate-700" />;
          },
          strong({ children, ...props }: any) {
            return <strong className="text-slate-100 font-semibold" {...props}>{children}</strong>;
          },
          em({ children, ...props }: any) {
            return <em className="text-slate-400" {...props}>{children}</em>;
          },
          a({ href, children, ...props }: any) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-gruvbox-cyan hover:text-gruvbox-cyan-bright underline transition-colors"
                {...props}
              >
                {children}
              </a>
            );
          },
        }}
      >
        {markdown}
      </ReactMarkdown>
    </div>
  );
}
