import { useCallback } from "react";
import { useDropzone } from "react-dropzone";

export default function DropzoneCard({
  onPick,
  disabled,
}: {
  onPick: (file: File) => void;
  disabled?: boolean;
}) {
  const onDrop = useCallback(
    (accepted: File[]) => {
      if (accepted?.[0]) onPick(accepted[0]);
    },
    [onPick]
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    multiple: false,
    disabled,
    maxSize: 25 * 1024 * 1024,
  });

  return (
    <div className="rounded-2xl bg-white p-5 shadow-soft">
      <div
        {...getRootProps()}
        className={[
          "cursor-pointer rounded-2xl border-2 border-dashed p-10 text-center transition",
          isDragActive ? "border-neutral-900 bg-neutral-50" : "border-neutral-200",
          disabled ? "cursor-not-allowed opacity-60" : "",
        ].join(" ")}
      >
        <input {...getInputProps()} />
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-neutral-100">
          ⬆️
        </div>
        <div className="text-sm font-semibold">
          Drag & drop your deed document here
        </div>
        <div className="mt-1 text-xs text-neutral-500">
          or click to browse • Max size 25MB
        </div>
        <div className="mt-6 inline-flex items-center justify-center rounded-xl border px-4 py-2 text-sm">
          Browse Files
        </div>
      </div>
    </div>
  );
}