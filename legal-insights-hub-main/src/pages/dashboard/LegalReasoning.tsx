import { useState, useRef, useEffect } from 'react';
import { Send, Paperclip, ThumbsUp, ThumbsDown, Copy, Share2, Trash2, Settings, Sparkles, ChevronDown, ChevronUp } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { suggestedQuestions } from '@/data/sampleData';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { postQuery, postLegalReason, clearSession, type QueryResponse, type IRACAnalysis } from '@/lib/api';

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: string;
  citations?: string[];
  irac?: IRACAnalysis | null;
  confidence?: number;
  reasoning_steps?: { step: number; text: string; legal_basis: string | null }[];
  sources?: string[];
}

const SESSION_ID = `session_${Date.now()}`;

const LegalReasoning = () => {
  const { toast } = useToast();
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: 'msg_001',
      role: 'assistant',
      content: `Hello! I'm your Sri Lankan Property Law Assistant. I can help you with questions about:

• Property transfers & sale deeds
• Prescription & adverse possession
• Title registration (Bim Saviya)
• Partition of co-owned land
• Mortgages & leases

How can I assist you today?`,
      timestamp: new Date().toISOString(),
    },
  ]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [expandedIrac, setExpandedIrac] = useState<Record<string, boolean>>({});

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim()) return;

    const userMessage: ChatMessage = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages(prev => [...prev, userMessage]);
    const question = input.trim();
    setInput('');
    setIsTyping(true);

    try {
      // Try the natural language query endpoint first
      const response = await postQuery({
        query: question,
        session_id: SESSION_ID,
        include_reasoning: true,
      });

      const assistantMessage: ChatMessage = {
        id: `msg_${Date.now() + 1}`,
        role: 'assistant',
        content: response.answer,
        timestamp: new Date().toISOString(),
        irac: response.irac_analysis,
        confidence: response.confidence,
        reasoning_steps: response.reasoning_steps,
        sources: response.sources,
        citations: response.related_statutes,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch {
      // If API fails, try legal reasoning endpoint
      try {
        const reasonResponse = await postLegalReason({
          question,
          include_irac: true,
        });

        const assistantMessage: ChatMessage = {
          id: `msg_${Date.now() + 1}`,
          role: 'assistant',
          content: reasonResponse.answer,
          timestamp: new Date().toISOString(),
          irac: reasonResponse.irac_analysis,
          confidence: reasonResponse.confidence,
          reasoning_steps: reasonResponse.reasoning_steps,
          citations: reasonResponse.referenced_statutes,
        };

        setMessages(prev => [...prev, assistantMessage]);
      } catch {
        // Both endpoints failed
        const errorMessage: ChatMessage = {
          id: `msg_${Date.now() + 1}`,
          role: 'assistant',
          content: 'I apologize, but I\'m unable to connect to the legal reasoning service right now. Please ensure the API is running and try again.',
          timestamp: new Date().toISOString(),
        };
        setMessages(prev => [...prev, errorMessage]);
      }
    } finally {
      setIsTyping(false);
    }
  };

  const handleSuggestedQuestion = (question: string) => {
    setInput(question);
  };

  const handleCopy = (content: string) => {
    navigator.clipboard.writeText(content);
    toast({ title: "Copied!", description: "Response copied to clipboard." });
  };

  const handleClearChat = async () => {
    try {
      await clearSession(SESSION_ID);
    } catch {
      // Ignore session clear errors
    }
    setMessages([messages[0]]);
    toast({ title: "Chat cleared", description: "Conversation has been reset." });
  };

  const toggleIrac = (msgId: string) => {
    setExpandedIrac(prev => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const markdownComponents = {
    h1: ({node, ...props}: any) => <h1 className="text-lg font-bold text-foreground mt-4 mb-2" {...props} />,
    h2: ({node, ...props}: any) => <h2 className="text-base font-bold text-foreground mt-4 mb-2" {...props} />,
    h3: ({node, ...props}: any) => <h3 className="text-sm font-bold text-foreground mt-3 mb-2" {...props} />,
    h4: ({node, ...props}: any) => <h4 className="text-sm font-semibold text-primary mt-3 mb-2" {...props} />,
    p: ({node, ...props}: any) => <p className="mb-2 text-foreground" {...props} />,
    ul: ({node, ...props}: any) => <ul className="list-disc list-inside mb-2 space-y-1" {...props} />,
    ol: ({node, ...props}: any) => <ol className="list-decimal list-inside mb-2 space-y-1" {...props} />,
    li: ({node, ...props}: any) => <li className="text-foreground" {...props} />,
    blockquote: ({node, ...props}: any) => <blockquote className="border-l-4 border-primary/30 pl-4 italic text-muted-foreground mb-2" {...props} />,
    code: ({node, inline, ...props}: any) => inline ? <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono text-foreground" {...props} /> : <code className="block bg-muted p-3 rounded mb-2 text-sm font-mono overflow-x-auto text-foreground" {...props} />,
    pre: ({node, ...props}: any) => <pre className="block bg-muted p-3 rounded mb-2 text-sm overflow-x-auto" {...props} />,
    strong: ({node, ...props}: any) => <strong className="font-bold text-foreground" {...props} />,
    em: ({node, ...props}: any) => <em className="italic" {...props} />,
    a: ({node, ...props}: any) => <a className="text-primary hover:underline" {...props} />,
  };

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-lg bg-primary/10">
            <Sparkles className="h-6 w-6 text-primary" />
          </div>
          <div>
            <h1 className="text-xl font-display font-bold text-foreground">Legal Assistant</h1>
            <p className="text-sm text-muted-foreground">AI-powered Sri Lankan Property Law guidance</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="ghost" size="icon" onClick={handleClearChat}>
            <Trash2 className="h-4 w-4" />
          </Button>
          <Button variant="ghost" size="icon">
            <Settings className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Chat Container */}
      <Card className="flex-1 flex flex-col overflow-hidden">
        <CardContent className="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-thin">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                "flex gap-3 animate-slide-up",
                message.role === 'user' ? "justify-end" : "justify-start"
              )}
            >
              {message.role === 'assistant' && (
                <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                  <Sparkles className="h-4 w-4 text-primary-foreground" />
                </div>
              )}
              
              <div className={cn(
                "max-w-[80%] rounded-2xl px-4 py-3",
                message.role === 'user' 
                  ? "bg-primary text-primary-foreground rounded-tr-sm" 
                  : "bg-muted rounded-tl-sm"
              )}>
                <div className={cn("text-sm", message.role === 'assistant' && "text-foreground")}>
                  {message.role === 'assistant' ? (
                    <ReactMarkdown 
                      remarkPlugins={[remarkGfm]}
                      components={markdownComponents}
                    >
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    message.content
                  )}
                </div>

                {/* Confidence badge */}
                {message.confidence !== undefined && (
                  <div className="mt-2 flex items-center gap-2">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-primary/10 text-primary font-medium">
                      {Math.round(message.confidence * 100)}% confidence
                    </span>
                  </div>
                )}

                {/* IRAC Analysis */}
                {message.irac && (
                  <div className="mt-3 border-t border-border/50 pt-2">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-7 px-2 text-xs text-muted-foreground"
                      onClick={() => toggleIrac(message.id)}
                    >
                      ⚖️ IRAC Analysis
                      {expandedIrac[message.id] ? <ChevronUp className="h-3 w-3 ml-1" /> : <ChevronDown className="h-3 w-3 ml-1" />}
                    </Button>
                    {expandedIrac[message.id] && (
                      <div className="mt-2 space-y-3 text-sm animate-slide-up">
                        <div className="p-3 rounded-lg bg-background/60">
                          <p className="text-xs font-semibold text-primary mb-1">📋 ISSUE</p>
                          <div className="text-muted-foreground">
                            <ReactMarkdown 
                              remarkPlugins={[remarkGfm]}
                              components={{
                                p: ({node, ...props}: any) => <span {...props} />,
                                strong: ({node, ...props}: any) => <strong className="font-bold" {...props} />,
                                em: ({node, ...props}: any) => <em className="italic" {...props} />,
                              }}
                            >
                              {message.irac.issue}
                            </ReactMarkdown>
                          </div>
                        </div>
                        <div className="p-3 rounded-lg bg-background/60">
                          <p className="text-xs font-semibold text-primary mb-1">📖 RULE</p>
                          <div className="text-muted-foreground">
                            <ReactMarkdown 
                              remarkPlugins={[remarkGfm]}
                              components={{
                                p: ({node, ...props}: any) => <span {...props} />,
                                strong: ({node, ...props}: any) => <strong className="font-bold" {...props} />,
                                em: ({node, ...props}: any) => <em className="italic" {...props} />,
                              }}
                            >
                              {message.irac.rule}
                            </ReactMarkdown>
                          </div>
                        </div>
                        <div className="p-3 rounded-lg bg-background/60">
                          <p className="text-xs font-semibold text-primary mb-1">🔍 APPLICATION</p>
                          <div className="text-muted-foreground">
                            <ReactMarkdown 
                              remarkPlugins={[remarkGfm]}
                              components={{
                                p: ({node, ...props}: any) => <span {...props} />,
                                strong: ({node, ...props}: any) => <strong className="font-bold" {...props} />,
                                em: ({node, ...props}: any) => <em className="italic" {...props} />,
                              }}
                            >
                              {message.irac.application}
                            </ReactMarkdown>
                          </div>
                        </div>
                        <div className="p-3 rounded-lg bg-background/60">
                          <p className="text-xs font-semibold text-primary mb-1">✅ CONCLUSION</p>
                          <div className="text-muted-foreground">
                            <ReactMarkdown 
                              remarkPlugins={[remarkGfm]}
                              components={{
                                p: ({node, ...props}: any) => <span {...props} />,
                                strong: ({node, ...props}: any) => <strong className="font-bold" {...props} />,
                                em: ({node, ...props}: any) => <em className="italic" {...props} />,
                              }}
                            >
                              {message.irac.conclusion}
                            </ReactMarkdown>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Reasoning Steps */}
                {message.reasoning_steps && message.reasoning_steps.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-border/50">
                    <p className="text-xs font-semibold text-muted-foreground mb-2">🧠 Reasoning Steps:</p>
                    <ol className="space-y-2">
                      {message.reasoning_steps.map((step) => (
                        <li key={step.step} className="text-xs text-muted-foreground flex gap-2">
                          <span className="font-medium flex-shrink-0">{step.step}.</span>
                          <span className="flex-1">
                            <ReactMarkdown 
                              remarkPlugins={[remarkGfm]}
                              components={{
                                p: ({node, ...props}: any) => <span {...props} />,
                                strong: ({node, ...props}: any) => <strong className="font-bold text-foreground" {...props} />,
                                em: ({node, ...props}: any) => <em className="italic" {...props} />,
                              }}
                            >
                              {step.text}
                            </ReactMarkdown>
                            {step.legal_basis && <span className="text-primary ml-1">({step.legal_basis})</span>}
                          </span>
                        </li>
                      ))}
                    </ol>
                  </div>
                )}
                
                {/* Citations */}
                {message.citations && message.citations.length > 0 && (
                  <div className="mt-3 pt-2 border-t border-border/50">
                    <p className="text-xs font-semibold text-muted-foreground mb-2">📚 Citations:</p>
                    <ul className="space-y-1">
                      {message.citations.map((citation, i) => (
                        <li key={i} className="text-xs text-muted-foreground">• {citation}</li>
                      ))}
                    </ul>
                  </div>
                )}
                
                {/* Actions */}
                {message.role === 'assistant' && message.id !== 'msg_001' && (
                  <div className="flex items-center gap-1 mt-3 pt-2 border-t border-border/50">
                    <Button variant="ghost" size="sm" className="h-7 px-2 text-muted-foreground hover:text-foreground">
                      <ThumbsUp className="h-3.5 w-3.5" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7 px-2 text-muted-foreground hover:text-foreground">
                      <ThumbsDown className="h-3.5 w-3.5" />
                    </Button>
                    <Button variant="ghost" size="sm" className="h-7 px-2 text-muted-foreground hover:text-foreground" onClick={() => handleCopy(message.content)}>
                      <Copy className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                )}
              </div>
              
              {message.role === 'user' && (
                <div className="w-8 h-8 rounded-full bg-secondary flex items-center justify-center flex-shrink-0">
                  <span className="text-xs font-medium text-secondary-foreground">You</span>
                </div>
              )}
            </div>
          ))}
          
          {isTyping && (
            <div className="flex gap-3 animate-fade-in">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center flex-shrink-0">
                <Sparkles className="h-4 w-4 text-primary-foreground" />
              </div>
              <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-3">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                  <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                  <div className="w-2 h-2 bg-muted-foreground/50 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
          
          <div ref={messagesEndRef} />
        </CardContent>

        {/* Suggested Questions */}
        {messages.length <= 1 && (
          <div className="px-4 py-3 border-t border-border">
            <p className="text-xs font-medium text-muted-foreground mb-2">Suggested Questions:</p>
            <div className="flex flex-wrap gap-2">
              {suggestedQuestions.slice(0, 4).map((question, i) => (
                <Button key={i} variant="outline" size="sm" className="text-xs h-8" onClick={() => handleSuggestedQuestion(question)}>
                  {question}
                </Button>
              ))}
            </div>
          </div>
        )}

        {/* Input */}
        <div className="p-4 border-t border-border">
          <div className="flex items-end gap-2">
            <Button variant="ghost" size="icon" className="flex-shrink-0">
              <Paperclip className="h-4 w-4" />
            </Button>
            <div className="flex-1 relative">
              <Textarea
                placeholder="Type your legal question..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                className="min-h-[44px] max-h-[120px] resize-none pr-12"
                rows={1}
              />
            </div>
            <Button size="icon" onClick={handleSend} disabled={!input.trim() || isTyping} className="flex-shrink-0">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
};

export default LegalReasoning;
