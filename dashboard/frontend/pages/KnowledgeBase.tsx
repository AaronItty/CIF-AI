import { useState, useEffect } from "react";
import {
  Upload, FileText, Trash2, CheckCircle, Loader2, Eye, Download, Search,
  Database, Hash, Clock, AlertTriangle, ExternalLink, Activity
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
import { formatDistanceToNow } from "date-fns";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface KBFile {
  id: string;
  name: string;
  status: "uploaded" | "processing" | "ready" | "failed";
  chunk_count: number;
  uploaded_at: string;
  processed_at?: string;
  file_size_bytes?: number;
  mime_type?: string;
  last_error?: string;
}

interface KBStats {
  total_documents: number;
  total_chunks: number;
  avg_chunks_per_doc: number;
  last_updated: string | null;
}

interface SearchResult {
  content: string;
  similarity: number;
}

const API_BASE = "http://localhost:8000/api/kb";

const KnowledgeBase = () => {
  const [files, setFiles] = useState<KBFile[]>([]);
  const [stats, setStats] = useState<KBStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searchMessage, setSearchMessage] = useState<string | null>(null);
  const [isSearching, setIsSearching] = useState(false);

  // Delete Dialog State
  const [fileToDelete, setFileToDelete] = useState<KBFile | null>(null);

  const fetchFiles = async () => {
    try {
      const res = await fetch(`${API_BASE}/files`);
      if (!res.ok) throw new Error(`HTTP error! status: ${res.status}`);
      const data = await res.json();
      setFiles(Array.isArray(data) ? data : []);
    } catch (error) {
      console.error("Failed to fetch files:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/stats`);
      if (res.ok) {
        const data = await res.json();
        setStats(data);
      }
    } catch (error) {
      console.error("Failed to fetch stats:", error);
    }
  };

  useEffect(() => {
    fetchFiles();
    fetchStats();
    const interval = setInterval(() => {
      fetchFiles();
      fetchStats();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData,
      });
      if (res.ok) {
        toast.success("File uploaded successfully! Processing started.");
        fetchFiles();
        fetchStats();
      } else {
        throw new Error("Upload failed");
      }
    } catch (error) {
      toast.error("Failed to upload document");
    } finally {
      setIsUploading(false);
      // Reset input
      event.target.value = '';
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`${API_BASE}/files/${id}`, { method: "DELETE" });
      setFiles(files.filter((f) => f.id !== id));
      fetchStats();
      toast.success("Document deleted permanently");
    } catch (error) {
      toast.error("Failed to delete document");
    } finally {
      setFileToDelete(null);
    }
  };

  const handleView = async (id: string) => {
    try {
      const res = await fetch(`${API_BASE}/view/${id}`);
      if (res.ok) {
        const data = await res.json();
        // Open in new tab for viewing
        window.open(data.url, '_blank', 'noopener,noreferrer');
      } else {
        const err = await res.json();
        toast.error(`View failed: ${err.detail || "Unknown error"}`);
      }
    } catch (error) {
      toast.error("Error accessing document");
    }
  };

  const handleDownload = async (id: string, fileName: string) => {
    try {
      const res = await fetch(`${API_BASE}/view/${id}`);
      if (res.ok) {
        const data = await res.json();
        // Create hidden link to force download
        const link = document.createElement('a');
        link.href = data.url;
        link.setAttribute('download', fileName);
        link.setAttribute('target', '_blank');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        toast.success("Download started");
      } else {
        const err = await res.json();
        toast.error(`Download failed: ${err.detail || "Unknown error"}`);
      }
    } catch (error) {
      toast.error("Error preparing download");
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    setSearchResults([]);
    setSearchMessage("Analyzing knowledge base...");

    try {
      const res = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery, limit: 2 })
      });
      if (res.ok) {
        const data = await res.json();
        let results: SearchResult[] = [];
        let message = "";

        if (data && typeof data === 'object' && 'results' in data) {
          results = (data.results || []) as SearchResult[];
          message = data.message || "";
        } else {
          results = (Array.isArray(data) ? data : []) as SearchResult[];
        }

        setSearchResults(results);

        if (results.length === 0) {
          setSearchMessage("No Direct Policy Found");
        } else if (results[0].similarity < 0.6) {
          setSearchMessage("⚠️ Low Confidence Matches Found");
        } else {
          setSearchMessage(`${results.length} Relevant Knowledge Fragments Found`);
        }
      }
    } catch (error) {
      toast.error("Search failed");
      setSearchMessage(null);
    } finally {
      setIsSearching(false);
    }
  };

  const highlightText = (text: string, query: string) => {
    if (!query.trim()) return text;
    const words = query.trim().split(/\s+/).filter(w => w.length > 2);
    if (words.length === 0) return text;

    const pattern = new RegExp(`(${words.join('|')})`, 'gi');
    const parts = text.split(pattern);

    return parts.map((part, i) =>
      pattern.test(part) ? (
        <span key={i} className="bg-primary/20 text-primary font-bold px-0.5 rounded transition-colors group-hover:bg-primary/30">
          {part}
        </span>
      ) : part
    );
  };

  const getConfidenceLevel = (similarity: number) => {
    if (similarity >= 0.75) return { label: "High Confidence", color: "text-success", bg: "bg-success/10", border: "border-success/30", bar: "bg-success" };
    if (similarity >= 0.60) return { label: "Medium Confidence", color: "text-primary", bg: "bg-primary/10", border: "border-primary/30", bar: "bg-primary" };
    return { label: "Low Confidence", color: "text-warning", bg: "bg-warning/10", border: "border-warning/30", bar: "bg-warning" };
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "0 B";
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const safeFormatDistance = (dateStr?: string | null) => {
    if (!dateStr) return "Never";
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) return "Invalid date";
    try {
      return formatDistanceToNow(date, { addSuffix: true });
    } catch (e) {
      return "Invalid date";
    }
  };

  const getProcessingTime = (uploaded: string, processed?: string) => {
    if (!processed || !uploaded) return null;
    const upDate = new Date(uploaded);
    const procDate = new Date(processed);
    if (isNaN(upDate.getTime()) || isNaN(procDate.getTime())) return null;
    const diff = (procDate.getTime() - upDate.getTime()) / 1000;
    return diff.toFixed(1) + "s";
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-20">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-3xl font-black tracking-tight text-foreground flex items-center gap-2">
            Intelligence <span className="text-primary">Base</span>
          </h1>
          <p className="text-sm text-muted-foreground mt-1 font-medium">
            Manage your agent's domain knowledge and audit semantic retrieval quality.
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="h-7 gap-1 px-3 border-primary/30 bg-primary/5 text-primary text-xs font-bold animate-pulse">
            <Activity size={12} /> Live Engine
          </Badge>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-card/40 backdrop-blur-md border-border/60 shadow-sm transition-all hover:border-primary/30">
          <CardHeader className="p-4 pb-2 space-y-0 flex flex-row items-center justify-between">
            <CardTitle className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Total Docs</CardTitle>
            <Database className="h-4 w-4 text-primary opacity-70" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-3xl font-black">{stats?.total_documents ?? 0}</div>
            <p className="text-xs text-muted-foreground mt-1 font-medium italic">Active internal assets</p>
          </CardContent>
        </Card>
        <Card className="bg-card/40 backdrop-blur-md border-border/60 shadow-sm transition-all hover:border-primary/30">
          <CardHeader className="p-4 pb-2 space-y-0 flex flex-row items-center justify-between">
            <CardTitle className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Total Chunks</CardTitle>
            <Hash className="h-4 w-4 text-primary opacity-70" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-3xl font-black">{stats?.total_chunks ?? 0}</div>
            <p className="text-xs text-muted-foreground mt-1 font-medium italic">Vector fragments</p>
          </CardContent>
        </Card>
        <Card className="bg-card/40 backdrop-blur-md border-border/60 shadow-sm transition-all hover:border-primary/30">
          <CardHeader className="p-4 pb-2 space-y-0 flex flex-row items-center justify-between">
            <CardTitle className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Avg Density</CardTitle>
            <Activity className="h-4 w-4 text-primary opacity-70" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-3xl font-black">{stats?.avg_chunks_per_doc ?? 0}</div>
            <p className="text-xs text-muted-foreground mt-1 font-medium italic">Fragments per doc</p>
          </CardContent>
        </Card>
        <Card className="bg-card/40 backdrop-blur-md border-border/60 shadow-sm transition-all hover:border-primary/30">
          <CardHeader className="p-4 pb-2 space-y-0 flex flex-row items-center justify-between">
            <CardTitle className="text-[10px] font-bold text-muted-foreground uppercase tracking-widest">Last Update</CardTitle>
            <Clock className="h-4 w-4 text-primary opacity-70" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-xl font-black truncate leading-tight">
              {safeFormatDistance(stats?.last_updated)}
            </div>
            <p className="text-xs text-muted-foreground mt-1 font-medium italic">Sync status</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Upload & List */}
        <div className="lg:col-span-7 space-y-6">
          {/* Upload Area */}
          <div className="group relative flex items-center justify-center rounded-2xl border-2 border-dashed border-border/80 bg-card/30 hover:bg-card/60 transition-all p-8 text-center overflow-hidden">
            <input
              id="kb-file-upload"
              type="file"
              className="absolute inset-0 opacity-0 cursor-pointer z-10"
              onChange={handleFileUpload}
              disabled={isUploading}
              accept=".pdf,.txt"
              title="Upload PDF or Knowledge source"
            />
            <div className="relative z-0">
              <div className="mx-auto w-14 h-14 rounded-2xl bg-secondary/50 flex items-center justify-center mb-4 group-hover:scale-110 group-hover:bg-primary/10 transition-all border border-transparent group-hover:border-primary/20">
                {isUploading ? (
                  <Loader2 size={24} className="text-primary animate-spin" />
                ) : (
                  <Upload size={24} className="text-muted-foreground group-hover:text-primary transition-colors" />
                )}
              </div>
              <h3 className="text-lg font-bold">Import Domain Knowledge</h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-[280px] mx-auto font-medium">
                Automatic processing, semantic chunking, and vector indexing for RAG operations.
              </p>
              <Button className="mt-5 font-bold px-6" variant="secondary" size="sm" disabled={isUploading}>
                Select Files
              </Button>
            </div>
          </div>

          {/* File List */}
          <div className="rounded-2xl border bg-card/20 backdrop-blur-sm overflow-hidden">
            <div className="border-b px-6 py-4 flex items-center justify-between bg-muted/30">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <FileText size={16} className="text-primary" />
                Knowledge Inventory
              </h3>
              <Badge variant="outline" className="text-[10px] font-bold px-2">{files.length} Assets</Badge>
            </div>
            <div className="divide-y relative min-h-[300px]">
              {isLoading && files.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="flex flex-col items-center gap-3">
                    <Loader2 className="animate-spin text-primary" size={40} />
                    <p className="text-xs font-bold text-muted-foreground animate-pulse uppercase tracking-widest">Accessing Vault...</p>
                  </div>
                </div>
              )}
              {files.length === 0 && !isLoading && (
                <div className="py-24 text-center">
                  <div className="w-16 h-16 bg-muted/50 rounded-full flex items-center justify-center mx-auto mb-4">
                    <FileText size={32} className="text-muted-foreground/30" />
                  </div>
                  <p className="text-sm text-muted-foreground font-medium italic">No intelligence assets indexed yet.</p>
                </div>
              )}
              {files.map((file) => (
                <div key={file.id} className="flex items-center justify-between px-6 py-5 hover:bg-muted/50 transition-all group">
                  <div className="flex items-start gap-4">
                    <div className="mt-0.5 p-2.5 rounded-xl bg-secondary/80 text-primary group-hover:bg-primary group-hover:text-primary-foreground transition-all shadow-sm">
                      <FileText size={20} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-base font-bold text-foreground leading-tight tracking-tight">{file.name}</p>
                        {file.status === "ready" && (
                          <Badge className="h-5 px-2 text-[10px] bg-success/10 text-success border-success/30 font-bold uppercase">Ready</Badge>
                        )}
                        {file.status === "processing" && (
                          <Badge className="h-5 px-2 text-[10px] bg-primary/10 text-primary border-primary/30 font-bold uppercase animate-pulse">Processing</Badge>
                        )}
                        {file.status === "failed" && (
                          <Badge className="h-5 px-2 text-[10px] bg-destructive/10 text-destructive border-destructive/30 font-bold uppercase">Failed</Badge>
                        )}
                      </div>
                      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground font-semibold">
                        <span className="flex items-center gap-1.5 opacity-80">
                          <Hash size={12} className="text-primary/60" /> {file.chunk_count} Sections
                        </span>
                        <span className="opacity-40">•</span>
                        <span className="flex items-center gap-1.5 opacity-80">
                          <Database size={12} className="text-primary/60" /> {formatFileSize(file.file_size_bytes)}
                        </span>
                        <span className="opacity-40">•</span>
                        <span className="flex items-center gap-1.5 text-primary/70">
                          <Clock size={12} /> {safeFormatDistance(file.uploaded_at)}
                        </span>
                        {file.status === 'ready' && file.processed_at && (
                          <>
                            <span className="opacity-40">•</span>
                            <span className="flex items-center gap-1.5 text-success/80">
                              <Activity size={12} /> {getProcessingTime(file.uploaded_at, file.processed_at)} prep
                            </span>
                          </>
                        )}
                      </div>
                      {file.last_error && (
                        <div className="mt-3 p-2 rounded-lg bg-destructive/5 border border-destructive/20 text-[11px] text-destructive flex items-start gap-2 font-bold max-w-md">
                          <AlertTriangle size={14} className="shrink-0" />
                          {file.last_error}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
                    {file.status === "ready" && (
                      <>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-10 w-10 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-xl"
                          onClick={() => handleView(file.id)}
                        >
                          <Eye size={18} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-10 w-10 text-muted-foreground hover:text-primary hover:bg-primary/10 rounded-xl"
                          onClick={() => handleDownload(file.id, file.name)}
                        >
                          <Download size={18} />
                        </Button>
                      </>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-10 w-10 text-muted-foreground hover:text-destructive hover:bg-destructive/10 rounded-xl"
                      onClick={() => setFileToDelete(file)}
                    >
                      <Trash2 size={18} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: RAG Search Test */}
        <div className="lg:col-span-5 space-y-6">
          <Card className="bg-card/40 backdrop-blur-md border-border/80 shadow-lg sticky top-24 overflow-hidden border-2">
            <div className="h-1 w-full bg-gradient-to-r from-primary/50 via-primary to-primary/50" />
            <CardHeader className="pb-4 border-b bg-muted/10">
              <CardTitle className="text-base font-black flex items-center gap-2.5">
                <Search size={20} className="text-primary animate-pulse" />
                Semantic Retrieval Audit
              </CardTitle>
              <p className="text-xs text-muted-foreground font-medium">Test exactly what the AI will find from your base.</p>
            </CardHeader>
            <CardContent className="p-5 space-y-6">
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="text-[10px] text-muted-foreground uppercase font-black tracking-widest">Query Intelligence</p>
                  {isSearching && (
                    <Badge variant="outline" className="text-[10px] h-5 border-primary/40 text-primary animate-pulse font-bold">
                      Ranking Results...
                    </Badge>
                  )}
                </div>
                <div className="flex gap-2 relative">
                  <Input
                    placeholder="Search your domain brain..."
                    className="h-11 text-sm bg-background/50 border-border/80 focus:border-primary/50 focus:ring-primary/20 transition-all font-medium pr-12"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  />
                  <Button
                    size="icon"
                    className="absolute right-1 top-1 h-9 w-9 bg-primary hover:bg-primary/90 shadow-md shadow-primary/20 rounded-lg group"
                    onClick={handleSearch}
                    disabled={isSearching || !searchQuery.trim()}
                  >
                    {isSearching ? <Loader2 size={18} className="animate-spin" /> : <Search size={18} className="group-hover:scale-110 transition-transform" />}
                  </Button>
                </div>
              </div>

              <div className="space-y-4 min-h-[300px]">
                {searchMessage && (
                  <div className="flex items-center gap-2 px-1">
                    {isSearching ? (
                      <Loader2 size={14} className="text-primary animate-spin" />
                    ) : (
                      <div className="h-1.5 w-1.5 rounded-full bg-primary animate-pulse" />
                    )}
                    <p className="text-xs text-primary font-black uppercase tracking-widest">
                      {searchMessage}
                    </p>
                  </div>
                )}

                {searchResults.length === 0 && !isSearching && (
                  <div className="py-20 text-center px-8 border border-dashed border-border/50 rounded-2xl bg-muted/5">
                    <div className="w-16 h-16 bg-muted/20 rounded-3xl flex items-center justify-center mx-auto mb-5">
                      <Database size={32} className="text-muted-foreground/20" />
                    </div>
                    <h4 className="text-sm font-bold text-foreground/80">Search Engine Idle</h4>
                    <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                      Enter a scenario (e.g., "damaged cookie refund") to verify retrieval precision.
                    </p>
                  </div>
                )}

                {searchResults.map((result, idx) => {
                  const conf = getConfidenceLevel(result.similarity);
                  return (
                    <div key={idx} className="group relative bg-card/60 border border-border/80 rounded-2xl overflow-hidden transition-all hover:border-primary/40 hover:shadow-xl hover:-translate-y-1 duration-300">
                      <div className={`h-1.5 w-full ${conf.bar} opacity-70`} />
                      <div className="p-5">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className={`h-6 text-[10px] font-black uppercase tracking-wider ${conf.bg} ${conf.color} ${conf.border}`}>
                              {conf.label}
                            </Badge>
                            <span className={`text-xs font-black ${conf.color}`}>
                              {(result.similarity * 100).toFixed(0)}%
                            </span>
                          </div>
                          <div className="h-8 w-8 rounded-full bg-muted/50 flex items-center justify-center text-[10px] font-black group-hover:bg-primary group-hover:text-primary-foreground transition-all">
                            #{idx + 1}
                          </div>
                        </div>

                        <div className="space-y-3">
                          <div className="text-[11px] font-black text-muted-foreground uppercase tracking-widest flex items-center gap-2">
                            <span className="h-1 w-4 bg-primary/30 rounded-full" />
                            Retrieved Context
                          </div>
                          <p className="text-[13px] text-foreground/90 leading-relaxed font-semibold whitespace-pre-wrap">
                            {highlightText(result.content, searchQuery)}
                          </p>
                        </div>

                        <div className="mt-5 pt-4 border-t border-border/40 flex items-center justify-between">
                          <div className="flex items-center gap-1.5">
                            <div className="h-6 w-6 rounded-lg bg-muted flex items-center justify-center group-hover:bg-primary/10 transition-colors">
                              <FileText size={12} className="text-muted-foreground group-hover:text-primary" />
                            </div>
                            <span className="text-[11px] text-muted-foreground font-black uppercase tracking-tight truncate max-w-[150px]">
                              Internal Fragment
                            </span>
                          </div>
                          <Button variant="ghost" size="sm" className="h-7 text-[10px] font-black uppercase tracking-tighter hover:text-primary">
                            Visualise Context <ExternalLink size={10} className="ml-1" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>

              {searchResults.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full text-xs font-black h-10 border-border/60 text-muted-foreground hover:text-primary hover:bg-primary/5 hover:border-primary/20 rounded-xl transition-all"
                  onClick={() => {
                    setSearchResults([]);
                    setSearchMessage(null);
                  }}
                >
                  Terminate Audit
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!fileToDelete} onOpenChange={() => setFileToDelete(null)}>
        <AlertDialogContent className="rounded-2xl border-2">
          <AlertDialogHeader>
            <AlertDialogTitle className="text-xl font-black">Permanent Data Destruction?</AlertDialogTitle>
            <AlertDialogDescription className="text-sm font-medium">
              You are about to purge <span className="font-black text-foreground">"{fileToDelete?.name}"</span> and its entire vector footprint ({fileToDelete?.chunk_count} semantic chunks) from the intelligence base.
              <br /><br />
              <span className="text-destructive font-black uppercase tracking-widest text-xs">Internal memory will be wiped immediately.</span>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter className="mt-4">
            <AlertDialogCancel className="rounded-xl font-bold">Retain Data</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => fileToDelete && handleDelete(fileToDelete.id)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90 rounded-xl font-black"
            >
              Confirm Purge
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default KnowledgeBase;
