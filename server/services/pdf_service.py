# server/services/pdf_service.py

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
import io # Needed for StreamingResponse

from sqlalchemy.orm import Session, joinedload

# Import models - adjust paths if needed
from ..models.problemset import Problemset
from ..models.problemset_problems import ProblemsetProblems
from ..models.problem import Problem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFGenerationError(Exception):
    """Custom exception for PDF generation failures."""
    def __init__(self, message, log=None):
        super().__init__(message)
        self.log = log # Store compilation log if available

class ProblemsetNotFound(Exception):
    """Custom exception for when a problemset isn't found."""
    pass

def _escape_latex(text: Optional[str]) -> str:
    """
    Basic LaTeX escaping for safety. Handles None input.
    More complex escaping might be needed depending on the source text.
    """
    if text is None:
        return ""
    text = str(text) # Ensure it's a string
    # Basic replacements - might need expansion based on your data
    chars_to_escape = {
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
        '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}', '<': r'\textless{}', '>': r'\textgreater{}',
    }
    # Escape special characters
    escaped_text = "".join(chars_to_escape.get(c, c) for c in text)
    # Handle newlines (replace with LaTeX double backslash)
    # Note: Be careful if your source already contains intended LaTeX newlines
    escaped_text = escaped_text.replace('\n', '\\\\')
    return escaped_text

def _generate_problemset_latex(problemset: Problemset) -> str:
    """
    Generates a LaTeX string from Problemset data, including related problems.
    """
    # Extract data and escape it for LaTeX
    title = _escape_latex(problemset.title)
    pset_type = _escape_latex(problemset.type)
    part_of = _escape_latex(problemset.part_of)
    group_name = _escape_latex(problemset.group_name)

    # --- Generate LaTeX for Problems ---
    problems_latex_parts = []
    if hasattr(problemset, 'problems') and problemset.problems:
        problems_latex_parts.append("\\section*{Problems}\n\\begin{enumerate}\n") # Use simple enumerate

        # Sort problems by position if available
        try:
            sorted_problems = sorted(problemset.problems, key=lambda psp: psp.position if psp.position is not None else float('inf'))
            logger.debug(f"Sorted {len(sorted_problems)} problems by position.")
        except AttributeError:
            logger.warning("ProblemsetProblems does not have 'position' attribute for sorting.")
            sorted_problems = problemset.problems # Use unsorted if no position

        for psp in sorted_problems: # psp is a ProblemsetProblems instance
            problem_text = "\\textit{Problem text not found or structure error.}"
            problem_category = ""
            if hasattr(psp, 'problem') and psp.problem:
                if hasattr(psp.problem, 'latex_text') and psp.problem.latex_text:
                    problem_text = psp.problem.latex_text # Assume problem text is already LaTeX
                else:
                    problem_text = "\\textit{Problem LaTeX text is missing.}"
                if hasattr(psp.problem, 'category') and psp.problem.category:
                    problem_category = f" (Category: {_escape_latex(psp.problem.category)})" # Add category info

            # DO NOT escape problem_text if it's already valid LaTeX
            # Only escape potentially problematic characters if needed, or trust the source
            # For now, we assume problemset.problem.latex_text IS valid LaTeX
            problems_latex_parts.append(f"  \\item {problem_text}{problem_category}\n\n")

        problems_latex_parts.append("\\end{enumerate}\n")
    else:
        problems_latex_parts.append("\\textit{No problems associated with this set.}\n")
        logger.warning(f"No problems found or loaded for Problemset ID {problemset.id}")

    problems_latex_str = "".join(problems_latex_parts)
    # --- End Problem LaTeX ---

    # --- Generate Final LaTeX Document ---
    latex_string = f"""
\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}}
\\usepackage[T1]{{fontenc}}
\\usepackage{{amsmath, amssymb, amsfonts}} % Math packages
\\usepackage{{enumitem}} % For list customization if needed
\\usepackage[margin=2.5cm]{{geometry}} % Page margins
\\usepackage{{hyperref}} % Clickable links, PDF metadata
\\hypersetup{{
    colorlinks=true, linkcolor=blue, urlcolor=blue,
    pdftitle={{{title}}}, pdfsubject={{Problemset: {pset_type}}},
    pdfauthor={{Skola Matematike}}, pdfkeywords={{{group_name if group_name else ''}, {part_of}}}
}}
\\usepackage{{palatino}} % Use Palatino font for better readability (optional)
\\linespread{{1.1}} % Slightly increased line spacing

\\title{{\\bfseries\\LARGE {title}}} % Larger, bold title
\\author{{Group: {group_name if group_name else 'N/A'} \\\\ Type: {pset_type} \\\\ Context: {part_of}}}
\\date{{\\today}}

\\begin{{document}}

\\maketitle
\\thispagestyle{{empty}} % No page number on title page
\\clearpage % Start content on a new page
\\pagenumbering{{arabic}} % Start page numbering

{problems_latex_str}

\\end{{document}}
"""
    # --- End Final LaTeX ---
    # logger.debug(f"Generated LaTeX string:\n{latex_string[:500]}...") # Log start of LaTeX
    return latex_string

