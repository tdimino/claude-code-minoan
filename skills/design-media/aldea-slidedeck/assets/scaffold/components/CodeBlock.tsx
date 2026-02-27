import React from 'react';

interface CodeBlockProps {
  code: string;
  language?: string;
  title?: string;
  compact?: boolean;
}

export const CodeBlock: React.FC<CodeBlockProps> = ({
  code,
  language = 'typescript',
  title,
  compact = false,
}) => {
  // Simple syntax highlighting
  const highlightCode = (code: string) => {
    return code
      // Keywords
      .replace(/\b(const|let|var|function|async|await|return|if|else|import|export|from|interface|type|class|extends|new)\b/g,
        '<span class="keyword">$1</span>')
      // Strings
      .replace(/(["'`])([^"'`\n]*)\1/g,
        '<span class="string">$1$2$1</span>')
      // Functions
      .replace(/\b([a-zA-Z_][a-zA-Z0-9_]*)\s*\(/g,
        '<span class="function">$1</span>(')
      // Comments
      .replace(/(\/\/[^\n]*)/g,
        '<span class="comment">$1</span>')
      // Types
      .replace(/: ([A-Z][a-zA-Z0-9_<>,\s]*)/g,
        ': <span class="type">$1</span>');
  };

  return (
    <div className="relative">
      {title && (
        <div className="flex items-center gap-2 mb-2">
          <div className="w-2 h-2 rounded-full bg-blueprint-cyan/60" />
          <span className="font-mono text-xs text-blueprint-cyan/80 uppercase tracking-wider">
            {title}
          </span>
        </div>
      )}
      <div className={`code-block ${compact ? 'text-[11px] p-3' : ''}`}>
        <pre>
          <code
            dangerouslySetInnerHTML={{ __html: highlightCode(code) }}
          />
        </pre>
      </div>
    </div>
  );
};

export default CodeBlock;
