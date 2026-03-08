import { useState } from 'react';
import { BookOpen, Search, Scale, BookOpenCheck, Gavel } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';
import { useQuery } from '@tanstack/react-query';
import { getStatutes, searchStatutes, getDefinitions, searchDefinitions, getLegalPrinciples, type Statute, type LegalDefinition, type LegalPrinciple } from '@/lib/api';

const LegalReference = () => {
  const [statuteSearch, setStatuteSearch] = useState('');
  const [defSearch, setDefSearch] = useState('');
  const [expandedStatute, setExpandedStatute] = useState<string | null>(null);

  // Statutes
  const { data: allStatutes, isLoading: statutesLoading } = useQuery({
    queryKey: ['statutes'],
    queryFn: getStatutes,
    retry: 1,
  });

  const { data: searchedStatutes, refetch: doStatuteSearch } = useQuery({
    queryKey: ['statutes-search', statuteSearch],
    queryFn: () => searchStatutes(statuteSearch),
    enabled: false,
  });

  // Definitions
  const { data: allDefinitions, isLoading: defsLoading } = useQuery({
    queryKey: ['definitions'],
    queryFn: getDefinitions,
    retry: 1,
  });

  const { data: searchedDefs, refetch: doDefSearch } = useQuery({
    queryKey: ['definitions-search', defSearch],
    queryFn: () => searchDefinitions(defSearch),
    enabled: false,
  });

  // Principles
  const { data: principles, isLoading: principlesLoading } = useQuery({
    queryKey: ['principles'],
    queryFn: getLegalPrinciples,
    retry: 1,
  });

  const displayStatutes = statuteSearch && searchedStatutes ? searchedStatutes.statutes : allStatutes ?? [];
  const displayDefs = defSearch && searchedDefs ? searchedDefs.definitions : allDefinitions ?? [];

  const handleStatuteSearch = () => {
    if (statuteSearch.trim()) doStatuteSearch();
  };

  const handleDefSearch = () => {
    if (defSearch.trim()) doDefSearch();
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 rounded-lg bg-primary/10">
          <BookOpen className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">Legal Reference</h1>
          <p className="text-muted-foreground">Browse statutes, definitions, and legal principles of Sri Lankan property law.</p>
        </div>
      </div>

      <Tabs defaultValue="statutes">
        <TabsList>
          <TabsTrigger value="statutes" className="flex items-center gap-2">
            <Scale className="h-4 w-4" /> Statutes
          </TabsTrigger>
          <TabsTrigger value="definitions" className="flex items-center gap-2">
            <BookOpenCheck className="h-4 w-4" /> Definitions
          </TabsTrigger>
          <TabsTrigger value="principles" className="flex items-center gap-2">
            <Gavel className="h-4 w-4" /> Principles
          </TabsTrigger>
        </TabsList>

        {/* Statutes Tab */}
        <TabsContent value="statutes" className="space-y-4">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search statutes (e.g., mortgage, registration)..."
                value={statuteSearch}
                onChange={(e) => setStatuteSearch(e.target.value)}
                className="pl-10"
                onKeyDown={(e) => e.key === 'Enter' && handleStatuteSearch()}
              />
            </div>
            <Button onClick={handleStatuteSearch} disabled={!statuteSearch.trim()}>Search</Button>
            {statuteSearch && (
              <Button variant="ghost" onClick={() => setStatuteSearch('')}>Clear</Button>
            )}
          </div>

          {statutesLoading ? (
            <div className="text-center py-8"><div className="animate-spin h-8 w-8 border-4 border-primary/30 border-t-primary rounded-full mx-auto" /></div>
          ) : displayStatutes.length === 0 ? (
            <Card><CardContent className="py-8 text-center text-muted-foreground">No statutes found. Connect the API to browse statutes.</CardContent></Card>
          ) : (
            <div className="space-y-3">
              {displayStatutes.map((statute, i) => (
                <Card key={i} className="cursor-pointer hover:shadow-sm transition-shadow" onClick={() => setExpandedStatute(expandedStatute === statute.statute_name ? null : statute.statute_name)}>
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-foreground">{statute.statute_name}</h3>
                          <Badge variant="secondary" className="text-xs">{statute.short_name}</Badge>
                        </div>
                        <p className="text-sm text-muted-foreground">{statute.act_number} • {statute.year}</p>
                        <p className="text-sm text-muted-foreground mt-1">{statute.description}</p>
                      </div>
                      <Badge variant="outline" className="ml-4">{statute.category}</Badge>
                    </div>

                    {expandedStatute === statute.statute_name && (
                      <div className="mt-4 pt-4 border-t space-y-3 animate-slide-up">
                        <div>
                          <p className="text-xs font-semibold text-muted-foreground mb-1">Applies to:</p>
                          <div className="flex flex-wrap gap-1">
                            {statute.applies_to.map((t, j) => (
                              <Badge key={j} variant="outline" className="text-xs">{t.replace('_', ' ')}</Badge>
                            ))}
                          </div>
                        </div>

                        {statute.key_provisions && statute.key_provisions.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-muted-foreground mb-1">Key Provisions:</p>
                            <ul className="space-y-1">
                              {statute.key_provisions.map((p, j) => (
                                <li key={j} className="text-sm text-foreground flex items-start gap-2">
                                  <span>•</span> {p}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}

                        {statute.sections && statute.sections.length > 0 && (
                          <div>
                            <p className="text-xs font-semibold text-muted-foreground mb-1">Sections:</p>
                            {statute.sections.map((s, j) => (
                              <div key={j} className="p-3 rounded-lg bg-muted/50 mb-2">
                                <p className="text-sm font-medium">{s.section}: {s.title}</p>
                                <p className="text-sm text-muted-foreground mt-1">{s.content}</p>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Definitions Tab */}
        <TabsContent value="definitions" className="space-y-4">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search definitions (e.g., mortgage, conveyance)..."
                value={defSearch}
                onChange={(e) => setDefSearch(e.target.value)}
                className="pl-10"
                onKeyDown={(e) => e.key === 'Enter' && handleDefSearch()}
              />
            </div>
            <Button onClick={handleDefSearch} disabled={!defSearch.trim()}>Search</Button>
            {defSearch && <Button variant="ghost" onClick={() => setDefSearch('')}>Clear</Button>}
          </div>

          {defsLoading ? (
            <div className="text-center py-8"><div className="animate-spin h-8 w-8 border-4 border-primary/30 border-t-primary rounded-full mx-auto" /></div>
          ) : displayDefs.length === 0 ? (
            <Card><CardContent className="py-8 text-center text-muted-foreground">No definitions found. Connect the API to browse legal definitions.</CardContent></Card>
          ) : (
            <div className="grid sm:grid-cols-2 gap-4">
              {displayDefs.map((def, i) => (
                <Card key={i}>
                  <CardContent className="p-4">
                    <h3 className="font-semibold text-foreground text-lg mb-2">{def.term}</h3>
                    <p className="text-sm text-muted-foreground mb-3">{def.definition}</p>
                    <p className="text-xs text-primary font-medium">Source: {def.source}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Principles Tab */}
        <TabsContent value="principles" className="space-y-4">
          {principlesLoading ? (
            <div className="text-center py-8"><div className="animate-spin h-8 w-8 border-4 border-primary/30 border-t-primary rounded-full mx-auto" /></div>
          ) : !principles || principles.length === 0 ? (
            <Card><CardContent className="py-8 text-center text-muted-foreground">No principles found. Connect the API to browse legal principles.</CardContent></Card>
          ) : (
            <div className="space-y-4">
              {principles.map((p, i) => (
                <Card key={i}>
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="p-3 rounded-full bg-primary/10 flex-shrink-0">
                        <Gavel className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <h3 className="font-display font-bold text-lg text-foreground italic">{p.principle_name}</h3>
                        <p className="text-sm text-primary font-medium mb-2">"{p.english_meaning}"</p>
                        <p className="text-sm text-muted-foreground mb-2">{p.description}</p>
                        <div className="p-3 rounded-lg bg-muted/50 mt-3">
                          <p className="text-xs font-semibold text-muted-foreground mb-1">Application:</p>
                          <p className="text-sm">{p.application}</p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default LegalReference;
