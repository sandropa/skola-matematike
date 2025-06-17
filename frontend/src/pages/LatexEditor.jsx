import React, { useState, useEffect, useRef, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import {
  Typography,
  Box,
  Paper,
  CircularProgress,
  Alert,
  Divider,
  Snackbar,
  Button
} from '@mui/material';
import { Code, ImageIcon } from 'lucide-react';

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
    id: 'fix-grammar',
    label: 'Fix Grammar & Text',
    route: '/llm/fix-grammar',
    contextMenuGroupId: '1_modification',
    contextMenuOrder: 1.7,
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

// Helper function to handle image paste and upload
async function handleImagePaste(editor, monaco, file) {
  if (!file || !file.type.startsWith('image/')) {
    return false; // Not an image
  }

  const position = editor.getPosition();
  if (!position) return false;

  // Create FormData for the image upload
  const formData = new FormData();
  formData.append('file', file);

  try {
    const response = await fetch(`${API_BASE_URL}/llm/extract-latex-from-image`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok || !response.body) {
      console.error('Error from image-to-latex API:', response.status, response.statusText);
      return false;
    }

    // Stream the response character by character
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let currentPosition = position;
    let done = false;

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      if (readerDone) {
        done = true;
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      for (const char of chunk) {
        const insertRange = new monaco.Range(
          currentPosition.lineNumber,
          currentPosition.column,
          currentPosition.lineNumber,
          currentPosition.column
        );
        editor.executeEdits('image-to-latex', [{ 
          range: insertRange, 
          text: char, 
          forceMoveMarkers: true 
        }]);
        currentPosition = editor.getSelection().getEndPosition();
        editor.revealPosition(currentPosition, monaco.editor.ScrollType.Smooth);
        await new Promise(res => setTimeout(res, 25)); // Small delay for smoother typing
      }
    }

    return true; // Successfully processed
  } catch (error) {
    console.error('Network error during image-to-latex conversion:', error);
    return false;
  }
}

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
          const insertRange = new monaco.Range(
            position.lineNumber,
            position.column,
            position.lineNumber,
            position.column
          );
          ed.executeEdits(id, [{ range: insertRange, text: selectedText, forceMoveMarkers: true }]);
          return;
        }
        if (!response.ok || !response.body) {
          console.error(`Error from ${route}:`, response.status, response.statusText);
          const insertRange = new monaco.Range(
            position.lineNumber,
            position.column,
            position.lineNumber,
            position.column
          );
          ed.executeEdits(id, [{ range: insertRange, text: selectedText, forceMoveMarkers: true }]);
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
              await new Promise(res => setTimeout(res, 25));
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
      if (!res.ok) {
        let errorMsg = `HTTP ${res.status}`;
        try {
          const errorData = await res.json();
          if (errorData && errorData.detail) errorMsg = errorData.detail;
          else if (typeof errorData === 'string') errorMsg = errorData;
        } catch (e) { /* Ignore if parsing error body fails */ }
        throw new Error(errorMsg);
      }
      const blob = await res.blob();
      if (blob.type !== 'application/pdf') throw new Error('Invalid PDF received from server');
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

  return { pdfUrl, isLoading, error, compile };
}

