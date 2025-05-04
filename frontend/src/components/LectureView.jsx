// src/components/LectureView.jsx
import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import axios from 'axios';

// --- Import the CSS file ---
import './LectureView.css';

function LectureView() {
  const { id } = useParams();
  const [lectureData, setLectureData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      setLectureData(null);
      // Use full URL for development if backend is on a different port
      const apiUrl = `http://127.0.0.1:8000/problemsets/${id}/lecture-data`;
      try {
        console.log(`Fetching data from: ${apiUrl}`);
        const response = await axios.get(apiUrl);
        console.log("API Response:", response.data);
        setLectureData(response.data);
      } catch (err) {
        console.error("Error fetching lecture data:", err);
        if (err.response && err.response.status === 404) {
          setError(`Lecture with ID ${id} not found or is not a 'predavanje'.`);
        } else {
          setError(`Failed to fetch lecture data: ${err.message}`);
        }
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [id]);

  if (loading) {
    return <div>Loading lecture data for ID: {id}...</div>;
  }

  if (error) {
    return <div style={{ color: 'red' }}>Error: {error}</div>;
  }

  if (!lectureData) {
    return <div>No lecture data available.</div>;
  }

  // Use optional chaining for safety
  const problems = lectureData?.problems || [];
  const title = lectureData?.title || 'Untitled Lecture';
  const type = lectureData?.type || 'N/A';
  const context = lectureData?.part_of || 'N/A'; // Assuming part_of is context
  const group = lectureData?.group_name || 'N/A'; // Assuming group_name exists

  return (
    // Use container div with class
    <div className="lecture-container">
      {/* Header section */}
      <div className="lecture-header">
        <h2>{title}</h2>
        <p>
          <strong>Type:</strong> {type} | <strong>Context:</strong> {context} | <strong>Group:</strong> {group}
        </p>
      </div>

      {/* Download button */}
      <a
        href={`http://127.0.0.1:8000/problemsets/${id}/pdf`} // Full URL for dev
        download={`${title.replace(/ /g, '_') || 'lecture'}-${id}.pdf`}
        target="_blank"
        rel="noopener noreferrer"
        className="download-button" // Apply button style
      >
        Download PDF
      </a>

      <hr style={{ marginBottom: '25px' }} />

      {/* Problems section */}
      <h3>Problems:</h3>
      {problems.length > 0 ? (
        // Use div or ul instead of ol if we handle numbering manually or don't need it
        <div className="problems-list">
          {/* Sort problems by position before mapping */}
          {problems
            .sort((a, b) => (a?.position ?? Infinity) - (b?.position ?? Infinity))
            .map((link) => (
            // Use a div for each problem item
            <div key={`${id}-${link.position}`} className="problem-item">
              <strong>
                Problem {link.position} (Category: {link?.problem?.category || 'N/A'})
              </strong>
              {/* Use pre and code tags with a class */}
              <pre className="latex-code-block">
                <code>{link?.problem?.latex_text || 'LaTeX content missing.'}</code>
              </pre>
            </div>
          ))}
        </div>
      ) : (
        <p>No problems associated with this lecture.</p>
      )}
    </div>
  );
}

export default LectureView;