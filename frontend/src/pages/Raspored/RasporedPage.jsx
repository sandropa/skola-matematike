import React, { useEffect, useState } from 'react';
import RasporedTable from './RasporedTable';
import { Paper, Typography, Box } from '@mui/material';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export default function RasporedPage() {
  const [schedule, setSchedule] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const cycles = [
      "I ciklus", "II ciklus", "III ciklus", "IV ciklus",
      "V ciklus", "VI ciklus", "VII ciklus"
    ];
    const groupNames = [
      "Grupa A1", "Grupa A2", "Grupa B", "Srednja grupa",
      "Napredna grupa", "Predolimpijska grupa", "Olimpijska grupa"
    ];
    const lecturers = [
      "Emin Mulamimović", "Amar Kurić", "Admir Beširević",
      "Adisa Bolić", "Adi Hujić", "Imana Alibašić", "Sandro Paradižik"
    ];
    const schedule = [];
    let id = 1;
    for (const cycle of cycles) {
      for (let week = 1; week <= 4; week++) {
        const groups = {};
        for (const group of groupNames) {
          groups[group] = {
            Tema: `Tema ${week}`,
            Datum: `${week}.2.2025.`,
            Predavač: lecturers[(week + groupNames.indexOf(group)) % lecturers.length],
            problemset_id: id,
            comments: ""
          };
          id++;
        }
        schedule.push({ cycle, row: week, groups });
      }
    }
    setSchedule(schedule);
    setLoading(false);
  }, []);

  return (
    <Paper sx={{ p: 2, m: 2 }}>
      <Typography
        variant="h5"
        gutterBottom
        align="center"
        sx={{ fontWeight: 'bold', fontSize: 32, letterSpacing: 2, mb: 3 }}
      >
        Raspored
      </Typography>
      <Box>
        <RasporedTable schedule={schedule} loading={loading} />
      </Box>
    </Paper>
  );
} 