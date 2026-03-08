import { useState } from 'react';
import { Shield, AlertTriangle, CheckCircle, AlertCircle, ChevronDown, ChevronUp, FileText, Download, Check, X, Scale } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { useQuery } from '@tanstack/react-query';
import { checkCompliance, getValidationChecklist, getDeedRequirements, type ComplianceResponse, type ValidationChecklist } from '@/lib/api';

const DEED_TYPES = [
  { value: 'sale_transfer', label: 'Sale Transfer' },
  { value: 'gift', label: 'Gift' },
  { value: 'will', label: 'Will' },
  { value: 'lease', label: 'Lease' },
  { value: 'mortgage', label: 'Mortgage' },
  { value: 'partition', label: 'Partition' },
];

const RiskDetection = () => {
  const { toast } = useToast();
  const [deedCode, setDeedCode] = useState('');
  const [selectedDeedType, setSelectedDeedType] = useState('');
  const [activeTab, setActiveTab] = useState<'compliance' | 'checklist'>('compliance');

  // Compliance check
  const { data: compliance, isLoading: complianceLoading, refetch: doComplianceCheck } = useQuery({
    queryKey: ['compliance-check', deedCode],
    queryFn: () => checkCompliance(deedCode),
    enabled: false,
  });

  // Validation checklist
  const { data: checklist, isLoading: checklistLoading, refetch: doChecklist } = useQuery({
    queryKey: ['validation-checklist', selectedDeedType],
    queryFn: () => getValidationChecklist(selectedDeedType),
    enabled: false,
  });

  // Deed requirements
  const { data: requirements, isLoading: reqLoading, refetch: doRequirements } = useQuery({
    queryKey: ['deed-requirements', selectedDeedType],
    queryFn: () => getDeedRequirements(selectedDeedType),
    enabled: false,
  });

  const handleComplianceCheck = () => {
    if (!deedCode.trim()) {
      toast({ title: "Enter a deed code", description: "Please provide a deed code to check compliance.", variant: "destructive" });
      return;
    }
    doComplianceCheck();
  };

  const handleChecklistLoad = () => {
    if (!selectedDeedType) {
      toast({ title: "Select a deed type", description: "Please select a deed type to view the checklist.", variant: "destructive" });
      return;
    }
    doChecklist();
    doRequirements();
  };

  const complianceScore = compliance ? Math.round(compliance.compliance_score * 100) : 0;
  const metCount = compliance?.items.filter(i => i.status === 'met').length ?? 0;
  const totalCount = compliance?.items.length ?? 0;

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 rounded-lg bg-primary/10">
          <Shield className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Compliance & Risk Detection</h1>
          <p className="text-muted-foreground">Check deed compliance and view legal requirements.</p>
        </div>
      </div>

      {/* Tab Selection */}
      <div className="flex gap-2">
        <Button variant={activeTab === 'compliance' ? 'default' : 'outline'} onClick={() => setActiveTab('compliance')}>
          <Shield className="h-4 w-4 mr-2" /> Compliance Check
        </Button>
        <Button variant={activeTab === 'checklist' ? 'default' : 'outline'} onClick={() => setActiveTab('checklist')}>
          <Scale className="h-4 w-4 mr-2" /> Requirements Checklist
        </Button>
      </div>

      {/* Compliance Check Tab */}
      {activeTab === 'compliance' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Check Deed Compliance</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-3">
                <Input
                  placeholder="Enter deed code (e.g., A 1100/188)..."
                  value={deedCode}
                  onChange={(e) => setDeedCode(e.target.value)}
                  className="flex-1"
                  onKeyDown={(e) => e.key === 'Enter' && handleComplianceCheck()}
                />
                <Button onClick={handleComplianceCheck} disabled={complianceLoading}>
                  {complianceLoading ? (
                    <><div className="h-4 w-4 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin mr-2" />Checking...</>
                  ) : (
                    <><Shield className="h-4 w-4 mr-2" />Check</>
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Compliance Results */}
          {compliance && (
            <div className="space-y-6 animate-slide-up">
              {/* Overall Score */}
              <Card>
                <CardContent className="py-8">
                  <div className="text-center space-y-4">
                    <p className="text-sm font-medium text-muted-foreground">COMPLIANCE ASSESSMENT</p>
                    <div className="flex items-center justify-center gap-4">
                      <div className={cn(
                        "text-5xl font-bold",
                        complianceScore >= 80 ? "text-success" :
                        complianceScore >= 60 ? "text-warning" : "text-destructive"
                      )}>
                        {complianceScore}%
                      </div>
                      <div className="text-left">
                        <p className="font-medium text-foreground">{compliance.deed_code}</p>
                        <p className="text-sm text-muted-foreground">{compliance.deed_type.replace('_', ' ')}</p>
                        <Badge variant={compliance.is_compliant ? "default" : "destructive"} className="mt-1">
                          {compliance.is_compliant ? '✅ Compliant' : '⚠️ Non-Compliant'}
                        </Badge>
                      </div>
                    </div>
                    <p className="text-sm text-muted-foreground">{metCount} of {totalCount} requirements met</p>
                  </div>
                </CardContent>
              </Card>

              {/* Compliance Items */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <CheckCircle className="h-5 w-5 text-success" />
                    Compliance Checklist
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {compliance.items.map((item, i) => (
                      <div key={i} className={cn(
                        "flex items-center gap-3 p-3 rounded-lg",
                        item.status === 'met' ? "bg-success/5" : "bg-destructive/5"
                      )}>
                        {item.status === 'met' ? (
                          <CheckCircle className="h-5 w-5 text-success flex-shrink-0" />
                        ) : (
                          <X className="h-5 w-5 text-destructive flex-shrink-0" />
                        )}
                        <span className={cn("text-sm", item.status === 'not_met' && "text-destructive font-medium")}>
                          {item.requirement}
                        </span>
                        {item.details && <span className="text-xs text-muted-foreground ml-auto">{item.details}</span>}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Recommendations */}
              {compliance.recommendations.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center gap-2">
                      <AlertTriangle className="h-5 w-5 text-warning" />
                      Recommendations
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      {compliance.recommendations.map((rec, i) => (
                        <div key={i} className="flex items-start gap-3 p-3 rounded-lg bg-warning/5 border border-warning/20">
                          <AlertTriangle className="h-4 w-4 text-warning flex-shrink-0 mt-0.5" />
                          <p className="text-sm">{rec}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Governing Statutes */}
              {compliance.governing_statutes.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-sm text-muted-foreground">Governing Statutes</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex flex-wrap gap-2">
                      {compliance.governing_statutes.map((s, i) => (
                        <Badge key={i} variant="outline">{s}</Badge>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
        </div>
      )}

      {/* Requirements Checklist Tab */}
      {activeTab === 'checklist' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">View Requirements by Deed Type</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-3">
                <Select value={selectedDeedType} onValueChange={setSelectedDeedType}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Select deed type..." />
                  </SelectTrigger>
                  <SelectContent>
                    {DEED_TYPES.map(t => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button onClick={handleChecklistLoad} disabled={checklistLoading || reqLoading}>
                  Load Requirements
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Requirements */}
          {requirements?.requirements && requirements.requirements.length > 0 && (
            <Card className="animate-slide-up">
              <CardHeader>
                <CardTitle className="text-lg">{requirements.requirements[0].requirement_name}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  {requirements.requirements[0].requirements.map((req, i) => (
                    <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                      <div className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center text-xs font-bold text-primary">
                        {i + 1}
                      </div>
                      <span className="text-sm">{req}</span>
                    </div>
                  ))}
                </div>
                <div className="grid sm:grid-cols-2 gap-4 pt-4 border-t">
                  <div className="p-3 rounded-lg bg-muted/50">
                    <p className="text-xs text-muted-foreground">Stamp Duty</p>
                    <p className="font-medium">{requirements.requirements[0].stamp_duty}</p>
                  </div>
                  <div className="p-3 rounded-lg bg-muted/50">
                    <p className="text-xs text-muted-foreground">Registration Fee</p>
                    <p className="font-medium">{requirements.requirements[0].registration_fee}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Validation Checklist */}
          {checklist && (
            <Card className="animate-slide-up">
              <CardHeader>
                <CardTitle className="text-lg">Validation Checklist</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Group by category */}
                {Object.entries(
                  checklist.checklist.reduce((acc, item) => {
                    if (!acc[item.category]) acc[item.category] = [];
                    acc[item.category].push(item);
                    return acc;
                  }, {} as Record<string, typeof checklist.checklist>)
                ).map(([category, items]) => (
                  <div key={category}>
                    <h3 className="text-sm font-semibold text-muted-foreground uppercase mb-2">{category.replace('_', ' ')}</h3>
                    <div className="space-y-2">
                      {items.map((item, i) => (
                        <div key={i} className="flex items-center gap-3 p-3 rounded-lg border">
                          <div className={cn(
                            "w-2 h-2 rounded-full",
                            item.mandatory ? "bg-destructive" : "bg-muted-foreground"
                          )} />
                          <span className="text-sm flex-1">{item.item}</span>
                          {item.mandatory && (
                            <Badge variant="destructive" className="text-xs">Required</Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))}

                {/* Notes */}
                {checklist.notes.length > 0 && (
                  <div className="pt-4 border-t">
                    <h3 className="text-sm font-semibold text-muted-foreground mb-2">Notes</h3>
                    <ul className="space-y-1">
                      {checklist.notes.map((note, i) => (
                        <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                          <span>•</span> {note}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

export default RiskDetection;
