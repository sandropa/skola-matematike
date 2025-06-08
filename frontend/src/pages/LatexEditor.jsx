import React, { useState, useEffect, useRef, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import {
  Typography,
  Box,
  Paper,
  CircularProgress,
  Alert,
  Divider
} from '@mui/material';
import { Code } from 'lucide-react';

// Base API URL for your backend
const API_BASE_URL = "http://localhost:8000";

// 1) Define editor features in a simple array
const features = [
  {
    id: 'fix-latex',
    label: 'Fix LaTeX',
    route: '/llm/fix-latex',
    contextMenuGroupId: '1_modification',
    contextMenuOrder: 1.6,
    streaming: true,
  },
  {
    id: 'replace-with-x',
    label: 'Replace with X',
    route: '/llm/replace-with-x',
    contextMenuGroupId: '1_modification',
    contextMenuOrder: 1.5,
    streaming: true,
  },
  // Add new features here
];

// 2) Register all features on monaco editor
function registerFeatures(editor, monaco) {
  features.forEach(({ id, label, route, contextMenuGroupId, contextMenuOrder, streaming }) => {
    editor.addAction({
      id,
      label: streaming ? `${label} (Streaming)` : label,
      contextMenuGroupId,
      contextMenuOrder,
      run: async function (ed) {
        const selection = ed.getSelection();
        if (!selection || selection.isEmpty()) return;
        const model = ed.getModel();
        if (!model) return;
        const selectedText = model.getValueInRange(selection);
        if (!selectedText) return;

        ed.executeEdits(id, [{ range: selection, text: '', forceMoveMarkers: true }]);
        let position = ed.getSelection().getStartPosition();
        if (!position) return;

        let response;
        try {
          response = await fetch(`${API_BASE_URL}${route}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: selectedText }),
          });
        } catch (err) {
          console.error(`Network error for ${id}:`, err);
          return;
        }
        if (!response.ok || !response.body) {
          console.error(`Error from ${route}:`, response.status, response.statusText);
          return;
        }

        if (streaming) {
          const reader = response.body.getReader();
          const decoder = new TextDecoder();
          let done = false;
          while (!done) {
            const { value, done: readerDone } = await reader.read();
            if (readerDone) { done = true; break; }
            const chunk = decoder.decode(value, { stream: true });
            for (const char of chunk) {
              const insertRange = new monaco.Range(
                position.lineNumber,
                position.column,
                position.lineNumber,
                position.column
              );
              ed.executeEdits(id, [{ range: insertRange, text: char, forceMoveMarkers: true }]);
              position = ed.getSelection().getEndPosition();
              ed.revealPosition(position, monaco.editor.ScrollType.Smooth);
              await new Promise(res => setTimeout(res, 10));
            }
          }
        } else {
          const text = await response.text();
          const insertRange = new monaco.Range(
            position.lineNumber,
            position.column,
            position.lineNumber,
            position.column
          );
          ed.executeEdits(id, [{ range: insertRange, text, forceMoveMarkers: true }]);
        }
      }
    });
  });
}

// 3) Hook to compile LaTeX to PDF
function usePdfCompiler(editorRef) {
  const [pdfUrl, setPdfUrl] = useState(null);
  const [isLoading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const compile = useCallback(async () => {
    const editor = editorRef.current;
    if (!editor) { setError('Editor not ready'); return; }
    const code = editor.getValue();
    if (!code.trim()) { setError('LaTeX code is empty'); return; }

    setLoading(true);
    setError(null);
    if (pdfUrl) URL.revokeObjectURL(pdfUrl);

    try {
      const res = await fetch(
        `${API_BASE_URL}/problemsets/compile-latex`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'application/pdf' },
          body: JSON.stringify({ latex_code: code }),
        }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      if (blob.type !== 'application/pdf') throw new Error('Invalid PDF');
      setPdfUrl(URL.createObjectURL(blob));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [editorRef, pdfUrl]);

  useEffect(() => {
    const handler = e => {
      if ((e.ctrlKey || e.metaKey) && e.key === 's') {
        e.preventDefault();
        compile();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [compile]);

  useEffect(() => () => { if (pdfUrl) URL.revokeObjectURL(pdfUrl); }, [pdfUrl]);

  return { pdfUrl, isLoading, error };
}

// 4) Editor panel
function EditorPanel({ code, onChange, editorRef, monacoRef }) {
  const handleMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    registerFeatures(editor, monaco);
  };

  return (
    <Paper
      elevation={3}
      sx={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 2,
        mr: { xs: 0.5, sm: 1 },
        overflow: 'hidden'
      }}
    >
      <Box sx={{ p: 1, bgcolor: '#e9e9e9', display: 'flex', alignItems: 'center', borderBottom: '1px solid #ddd' }}>
        <Code size={18} style={{ marginRight: '8px' }} />
        <Typography variant="subtitle2" sx={{ fontWeight: 'medium' }}>LaTeX Source (Ctrl+S to Compile)</Typography>
      </Box>
      <Box sx={{ flexGrow: 1, position: 'relative', overflow: 'hidden' }}>
        <Editor
          height="100%"
          language="latex"
          value={code}
          onMount={handleMount}
          onChange={onChange}
          theme="vs"
          options={{ minimap: { enabled: false }, fontSize: 14, wordWrap: 'on', lineNumbers: 'on', scrollBeyondLastLine: false, automaticLayout: true, renderLineHighlight: 'gutter', tabSize: 2, insertSpaces: true }}
        />
      </Box>
    </Paper>
  );
}

// 5) Preview panel
function PreviewPanel({ pdfUrl, isLoading, error }) {
  return (
    <Paper
      elevation={3}
      sx={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        borderRadius: 2,
        ml: { xs: 0.5, sm: 1 },
        overflow: 'hidden'
      }}
    >
      <Box sx={{ flexGrow: 1, bgcolor: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', p: isLoading || error || !pdfUrl ? 2 : 0, overflow: 'hidden' }}>
        {isLoading ? (
          <Box sx={{ textAlign: 'center' }}>
            <CircularProgress />
            <Typography variant="body2" sx={{ mt: 1 }}>Compiling PDF...</Typography>
          </Box>
        ) : error ? (
          <Alert severity="error" sx={{ width: '95%', m: 'auto' }}>{error}</Alert>
        ) : pdfUrl ? (
          <iframe src={pdfUrl} title="PDF Preview" style={{ width: '100%', height: '100%', border: 'none' }} />
        ) : (
          <Typography variant="body2" color="text.secondary" align="center">Preview will appear here after compilation.<br/>Press Ctrl+S (or Cmd+S).</Typography>
        )}
      </Box>
    </Paper>
  );
}

// 6) Main component
export default function LatexEditor() {
  const [code, setCode] = useState('% Welcome to the LaTeX Editor!\n\% Edit, then Ctrl+S to compile.\n\n\\documentclass{article}\n\n\\begin{document}Hello, world!\n\n\\end{document}');
  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  const { pdfUrl, isLoading, error } = usePdfCompiler(editorRef);

  return (
    <Box sx={{ height: 'calc(100vh - 64px)', display: 'flex', p: 2, bgcolor: '#f5f5f5' }}>
      <EditorPanel code={code} onChange={v => setCode(v || '')} editorRef={editorRef} monacoRef={monacoRef} />
      <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
      <PreviewPanel pdfUrl={pdfUrl} isLoading={isLoading} error={error} />
    </Box>
  );
}
