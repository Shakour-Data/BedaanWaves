-- Fix macro_indicators duplicates and add unique constraint

-- Step 1: Delete duplicate (indicator_code, period) rows, keeping most recent
DELETE FROM macro_indicators
WHERE period IS NOT NULL
  AND id::text NOT IN (
      SELECT MAX(id::text)
      FROM macro_indicators
      WHERE period IS NOT NULL
      GROUP BY indicator_code, period
  );

-- Step 2: Add the unique constraint (use DO block to check existence)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uix_macro_indicator' 
        AND conrelid = 'macro_indicators'::regclass
    ) THEN
        ALTER TABLE macro_indicators
            ADD CONSTRAINT uix_macro_indicator
            UNIQUE (indicator_code, period);
        RAISE NOTICE 'Added uix_macro_indicator constraint';
    ELSE
        RAISE NOTICE 'uix_macro_indicator constraint already exists';
    END IF;
END $$;

-- Step 3: Verify no more duplicates
\echo 'Verifying no duplicates remain...'
SELECT count(*) AS duplicate_count FROM (
    SELECT indicator_code, period FROM macro_indicators 
    WHERE period IS NOT NULL 
    GROUP BY indicator_code, period HAVING count(*) > 1
) d;

-- Step 4: Verify the index exists
\echo 'Checking idx_macro_indicator_code_as_of...'
SELECT indexname FROM pg_indexes 
WHERE tablename = 'macro_indicators' AND indexname = 'idx_macro_indicator_code_as_of';