def compile_latex_to_pdf(latex_content: str) -> bytes:
    """
    Compiles a given LaTeX string into PDF bytes using pdflatex.
    Handles temporary files and captures logs.
    """
    pdflatex_cmd = shutil.which("pdflatex")
    if not pdflatex_cmd:
        logger.error("pdflatex command not found in PATH.")
        raise FileNotFoundError("pdflatex command not found. Ensure a TeX distribution is installed and in the system PATH.")

    # Use a temporary directory for all intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        # Define base name for output files
        output_base_name = "problemset_output"
        tex_filename = f"{output_base_name}.tex"
        pdf_filename = f"{output_base_name}.pdf"
        log_filename = f"{output_base_name}.log"
        aux_filename = f"{output_base_name}.aux" # Common auxiliary file

        tex_filepath = temp_path / tex_filename
        pdf_filepath = temp_path / pdf_filename
        log_filepath = temp_path / log_filename

        # Write the LaTeX content to the .tex file
        try:
            with open(tex_filepath, "w", encoding="utf-8") as f:
                f.write(latex_content)
            logger.info(f"Temporary .tex file written to {tex_filepath}")
        except IOError as e:
            logger.error(f"Failed to write temporary .tex file: {e}", exc_info=True)
            raise PDFGenerationError(f"Failed to write temporary LaTeX file: {e}")

        # Command for pdflatex
        # Use the output_base_name for -jobname
        cmd = [
            pdflatex_cmd,
            "-interaction=nonstopmode",
            f"-output-directory={temp_dir}",
            f"-jobname={output_base_name}", # <-- CORRECTED: Use the base name string
            str(tex_filepath),
        ]

        log_output = ""
        compilation_successful = False
        # Run pdflatex twice for references, TOC, etc.
        for i in range(2):
            logger.info(f"Running pdflatex command (Pass {i+1}/2): {' '.join(cmd)}")
            try:
                process = subprocess.run(
                    cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", check=False, timeout=30 # Added timeout
                )
                # Append logs from stdout/stderr
                log_output += f"\n--- Pass {i+1} ---\nReturn Code: {process.returncode}\n"
                if process.stdout: log_output += f"Stdout:\n{process.stdout}\n"
                if process.stderr: log_output += f"Stderr:\n{process.stderr}\n"

                # Try reading the specific .log file
                if log_filepath.exists():
                    try:
                        with open(log_filepath, "r", encoding="utf-8", errors="replace") as logf:
                            partial_log = logf.read()
                        log_output += f"\nLog File Content (Pass {i+1}):\n{partial_log}\n"
                        # Check for common LaTeX error indicators in the log
                        if "! LaTeX Error:" in partial_log or "Fatal error occurred" in partial_log:
                             logger.warning(f"LaTeX errors detected in log file on pass {i+1}.")
                             if process.returncode != 0: # Combine log check with return code
                                 raise PDFGenerationError(f"pdflatex compilation failed with errors (see log).", log=log_output)
                    except IOError:
                        log_output += f"\nCould not read log file {log_filepath} on pass {i+1}.\n"
                else:
                     log_output += f"\nLog file {log_filepath} not found after pass {i+1}.\n"

                # Check return code strictly after potential log reading
                if process.returncode != 0:
                    logger.error(f"pdflatex failed on pass {i+1} with return code {process.returncode}.")
                    raise PDFGenerationError(f"pdflatex exited with code {process.returncode} on pass {i+1}.", log=log_output)

                # If we completed the second pass without non-zero return code
                if i == 1 and process.returncode == 0:
                     compilation_successful = True

            except FileNotFoundError:
                logger.error("pdflatex command execution failed: FileNotFoundError.")
                raise # Re-raise the original FileNotFoundError
            except subprocess.TimeoutExpired:
                 logger.error("pdflatex command timed out.")
                 raise PDFGenerationError("pdflatex compilation timed out after 30 seconds.", log=log_output)
            except Exception as e:
                # Log the original exception type and message
                logger.error(f"Subprocess execution failed unexpectedly: {type(e).__name__} - {e}", exc_info=True)
                # Wrap the original error message in the custom exception
                raise PDFGenerationError(f"Subprocess execution failed: {e}", log=log_output)


        # Final check after loops
        if not compilation_successful or not pdf_filepath.is_file():
            logger.error(f"PDF file not found or compilation failed after 2 passes: {pdf_filepath}")
            raise PDFGenerationError("PDF file was not generated successfully after 2 compilation passes.", log=log_output)

        # Read the generated PDF bytes
        try:
            with open(pdf_filepath, "rb") as f:
                pdf_bytes = f.read()
            logger.info(f"Successfully generated and read PDF: {pdf_filepath} ({len(pdf_bytes)} bytes)")
            return pdf_bytes
        except IOError as e:
            logger.error(f"Failed to read generated PDF file: {e}", exc_info=True)
            raise PDFGenerationError(f"Failed to read generated PDF file: {e}", log=log_output)


