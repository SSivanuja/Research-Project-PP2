import { useState, useMemo } from 'react';
import { Search, ZoomIn, ZoomOut, Filter, User, Home, FileText, Building, MapPin, X, ExternalLink, GitBranch } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { sampleGraphNodes, sampleGraphEdges, GraphNode, GraphEdge } from '@/data/sampleData';
import { cn } from '@/lib/utils';

const nodeTypeConfig = {
  PERSON: { color: 'bg-blue-500', icon: User, label: 'Person' },
  PROPERTY: { color: 'bg-green-500', icon: Home, label: 'Property' },
  DOCUMENT: { color: 'bg-yellow-500', icon: FileText, label: 'Document' },
  ORGANIZATION: { color: 'bg-red-500', icon: Building, label: 'Organization' },
  LOCATION: { color: 'bg-purple-500', icon: MapPin, label: 'Location' },
};

const edgeTypeConfig = {
  OWNS: { color: 'stroke-green-500', label: 'owns' },
  TRANSFERRED_TO: { color: 'stroke-blue-500', label: 'transferred' },
  LOCATED_IN: { color: 'stroke-purple-500', label: 'located in' },
  REFERENCES: { color: 'stroke-yellow-500', label: 'references' },
  MORTGAGED_TO: { color: 'stroke-red-500', label: 'mortgaged' },
};

