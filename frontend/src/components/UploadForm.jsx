import { useState } from "react";

import { apiErrorMessage } from "../api/client";
import { useUploadContract } from "../api/hooks";

export default function UploadForm({ onReviewed }) {
  const [text, setText] = useState("");
  const [file, setFile] = useState(null);
  const upload = useUploadContract();

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!file && !text.trim()) return;
    try {
      const contract = await upload.mutateAsync({ file, text, filename: file?.name });
      setText("");
      setFile(null);
      event.target.reset();
      onReviewed?.(contract.id);
    } catch {
      // surfaced via upload.isError below
    }
  };

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <label className="upload-zone">
        <div className="icon-wrap">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 16V4M12 4l-4 4M12 4l4 4" stroke="#332404" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            <path d="M4 16v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" stroke="#332404" strokeWidth="2" strokeLinecap="round" />
          </svg>
        </div>
        <h3>{file ? file.name : "Upload a contract"}</h3>
        <p>Click to choose a file</p>
        <div className="format-row">
          <span className="format-chip">TXT</span>
          <span className="format-chip">DOCX</span>
          <span className="format-chip">PDF</span>
        </div>
        <input
          type="file"
          accept=".txt,.docx,.pdf"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          hidden
        />
      </label>

      <div className="upload-form__divider">or paste contract text</div>

      <textarea
        rows={6}
        placeholder="Paste the full contract text here..."
        value={text}
        onChange={(e) => setText(e.target.value)}
        disabled={!!file}
      />

      <button className="btn btn-primary" type="submit" disabled={upload.isPending || (!file && !text.trim())}>
        {upload.isPending ? "Reviewing..." : "Review contract"}
      </button>

      {upload.isError && <p className="form-error">{apiErrorMessage(upload.error)}</p>}
    </form>
  );
}
