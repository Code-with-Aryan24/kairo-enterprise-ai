import { useEffect, useRef, useState } from "react";
import {
  FileText,
  Upload,
  Database,
  Search,
  ArrowRight,
} from "lucide-react";

import PageHeader from "../components/common/PageHeader";
import { uploadDocument, getDocuments } from "../services/api";

function Knowledge() {
  const fileInputRef = useRef(null);

  const [uploading, setUploading] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [loadingDocuments, setLoadingDocuments] = useState(true);
  const [uploadResult, setUploadResult] = useState(null);
  const [error, setError] = useState("");

  // Knowledge statistics are now based on real document data
  const knowledgeStats = [
    {
      label: "Documents",
      value: documents.length,
      icon: FileText,
    },
    {
      label: "Knowledge Sources",
      value: documents.length,
      icon: Database,
    },
    {
      label: "Indexed Chunks",
      value: 0,
      icon: Search,
    },
  ];

  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  // Load existing documents when the Knowledge page opens
  useEffect(() => {
    async function loadDocuments() {
      try {
        const data = await getDocuments();
        setDocuments(data.documents);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoadingDocuments(false);
      }
    }

    loadDocuments();
  }, []);

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];

    if (!file) {
      return;
    }

    setError("");
    setUploadResult(null);

    if (file.type !== "application/pdf") {
      setError("Only PDF documents are currently supported.");
      return;
    }

    try {
      setUploading(true);

      const result = await uploadDocument(file);

      setUploadResult(result);

      // Add the newly uploaded document to the current list
      setDocuments((currentDocuments) => [
        ...currentDocuments,
        result,
      ]);
    } catch (err) {
      setError(err.message);
    } finally {
      setUploading(false);
      event.target.value = "";
    }
  };

  return (
    <div className="p-4 sm:p-6 lg:p-8">
      <PageHeader
        title="Knowledge"
        description="Manage enterprise knowledge sources that power KAIRO's AI responses."
      />

      {/* Stats */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {knowledgeStats.map((stat) => {
          const Icon = stat.icon;

          return (
            <div
              key={stat.label}
              className="rounded-xl border border-slate-200 bg-white p-5"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-500">
                    {stat.label}
                  </p>

                  <p className="mt-2 text-2xl font-bold text-slate-900">
                    {stat.value}
                  </p>
                </div>

                <div className="rounded-lg bg-slate-100 p-3">
                  <Icon size={20} className="text-slate-600" />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Upload area */}
      <div className="mt-6 rounded-xl border border-dashed border-slate-300 bg-white p-8">
        <div className="flex flex-col items-center text-center">
          <div className="rounded-full bg-blue-50 p-4">
            <Upload size={24} className="text-blue-600" />
          </div>

          <h2 className="mt-4 text-lg font-semibold text-slate-900">
            Add knowledge to KAIRO
          </h2>

          <p className="mt-2 max-w-md text-sm text-slate-500">
            Upload enterprise PDF documents that KAIRO can process
            and eventually use for retrieval-augmented generation.
          </p>

          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            className="hidden"
          />

          <button
            onClick={handleUploadClick}
            disabled={uploading}
            className="mt-5 inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-medium text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {uploading ? "Uploading..." : "Upload Document"}

            {!uploading && <ArrowRight size={16} />}
          </button>

          {/* Success */}
          {uploadResult && (
            <div className="mt-5 w-full max-w-md rounded-lg border border-green-200 bg-green-50 p-4 text-left">
              <p className="text-sm font-medium text-green-800">
                Document uploaded successfully.
              </p>

              <p className="mt-1 text-sm text-green-700">
                {uploadResult.filename}
              </p>
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="mt-5 w-full max-w-md rounded-lg border border-red-200 bg-red-50 p-4 text-left">
              <p className="text-sm font-medium text-red-800">
                Upload failed
              </p>

              <p className="mt-1 text-sm text-red-700">
                {error}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Document list */}
      <div className="mt-6 rounded-xl border border-slate-200 bg-white">
        <div className="border-b border-slate-200 px-5 py-4">
          <h2 className="font-semibold text-slate-900">
            Documents
          </h2>

          <p className="mt-1 text-sm text-slate-500">
            Documents currently available to KAIRO.
          </p>
        </div>

        {loadingDocuments ? (
          <div className="p-5 text-sm text-slate-500">
            Loading documents...
          </div>
        ) : documents.length === 0 ? (
          <div className="p-5 text-sm text-slate-500">
            No documents have been uploaded yet.
          </div>
        ) : (
          <div className="divide-y divide-slate-200">
            {documents.map((document) => (
              <div
                key={document.document_id}
                className="flex items-center justify-between gap-4 px-5 py-4"
              >
                <div className="flex min-w-0 items-center gap-3">
                  <div className="rounded-lg bg-slate-100 p-2">
                    <FileText
                      size={18}
                      className="text-slate-600"
                    />
                  </div>

                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-slate-900">
                      {document.filename}
                    </p>

                    <p className="mt-1 text-xs text-slate-500">
                      PDF ·{" "}
                      {(document.size_bytes / 1024).toFixed(1)} KB
                    </p>
                  </div>
                </div>

                <span className="shrink-0 rounded-full bg-green-50 px-2.5 py-1 text-xs font-medium text-green-700">
                  Uploaded
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Knowledge;