// 4) Editor panel with image paste handling
function EditorPanel({ code, onChange, editorRef, monacoRef, onImageProcessing, problemsetId, setProblemsetId }) {
  const [isProcessingImage, setIsProcessingImage] = useState(false);
  const [saveStatus, setSaveStatus] = useState({ success: false, message: '' });

  const handleSaveDraft = async () => {
    const editor = editorRef.current;
    if (!editor) {
      setSaveStatus({ success: false, message: 'Editor not ready' });
      return;
    }

    const latexCode = editor.getValue();
    if (!latexCode.trim()) {
      setSaveStatus({ success: false, message: 'LaTeX code is empty' });
      return;
    }

    try {
      let currentProblemsetId = problemsetId;

      // Only create a new problemset if we don't have an ID in the URL
      if (!currentProblemsetId) {
        const createResponse = await fetch(`${API_BASE_URL}/problemsets`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: 'New Problemset',
            type: 'predavanje',
            part_of: 'skola matematike',
            group_name: 'pocetna'
          })
        });

        if (!createResponse.ok) {
          const errorData = await createResponse.json();
          throw new Error(errorData.detail || 'Failed to create problemset');
        }

        const newProblemset = await createResponse.json();
        currentProblemsetId = newProblemset.id;
        
        // Update the URL to include the new problemset ID
        window.history.replaceState({}, '', `/editor/${currentProblemsetId}`);
        // Update the problemsetId state
        setProblemsetId(currentProblemsetId);
      }

      // Now save the draft
      const response = await fetch(`${API_BASE_URL}/problemsets/${currentProblemsetId}/draft`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_latex: latexCode })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save draft');
      }

      setSaveStatus({ success: true, message: 'Draft saved successfully' });
    } catch (error) {
      console.error('Error saving draft:', error);
      setSaveStatus({ success: false, message: error.message || 'Failed to save draft' });
    }
  };

  const handleFinalize = async () => {
    const editor = editorRef.current;
    if (!editor) {
      setSaveStatus({ success: false, message: 'Editor not ready' });
      return;
    }

    const latexCode = editor.getValue();
    if (!latexCode.trim()) {
      setSaveStatus({ success: false, message: 'LaTeX code is empty' });
      return;
    }

    try {
      let currentProblemsetId = problemsetId;

      // Only create a new problemset if we don't have an ID in the URL
      if (!currentProblemsetId) {
        const createResponse = await fetch(`${API_BASE_URL}/problemsets`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            title: 'New Problemset',
            type: 'predavanje',
            part_of: 'skola matematike',
            group_name: 'pocetna'
          })
        });

        if (!createResponse.ok) {
          const errorData = await createResponse.json();
          throw new Error(errorData.detail || 'Failed to create problemset');
        }

        const newProblemset = await createResponse.json();
        currentProblemsetId = newProblemset.id;
        
        // Update the URL to include the new problemset ID
        window.history.replaceState({}, '', `/editor/${currentProblemsetId}`);
        // Update the problemsetId state
        setProblemsetId(currentProblemsetId);
      }

      // First save the draft
      const saveResponse = await fetch(`${API_BASE_URL}/problemsets/${currentProblemsetId}/draft`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_latex: latexCode })
      });

      if (!saveResponse.ok) {
        const errorData = await saveResponse.json();
        throw new Error(errorData.detail || 'Failed to save draft');
      }

      // Then finalize the problemset
      const finalizeResponse = await fetch(`${API_BASE_URL}/problemsets/${currentProblemsetId}/finalize`, {
        method: 'PUT'
      });

      if (!finalizeResponse.ok) {
        const errorData = await finalizeResponse.json();
        throw new Error(errorData.detail || 'Failed to finalize problemset');
      }

      setSaveStatus({ success: true, message: 'Problemset finalized successfully' });
    } catch (error) {
      console.error('Error finalizing problemset:', error);
      setSaveStatus({ success: false, message: error.message || 'Failed to finalize problemset' });
    }
  };

  const handleMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    registerFeatures(editor, monaco);

    // Add paste event listener for image handling
    editor.onDidPaste(async (e) => {
      // Check if clipboard contains files
      if (navigator.clipboard && navigator.clipboard.read) {
        try {
          const clipboardItems = await navigator.clipboard.read();
          for (const clipboardItem of clipboardItems) {
            for (const type of clipboardItem.types) {
              if (type.startsWith('image/')) {
                const blob = await clipboardItem.getType(type);
                const file = new File([blob], 'pasted-image', { type });
                
                setIsProcessingImage(true);
                onImageProcessing(true);
                
                const success = await handleImagePaste(editor, monaco, file);
                
                setIsProcessingImage(false);
                onImageProcessing(false);
                
                if (success) {
                  return; // Successfully processed, exit
                }
              }
            }
          }
        } catch (error) {
          console.error('Error reading clipboard:', error);
          setIsProcessingImage(false);
          onImageProcessing(false);
        }
      }
    });

    // Alternative: Listen for native paste events (fallback)
    const pasteHandler = async (e) => {
      if (e.clipboardData && e.clipboardData.files && e.clipboardData.files.length > 0) {
        const file = e.clipboardData.files[0];
        if (file && file.type.startsWith('image/')) {
          e.preventDefault();
          
          setIsProcessingImage(true);
          onImageProcessing(true);
          
          const success = await handleImagePaste(editor, monaco, file);
          
          setIsProcessingImage(false);
          onImageProcessing(false);
        }
      }
    };

    const editorDomNode = editor.getDomNode();
    if (editorDomNode) {
      editorDomNode.addEventListener('paste', pasteHandler);
      
      // Clean up on unmount
      return () => {
        editorDomNode.removeEventListener('paste', pasteHandler);
      };
    }
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
        overflow: 'hidden',
        position: 'relative'
      }}
    >
      <Box sx={{ p: 1, bgcolor: '#e9e9e9', display: 'flex', alignItems: 'center', borderBottom: '1px solid #ddd' }}>
        <Code size={18} style={{ marginRight: '8px' }} />
        <Typography variant="subtitle2" sx={{ fontWeight: 'medium' }}>
          LaTeX Source (Ctrl+S to Compile, Ctrl+V to paste images)
        </Typography>
        <Box sx={{ ml: 'auto', display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            size="small"
            onClick={handleSaveDraft}
            sx={{
              bgcolor: 'white',
              borderColor: 'primary.main',
              color: 'primary.main',
              '&:hover': {
                bgcolor: 'primary.main',
                color: 'white'
              }
            }}
          >
            Sačuvaj skicu
          </Button>
          <Button
            variant="outlined"
            size="small"
            onClick={handleFinalize}
            sx={{
              bgcolor: 'white',
              borderColor: 'primary.main',
              color: 'primary.main',
              '&:hover': {
                bgcolor: 'primary.main',
                color: 'white'
              }
            }}
          >
            Finaliziraj
          </Button>
        </Box>
        {isProcessingImage && (
          <Box sx={{ ml: 'auto', display: 'flex', alignItems: 'center' }}>
            <CircularProgress size={16} sx={{ mr: 1 }} />
            <Typography variant="caption" color="primary">
              Converting image...
            </Typography>
          </Box>
        )}
      </Box>
      
      {/* Processing overlay */}
      {isProcessingImage && (
        <Box
          sx={{
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            bgcolor: 'rgba(255, 255, 255, 0.8)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            flexDirection: 'column'
          }}
        >
          <CircularProgress size={48} />
          <Typography variant="body2" sx={{ mt: 2 }}>
            <ImageIcon size={16} style={{ marginRight: '8px', verticalAlign: 'middle' }} />
            Converting image to LaTeX...
          </Typography>
        </Box>
      )}
      
      <Box sx={{ flexGrow: 1, position: 'relative', overflow: 'hidden' }}>
        {code === null ? (
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
            <CircularProgress />
            <Typography sx={{ ml: 2 }}>Loading template...</Typography>
          </Box>
        ) : (
          <Editor
            height="100%"
            language="latex"
            value={code}
            onMount={handleMount}
            onChange={onChange}
            theme="vs"
            options={{
              minimap: { enabled: false },
              fontSize: 14,
              wordWrap: 'on',
              lineNumbers: 'on',
              scrollBeyondLastLine: false,
              automaticLayout: true,
              renderLineHighlight: 'gutter',
              tabSize: 2,
              insertSpaces: true,
              padding: { top: 10, bottom: 10 },
            }}
          />
        )}
      </Box>
      {saveStatus.message && (
        <Snackbar
          open={!!saveStatus.message}
          autoHideDuration={3000}
          onClose={() => setSaveStatus({ success: false, message: '' })}
        >
          <Alert severity={saveStatus.success ? 'success' : 'error'}>
            {saveStatus.message}
          </Alert>
        </Snackbar>
      )}
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
          <Alert severity="error" sx={{ width: '95%', m: 'auto' }}>Error: {error}</Alert>
        ) : pdfUrl ? (
          <iframe src={pdfUrl} title="PDF Preview" style={{ width: '100%', height: '100%', border: 'none' }} />
        ) : (
          <Typography variant="body2" color="text.secondary" align="center">
            Preview will appear here after compilation.<br/>
            Edit the LaTeX source and press Ctrl+S (or Cmd+S).<br/>
            <strong>Paste images with Ctrl+V to convert them to LaTeX!</strong>
          </Typography>
        )}
      </Box>
    </Paper>
  );
}

