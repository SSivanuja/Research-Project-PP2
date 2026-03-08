import { Clock, FileText, Brain, Shield, GitBranch, Search } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { cn } from '@/lib/utils';

const historyItems = [
  {
    id: '1',
    action: 'Document analyzed',
    description: 'Sale_Deed_Colombo_2024.pdf processed successfully',
    type: 'document',
    timestamp: '2 hours ago',
  },
  {
    id: '2',
    action: 'Legal query',
    description: 'What are the requirements for a valid sale deed?',
    type: 'reasoning',
    timestamp: '3 hours ago',
  },
  {
    id: '3',
    action: 'Risk assessment',
    description: 'Risk analysis completed for Gift_Deed_Gampaha.pdf',
    type: 'risk',
    timestamp: '5 hours ago',
  },
  {
    id: '4',
    action: 'Knowledge graph updated',
    description: '3 new entities extracted and linked',
    type: 'graph',
    timestamp: 'Yesterday',
  },
  {
    id: '5',
    action: 'Document analyzed',
    description: 'Mortgage_Bond_Kandy.pdf processed with 2 risks identified',
    type: 'document',
    timestamp: 'Yesterday',
  },
  {
    id: '6',
    action: 'Legal query',
    description: 'Can foreigners own land in Sri Lanka?',
    type: 'reasoning',
    timestamp: '2 days ago',
  },
  {
    id: '7',
    action: 'Document analyzed',
    description: 'Partition_Deed_Matara.pdf processed successfully',
    type: 'document',
    timestamp: '2 days ago',
  },
];

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'document':
      return <FileText className="h-4 w-4" />;
    case 'reasoning':
      return <Brain className="h-4 w-4" />;
    case 'risk':
      return <Shield className="h-4 w-4" />;
    case 'graph':
      return <GitBranch className="h-4 w-4" />;
    default:
      return <Clock className="h-4 w-4" />;
  }
};

const getTypeColor = (type: string) => {
  switch (type) {
    case 'document':
      return 'bg-primary/10 text-primary';
    case 'reasoning':
      return 'bg-secondary/10 text-secondary';
    case 'risk':
      return 'bg-warning/10 text-warning';
    case 'graph':
      return 'bg-success/10 text-success';
    default:
      return 'bg-muted text-muted-foreground';
  }
};

const History = () => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Activity History</h1>
          <p className="text-muted-foreground">View your recent actions and analysis history</p>
        </div>
        <div className="relative max-w-xs">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input placeholder="Search history..." className="pl-10" />
        </div>
      </div>

      {/* Timeline */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Clock className="h-5 w-5 text-primary" />
            Recent Activity
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="relative">
            {/* Timeline line */}
            <div className="absolute left-5 top-0 bottom-0 w-px bg-border" />
            
            {/* Timeline items */}
            <div className="space-y-6">
              {historyItems.map((item, index) => (
                <div 
                  key={item.id}
                  className="relative flex gap-4 animate-slide-up"
                  style={{ animationDelay: `${index * 50}ms` }}
                >
                  {/* Icon */}
                  <div className={cn(
                    "relative z-10 flex h-10 w-10 items-center justify-center rounded-full",
                    getTypeColor(item.type)
                  )}>
                    {getTypeIcon(item.type)}
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 pt-1">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <p className="font-medium text-foreground">{item.action}</p>
                        <p className="text-sm text-muted-foreground mt-0.5">
                          {item.description}
                        </p>
                      </div>
                      <span className="text-xs text-muted-foreground whitespace-nowrap">
                        {item.timestamp}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default History;
