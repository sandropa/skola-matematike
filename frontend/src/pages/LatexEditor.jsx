import { useState, useEffect, useRef, useCallback } from 'react';
import Editor from '@monaco-editor/react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Box, 
  Paper, 
  IconButton, 
  Divider, 
  Tooltip, 
  Snackbar, 
  Alert,
  CircularProgress
} from '@mui/material';

import { 
  Save,
  Download,
  Code,
  FileText,
  ZoomIn,
  ZoomOut
} from 'lucide-react';

export default function LatexEditor() {
    return (
        <Box sx={{ 
            height: "100vh", 
            display: "flex", 
            flexDirection: "row",
            overflow: "hidden",
            bgcolor: "#f5f5f5",
            py: 5,
        }}>
            {/* Latex panel */}
            <Paper
                elevation={3}
                sx={{
                    width: "50%",
                    display: "flex",
                    flexDirection: "column",
                    flexGrow: 1,
                    m: 1,
                    borderRadius: 2,
                    overflow: "hidden",
                }}
            >
                <Box sx={{
                    p: 1,
                    bgcolor: '#f0f0f0',
                    display: "flex",
                    alignItems: "center" 
                }}>
                    <Code size={18} className="mr-2"/>
                    <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
                        LaTeX
                    </Typography>
                </Box>
                <Box sx={{ flexGrow: 1, overflow: "hidden"}}>
                    <Editor
                        height="100%"
                        defaultLanguage="latex"
                        // value={latexCode}
                        // onChange={setLatexCode}
                        // onMount={handleEditorDidMount}
                        theme="vs"
                        options={{
                            minimap: { enabled: false },
                            fontSize: 15,
                            wordWrap: "on",
                            lineNumbers: "on",
                            scrollBeyondLastLine: false,
                            automaticLayout: true,
                        }}
                    />
                </Box>
            </Paper>

            <Divider orientation="vertical" flexItem sx = {{ my: 1 }} />

            <Paper
                elevation={3}
                sx={{
                    width: "50%",
                    display: "flex",
                    flexDirection: "column",
                    m: 1, // Margin
                    borderRadius: 2,
                    overflow: "hidden",
                    flexGrow: 1,      // <<< Ensures this Paper takes available vertical space if parent is column flex
                                      // For row flex, parent needs align-items: stretch (default) for children to fill height
                    // bgcolor: "#fafafa" // Optional: outer background for the preview paper
                }}
            >
                <Box sx={{ // This is the "header" area for the preview, if you want one
                    p: 1,
                    bgcolor: '#f0f0f0', // Example header color
                    display: "flex",
                    alignItems: "center"
                }}>
                    <FileText size={18} style={{ marginRight: '8px' }}/>
                    <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
                        Preview
                    </Typography>
                    {/* You could add zoom or other controls here later */}
                </Box>
                <Box
                    sx={{
                        flexGrow: 1,          // Makes this Box fill the Paper vertically
                        bgcolor: "#e0e0e0",   // Background for the empty content area
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        p: 2
                    }}
                >
                    <Typography variant="body2" color="text.secondary">
                        Preview will appear here
                    </Typography>
                </Box>
            </Paper>
            
        </Box>
    );
}