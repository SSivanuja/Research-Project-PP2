import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import Logo from '@/components/Logo';
import { useAuth } from '@/contexts/AuthContext';
import { FileText, Brain, GitBranch, Shield, ArrowRight } from 'lucide-react';

const features = [
  { icon: FileText, text: 'Intelligent Document Analysis', desc: 'AI-powered analysis of legal documents' },
  { icon: Brain, text: 'Legal Reasoning Engine', desc: 'Advanced reasoning for complex legal cases' },
  { icon: GitBranch, text: 'Knowledge Graph', desc: 'Explore relationships between legal concepts' },
  { icon: Shield, text: 'Risk Detection', desc: 'Identify potential legal risks automatically' },
];

const Index = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();

  const handleGetStarted = () => {
    if (isAuthenticated) {
      navigate('/dashboard');
    } else {
      navigate('/login');
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary/5 via-background to-secondary/5">
      {/* Header */}
      <header className="border-b border-border/40 backdrop-blur-sm sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <Logo size="md" />
          <nav className="hidden md:flex gap-8">
            <a href="#features" className="text-sm font-medium hover:text-primary transition-colors">Features</a>
            <a href="#about" className="text-sm font-medium hover:text-primary transition-colors">About</a>
            <a href="#contact" className="text-sm font-medium hover:text-primary transition-colors">Contact</a>
          </nav>
          <Button onClick={handleGetStarted} className="gap-2">
            Get Started <ArrowRight className="h-4 w-4" />
          </Button>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 md:py-32">
        <div className="max-w-3xl">
          <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6">
            Legal Intelligence
            <span className="text-primary"> Reimagined</span>
          </h1>
          <p className="text-xl text-muted-foreground mb-8 leading-relaxed">
            Harness the power of AI to analyze legal documents, understand complex relationships, and identify risks with unprecedented accuracy.
          </p>
          <div className="flex gap-4">
            <Button size="lg" onClick={handleGetStarted}>
              Start Exploring
            </Button>
            <Button size="lg" variant="outline">
              Learn More
            </Button>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="bg-muted/30 py-16 md:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold mb-12 text-center">Powerful Features</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => {
              const Icon = feature.icon;
              return (
                <div key={index} className="p-6 rounded-lg border border-border/40 hover:border-primary/50 hover:bg-primary/5 transition-all">
                  <Icon className="h-8 w-8 text-primary mb-4" />
                  <h3 className="font-semibold mb-2">{feature.text}</h3>
                  <p className="text-sm text-muted-foreground">{feature.desc}</p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16 md:py-24 text-center">
        <h2 className="text-3xl font-bold mb-6">Ready to Transform Your Legal Workflows?</h2>
        <p className="text-lg text-muted-foreground mb-8 max-w-2xl mx-auto">
          Join thousands of legal professionals using Legal Insights Hub to make smarter decisions faster.
        </p>
        <Button size="lg" onClick={handleGetStarted} className="gap-2">
          Get Started Now <ArrowRight className="h-4 w-4" />
        </Button>
      </section>

      {/* Footer */}
      <footer className="border-t border-border/40 py-8 bg-muted/20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center text-sm text-muted-foreground">
          <p>&copy; 2026 Legal Insights Hub. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default Index;
