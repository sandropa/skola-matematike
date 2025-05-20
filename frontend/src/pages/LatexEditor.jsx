import { useState, useEffect, useRef, useCallback } from 'react';
import Editor from '@monaco-editor/react'; // No need to import Monaco separately if using @monaco-editor/react >= v4
import {
    Typography,
    Box,
    Paper,
    CircularProgress,
    Alert,
    Divider
} from '@mui/material';
import {
    Code,
    // FileText, // Not used in the modified preview panel header
} from 'lucide-react';

const API_BASE_URL = "http://localhost:8000";

export default function LatexEditor() {
    const [latexCode, setLatexCode] = useState(
        "% Welcome to the LaTeX Editor!\n" +
        "% Select some text, right-click, and choose 'Replace with X (Streaming)'\n" +
        "\\documentclass[11pt,a4paper]{article}\n" +
        "\\usepackage[utf8]{inputenc}\n" +
        "\\usepackage[T1]{fontenc}\n" +
        "\\usepackage{amsmath, amssymb, amsfonts}\n" +
        "\\usepackage[margin=2.5cm]{geometry}\n" +
        "\\usepackage{palatino}\n" +
        "\\linespread{1.1}\n\n" +
        "\\title{\\bfseries\\LARGE My Awesome Document}\n" +
        "\\author{Your Name}\n" +
        "\\date{\\today}\n\n" +
        "\\begin{document}\n\n" +
        "\\maketitle\n" +
        "\\thispagestyle{empty}\n" +
        "\\clearpage\n" +
        "\\pagenumbering{arabic}\n\n" +
        "\\section{Introduction}\n" +
        "Hello, world! This is a sample LaTeX document. You can edit this code and press " +
        "Ctrl+S (or Cmd+S on Mac) to compile and see the PDF preview on the right.\n\n" +
        "Let's try some math: $E = mc^2$.\n\n" +
        "\\begin{itemize}\n" +
        "    \\item Item 1\n" +
        "    \\item Item 2\n" +
        "\\end{itemize}\n\n" +
        "\\end{document}"
    );
    const editorRef = useRef(null);
    const monacoRef = useRef(null); // To store the monaco instance for utilities like Range

    const [pdfUrl, setPdfUrl] = useState(null);
    const [isLoadingPdf, setIsLoadingPdf] = useState(false);
    const [pdfError, setPdfError] = useState(null);

    const handleEditorDidMount = (editor, monaco) => {
        editorRef.current = editor;
        monacoRef.current = monaco; // Store monaco instance

        // --- Add custom action to context menu ---
        editor.addAction({
            id: 'replace-with-x-streaming',
            label: 'Replace with X (Streaming)',
            // keybindings: [monaco.KeyMod.CtrlCmd | monaco.KeyCode.KEY_K], // Optional: Define keybindings
            contextMenuGroupId: '1_modification', // Group in context menu (e.g., 'navigation', '1_modification')
            contextMenuOrder: 1.5, // Order within the group (lower numbers appear first)
            
            // The function that will be executed when the action is triggered
            run: async function (ed) {
                const currentMonacoInstance = monacoRef.current;
                if (!currentMonacoInstance) {
                    console.error("Monaco instance not available for action.");
                    return;
                }

                const selection = ed.getSelection();
                if (!selection || selection.isEmpty()) {
                    // You could show a small notification using a snackbar or alert if desired
                    console.log("No text selected for replacement.");
                    return;
                }

                const selectedText = ed.getModel().getValueInRange(selection);
                const originalLength = selectedText.length;

                if (originalLength === 0) return;

                const initialSelectionRange = selection;

                // 1. Clear the selected text immediately.
                // This provides instant feedback that something is happening.
                ed.executeEdits('replace-x-init', [{
                    range: initialSelectionRange,
                    text: '', // Replace selection with empty string
                    forceMoveMarkers: true // Important for subsequent edits and cursor position
                }]);

                // After clearing, the selection is collapsed at the start of the original selection.
                // This is our starting point for inserting new characters.
                let currentPosition = ed.getSelection().getStartPosition();

                // 2. "Stream" 'x' characters one by one
                for (let i = 0; i < originalLength; i++) {
                    // Create a range for the single character insertion at the current position
                    const insertRange = new currentMonacoInstance.Range(
                        currentPosition.lineNumber,
                        currentPosition.column,
                        currentPosition.lineNumber,
                        currentPosition.column
                    );

                    // Execute the edit to insert 'x'
                    ed.executeEdits('replace-x-stream-char', [{
                        range: insertRange,
                        text: 'x',
                        forceMoveMarkers: true // Moves cursor/selection to end of insert
                    }]);

                    // Update currentPosition to the end of the newly inserted 'x'
                    currentPosition = ed.getSelection().getEndPosition();

                    // Optional: Reveal the current typing position if it's off-screen
                    ed.revealPosition(currentPosition, currentMonacoInstance.editor.ScrollType.Smooth);

                    // Simulate delay for the streaming effect
                    // Adjust delay (in ms) for faster/slower typing
                    await new Promise(resolve => setTimeout(resolve, 75)); 
                }
            }
        });
        // --- End of custom action ---
    };

    const handleEditorChange = (value, event) => {
        setLatexCode(value);
    };

    const compileAndDisplayPdf = useCallback(async () => {
        if (!editorRef.current) {
            setPdfError("Editor not initialized. Please wait a moment.");
            return;
        }
        const currentLatexCode = editorRef.current.getValue();
        if (!currentLatexCode || !currentLatexCode.trim()) {
            setPdfError("LaTeX code is empty. Nothing to compile.");
            return;
        }

        setIsLoadingPdf(true);
        setPdfError(null);
        if (pdfUrl) {
            URL.revokeObjectURL(pdfUrl);
            setPdfUrl(null);
        }

        try {
            const compileEndpoint = `${API_BASE_URL}/problemsets/compile-latex`;
            const response = await fetch(compileEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/pdf',
                },
                body: JSON.stringify({ latex_code: currentLatexCode }),
            });

            if (!response.ok) {
                let errorDetail = "Failed to compile PDF.";
                try {
                    const errorData = await response.json();
                    errorDetail = errorData.detail || errorDetail;
                } catch (e) {
                    errorDetail = response.statusText || errorDetail;
                    if (response.status === 0) {
                        errorDetail = "Network error. Cannot connect to the server.";
                    }
                }
                throw new Error(`HTTP error ${response.status}: ${errorDetail}`);
            }

            const blob = await response.blob();
            if (blob.type !== "application/pdf") {
                console.error("Server did not return a PDF. Content-Type:", blob.type);
                const textResponse = await blob.text();
                throw new Error(`Expected a PDF, but received ${blob.type}. Server response: ${textResponse.substring(0, 200)}...`);
            }

            const newPdfUrl = URL.createObjectURL(blob);
            setPdfUrl(newPdfUrl);

        } catch (error) {
            console.error("Error fetching or displaying PDF:", error);
            setPdfError(error.message || "An unknown error occurred while compiling.");
        } finally {
            setIsLoadingPdf(false);
        }
    }, [pdfUrl]); // pdfUrl dependency is for revoking old URL

    useEffect(() => {
        const handleKeyDown = (event) => {
            if ((event.ctrlKey || event.metaKey) && event.key === 's') {
                event.preventDefault();
                compileAndDisplayPdf();
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [compileAndDisplayPdf]);

    useEffect(() => {
        // Initial compile on load if desired (optional)
        // compileAndDisplayPdf(); 

        // Cleanup PDF URL on component unmount
        return () => {
            if (pdfUrl) {
                URL.revokeObjectURL(pdfUrl);
            }
        };
    }, [pdfUrl]); // Only re-run if pdfUrl changes (for cleanup)

    return (
        <Box sx={{
            height: "100vh",
            display: "flex",
            overflow: "hidden",
            bgcolor: "#f5f5f5",
            p: { xs: 1, sm: 2 },
        }}>
            <Paper
                elevation={3}
                sx={{
                    flex: 1,
                    height: '100%',
                    display: "flex",
                    flexDirection: "column",
                    mr: { xs: 0.5, sm: 1 },
                    borderRadius: 2,
                    overflow: "hidden",
                }}
            >
                <Box sx={{
                    p: 1,
                    bgcolor: '#e9e9e9',
                    display: "flex",
                    alignItems: "center",
                    borderBottom: '1px solid #ddd'
                }}>
                    <Code size={18} style={{ marginRight: '8px' }} />
                    <Typography variant="subtitle2" sx={{ flexGrow: 1, fontWeight: 'medium' }}>
                        LaTeX Source (Ctrl+S to Compile)
                    </Typography>
                </Box>
                <Box sx={{ flexGrow: 1, overflow: "hidden", position: 'relative' }}>
                    <Editor
                        height="100%"
                        language="latex"
                        value={latexCode}
                        onMount={handleEditorDidMount}
                        onChange={handleEditorChange}
                        theme="vs" // You can change theme e.g., "vs-dark"
                        options={{
                            minimap: { enabled: false },
                            fontSize: 14,
                            wordWrap: "on",
                            lineNumbers: "on",
                            scrollBeyondLastLine: false,
                            automaticLayout: true,
                            renderLineHighlight: "gutter",
                            tabSize: 2,
                            insertSpaces: true,
                            // Ensure context menu is enabled (it is by default)
                            // contextmenu: true, 
                        }}
                    />
                </Box>
            </Paper>

            <Divider orientation="vertical" flexItem sx={{ mx: { xs: 0.5, sm: 1} }} />

            <Paper
                elevation={3}
                sx={{
                    flex: 1,
                    height: '100%',
                    display: "flex",
                    flexDirection: "column",
                    ml: { xs: 0.5, sm: 1 },
                    borderRadius: 2,
                    overflow: "hidden",
                }}
            >
                {/* Header for Preview Panel (optional) */}
                {/* <Box sx={{ p: 1, bgcolor: '#e9e9e9', display: "flex", alignItems: "center", borderBottom: '1px solid #ddd' }}>
                    <FileText size={18} style={{ marginRight: '8px' }} />
                    <Typography variant="subtitle2" sx={{ flexGrow: 1, fontWeight: 'medium' }}>Preview</Typography>
                </Box> */}
                <Box
                    sx={{
                        flexGrow: 1,
                        bgcolor: "#ffffff",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        p: isLoadingPdf || pdfError || !pdfUrl ? 2 : 0,
                        overflow: "hidden" // Important for iframe to not cause double scrollbars
                    }}
                >
                    {isLoadingPdf ? (
                        <Box sx={{ textAlign: 'center' }}>
                            <CircularProgress />
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                Compiling PDF...
                            </Typography>
                        </Box>
                    ) : pdfError ? (
                        <Alert severity="error" sx={{ width: '95%', m: 'auto' }}>{pdfError}</Alert>
                    ) : pdfUrl ? (
                        <iframe
                            src={pdfUrl}
                            title="PDF Preview"
                            style={{
                                width: "100%",
                                height: "100%",
                                border: "none",
                            }}
                        />
                    ) : (
                        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center' }}>
                            Preview will appear here after successful compilation.
                            <br />
                            Press Ctrl+S (or Cmd+S) in the editor.
                        </Typography>
                    )}
                </Box>
            </Paper>
        </Box>
    );
}