import { useState } from 'react';
import { Search, Filter, FileText, MapPin, User, Eye, ChevronLeft, ChevronRight, Compass, Clock, Scale } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import { useQuery } from '@tanstack/react-query';
import { search, getDeedDetails, getDeedsByPerson, getDeedsByDistrict, getDeedsByType, getDeedHistory, checkCompliance, type DeedDetails, type DeedSearchResult, type OwnershipChainItem, type ComplianceResponse, type SearchResponse } from '@/lib/api';

const DEED_TYPES = [
  { value: 'sale_transfer', label: 'Sale Transfer' },
  { value: 'gift', label: 'Gift' },
  { value: 'will', label: 'Will' },
  { value: 'lease', label: 'Lease' },
  { value: 'mortgage', label: 'Mortgage' },
  { value: 'partition', label: 'Partition' },
];

const DISTRICTS = [
  'Colombo', 'Gampaha', 'Kalutara', 'Kandy', 'Matale', 'Nuwara Eliya',
  'Galle', 'Matara', 'Hambantota', 'Jaffna', 'Kilinochchi', 'Mannar',
  'Mullaitivu', 'Vavuniya', 'Batticaloa', 'Ampara', 'Trincomalee',
  'Kurunegala', 'Puttalam', 'Anuradhapura', 'Polonnaruwa', 'Badulla',
  'Monaragala', 'Ratnapura', 'Kegalle',
];

