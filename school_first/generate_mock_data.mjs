import fs from 'node:fs/promises';
import path from 'node:path';

import { buildProofPack } from './analytics.js';
import { generateSchoolFirstMockData } from './mock_data.js';

const outPath = process.argv[2] || 'artifacts/school_first_mock_data_sample.json';
const seedArg = Number(process.argv[3] || 20260321);
const dataset = generateSchoolFirstMockData({ seed: seedArg });
const proof = buildProofPack(dataset);

await fs.mkdir(path.dirname(outPath), { recursive: true });
await fs.writeFile(
  outPath,
  JSON.stringify({ meta: dataset.meta, dataset, proof }, null, 2),
  'utf8'
);

console.log(`wrote ${outPath}`);
