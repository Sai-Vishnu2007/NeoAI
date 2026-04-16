import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
// 🔥 ADDED Copy and Check to the Lucide imports (Bot is still here if you need it elsewhere, but we aren't using it for the avatar anymore!)
import { ChevronDown, ChevronUp, Brain, User, Bot, Copy, Check } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { dracula } from 'react-syntax-highlighter/dist/esm/styles/prism';

// 🔥 NEW: Extracted CodeBlock component to manage the "Copied" state perfectly
const CodeBlock = ({ node, inline, className, children, ...props }) => {
  const [copied, setCopied] = useState(false);
  const match = /language-(\w+)/.exec(className || '');
  const codeString = String(children).replace(/\n$/, '');

  const handleCopy = () => {
    navigator.clipboard.writeText(codeString);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (!inline && match) {
    return (
      <div className="relative my-4 rounded-xl overflow-hidden border border-cyber-purple/30 bg-[#282a36] shadow-lg">
        {/* Top Bar for Code Block */}
        <div className="flex items-center justify-between px-4 py-2 bg-[#1e1f29] border-b border-cyber-purple/20">
          <span className="text-xs font-mono text-cyber-purple uppercase">{match[1]}</span>
          <button
            onClick={handleCopy}
            className="flex items-center space-x-1 text-xs text-slate-400 hover:text-cyber-pink transition-colors"
          >
            {copied ? <Check className="w-4 h-4 text-green-400" /> : <Copy className="w-4 h-4" />}
            <span>{copied ? 'Copied!' : 'Copy'}</span>
          </button>
        </div>
        {/* Syntax Highlighter */}
        <SyntaxHighlighter
          style={dracula}
          language={match[1]}
          PreTag="div"
          customStyle={{
            borderRadius: '0 0 8px 8px',
            padding: '1rem',
            margin: 0,
            background: 'transparent',
          }}
          {...props}
        >
          {codeString}
        </SyntaxHighlighter>
      </div>
    );
  }

  return (
    <code className={`${className} bg-cyber-darker px-2 py-1 rounded text-cyber-pink`} {...props}>
      {children}
    </code>
  );
};

const MessageBubble = ({ message, isUser }) => {
  const [showReasoning, setShowReasoning] = useState(false);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -20 }}
      transition={{ duration: 0.4 }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-6`}
    >
      <div className={`flex items-start space-x-3 max-w-3xl ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
        
        {/* 🔥 UPDATED: Avatar Wrapper with overflow-hidden and custom Logo */}
        <div
          className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center overflow-hidden ${
            isUser
              ? 'bg-gradient-to-br from-cyber-purple to-cyber-pink'
              : 'glass border-2 border-cyber-purple'
          }`}
        >
          {isUser ? (
            <User className="w-5 h-5 text-white" />
          ) : (
            <img src="/neo-logo.png" alt="Neo AI" className="w-full h-full object-cover" />
          )}
        </div>

        {/* Message Content */}
        <div className={`flex-1 ${isUser ? 'items-end' : 'items-start'}`}>
          {/* Brain Process Accordion (Only for AI messages with reasoning) */}
          {!isUser && message.reasoning_content && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              className="mb-3"
            >
              <button
                onClick={() => setShowReasoning(!showReasoning)}
                className="w-full glass-hover rounded-lg p-3 flex items-center justify-between text-left group"
              >
                <div className="flex items-center space-x-2">
                  <Brain className="w-5 h-5 text-cyber-pink group-hover:animate-pulse" />
                  <span className="text-sm font-medium text-cyber-purple">
                    Brain Process
                  </span>
                </div>
                {showReasoning ? (
                  <ChevronUp className="w-5 h-5 text-cyber-purple" />
                ) : (
                  <ChevronDown className="w-5 h-5 text-cyber-purple" />
                )}
              </button>

              <AnimatePresence>
                {showReasoning && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3 }}
                    className="overflow-hidden"
                  >
                    <div className="mt-2 glass rounded-lg p-4 border-l-4 border-cyber-pink">
                      <div className="text-sm text-slate-300 whitespace-pre-wrap font-mono">
                        {message.reasoning_content}
                      </div>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )}

          {/* Main Message Bubble */}
          <div
            className={`rounded-2xl p-4 ${
              isUser
                ? 'bg-gradient-to-br from-cyber-purple to-cyber-blue text-white'
                : 'glass text-slate-100'
            }`}
          >
            <div className="prose prose-invert max-w-none">
              <ReactMarkdown
                components={{
                  // 🔥 UPDATED: Passing our new extracted CodeBlock component here
                  code: CodeBlock,
                  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc ml-4 mb-2">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal ml-4 mb-2">{children}</ol>,
                  li: ({ children }) => <li className="mb-1">{children}</li>,
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-cyber-pink hover:text-cyber-purple underline"
                    >
                      {children}
                    </a>
                  ),
                  h1: ({ children }) => <h1 className="text-2xl font-bold mb-2">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-xl font-bold mb-2">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-lg font-bold mb-2">{children}</h3>,
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-cyber-purple pl-4 italic my-2">
                      {children}
                    </blockquote>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          </div>

          {/* Timestamp */}
          <div className={`mt-1 text-xs text-slate-500 ${isUser ? 'text-right' : 'text-left'}`}>
            {message.timestamp ? new Date(message.timestamp).toLocaleTimeString() : 'Just now'}
          </div>
        </div>
      </div>
    </motion.div>
  );
};

export default MessageBubble;