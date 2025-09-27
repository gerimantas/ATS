-- Migration 002: Add cex_symbol column to signals table
-- This migration adds the cex_symbol column required for reward calculation

-- Add cex_symbol column after pair_symbol
ALTER TABLE signals ADD COLUMN IF NOT EXISTS cex_symbol VARCHAR(20);

-- Add index on cex_symbol for performance
CREATE INDEX IF NOT EXISTS idx_signals_cex_symbol ON signals(cex_symbol);

-- Add comment to document the column
COMMENT ON COLUMN signals.cex_symbol IS 'CEX symbol without quote currency (e.g., SOL, ETH, BTC)';