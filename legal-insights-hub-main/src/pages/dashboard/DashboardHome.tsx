import { FileText, Brain, GitBranch, AlertTriangle, Upload, MessageSquare, BarChart3, FileSearch, ArrowUpRight, ArrowDownRight, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAuth } from '@/contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import { weeklyData } from '@/data/sampleData';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { cn } from '@/lib/utils';
import { useQuery } from '@tanstack/react-query';
import { getStats, type StatsResponse } from '@/lib/api';

const COLORS = [
  'hsl(var(--primary))',
  'hsl(var(--secondary))',
  'hsl(var(--accent))',
  'hsl(var(--success))',
  'hsl(var(--warning))',
  'hsl(var(--destructive))',
];

const StatCard = ({ 
  icon: Icon, 
  label, 
  value, 
  change, 
  changeType 
}: { 
  icon: React.ElementType; 
  label: string; 
  value: number; 
  change?: number;
  changeType?: 'up' | 'down';
}) => (
  <Card className="hover:shadow-card-hover transition-shadow duration-200">
    <CardContent className="p-6">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2.5 rounded-lg bg-primary/10">
            <Icon className="h-5 w-5 text-primary" />
          </div>
          <div>
            <p className="text-2xl font-bold text-foreground">{value}</p>
            <p className="text-sm text-muted-foreground">{label}</p>
          </div>
        </div>
        {change !== undefined && changeType && (
          <div className={cn(
            "flex items-center gap-1 text-sm font-medium px-2 py-1 rounded-full",
            changeType === 'up' ? "text-success bg-success/10" : "text-destructive bg-destructive/10"
          )}>
            {changeType === 'up' ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
            {Math.abs(change)}%
          </div>
        )}
      </div>
    </CardContent>
  </Card>
);

const DashboardHome = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  const { data: stats, isLoading } = useQuery<StatsResponse>({
    queryKey: ['stats'],
    queryFn: getStats,
    retry: 1,
    staleTime: 30000,
  });

  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 17) return 'Good Afternoon';
    return 'Good Evening';
  };

  const deedBreakdownData = stats?.deed_breakdown
    ? Object.entries(stats.deed_breakdown).map(([name, value]) => ({
        name: name.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase()),
        value,
      }))
    : [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Welcome Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-display font-bold text-foreground">
            {getGreeting()}, {user?.name.split(' ')[0]} 👋
          </h1>
          <p className="text-muted-foreground mt-1">
            Here's your legal analysis overview for today.
          </p>
        </div>
        <Button onClick={() => navigate('/dashboard/analyzer')} className="md:w-auto">
          <Upload className="h-4 w-4 mr-2" />
          Upload Document
        </Button>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {isLoading ? (
          Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="p-6">
                <div className="animate-pulse flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-muted" />
                  <div className="space-y-2">
                    <div className="h-6 w-16 bg-muted rounded" />
                    <div className="h-4 w-24 bg-muted rounded" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        ) : (
          <>
            <StatCard 
              icon={FileText} 
              label="Total Deeds" 
              value={stats?.total_deeds ?? 0} 
            />
            <StatCard 
              icon={Brain} 
              label="Total Persons" 
              value={stats?.total_persons ?? 0} 
            />
            <StatCard 
              icon={GitBranch} 
              label="Total Properties" 
              value={stats?.total_properties ?? 0} 
            />
            <StatCard 
              icon={AlertTriangle} 
              label="Districts Covered" 
              value={stats?.total_districts ?? 0} 
            />
          </>
        )}
      </div>

      {/* Main Content Grid */}
      <div className="grid lg:grid-cols-5 gap-6">
        {/* Deed Breakdown - Left 60% */}
        <Card className="lg:col-span-3">
          <CardHeader className="flex flex-row items-center justify-between pb-4">
            <CardTitle className="text-lg font-semibold">Deed Types Distribution</CardTitle>
            <Button variant="ghost" size="sm" onClick={() => navigate('/dashboard/documents')}>
              Explore Deeds
              <ArrowUpRight className="h-4 w-4 ml-1" />
            </Button>
          </CardHeader>
          <CardContent>
            {deedBreakdownData.length > 0 ? (
              <div className="flex flex-col md:flex-row items-center gap-6">
                <div className="h-[220px] w-[220px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={deedBreakdownData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={100}
                        paddingAngle={2}
                        dataKey="value"
                      >
                        {deedBreakdownData.map((_, index) => (
                          <Cell key={index} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{
                          backgroundColor: 'hsl(var(--card))',
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '8px',
                          fontSize: '12px',
                        }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex-1 space-y-2">
                  {deedBreakdownData.map((item, i) => (
                    <div key={item.name} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[i % COLORS.length] }} />
                        <span className="text-sm text-foreground">{item.name}</span>
                      </div>
                      <span className="text-sm font-semibold text-foreground">{item.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div className="h-[220px] flex items-center justify-center">
                <p className="text-muted-foreground text-sm">
                  {isLoading ? 'Loading...' : 'Connect API to see deed breakdown'}
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Actions - Right 40% */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="pb-4">
              <CardTitle className="text-lg font-semibold">Quick Actions</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button 
                className="w-full justify-start" 
                size="lg"
                onClick={() => navigate('/dashboard/reasoning')}
              >
                <MessageSquare className="h-5 w-5 mr-3" />
                Ask Legal Question
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-start" 
                size="lg"
                onClick={() => navigate('/dashboard/documents')}
              >
                <FileSearch className="h-5 w-5 mr-3" />
                Search Deeds
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-start" 
                size="lg"
                onClick={() => navigate('/dashboard/risk-detection')}
              >
                <AlertTriangle className="h-5 w-5 mr-3" />
                Check Compliance
              </Button>
              <Button 
                variant="outline" 
                className="w-full justify-start" 
                size="lg"
                onClick={() => navigate('/dashboard/legal-reference')}
              >
                <BookOpen className="h-5 w-5 mr-3" />
                Legal Reference
              </Button>
            </CardContent>
          </Card>

          {/* Additional Stats */}
          {stats && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-lg font-semibold flex items-center gap-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  Knowledge Base
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Statutes</span>
                  <span className="font-semibold">{stats.total_statutes}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Legal Definitions</span>
                  <span className="font-semibold">{stats.total_definitions}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Properties</span>
                  <span className="font-semibold">{stats.total_properties}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Districts</span>
                  <span className="font-semibold">{stats.total_districts}</span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default DashboardHome;
