"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { UploadCloud, FileSpreadsheet, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface Props {
  onUpload: (file: File) => void;
  loading?: boolean;
}

export function DropZone({ onUpload, loading }: Props) {
  const [file, setFile] = useState<File | null>(null);

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted[0]) setFile(accepted[0]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "text/csv": [".csv"], "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"] },
    maxFiles: 1,
  });

  return (
    <div className="space-y-4">
      <div
        {...getRootProps()}
        className={cn(
          "border-2 border-dashed rounded-xl p-10 text-center cursor-pointer transition-colors",
          isDragActive
            ? "border-brand bg-brand/5"
            : "border-gray-300 hover:border-brand hover:bg-gray-50"
        )}
      >
        <input {...getInputProps()} />
        <UploadCloud className="mx-auto h-10 w-10 text-gray-400 mb-3" />
        <p className="text-sm font-medium text-gray-700">
          {isDragActive ? "Drop it here" : "Drag & drop your CSV or Excel file"}
        </p>
        <p className="text-xs text-gray-500 mt-1">or click to browse</p>
      </div>

      {file && (
        <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-gray-50 px-4 py-3">
          <div className="flex items-center gap-3">
            <FileSpreadsheet className="h-5 w-5 text-brand" />
            <div>
              <p className="text-sm font-medium text-gray-800">{file.name}</p>
              <p className="text-xs text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={() => onUpload(file)}
              disabled={loading}
            >
              {loading ? "Uploading…" : "Upload"}
            </Button>
            <button
              onClick={() => setFile(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
