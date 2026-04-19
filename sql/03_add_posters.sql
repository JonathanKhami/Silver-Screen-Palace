-- ============================================================
-- Migration: Add movie posters and descriptions
-- Run this ONCE in MySQL Workbench after pulling the update.
-- ============================================================
USE silver_screen;

-- Add columns (won't error if they already exist in future runs)
ALTER TABLE MOVIE ADD COLUMN MOVIE_POSTER VARCHAR(500) NULL;
ALTER TABLE MOVIE ADD COLUMN MOVIE_DESCRIPTION TEXT NULL;

-- Populate posters & descriptions for seeded movies (using TMDB public image URLs)
UPDATE MOVIE SET
  MOVIE_POSTER = 'https://image.tmdb.org/t/p/w500/1pdfLvkbY9ohJlCjQH2CZjjYVvJ.jpg',
  MOVIE_DESCRIPTION = 'Paul Atreides unites with the Fremen to seek revenge against the conspirators who destroyed his family. Facing a choice between the love of his life and the fate of the known universe, he endeavors to prevent a terrible future only he can foresee.'
WHERE MOVIE_TITLE = 'Dune: Part Two';

UPDATE MOVIE SET
  MOVIE_POSTER = 'https://image.tmdb.org/t/p/w500/vpnVM9B6NMmQpWeZvzLvDESb2QE.jpg',
  MOVIE_DESCRIPTION = 'Teenager Riley''s mind headquarters is undergoing a sudden demolition to make room for something entirely unexpected: new Emotions! Joy, Sadness, Anger, Fear and Disgust have long been running a successful operation, but they aren''t sure how to feel when Anxiety shows up.'
WHERE MOVIE_TITLE = 'Inside Out 2';

UPDATE MOVIE SET
  MOVIE_POSTER = 'https://image.tmdb.org/t/p/w500/8cdWjvZQUExUUTzyp4t6EDMubfO.jpg',
  MOVIE_DESCRIPTION = 'A listless Wade Wilson toils away in civilian life with his days as the morally flexible mercenary, Deadpool, behind him. But when his homeworld faces an existential threat, Wade must reluctantly suit-up again with an even more reluctant Wolverine.'
WHERE MOVIE_TITLE = 'Deadpool & Wolverine';

UPDATE MOVIE SET
  MOVIE_POSTER = 'https://image.tmdb.org/t/p/w500/wTnV3PCVW5O92JMrFvvrRcV39RU.jpg',
  MOVIE_DESCRIPTION = 'After a shipwreck, an intelligent robot called Roz is stranded on an uninhabited island. To survive the harsh environment, Roz bonds with the island''s animals and cares for an orphaned baby goose.'
WHERE MOVIE_TITLE = 'The Wild Robot';

UPDATE MOVIE SET
  MOVIE_POSTER = 'https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg',
  MOVIE_DESCRIPTION = 'The story of J. Robert Oppenheimer''s role in the development of the atomic bomb during World War II.'
WHERE MOVIE_TITLE = 'Oppenheimer';
