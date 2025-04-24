-- Initial schema for face recognition system
-- This file is used if Prisma migrations fail

-- Make sure the vector extension is enabled
CREATE EXTENSION IF NOT EXISTS vector;

-- Create Person table
CREATE TABLE IF NOT EXISTS "Person" (
    "id" TEXT PRIMARY KEY,
    "name" TEXT NOT NULL,
    "faceVector" vector(512),
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create Face table
CREATE TABLE IF NOT EXISTS "Face" (
    "id" TEXT PRIMARY KEY,
    "imageData" BYTEA NOT NULL,
    "faceVector" vector(512),
    "personId" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT "Face_personId_fkey" FOREIGN KEY ("personId") REFERENCES "Person"("id") ON DELETE RESTRICT ON UPDATE CASCADE
);

-- Create Detection table
CREATE TABLE IF NOT EXISTS "Detection" (
    "id" TEXT PRIMARY KEY,
    "streamId" TEXT NOT NULL,
    "timestamp" DOUBLE PRECISION NOT NULL,
    "bbox" JSONB NOT NULL,
    "confidence" DOUBLE PRECISION NOT NULL,
    "personId" TEXT,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "processedAt" DOUBLE PRECISION NOT NULL,
    CONSTRAINT "Detection_personId_fkey" FOREIGN KEY ("personId") REFERENCES "Person"("id") ON DELETE SET NULL ON UPDATE CASCADE
);

-- Create Stream table
CREATE TABLE IF NOT EXISTS "Stream" (
    "id" TEXT PRIMARY KEY,
    "name" TEXT NOT NULL,
    "rtspUrl" TEXT NOT NULL UNIQUE,
    "description" TEXT,
    "active" BOOLEAN NOT NULL DEFAULT true,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS "Person_faceVector_idx" ON "Person" USING gist("faceVector");
CREATE INDEX IF NOT EXISTS "Face_faceVector_idx" ON "Face" USING gist("faceVector");
CREATE INDEX IF NOT EXISTS "Detection_streamId_timestamp_idx" ON "Detection"("streamId", "timestamp"); 