# def get_problemset_pdf(db: Session, problemset_id: int) -> bytes:
#     """
#     Fetches Problemset data (with related problems), generates LaTeX, compiles it,
#     and returns PDF bytes.
#     """
#     logger.info(f"Initiating PDF generation for Problemset ID: {problemset_id}")

#     # Eagerly load the necessary relationships
#     problemset = db.query(Problemset).options(
#         joinedload(Problemset.problems) # Load the list of ProblemsetProblems links
#         .joinedload(ProblemsetProblems.problem) # For each link, load the actual Problem
#     ).filter(Problemset.id == problemset_id).first()

#     if not problemset:
#         logger.warning(f"Problemset with ID {problemset_id} not found in database.")
#         raise ProblemsetNotFound(f"Problemset with ID {problemset_id} not found.")

#     logger.info(f"Generating LaTeX for Problemset '{problemset.title}' (ID: {problemset_id})")
#     try:
#         latex_content = _generate_problemset_latex(problemset)
#     except Exception as e:
#         logger.exception(f"Error generating LaTeX content for problemset {problemset_id}: {e}")
#         raise PDFGenerationError(f"Failed to generate LaTeX content: {e}")

#     logger.info(f"Compiling LaTeX to PDF for Problemset ID: {problemset_id}")
#     try:
#         pdf_bytes = compile_latex_to_pdf(latex_content)
#         logger.info(f"PDF compilation successful for Problemset ID: {problemset_id}")
#         return pdf_bytes
#     except (PDFGenerationError, FileNotFoundError) as e:
#         # Log already happened in compile_latex_to_pdf or above
#         logger.error(f"PDF generation failed for Problemset ID {problemset_id}: {e}")
#         raise # Re-raise the specific error for the router to handle
#     except Exception as e:
#         logger.exception(f"Unexpected error during PDF compilation for problemset {problemset_id}: {e}")
#         raise PDFGenerationError(f"An unexpected error occurred during PDF compilation: {e}")


def get_problemset_pdf(db: Session, problemset_id: int) -> bytes:
    """
    Fetches Problemset data (with related problems), uses existing raw_latex if available
    or generates it, compiles to PDF, and returns PDF bytes.
    """
    logger.info(f"Initiating PDF generation for Problemset ID: {problemset_id}")

    # Eagerly load the necessary relationships
    problemset = (
        db.query(Problemset)
        .options(
            joinedload(Problemset.problems)
            .joinedload(ProblemsetProblems.problem)
        )
        .filter(Problemset.id == problemset_id)
        .first()
    )

    if not problemset:
        logger.warning(f"Problemset with ID {problemset_id} not found in database.")
        raise ProblemsetNotFound(f"Problemset with ID {problemset_id} not found.")

    # Decide whether to use stored LaTeX or generate new
    if problemset.raw_latex:
        logger.info(f"Using raw LaTeX from DB for Problemset ID: {problemset_id}")
        latex_content = problemset.raw_latex
    else:
        logger.info(f"Generating LaTeX for Problemset '{problemset.title}' (ID: {problemset_id})")
        try:
            latex_content = _generate_problemset_latex(problemset)
        except Exception as e:
            logger.exception(f"Error generating LaTeX content for Problemset ID {problemset_id}: {e}")
            raise PDFGenerationError(f"Failed to generate LaTeX content: {e}")

    # Compile to PDF
    logger.info(f"Compiling LaTeX to PDF for Problemset ID: {problemset_id}")
    try:
        pdf_bytes = compile_latex_to_pdf(latex_content)
        logger.info(f"PDF compilation successful for Problemset ID: {problemset_id}")
        return pdf_bytes
    except (PDFGenerationError, FileNotFoundError) as e:
        logger.error(f"PDF generation failed for Problemset ID {problemset_id}: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error during PDF compilation for Problemset ID {problemset_id}: {e}")
        raise PDFGenerationError(f"An unexpected error occurred during PDF compilation: {e}")
