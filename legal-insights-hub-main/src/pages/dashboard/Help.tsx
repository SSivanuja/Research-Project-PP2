import { HelpCircle, Book, MessageCircle, Mail, ExternalLink, ChevronRight } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const faqs = [
  {
    question: 'How do I upload a document for analysis?',
    answer: 'Navigate to the Document Analyzer tab and either drag & drop your file or click to browse. We support PDF, DOCX, and image formats up to 25MB.',
  },
  {
    question: 'What types of legal documents can be analyzed?',
    answer: 'LegalVision supports Sri Lankan property documents including Sale Deeds, Gift Deeds, Mortgage Bonds, Partition Deeds, and Lease Agreements.',
  },
  {
    question: 'How accurate is the AI analysis?',
    answer: 'Our AI achieves 90-95% accuracy for standard property documents. Always verify critical legal details with the original document.',
  },
  {
    question: 'Can I export my analysis results?',
    answer: 'Yes! You can export results as PDF reports or JSON files from the Export tab in the Document Analyzer.',
  },
];

const Help = () => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Help & Support</h1>
        <p className="text-muted-foreground">Find answers and get assistance</p>
      </div>

      {/* Search */}
      <Card>
        <CardContent className="pt-6">
          <div className="text-center mb-6">
            <HelpCircle className="h-12 w-12 text-primary mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-foreground">How can we help you?</h2>
            <p className="text-muted-foreground mt-1">Search our knowledge base or browse common questions</p>
          </div>
          <div className="max-w-md mx-auto">
            <Input placeholder="Search for help articles..." className="text-center" />
          </div>
        </CardContent>
      </Card>

      {/* Quick Links */}
      <div className="grid sm:grid-cols-3 gap-4">
        <Card className="hover:shadow-card-hover transition-shadow cursor-pointer">
          <CardContent className="pt-6 text-center">
            <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-4">
              <Book className="h-6 w-6 text-primary" />
            </div>
            <h3 className="font-semibold text-foreground">Documentation</h3>
            <p className="text-sm text-muted-foreground mt-1">Read our guides and tutorials</p>
          </CardContent>
        </Card>
        
        <Card className="hover:shadow-card-hover transition-shadow cursor-pointer">
          <CardContent className="pt-6 text-center">
            <div className="h-12 w-12 rounded-full bg-secondary/10 flex items-center justify-center mx-auto mb-4">
              <MessageCircle className="h-6 w-6 text-secondary" />
            </div>
            <h3 className="font-semibold text-foreground">Live Chat</h3>
            <p className="text-sm text-muted-foreground mt-1">Chat with our support team</p>
          </CardContent>
        </Card>
        
        <Card className="hover:shadow-card-hover transition-shadow cursor-pointer">
          <CardContent className="pt-6 text-center">
            <div className="h-12 w-12 rounded-full bg-accent/10 flex items-center justify-center mx-auto mb-4">
              <Mail className="h-6 w-6 text-accent-foreground" />
            </div>
            <h3 className="font-semibold text-foreground">Email Support</h3>
            <p className="text-sm text-muted-foreground mt-1">support@legalvision.lk</p>
          </CardContent>
        </Card>
      </div>

      {/* FAQs */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Frequently Asked Questions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {faqs.map((faq, index) => (
            <div 
              key={index}
              className="p-4 rounded-lg bg-muted/30 hover:bg-muted/50 transition-colors cursor-pointer"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h4 className="font-medium text-foreground">{faq.question}</h4>
                  <p className="text-sm text-muted-foreground mt-1">{faq.answer}</p>
                </div>
                <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0" />
              </div>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* Contact */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <h3 className="font-semibold text-foreground">Still need help?</h3>
              <p className="text-sm text-muted-foreground">Our team is here to assist you</p>
            </div>
            <div className="flex gap-3">
              <Button variant="outline">
                <MessageCircle className="h-4 w-4 mr-2" />
                Start Chat
              </Button>
              <Button>
                <ExternalLink className="h-4 w-4 mr-2" />
                Contact Us
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Help;
