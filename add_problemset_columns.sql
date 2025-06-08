-- Add raw_latex and status columns to problemsets table
ALTER TABLE problemsets 
ADD COLUMN raw_latex TEXT,
ADD COLUMN status VARCHAR(20) NOT NULL DEFAULT 'DRAFT';

-- Add check constraint for status
ALTER TABLE problemsets
ADD CONSTRAINT problemsets_status_check 
CHECK (status IN ('DRAFT', 'FINALIZED')); 