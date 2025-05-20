import { useState, useEffect, useRef, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import {
    Typography,
    Box,
    Paper,
    CircularProgress, // For loading state
    Alert,         // For error messages
    Divider        // For vertical divider between panels
} from '@mui/material';

import {
    Code,         // Icon for LaTeX editor
    FileText,     // Icon for Preview
} from 'lucide-react';

// IMPORTANT: Adjust this to your FastAPI backend URL
const API_BASE_URL = "http://localhost:8000"; // e.g., http://localhost:8000 or your production URL

export default function LatexEditor() {
    const [latexCode, setLatexCode] = useState(
        "% Welcome to the LaTeX Editor!\n" +
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

    const [pdfUrl, setPdfUrl] = useState(null);
    const [isLoadingPdf, setIsLoadingPdf] = useState(false);
    const [pdfError, setPdfError] = useState(null);

    const handleEditorDidMount = (editor, monaco) => {
        editorRef.current = editor;
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
    }, [pdfUrl]);

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
        return () => {
            if (pdfUrl) {
                URL.revokeObjectURL(pdfUrl);
            }
        };
    }, [pdfUrl]);

    return (
        <Box sx={{
            height: "100vh",
            display: "flex", // Default flexDirection is "row"
            overflow: "hidden",
            bgcolor: "#f5f5f5",
            p: { xs: 1, sm: 2 }, // Padding around the entire layout
        }}>
            {/* --- Latex Panel (Left Side) --- */}
            <Paper
                elevation={3}
                sx={{
                    flex: 1, // Takes 50% of available width (along with preview panel)
                    // Or width: 'calc(50% - 8px)' if you want to account for divider/margins precisely
                    height: '100%', // Take full available height within the parent Box
                    display: "flex",
                    flexDirection: "column",
                    mr: { xs: 0.5, sm: 1 }, // Margin to the right, before divider/next panel
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
                        LaTeX Source (Ctrl+S or Cmd+S to Compile)
                    </Typography>
                </Box>
                <Box sx={{ flexGrow: 1, overflow: "hidden", position: 'relative' }}>
                    <Editor
                        height="100%"
                        language="latex"
                        value={latexCode}
                        onMount={handleEditorDidMount}
                        onChange={handleEditorChange}
                        theme="vs"
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
                        }}
                    />
                </Box>
            </Paper>

            <Divider orientation="vertical" flexItem sx={{ mx: { xs: 0.5, sm: 1} }} />

            {/* --- Preview Panel (Right Side) --- */}
            <Paper
                elevation={3}
                sx={{
                    flex: 1, // Takes 50% of available width
                    height: '100%', // Take full available height
                    display: "flex",
                    flexDirection: "column",
                    ml: { xs: 0.5, sm: 1 }, // Margin to the left, after divider/previous panel
                    borderRadius: 2,
                    overflow: "hidden",
                }}
            >
                {/* <Box sx={{
                    p: 1,
                    bgcolor: '#e9e9e9',
                    display: "flex",
                    alignItems: "center",
                    borderBottom: '1px solid #ddd'
                }}>
                    <FileText size={18} style={{ marginRight: '8px' }} />
                    <Typography variant="subtitle2" sx={{ flexGrow: 1, fontWeight: 'medium' }}>
                        Preview
                    </Typography>
                </Box> */}
                <Box
                    sx={{
                        flexGrow: 1,
                        bgcolor: "#ffffff",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        p: isLoadingPdf || pdfError || !pdfUrl ? 2 : 0,
                        overflow: "hidden"
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