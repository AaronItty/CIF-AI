import { useState, useEffect } from "react";
import { Upload, FileText, Trash2, CheckCircle, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

interface KBFile {
  id: string;
  name: string;
  status: "uploaded" | "processing" | "ready" | "failed";
  chunk_count: number;
  created_at: string;
}

const API_BASE = "http://localhost:8000/api/kb";

const KnowledgeBase = () => {
  const [files, setFiles] = useState<KBFile[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);

  const fetchFiles = async () => {
    try {
      const res = await fetch(`${API_BASE}/files`);
      if (!res.ok) {
        throw new Error(`HTTP error! status: ${res.status}`);
      }
      const data = await res.json();
      if (Array.isArray(data)) {
        setFiles(data);
      } else {
        console.error("API did not return an array:", data);
        setFiles([]);
      }
    } catch (error) {
      console.error("Failed to fetch files:", error);
      toast.error("Failed to load knowledge base documents");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchFiles();
    const interval = setInterval(fetchFiles, 5000); // Poll status
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
      } else {
        throw new Error("Upload failed");
      }
    } catch (error) {
      toast.error("Failed to upload document");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await fetch(`${API_BASE}/files/${id}`, { method: "DELETE" });
      setFiles(files.filter((f) => f.id !== id));
      toast.success("Document deleted");
    } catch (error) {
      toast.error("Failed to delete document");
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-foreground">Knowledge Base</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Upload domain documents that power AI policy decisions through RAG.
        </p>
      </div>

      {/* Upload Area */}
      <div className="flex items-center justify-center rounded-xl border-2 border-dashed border-border bg-card p-10 relative">
        <input
          type="file"
          className="absolute inset-0 opacity-0 cursor-pointer"
          onChange={handleFileUpload}
          disabled={isUploading}
          aria-label="Upload knowledge base files"
        />
        <div className="text-center">
          {isUploading ? (
            <Loader2 size={32} className="mx-auto text-primary animate-spin mb-3" />
          ) : (
            <Upload size={32} className="mx-auto text-muted-foreground mb-3" />
          )}
          <p className="text-sm font-medium text-foreground">Drop PDF or TXT files here</p>
          <p className="text-xs text-muted-foreground mt-1">These documents will be embedded and used for AI reasoning.</p>
          <Button className="mt-4" size="sm" disabled={isUploading}>
            <Upload size={14} className="mr-2" />
            {isUploading ? "Uploading..." : "Choose Files"}
          </Button>
        </div>
      </div>

      {/* File List */}
      <div className="rounded-xl border bg-card">
        <div className="border-b px-5 py-3">
          <h3 className="text-sm font-semibold text-foreground">Uploaded Documents ({files.length})</h3>
        </div>
        <div className="divide-y relative min-h-[100px]">
          {isLoading && files.length === 0 && (
            <div className="flex items-center justify-center p-10">
              <Loader2 className="animate-spin text-muted-foreground" />
            </div>
          )}
          {files.length === 0 && !isLoading && (
            <div className="p-10 text-center text-sm text-muted-foreground italic">
              No documents found. Upload your first document to get started.
            </div>
          )}
          {files.map((file) => (
            <div key={file.id} className="flex items-center justify-between px-5 py-3">
              <div className="flex items-center gap-3">
                <FileText size={18} className="text-primary" />
                <div>
                  <p className="text-sm font-medium text-foreground">{file.name}</p>
                  <p className="text-xs text-muted-foreground">
                    {file.chunk_count} chunks · Uploaded {new Date(file.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {file.status === "ready" ? (
                  <span className="flex items-center gap-1 text-xs font-medium text-success">
                    <CheckCircle size={12} /> Embedded
                  </span>
                ) : file.status === "failed" ? (
                  <span className="text-xs font-medium text-destructive">Failed</span>
                ) : (
                  <span className="flex items-center gap-2 text-xs font-medium text-warning">
                    <Loader2 size={12} className="animate-spin" /> Processing...
                  </span>
                )}
                <button
                  onClick={() => handleDelete(file.id)}
                  className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
                  aria-label={`Delete ${file.name}`}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};


export default KnowledgeBase;