const Documents = () => {
  const { toast } = useToast();
  const [searchMode, setSearchMode] = useState<'general' | 'person' | 'district' | 'type'>('general');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedDistrict, setSelectedDistrict] = useState('');
  const [selectedType, setSelectedType] = useState('');
  const [selectedDeedCode, setSelectedDeedCode] = useState<string | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // General search
  const { data: searchResults, isLoading: searchLoading, refetch: doSearch } = useQuery({
    queryKey: ['search', searchTerm],
    queryFn: () => search(searchTerm),
    enabled: false,
  });

  // Person search
  const { data: personResults, isLoading: personLoading, refetch: doPersonSearch } = useQuery({
    queryKey: ['deeds-by-person', searchTerm],
    queryFn: () => getDeedsByPerson(searchTerm),
    enabled: false,
  });

  // District search
  const { data: districtResults, isLoading: districtLoading, refetch: doDistrictSearch } = useQuery({
    queryKey: ['deeds-by-district', selectedDistrict],
    queryFn: () => getDeedsByDistrict(selectedDistrict),
    enabled: false,
  });

  // Type search
  const { data: typeResults, isLoading: typeLoading, refetch: doTypeSearch } = useQuery({
    queryKey: ['deeds-by-type', selectedType],
    queryFn: () => getDeedsByType(selectedType),
    enabled: false,
  });

  // Deed details
  const { data: deedDetails, isLoading: deedLoading } = useQuery({
    queryKey: ['deed-details', selectedDeedCode],
    queryFn: () => getDeedDetails(selectedDeedCode!),
    enabled: !!selectedDeedCode,
  });

  // Ownership history
  const { data: deedHistory } = useQuery({
    queryKey: ['deed-history', selectedDeedCode],
    queryFn: () => getDeedHistory(selectedDeedCode!),
    enabled: !!selectedDeedCode,
  });

  // Compliance
  const { data: compliance, refetch: doComplianceCheck } = useQuery({
    queryKey: ['compliance', selectedDeedCode],
    queryFn: () => checkCompliance(selectedDeedCode!),
    enabled: false,
  });

  const handleSearch = () => {
    setHasSearched(true);
    setSelectedDeedCode(null);
    switch (searchMode) {
      case 'general': doSearch(); break;
      case 'person': doPersonSearch(); break;
      case 'district': doDistrictSearch(); break;
      case 'type': doTypeSearch(); break;
    }
  };

  const handleViewDeed = (deedCode: string) => {
    setSelectedDeedCode(deedCode);
  };

  const handleCheckCompliance = () => {
    if (selectedDeedCode) doComplianceCheck();
  };

  const isLoading = searchLoading || personLoading || districtLoading || typeLoading;

  const getDeedResults = (): DeedSearchResult[] => {
    if (searchMode === 'person') return personResults?.deeds ?? [];
    if (searchMode === 'district') return districtResults?.deeds ?? [];
    if (searchMode === 'type') return typeResults?.deeds ?? [];
    return [];
  };

  const formatAmount = (amount: number) => {
    return `LKR ${amount.toLocaleString()}`;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-display font-bold text-foreground">Deed Explorer</h1>
        <p className="text-muted-foreground">Search and explore property deeds across Sri Lanka</p>
      </div>

      {/* Search Panel */}
      <Card>
        <CardContent className="p-6">
          <Tabs value={searchMode} onValueChange={(v) => { setSearchMode(v as typeof searchMode); setHasSearched(false); }}>
            <TabsList className="mb-4">
              <TabsTrigger value="general" className="flex items-center gap-2">
                <Search className="h-4 w-4" /> General
              </TabsTrigger>
              <TabsTrigger value="person" className="flex items-center gap-2">
                <User className="h-4 w-4" /> By Person
              </TabsTrigger>
              <TabsTrigger value="district" className="flex items-center gap-2">
                <MapPin className="h-4 w-4" /> By District
              </TabsTrigger>
              <TabsTrigger value="type" className="flex items-center gap-2">
                <FileText className="h-4 w-4" /> By Type
              </TabsTrigger>
            </TabsList>

            <TabsContent value="general" className="space-y-0">
              <div className="flex gap-3">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="Search deeds, persons, properties..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" onKeyDown={(e) => e.key === 'Enter' && handleSearch()} />
                </div>
                <Button onClick={handleSearch} disabled={!searchTerm.trim()}>Search</Button>
              </div>
            </TabsContent>

            <TabsContent value="person" className="space-y-0">
              <div className="flex gap-3">
                <div className="relative flex-1">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input placeholder="Enter person name (e.g., PERERA)..." value={searchTerm} onChange={(e) => setSearchTerm(e.target.value)} className="pl-10" onKeyDown={(e) => e.key === 'Enter' && handleSearch()} />
                </div>
                <Button onClick={handleSearch} disabled={!searchTerm.trim()}>Search</Button>
              </div>
            </TabsContent>

            <TabsContent value="district" className="space-y-0">
              <div className="flex gap-3">
                <Select value={selectedDistrict} onValueChange={setSelectedDistrict}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Select a district..." />
                  </SelectTrigger>
                  <SelectContent>
                    {DISTRICTS.map(d => (
                      <SelectItem key={d} value={d}>{d}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button onClick={handleSearch} disabled={!selectedDistrict}>Search</Button>
              </div>
            </TabsContent>

            <TabsContent value="type" className="space-y-0">
              <div className="flex gap-3">
                <Select value={selectedType} onValueChange={setSelectedType}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Select deed type..." />
                  </SelectTrigger>
                  <SelectContent>
                    {DEED_TYPES.map(t => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Button onClick={handleSearch} disabled={!selectedType}>Search</Button>
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Deed Detail View */}
      {selectedDeedCode && (
        <div className="space-y-4 animate-slide-up">
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={() => setSelectedDeedCode(null)}>
              <ChevronLeft className="h-4 w-4 mr-1" /> Back to results
            </Button>
          </div>

          {deedLoading ? (
            <Card><CardContent className="p-8 text-center"><div className="animate-spin h-8 w-8 border-4 border-primary/30 border-t-primary rounded-full mx-auto" /></CardContent></Card>
          ) : deedDetails ? (
            <div className="grid lg:grid-cols-3 gap-4">
              {/* Main Info */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center gap-2">
                      <FileText className="h-5 w-5 text-primary" />
                      Deed {deedDetails.deed_code}
                    </CardTitle>
                    <Badge variant="secondary">{deedDetails.deed_type.replace('_', ' ')}</Badge>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Overview */}
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground">Date</p>
                      <p className="font-medium">{deedDetails.date}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">District</p>
                      <p className="font-medium">{deedDetails.district}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Registry</p>
                      <p className="font-medium">{deedDetails.registry}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Amount</p>
                      <p className="font-medium">{formatAmount(deedDetails.amount)}</p>
                    </div>
                  </div>

                  {/* Parties */}
                  <div>
                    <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                      <User className="h-4 w-4" /> Parties
                    </h3>
                    <div className="grid sm:grid-cols-2 gap-3">
                      {deedDetails.parties.map((party, i) => (
                        <div key={i} className="p-3 rounded-lg bg-muted/50">
                          <p className="text-xs text-muted-foreground uppercase mb-1">{party.role}</p>
                          <p className="font-medium">{party.name}</p>
                          {party.nic && <p className="text-xs text-muted-foreground mt-1">NIC: {party.nic}</p>}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Property */}
                  <div>
                    <h3 className="font-semibold text-sm mb-3 flex items-center gap-2">
                      <Compass className="h-4 w-4" /> Property Details
                    </h3>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-3">
                      <div className="p-3 rounded-lg bg-muted/50">
                        <p className="text-xs text-muted-foreground">Lot</p>
                        <p className="font-medium">{deedDetails.property.lot}</p>
                      </div>
                      <div className="p-3 rounded-lg bg-muted/50">
                        <p className="text-xs text-muted-foreground">Extent</p>
                        <p className="font-medium">{deedDetails.property.extent}</p>
                      </div>
                      <div className="p-3 rounded-lg bg-muted/50">
                        <p className="text-xs text-muted-foreground">Plan No</p>
                        <p className="font-medium">{deedDetails.property.plan_no}</p>
                      </div>
                      <div className="p-3 rounded-lg bg-muted/50">
                        <p className="text-xs text-muted-foreground">Assessment</p>
                        <p className="font-medium">{deedDetails.property.assessment_no}</p>
                      </div>
                    </div>

                    {/* Boundaries */}
                    <div className="border rounded-lg overflow-hidden">
                      <div className="bg-muted/50 px-4 py-2 text-xs font-semibold text-muted-foreground">BOUNDARIES</div>
                      <div className="divide-y divide-border">
                        {Object.entries(deedDetails.property.boundaries).map(([dir, desc]) => (
                          <div key={dir} className="flex px-4 py-2">
                            <span className="text-sm font-medium w-16 capitalize">{dir}:</span>
                            <span className="text-sm text-muted-foreground">{desc}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>

                  {/* Statutes */}
                  {deedDetails.governing_statutes.length > 0 && (
                    <div>
                      <h3 className="font-semibold text-sm mb-2 flex items-center gap-2">
                        <Scale className="h-4 w-4" /> Governing Statutes
                      </h3>
                      <div className="flex flex-wrap gap-2">
                        {deedDetails.governing_statutes.map((s, i) => (
                          <Badge key={i} variant="outline">{s}</Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {deedDetails.prior_deed && (
                    <div className="p-3 rounded-lg bg-muted/50">
                      <p className="text-xs text-muted-foreground">Prior Deed Reference</p>
                      <Button variant="link" className="p-0 h-auto text-primary" onClick={() => handleViewDeed(deedDetails.prior_deed!)}>
                        {deedDetails.prior_deed}
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Side Panel */}
              <div className="space-y-4">
                {/* Actions */}
                <Card>
                  <CardContent className="p-4 space-y-3">
                    <Button className="w-full" onClick={handleCheckCompliance}>
                      <Scale className="h-4 w-4 mr-2" /> Check Compliance
                    </Button>
                  </CardContent>
                </Card>

                {/* Compliance Result */}
                {compliance && (
                  <Card className="animate-slide-up">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm">Compliance Check</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div className="text-center">
                        <p className={cn(
                          "text-3xl font-bold",
                          compliance.compliance_score >= 0.8 ? "text-success" :
                          compliance.compliance_score >= 0.6 ? "text-warning" : "text-destructive"
                        )}>
                          {Math.round(compliance.compliance_score * 100)}%
                        </p>
                        <p className="text-xs text-muted-foreground">Compliance Score</p>
                      </div>
                      <div className="space-y-1">
                        {compliance.items.map((item, i) => (
                          <div key={i} className="flex items-center gap-2 text-sm">
                            <span>{item.status === 'met' ? '✅' : '❌'}</span>
                            <span className={cn(item.status === 'not_met' && "text-destructive")}>{item.requirement}</span>
                          </div>
                        ))}
                      </div>
                      {compliance.recommendations.length > 0 && (
                        <div className="pt-2 border-t">
                          <p className="text-xs font-semibold text-muted-foreground mb-1">Recommendations:</p>
                          {compliance.recommendations.map((r, i) => (
                            <p key={i} className="text-xs text-warning">⚠️ {r}</p>
                          ))}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                )}

                {/* Ownership History */}
                {deedHistory && deedHistory.chain.length > 0 && (
                  <Card>
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center gap-2">
                        <Clock className="h-4 w-4" /> Ownership History
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {deedHistory.chain.map((item, i) => (
                          <div key={i} className="relative pl-6">
                            <div className="absolute left-0 top-1 w-3 h-3 rounded-full bg-primary" />
                            {i < deedHistory.chain.length - 1 && (
                              <div className="absolute left-[5px] top-4 w-0.5 h-full bg-border" />
                            )}
                            <div>
                              <p className="text-xs text-muted-foreground">{item.date}</p>
                              <p className="text-sm font-medium">{item.type.replace('_', ' ')}</p>
                              <div className="text-xs text-muted-foreground mt-1">
                                {item.parties.map((p, j) => (
                                  <span key={j}>{p.role}: {p.name}{j < item.parties.length - 1 ? ' → ' : ''}</span>
                                ))}
                              </div>
                              <Button variant="link" className="p-0 h-auto text-xs" onClick={() => handleViewDeed(item.deed)}>
                                {item.deed}
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          ) : (
            <Card><CardContent className="p-8 text-center text-muted-foreground">Deed not found</CardContent></Card>
          )}
        </div>
      )}

      {/* Search Results */}
      {!selectedDeedCode && hasSearched && (
        <div className="space-y-4 animate-slide-up">
          {isLoading ? (
            <Card><CardContent className="p-8 text-center"><div className="animate-spin h-8 w-8 border-4 border-primary/30 border-t-primary rounded-full mx-auto" /><p className="text-muted-foreground mt-4">Searching...</p></CardContent></Card>
          ) : (
            <>
              {/* General search results */}
              {searchMode === 'general' && searchResults && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Search Results ({searchResults.total_results})</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {searchResults.total_results === 0 ? (
                      <p className="text-muted-foreground text-center py-8">No results found for "{searchTerm}"</p>
                    ) : (
                      <div className="space-y-6">
                        {Object.entries(searchResults.results_by_type).map(([type, results]) => (
                          <div key={type}>
                            <h3 className="text-sm font-semibold text-muted-foreground mb-2">{type} ({results.length})</h3>
                            <div className="space-y-2">
                              {results.map((r, i) => (
                                <div key={i} className="flex items-center justify-between p-3 rounded-lg hover:bg-muted/50 transition-colors">
                                  <div>
                                    <p className="font-medium text-sm">{r.name}</p>
                                    {r.extra && <p className="text-xs text-muted-foreground">{r.extra}</p>}
                                  </div>
                                  {r.code && (
                                    <Button variant="outline" size="sm" onClick={() => handleViewDeed(r.code!)}>
                                      <Eye className="h-4 w-4 mr-1" /> View
                                    </Button>
                                  )}
                                </div>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}

              {/* Deed list results */}
              {searchMode !== 'general' && (
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">
                      {searchMode === 'person' && `Deeds for "${searchTerm}" (${personResults?.count ?? 0})`}
                      {searchMode === 'district' && `Deeds in ${selectedDistrict} (${districtResults?.count ?? 0})`}
                      {searchMode === 'type' && `${selectedType.replace('_', ' ')} Deeds (${typeResults?.count ?? 0})`}
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    {getDeedResults().length === 0 ? (
                      <p className="text-muted-foreground text-center py-8">No deeds found</p>
                    ) : (
                      <div className="space-y-3">
                        {getDeedResults().map((deed, i) => (
                          <div key={i} className="flex items-center justify-between p-4 rounded-lg border hover:shadow-sm transition-all cursor-pointer" onClick={() => handleViewDeed(deed.deed_code)}>
                            <div className="flex items-center gap-4">
                              <div className="p-2 rounded-lg bg-primary/10">
                                <FileText className="h-5 w-5 text-primary" />
                              </div>
                              <div>
                                <p className="font-medium">{deed.deed_code}</p>
                                <p className="text-sm text-muted-foreground">
                                  {deed.deed_type.replace('_', ' ')} • {deed.date} • {deed.district}
                                </p>
                                {deed.person && <p className="text-xs text-muted-foreground mt-1">{deed.person} ({deed.role})</p>}
                              </div>
                            </div>
                            <div className="text-right">
                              {deed.amount > 0 && <p className="font-medium text-sm">{formatAmount(deed.amount)}</p>}
                              {deed.extent && <p className="text-xs text-muted-foreground">{deed.extent}</p>}
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </div>
      )}

      {/* Empty state */}
      {!selectedDeedCode && !hasSearched && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 text-center">
            <FileText className="h-12 w-12 text-muted-foreground/50 mb-4" />
            <h3 className="text-lg font-medium text-foreground mb-2">Search Property Deeds</h3>
            <p className="text-muted-foreground max-w-md">
              Use the search panel above to find deeds by name, person, district, or type. 
              You can view deed details, check compliance, and trace ownership history.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default Documents;
