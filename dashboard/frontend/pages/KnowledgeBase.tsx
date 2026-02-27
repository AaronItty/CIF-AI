import { useState } from "react";
import { Upload, FileText, Trash2, CheckCircle } from "lucide-react";
import { Button } from "@/components/ui/button";

interface KBFile {
  name: string;
  size: string;
  status: "embedded" | "processing";
  uploadedAt: string;
}

const initialFiles: KBFile[] = [
  { name: "refund-policy-v2.pdf", size: "245 KB", status: "embedded", uploadedAt: "2026-02-25" },
  { name: "shipping-guidelines.pdf", size: "180 KB", status: "embedded", uploadedAt: "2026-02-24" },
  { name: "product-catalog-2026.txt", size: "1.2 MB", status: "processing", uploadedAt: "2026-02-27" },
  { name: "faq-customer-support.pdf", size: "92 KB", status: "embedded", uploadedAt: "2026-02-20" },
];

const KnowledgeBase = () => {
  const [files, setFiles] = useState(initialFiles);

  const handleDelete = (name: string) => {
    setFiles(files.filter((f) => f.name !== name));
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
      <div className="flex items-center justify-center rounded-xl border-2 border-dashed border-border bg-card p-10">
        <div className="text-center">
          <Upload size={32} className="mx-auto text-muted-foreground mb-3" />
          <p className="text-sm font-medium text-foreground">Drop PDF or TXT files here</p>
          <p className="text-xs text-muted-foreground mt-1">These documents will be embedded and used for AI reasoning.</p>
          <Button className="mt-4" size="sm">
            <Upload size={14} className="mr-2" />
            Choose Files
          </Button>
        </div>
      </div>

      {/* File List */}
      <div className="rounded-xl border bg-card">
        <div className="border-b px-5 py-3">
          <h3 className="text-sm font-semibold text-foreground">Uploaded Documents ({files.length})</h3>
        </div>
        <div className="divide-y">
          {files.map((file) => (
            <div key={file.name} className="flex items-center justify-between px-5 py-3">
              <div className="flex items-center gap-3">
                <FileText size={18} className="text-primary" />
                <div>
                  <p className="text-sm font-medium text-foreground">{file.name}</p>
                  <p className="text-xs text-muted-foreground">{file.size} · Uploaded {file.uploadedAt}</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                {file.status === "embedded" ? (
                  <span className="flex items-center gap-1 text-xs font-medium text-success">
                    <CheckCircle size={12} /> Embedded
                  </span>
                ) : (
                  <span className="text-xs font-medium text-warning">Processing...</span>
                )}
                <button
                  onClick={() => handleDelete(file.name)}
                  className="flex h-7 w-7 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
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