const KnowledgeGraph = () => {
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [zoom, setZoom] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({
    PERSON: true,
    PROPERTY: true,
    DOCUMENT: true,
    ORGANIZATION: true,
    LOCATION: true,
  });

  const filteredNodes = useMemo(() => {
    return sampleGraphNodes.filter(node => {
      const matchesFilter = filters[node.type];
      const matchesSearch = node.label.toLowerCase().includes(searchTerm.toLowerCase());
      return matchesFilter && matchesSearch;
    });
  }, [searchTerm, filters]);

  const filteredEdges = useMemo(() => {
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    return sampleGraphEdges.filter(edge => 
      nodeIds.has(edge.from) && nodeIds.has(edge.to)
    );
  }, [filteredNodes]);

  // Simple force-directed layout simulation (positions are pre-calculated for demo)
  const nodePositions: Record<string, { x: number; y: number }> = {
    '1': { x: 200, y: 150 },
    '2': { x: 450, y: 150 },
    '3': { x: 325, y: 280 },
    '4': { x: 150, y: 350 },
    '5': { x: 500, y: 350 },
    '6': { x: 100, y: 250 },
    '7': { x: 50, y: 150 },
    '8': { x: 550, y: 250 },
  };

  const getRelatedEdges = (nodeId: string) => {
    return sampleGraphEdges.filter(e => e.from === nodeId || e.to === nodeId);
  };

  const getRelatedNodes = (nodeId: string) => {
    const edges = getRelatedEdges(nodeId);
    const relatedIds = edges.map(e => e.from === nodeId ? e.to : e.from);
    return sampleGraphNodes.filter(n => relatedIds.includes(n.id));
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center gap-3 mb-2">
        <div className="p-2 rounded-lg bg-primary/10">
          <GitBranch className="h-6 w-6 text-primary" />
        </div>
        <div>
          <h1 className="text-2xl font-display font-bold text-foreground">
            Legal Knowledge Graph
          </h1>
          <p className="text-muted-foreground">
            Visualize relationships between parties, properties, and legal documents.
          </p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search entities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>
        <Button 
          variant="outline" 
          size="icon"
          onClick={() => setShowFilters(!showFilters)}
          className={cn(showFilters && "bg-muted")}
        >
          <Filter className="h-4 w-4" />
        </Button>
        <div className="flex items-center gap-1">
          <Button 
            variant="outline" 
            size="icon"
            onClick={() => setZoom(z => Math.min(z + 0.2, 2))}
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button 
            variant="outline" 
            size="icon"
            onClick={() => setZoom(z => Math.max(z - 0.2, 0.5))}
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <Card className="animate-slide-up">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-6">
              {Object.entries(nodeTypeConfig).map(([type, config]) => (
                <div key={type} className="flex items-center space-x-2">
                  <Checkbox
                    id={`filter-${type}`}
                    checked={filters[type as keyof typeof filters]}
                    onCheckedChange={(checked) => 
                      setFilters(f => ({ ...f, [type]: checked === true }))
                    }
                  />
                  <Label 
                    htmlFor={`filter-${type}`}
                    className="flex items-center gap-2 cursor-pointer"
                  >
                    <div className={cn("w-3 h-3 rounded-full", config.color)} />
                    {config.label}
                  </Label>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <div className="grid lg:grid-cols-4 gap-4">
        {/* Graph Visualization */}
        <Card className="lg:col-span-3 overflow-hidden">
          <CardContent className="p-0">
            <div className="relative h-[500px] bg-muted/20 overflow-hidden">
              <svg 
                className="w-full h-full"
                style={{ transform: `scale(${zoom})`, transformOrigin: 'center' }}
              >
                {/* Edges */}
                {filteredEdges.map((edge) => {
                  const from = nodePositions[edge.from];
                  const to = nodePositions[edge.to];
                  if (!from || !to) return null;
                  
                  const config = edgeTypeConfig[edge.type];
                  const midX = (from.x + to.x) / 2;
                  const midY = (from.y + to.y) / 2;
                  
                  return (
                    <g key={edge.id}>
                      <line
                        x1={from.x}
                        y1={from.y}
                        x2={to.x}
                        y2={to.y}
                        className={cn("stroke-2", config.color)}
                        strokeOpacity={0.5}
                        strokeDasharray={edge.type === 'LOCATED_IN' ? "5,5" : edge.type === 'REFERENCES' ? "2,2" : undefined}
                      />
                      <text
                        x={midX}
                        y={midY - 8}
                        textAnchor="middle"
                        className="text-[10px] fill-muted-foreground"
                      >
                        {edge.label}
                      </text>
                    </g>
                  );
                })}
                
                {/* Nodes */}
                {filteredNodes.map((node) => {
                  const pos = nodePositions[node.id];
                  if (!pos) return null;
                  
                  const config = nodeTypeConfig[node.type];
                  const Icon = config.icon;
                  const isSelected = selectedNode?.id === node.id;
                  
                  return (
                    <g 
                      key={node.id} 
                      className="cursor-pointer"
                      onClick={() => setSelectedNode(isSelected ? null : node)}
                    >
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r={isSelected ? 32 : 28}
                        className={cn(
                          "transition-all duration-200",
                          isSelected 
                            ? "fill-primary stroke-primary stroke-2" 
                            : "fill-card stroke-border hover:stroke-primary"
                        )}
                        strokeWidth={2}
                      />
                      <circle
                        cx={pos.x}
                        cy={pos.y}
                        r={14}
                        className={config.color}
                      />
                      <foreignObject
                        x={pos.x - 8}
                        y={pos.y - 8}
                        width={16}
                        height={16}
                      >
                        <Icon className="h-4 w-4 text-white" />
                      </foreignObject>
                      <text
                        x={pos.x}
                        y={pos.y + 45}
                        textAnchor="middle"
                        className={cn(
                          "text-xs font-medium",
                          isSelected ? "fill-primary" : "fill-foreground"
                        )}
                      >
                        {node.label.length > 15 ? node.label.slice(0, 15) + '...' : node.label}
                      </text>
                    </g>
                  );
                })}
              </svg>
              
              {/* Empty state */}
              {filteredNodes.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <p className="text-muted-foreground">No entities match your filters</p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Details Panel */}
        <div className="space-y-4">
          {/* Selected Entity Details */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Entity Details
              </CardTitle>
            </CardHeader>
            <CardContent>
              {selectedNode ? (
                <div className="space-y-4 animate-fade-in">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={cn(
                        "w-10 h-10 rounded-full flex items-center justify-center",
                        nodeTypeConfig[selectedNode.type].color
                      )}>
                        {(() => {
                          const Icon = nodeTypeConfig[selectedNode.type].icon;
                          return <Icon className="h-5 w-5 text-white" />;
                        })()}
                      </div>
                      <div>
                        <p className="text-xs text-muted-foreground uppercase">
                          {nodeTypeConfig[selectedNode.type].label}
                        </p>
                        <p className="font-semibold text-foreground">
                          {selectedNode.label}
                        </p>
                      </div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="icon" 
                      className="h-8 w-8"
                      onClick={() => setSelectedNode(null)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  
                  {/* Data */}
                  <div className="space-y-2">
                    {Object.entries(selectedNode.data).map(([key, value]) => (
                      <div key={key} className="flex justify-between text-sm">
                        <span className="text-muted-foreground capitalize">{key}:</span>
                        <span className="font-medium text-foreground text-right">{value}</span>
                      </div>
                    ))}
                  </div>
                  
                  {/* Relationships */}
                  <div className="pt-3 border-t border-border">
                    <p className="text-xs font-medium text-muted-foreground mb-2">
                      Relationships ({getRelatedEdges(selectedNode.id).length})
                    </p>
                    <div className="space-y-2">
                      {getRelatedEdges(selectedNode.id).map(edge => {
                        const relatedNode = sampleGraphNodes.find(
                          n => n.id === (edge.from === selectedNode.id ? edge.to : edge.from)
                        );
                        return relatedNode ? (
                          <div 
                            key={edge.id}
                            className="flex items-center gap-2 text-sm cursor-pointer hover:bg-muted/50 p-2 rounded-lg -mx-2"
                            onClick={() => setSelectedNode(relatedNode)}
                          >
                            <span className="text-muted-foreground">→</span>
                            <span className="text-muted-foreground">{edge.label}:</span>
                            <span className="font-medium">{relatedNode.label}</span>
                          </div>
                        ) : null;
                      })}
                    </div>
                  </div>
                  
                  <div className="flex gap-2 pt-2">
                    <Button variant="outline" size="sm" className="flex-1">
                      View Profile
                    </Button>
                    <Button variant="outline" size="sm" className="flex-1">
                      <ExternalLink className="h-3 w-3 mr-1" />
                      Find More
                    </Button>
                  </div>
                </div>
              ) : (
                <p className="text-sm text-muted-foreground text-center py-8">
                  Click a node to view details
                </p>
              )}
            </CardContent>
          </Card>

          {/* Legend */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Legend
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {/* Node types */}
              <div className="space-y-2">
                <p className="text-xs font-medium text-muted-foreground">Entities</p>
                {Object.entries(nodeTypeConfig).map(([type, config]) => (
                  <div key={type} className="flex items-center gap-2 text-sm">
                    <div className={cn("w-3 h-3 rounded-full", config.color)} />
                    <span>{config.label}</span>
                  </div>
                ))}
              </div>
              
              {/* Edge types */}
              <div className="space-y-2 pt-2 border-t border-border">
                <p className="text-xs font-medium text-muted-foreground">Relationships</p>
                {Object.entries(edgeTypeConfig).map(([type, config]) => (
                  <div key={type} className="flex items-center gap-2 text-sm">
                    <div className={cn(
                      "w-6 h-0.5",
                      config.color.replace('stroke-', 'bg-')
                    )} />
                    <span>{config.label}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraph;