// 6) Main component
export default function LatexEditor() {
  const [code, setCode] = useState(null);
  const [templateError, setTemplateError] = useState(null);
  const [isProcessingImage, setIsProcessingImage] = useState(false);
  const [snackbarOpen, setSnackbarOpen] = useState(false);
  const [snackbarMessage, setSnackbarMessage] = useState('');
  const [problemsetId, setProblemsetId] = useState(null);
  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  const { pdfUrl, isLoading: isCompiling, error: compileError } = usePdfCompiler(editorRef);

  // Get problemsetId from URL
  useEffect(() => {
    const pathParts = window.location.pathname.split('/');
    const id = parseInt(pathParts[pathParts.length - 1]);
    if (!isNaN(id)) {
      setProblemsetId(id);
    }
  }, []);

  const handleImageProcessing = (processing) => {
    setIsProcessingImage(processing);
    if (processing) {
      setSnackbarMessage('Processing image... LaTeX code will appear shortly.');
      setSnackbarOpen(true);
    }
  };

  // Effect to load the template or existing problemset
  useEffect(() => {
    if (problemsetId) {
      // Load existing problemset
      fetch(`${API_BASE_URL}/problemsets/${problemsetId}`)
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} while fetching problemset.`);
          }
          return response.json();
        })
        .then(data => {
          if (data.raw_latex && data.raw_latex.trim() !== "") {
            setCode(data.raw_latex);
          } else {
            setCode(""); // Show nothing if raw_latex is empty
          }
        })
        .catch(err => {
          console.error("Failed to load problemset:", err);
          setTemplateError(err.message);
          setCode('% Welcome to the LaTeX Editor!\n% Failed to load problemset.\n\n\\documentclass{article}\n\n\\begin{document}\n\nHello, world!\n\n\\end{document}');
        });
    } else {
      // Load default template
      fetch('/latex_template.tex')
        .then(response => {
          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status} while fetching template.`);
          }
          return response.text();
        })
        .then(text => {
          setCode(text);
        })
        .catch(err => {
          console.error("Failed to load LaTeX template:", err);
          setTemplateError(err.message);
          setCode('% Welcome to the LaTeX Editor!\n% Failed to load template.\n\n\\documentclass{article}\n\n\\begin{document}\n\nHello, world!\n\n\\end{document}');
        });
    }
  }, [problemsetId]);

  if (templateError && code === null) {
    return <Alert severity="error">Failed to load LaTeX template: {templateError}</Alert>;
  }

  return (
    <Box sx={{ height: 'calc(100vh - 64px)', display: 'flex', p: 2, bgcolor: '#f5f5f5' }}>
      <EditorPanel 
        code={code} 
        onChange={v => setCode(v || '')} 
        editorRef={editorRef} 
        monacoRef={monacoRef}
        onImageProcessing={handleImageProcessing}
        problemsetId={problemsetId}
        setProblemsetId={setProblemsetId}
      />
      <Divider orientation="vertical" flexItem sx={{ mx: 1 }} />
      <PreviewPanel pdfUrl={pdfUrl} isLoading={isCompiling} error={compileError} />
      
      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000}
        onClose={() => setSnackbarOpen(false)}
        message={snackbarMessage}
      />
    </Box>
  );
}