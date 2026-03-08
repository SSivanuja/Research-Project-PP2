import { useState, useCallback } from 'react';
import { Upload, FileText, CheckCircle, Loader2, AlertCircle, Copy, Download, ExternalLink } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { extractedDeedData } from '@/data/sampleData';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';

type ProcessingStep = {
  label: string;
  status: 'pending' | 'processing' | 'complete';
};

const DocumentAnalyzer = () => {
  const { toast } = useToast();
  const [file, setFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingSteps, setProcessingSteps] = useState<ProcessingStep[]>([
    { label: 'Text extraction', status: 'pending' },
    { label: 'Language detection', status: 'pending' },
    { label: 'AI summarization', status: 'pending' },
    { label: 'Generating structured output', status: 'pending' },
  ]);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      handleFile(droppedFile);
    }
  }, []);

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      handleFile(selectedFile);
    }
  };

  const handleFile = (selectedFile: File) => {
    setFile(selectedFile);
    simulateUploadAndProcess();
  };

  const simulateUploadAndProcess = () => {
    setIsProcessing(true);
    setUploadProgress(0);
    
    // Simulate upload progress
    const uploadInterval = setInterval(() => {
      setUploadProgress(prev => {
        if (prev >= 100) {
          clearInterval(uploadInterval);
          simulateProcessing();
          return 100;
        }
        return prev + 10;
      });
    }, 150);
  };

  const simulateProcessing = () => {
    const steps = [...processingSteps];
    let currentStep = 0;

    const processStep = () => {
      if (currentStep < steps.length) {
        steps[currentStep].status = 'processing';
        setProcessingSteps([...steps]);

        setTimeout(() => {
          steps[currentStep].status = 'complete';
          setProcessingSteps([...steps]);
          currentStep++;
          
          if (currentStep < steps.length) {
            setTimeout(processStep, 500);
          } else {
            setIsProcessing(false);
            setIsComplete(true);
            toast({
              title: "Analysis Complete",
              description: "Document has been successfully analyzed.",
            });
          }
        }, 1000);
      }
    };

    setTimeout(processStep, 500);
  };

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text);
    toast({
      title: "Copied!",
      description: "Content copied to clipboard.",
    });
  };

  const resetUpload = () => {
    setFile(null);
    setIsProcessing(false);
    setIsComplete(false);
    setUploadProgress(0);
    setProcessingSteps([
      { label: 'Text extraction', status: 'pending' },
      { label: 'Language detection', status: 'pending' },
      { label: 'AI summarization', status: 'pending' },
      { label: 'Generating structured output', status: 'pending' },
    ]);
  };

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-2">
          <div className="p-2 rounded-lg bg-primary/10">
            <FileText className="h-6 w-6 text-primary" />
          </div>
          <h1 className="text-2xl font-display font-bold text-foreground">
            Legal Document Analyzer & Summariser
          </h1>
        </div>
        <p className="text-muted-foreground">
          Automatically extract key information and generate summaries from property deeds.
        </p>
      </div>

      {/* Upload Section */}
      {!isProcessing && !isComplete && (
        <Card>
          <CardContent className="p-8">
            <div
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={cn(
                "border-2 border-dashed rounded-xl p-12 text-center transition-all duration-200 cursor-pointer",
                isDragging 
                  ? "border-primary bg-primary/5" 
                  : "border-border hover:border-primary/50 hover:bg-muted/30"
              )}
            >
              <input
                type="file"
                accept=".pdf,.docx,.png,.jpg,.jpeg"
                onChange={handleFileInput}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <div className="flex flex-col items-center gap-4">
                  <div className="p-4 rounded-full bg-muted">
                    <Upload className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <div>
                    <p className="text-lg font-medium text-foreground mb-1">
                      Drag & drop your deed document here
                    </p>
                    <p className="text-muted-foreground">
                      or click to browse
                    </p>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    <p>Supports: PDF, DOCX, Images (PNG, JPG)</p>
                    <p>Maximum size: 25MB</p>
                  </div>
                  <Button variant="outline" className="mt-2">
                    Browse Files
                  </Button>
                </div>
              </label>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Processing State */}
      {isProcessing && (
        <Card>
          <CardContent className="p-8">
            <div className="space-y-6">
              {/* Upload Progress */}
              {uploadProgress < 100 && (
                <div className="space-y-3">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Uploading document...</span>
                    <span className="font-medium">{uploadProgress}%</span>
                  </div>
                  <Progress value={uploadProgress} className="h-2" />
                  <p className="text-sm text-muted-foreground">
                    {file?.name} ({(file?.size ? file.size / (1024 * 1024) : 0).toFixed(2)} MB)
                  </p>
                </div>
              )}

              {/* Processing Steps */}
              {uploadProgress >= 100 && (
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    <Loader2 className="h-5 w-5 text-primary animate-spin" />
                    <span className="font-medium text-foreground">Processing Document...</span>
                  </div>
                  
                  <div className="space-y-3 ml-2">
                    {processingSteps.map((step, index) => (
                      <div key={index} className="flex items-center gap-3">
                        <div className="w-5 h-5 flex items-center justify-center">
                          {step.status === 'complete' && (
                            <CheckCircle className="h-5 w-5 text-success" />
                          )}
                          {step.status === 'processing' && (
                            <Loader2 className="h-4 w-4 text-primary animate-spin" />
                          )}
                          {step.status === 'pending' && (
                            <div className="h-2 w-2 rounded-full bg-muted-foreground/30" />
                          )}
                        </div>
                        <span className={cn(
                          "text-sm",
                          step.status === 'complete' ? "text-foreground" : "text-muted-foreground"
                        )}>
                          {step.label}
                          {step.status === 'complete' && " complete"}
                          {step.status === 'processing' && "..."}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Results */}
      {isComplete && (
        <div className="space-y-6 animate-slide-up">
          {/* Document Info Card */}
          <Card>
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-xl bg-destructive/10">
                    <FileText className="h-8 w-8 text-destructive" />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-foreground">{file?.name || 'Sale_Deed_Colombo_2024.pdf'}</h3>
                    <div className="flex flex-wrap items-center gap-x-6 gap-y-2 mt-2 text-sm text-muted-foreground">
                      <span>Type: <strong className="text-foreground">{extractedDeedData.documentInfo.type}</strong></span>
                      <span>Date: <strong className="text-foreground">{extractedDeedData.documentInfo.date}</strong></span>
                      <span>Registry: <strong className="text-foreground">{extractedDeedData.documentInfo.registry}</strong></span>
                      <span>Code: <strong className="text-foreground">{extractedDeedData.documentInfo.code}</strong></span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-sm text-muted-foreground">Confidence:</span>
                  <span className="text-sm font-bold text-success">{extractedDeedData.documentInfo.confidence}%</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Results Tabs */}
          <Tabs defaultValue="summary" className="w-full">
            <TabsList className="grid w-full grid-cols-4 mb-6">
              <TabsTrigger value="summary">Summary</TabsTrigger>
              <TabsTrigger value="extracted">Extracted Data</TabsTrigger>
              <TabsTrigger value="original">Original Text</TabsTrigger>
              <TabsTrigger value="export">Export</TabsTrigger>
            </TabsList>

            <TabsContent value="summary">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between">
                  <CardTitle className="text-lg">AI-Generated Summary</CardTitle>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    onClick={() => handleCopy(extractedDeedData.summary)}
                  >
                    <Copy className="h-4 w-4 mr-2" />
                    Copy
                  </Button>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none text-foreground whitespace-pre-line">
                    {extractedDeedData.summary}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="extracted" className="space-y-4">
              {/* Parties */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Parties</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-3 p-4 rounded-lg bg-muted/30">
                      <h4 className="font-semibold text-foreground">Vendor</h4>
                      <div className="space-y-2 text-sm">
                        <p><span className="text-muted-foreground">Name:</span> <strong>{extractedDeedData.parties.vendor.name}</strong></p>
                        <p><span className="text-muted-foreground">NIC:</span> {extractedDeedData.parties.vendor.nic}</p>
                        <p><span className="text-muted-foreground">Address:</span> {extractedDeedData.parties.vendor.address}</p>
                      </div>
                    </div>
                    <div className="space-y-3 p-4 rounded-lg bg-muted/30">
                      <h4 className="font-semibold text-foreground">Vendee</h4>
                      <div className="space-y-2 text-sm">
                        <p><span className="text-muted-foreground">Name:</span> <strong>{extractedDeedData.parties.vendee.name}</strong></p>
                        <p><span className="text-muted-foreground">NIC:</span> {extractedDeedData.parties.vendee.nic}</p>
                        <p><span className="text-muted-foreground">Address:</span> {extractedDeedData.parties.vendee.address}</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Property Details */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Property Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid md:grid-cols-2 gap-6">
                    <div className="space-y-3">
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <p className="text-muted-foreground">Plan Number</p>
                          <p className="font-medium">{extractedDeedData.property.planNumber}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Lot Numbers</p>
                          <p className="font-medium">{extractedDeedData.property.lotNumbers}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Extent</p>
                          <p className="font-medium">{extractedDeedData.property.extent}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Assessment No</p>
                          <p className="font-medium">{extractedDeedData.property.assessmentNo}</p>
                        </div>
                      </div>
                    </div>
                    <div className="space-y-3 p-4 rounded-lg bg-muted/30">
                      <h4 className="font-semibold text-foreground text-sm">Boundaries</h4>
                      <div className="space-y-2 text-sm">
                        <p><span className="text-muted-foreground">North:</span> {extractedDeedData.property.boundaries.north}</p>
                        <p><span className="text-muted-foreground">East:</span> {extractedDeedData.property.boundaries.east}</p>
                        <p><span className="text-muted-foreground">South:</span> {extractedDeedData.property.boundaries.south}</p>
                        <p><span className="text-muted-foreground">West:</span> {extractedDeedData.property.boundaries.west}</p>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Administrative */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Administrative Details</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="text-muted-foreground">District</p>
                      <p className="font-medium">{extractedDeedData.administrative.district}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Province</p>
                      <p className="font-medium">{extractedDeedData.administrative.province}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">DS Division</p>
                      <p className="font-medium">{extractedDeedData.administrative.dsDivision}</p>
                    </div>
                    <div>
                      <p className="text-muted-foreground">Registry</p>
                      <p className="font-medium">{extractedDeedData.administrative.registry}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="original">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Original Document Text</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="p-4 bg-muted/30 rounded-lg text-sm text-muted-foreground italic">
                    <p>Original document text extraction would appear here. This includes the full OCR/parsed text from the uploaded document.</p>
                    <p className="mt-4">For demo purposes, this section shows a placeholder. In production, the actual extracted text from the PDF would be displayed here with highlighting and search capabilities.</p>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="export">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Export Options</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    <Button variant="outline" className="h-auto py-4 flex-col gap-2">
                      <Download className="h-5 w-5" />
                      <span>Download PDF Report</span>
                    </Button>
                    <Button variant="outline" className="h-auto py-4 flex-col gap-2">
                      <Download className="h-5 w-5" />
                      <span>Export as JSON</span>
                    </Button>
                    <Button variant="outline" className="h-auto py-4 flex-col gap-2">
                      <ExternalLink className="h-5 w-5" />
                      <span>Share Analysis</span>
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          {/* Reset Button */}
          <div className="flex justify-center">
            <Button variant="outline" onClick={resetUpload}>
              Analyze Another Document
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentAnalyzer;
