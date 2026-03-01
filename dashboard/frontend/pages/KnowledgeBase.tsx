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
        window.open(data.url, '_blank');
      } else {
        toast.error("Failed to generate access URL");
      }
    } catch (error) {
      toast.error("Error accessing document");
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;
    setIsSearching(true);
    try {
      const res = await fetch(`${API_BASE}/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: searchQuery, limit: 3 })
      });
      if (res.ok) {
        const data = await res.json();
        // Handle both old (array) and new (object with results) structures
        if (data && typeof data === 'object' && 'results' in data) {
          setSearchResults(data.results || []);
          setSearchMessage(data.message || null);
        } else {
          setSearchResults(Array.isArray(data) ? data : []);
          setSearchMessage(null);
        }
      }
    } catch (error) {
      toast.error("Search failed");
    } finally {
      setIsSearching(false);
    }
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
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex items-end justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">Knowledge Base</h1>
          <p className="text-sm text-muted-foreground mt-1">
            Manage your domain intelligence assets and audit RAG search retrieval.
          </p>
        </div>
        <div className="flex gap-2">
          <Badge variant="outline" className="h-6 gap-1 px-2 border-primary/20 bg-primary/5 text-primary">
            <Activity size={12} /> Live
          </Badge>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-card/50 backdrop-blur-sm border-border">
          <CardHeader className="p-4 pb-2 space-y-0 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase">Total Docs</CardTitle>
            <Database className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold">{stats?.total_documents ?? 0}</div>
            <p className="text-[10px] text-muted-foreground mt-1">Active indexed files</p>
          </CardContent>
        </Card>
        <Card className="bg-card/50 backdrop-blur-sm border-border">
          <CardHeader className="p-4 pb-2 space-y-0 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase">Total Chunks</CardTitle>
            <Hash className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold">{stats?.total_chunks ?? 0}</div>
            <p className="text-[10px] text-muted-foreground mt-1">Fragmented vectors</p>
          </CardContent>
        </Card>
        <Card className="bg-card/50 backdrop-blur-sm border-border">
          <CardHeader className="p-4 pb-2 space-y-0 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase">Avg Chunks / Doc</CardTitle>
            <Activity className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-2xl font-bold">{stats?.avg_chunks_per_doc ?? 0}</div>
            <p className="text-[10px] text-muted-foreground mt-1">Information density</p>
          </CardContent>
        </Card>
        <Card className="bg-card/50 backdrop-blur-sm border-border">
          <CardHeader className="p-4 pb-2 space-y-0 flex flex-row items-center justify-between">
            <CardTitle className="text-xs font-medium text-muted-foreground uppercase">Last Updated</CardTitle>
            <Clock className="h-4 w-4 text-primary" />
          </CardHeader>
          <CardContent className="p-4 pt-0">
            <div className="text-lg font-bold truncate">
              {safeFormatDistance(stats?.last_updated)}
            </div>
            <p className="text-[10px] text-muted-foreground mt-1">Database activity</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Upload & List */}
        <div className="lg:col-span-8 space-y-6">
          {/* Upload Area */}
          <div className="group relative flex items-center justify-center rounded-xl border-2 border-dashed border-border bg-card/50 hover:bg-card/80 transition-all p-8 text-center overflow-hidden">
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
              <div className="mx-auto w-12 h-12 rounded-full bg-secondary flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                {isUploading ? (
                  <Loader2 size={24} className="text-primary animate-spin" />
                ) : (
                  <Upload size={24} className="text-muted-foreground group-hover:text-primary transition-colors" />
                )}
              </div>
              <h3 className="text-sm font-semibold">Drop PDF or Knowledge source</h3>
              <p className="text-xs text-muted-foreground mt-1 max-w-[200px] mx-auto">
                Automatic PDF extraction, sanitization, and vector embedding.
              </p>
              <Button className="mt-4" variant="secondary" size="sm" disabled={isUploading}>
                Select Files
              </Button>
            </div>
          </div>

          {/* File List */}
          <div className="rounded-xl border bg-card/30 backdrop-blur-sm">
            <div className="border-b px-5 py-4 flex items-center justify-between">
              <h3 className="text-sm font-bold flex items-center gap-2">
                <Database size={16} className="text-primary" />
                Ingested Assets
              </h3>
              <Badge variant="outline" className="text-[10px]">{files.length} Files</Badge>
            </div>
            <div className="divide-y relative min-h-[200px]">
              {isLoading && files.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <Loader2 className="animate-spin text-primary" size={32} />
                </div>
              )}
              {files.length === 0 && !isLoading && (
                <div className="py-20 text-center">
                  <FileText size={40} className="mx-auto text-muted-foreground/20 mb-3" />
                  <p className="text-sm text-muted-foreground italic">No documents indexed yet.</p>
                </div>
              )}
              {files.map((file) => (
                <div key={file.id} className="flex items-center justify-between px-5 py-4 hover:bg-secondary/20 transition-colors">
                  <div className="flex items-start gap-4">
                    <div className="mt-1 p-2 rounded-lg bg-secondary/50 text-primary">
                      <FileText size={20} />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="text-sm font-semibold text-foreground leading-none">{file.name}</p>
                        {file.status === "ready" && (
                          <Badge className="h-4 px-1 text-[10px] bg-success/10 text-success border-success/20">Embedded</Badge>
                        )}
                        {file.status === "failed" && (
                          <Badge variant="destructive" className="h-4 px-1 text-[10px]">Failed</Badge>
                        )}
                      </div>
                      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-1">
                          <Hash size={10} /> {file.chunk_count} Chunks
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1">
                          <Database size={10} /> {formatFileSize(file.file_size_bytes)}
                        </span>
                        <span>•</span>
                        <span className="flex items-center gap-1 text-primary/80">
                          <Clock size={10} /> Uploaded {safeFormatDistance(file.uploaded_at)}
                        </span>
                        {file.status === 'ready' && file.processed_at && (
                          <>
                            <span>•</span>
                            <span className="flex items-center gap-1">
                              <Activity size={10} /> Embedded in {getProcessingTime(file.uploaded_at, file.processed_at)}
                            </span>
                          </>
                        )}
                      </div>
                      {file.last_error && (
                        <p className="mt-2 text-[10px] text-destructive flex items-start gap-1">
                          <AlertTriangle size={10} className="mt-0.5 shrink-0" />
                          {file.last_error}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {file.status === "ready" && (
                      <>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/5"
                          onClick={() => handleView(file.id)}
                          title="View document"
                        >
                          <Eye size={16} />
                        </Button>
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-muted-foreground hover:text-primary hover:bg-primary/5"
                          onClick={() => handleView(file.id)} // View usually handles download if headers permit
                          title="Download"
                        >
                          <Download size={16} />
                        </Button>
                      </>
                    )}
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive hover:bg-destructive/5"
                      onClick={() => setFileToDelete(file)}
                      aria-label="Delete document"
                    >
                      <Trash2 size={16} />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column: RAG Search Test */}
        <div className="lg:col-span-4 space-y-6">
          <Card className="bg-card/50 backdrop-blur-sm border-border sticky top-20">
            <CardHeader className="pb-3 border-b">
              <CardTitle className="text-sm font-bold flex items-center gap-2">
                <Search size={16} className="text-primary" />
                RAG Search Test
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 space-y-4">
              <div className="space-y-2">
                <p className="text-[10px] text-muted-foreground uppercase font-medium">Verify Retrieval Quality</p>
                <div className="flex gap-2">
                  <Input
                    placeholder="Ask your knowledge base..."
                    className="h-9 text-xs"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
                  />
                  <Button
                    size="sm"
                    className="h-9 px-3 shrink-0"
                    onClick={handleSearch}
                    disabled={isSearching || !searchQuery.trim()}
                  >
                    {isSearching ? <Loader2 size={14} className="animate-spin" /> : <Search size={14} />}
                  </Button>
                </div>
              </div>

              <div className="space-y-3 min-h-[100px]">
                {searchMessage && (
                  <p className="text-[10px] text-primary/80 font-medium px-1 animate-in fade-in slide-in-from-top-1">
                    {searchMessage}
                  </p>
                )}

                {searchResults.length === 0 && !isSearching && (
                  <div className="py-10 text-center px-4">
                    <Database size={24} className="mx-auto text-muted-foreground/20 mb-2" />
                    <p className="text-[10px] text-muted-foreground italic">Type a query to see what the AI retrieves from your assets.</p>
                  </div>
                )}

                {searchResults.map((result, idx) => (
                  <div key={idx} className="p-3 rounded-lg bg-secondary/30 border border-border/50 text-[11px] relative group transition-all hover:border-primary/30">
                    <div className="absolute top-2 right-2 flex gap-1">
                      <Badge variant="outline" className="text-[9px] bg-background/50 h-4 border-primary/20 text-primary">
                        {(result.similarity * 100).toFixed(0)}% Match
                      </Badge>
                    </div>
                    <p className="text-muted-foreground leading-relaxed italic line-clamp-4">
                      "{result.content}"
                    </p>
                    <div className="mt-2 text-[9px] text-primary/60 font-medium">
                      Source: Fragment {idx + 1}
                    </div>
                  </div>
                ))}
              </div>

              {searchResults.length > 0 && (
                <Button variant="ghost" size="sm" className="w-full text-[10px] h-7" onClick={() => setSearchResults([])}>
                  Clear Results
                </Button>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={!!fileToDelete} onOpenChange={() => setFileToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete <span className="font-bold text-foreground">"{fileToDelete?.name}"</span> and its {fileToDelete?.chunk_count} vector chunks. This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => fileToDelete && handleDelete(fileToDelete.id)}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete Document
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default KnowledgeBase;
