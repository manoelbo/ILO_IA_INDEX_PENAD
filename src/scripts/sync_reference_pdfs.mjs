#!/usr/bin/env node

import { createHash } from "node:crypto";
import { promises as fs } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const workspaceRoot = path.resolve(scriptDirectory, "../..");
const bibliographyPath = process.argv[2]
  ? path.resolve(process.cwd(), process.argv[2])
  : path.join(workspaceRoot, "references", "library.bib");
const referencesDirectory = path.dirname(bibliographyPath);
const pdfDirectory = path.join(referencesDirectory, "pdfs");
const indexPath = path.join(referencesDirectory, "PDF_INDEX.md");
const manifestPath = path.join(referencesDirectory, "pdf_manifest.tsv");

function getField(entryText, fieldName) {
  const pattern = new RegExp(
    `^\\s*${fieldName}\\s*=\\s*\\{(.*)\\},\\s*$`,
    "m",
  );
  return entryText.match(pattern)?.[1] ?? "";
}

function parseAttachment(segment) {
  const pdfSuffix = ":application/pdf";
  if (!segment.endsWith(pdfSuffix)) {
    return null;
  }

  const payload = segment.slice(0, -pdfSuffix.length);
  const separatorIndex = payload.indexOf(":");
  if (separatorIndex === -1) {
    return null;
  }

  return {
    label: payload.slice(0, separatorIndex) || "PDF",
    source: payload.slice(separatorIndex + 1),
  };
}

function resolveAttachmentPath(source) {
  return path.isAbsolute(source)
    ? source
    : path.resolve(referencesDirectory, source);
}

function portablePath(filePath) {
  return path.relative(referencesDirectory, filePath).split(path.sep).join("/");
}

function safeCitationKey(citationKey) {
  const safeKey = citationKey.replace(/[^A-Za-z0-9._-]/g, "_");
  if (!safeKey || safeKey === "." || safeKey === "..") {
    throw new Error(`Unsafe citation key: ${citationKey}`);
  }
  return safeKey;
}

function plainText(value) {
  return value
    .replace(/[{}]/g, "")
    .replace(/\\([&%_#])/g, "$1")
    .replace(/\s+/g, " ")
    .trim();
}

function markdownCell(value) {
  return plainText(value).replace(/\|/g, "\\|");
}

function tsvCell(value) {
  return plainText(value).replace(/[\t\r\n]+/g, " ");
}

async function sha256(filePath) {
  const hash = createHash("sha256");
  const file = await fs.open(filePath, "r");

  try {
    for await (const chunk of file.readableWebStream()) {
      hash.update(Buffer.from(chunk));
    }
  } finally {
    await file.close();
  }

  return hash.digest("hex");
}

async function filesMatch(sourcePath, destinationPath) {
  try {
    const [sourceStat, destinationStat] = await Promise.all([
      fs.stat(sourcePath),
      fs.stat(destinationPath),
    ]);
    if (sourceStat.size !== destinationStat.size) {
      return false;
    }
    return (await sha256(sourcePath)) === (await sha256(destinationPath));
  } catch (error) {
    if (error.code === "ENOENT") {
      return false;
    }
    throw error;
  }
}

async function atomicWrite(filePath, contents) {
  const temporaryPath = `${filePath}.tmp`;
  await fs.writeFile(temporaryPath, contents, "utf8");
  await fs.rename(temporaryPath, filePath);
}

const bibliography = await fs.readFile(bibliographyPath, "utf8");
const entryPattern = /^@([A-Za-z]+)\{([^,\s]+),\s*$/gm;
const entryStarts = [...bibliography.matchAll(entryPattern)];

if (entryStarts.length === 0) {
  throw new Error(`No BibLaTeX entries found in ${bibliographyPath}`);
}

const entries = entryStarts.map((match, index) => {
  const start = match.index;
  const end =
    index + 1 < entryStarts.length ? entryStarts[index + 1].index : bibliography.length;
  const text = bibliography.slice(start, end);
  const fileMatch = text.match(/^(\s*file\s*=\s*\{)(.*)(\},\s*)$/m);

  return {
    citationKey: match[2],
    start,
    end,
    text,
    fileMatch,
    title: getField(text, "title"),
    date: getField(text, "date"),
    doi: getField(text, "doi"),
  };
});

const duplicateKeys = entries
  .map((entry) => entry.citationKey)
  .filter((key, index, keys) => keys.indexOf(key) !== index);
if (duplicateKeys.length > 0) {
  throw new Error(`Duplicate citation keys: ${[...new Set(duplicateKeys)].join(", ")}`);
}

const jobs = [];
const entriesWithoutPdfs = [];
for (const entry of entries) {
  if (!entry.fileMatch) {
    entry.rewrittenText = entry.text;
    entriesWithoutPdfs.push(entry.citationKey);
    continue;
  }

  const segments = entry.fileMatch[2].split(/;\s*/);
  let pdfNumber = 0;
  const rewrittenSegments = [];

  for (const segment of segments) {
    const attachment = parseAttachment(segment);
    if (!attachment) {
      rewrittenSegments.push(segment);
      continue;
    }

    pdfNumber += 1;
    const suffix = pdfNumber === 1 ? "" : `--${pdfNumber}`;
    const fileName = `${safeCitationKey(entry.citationKey)}${suffix}.pdf`;
    const sourcePath = resolveAttachmentPath(attachment.source);
    const destinationPath = path.join(pdfDirectory, fileName);

    jobs.push({
      citationKey: entry.citationKey,
      title: entry.title,
      date: entry.date,
      doi: entry.doi,
      pdfNumber,
      sourcePath,
      destinationPath,
    });
    rewrittenSegments.push(
      `${attachment.label}:${portablePath(destinationPath)}:application/pdf`,
    );
  }

  if (pdfNumber === 0) {
    entry.rewrittenText = entry.text;
    entriesWithoutPdfs.push(entry.citationKey);
    continue;
  }

  entry.rewrittenText = entry.text.replace(
    entry.fileMatch[0],
    `${entry.fileMatch[1]}${rewrittenSegments.join(";")}${entry.fileMatch[3]}`,
  );
}

const missingSources = [];
for (const job of jobs) {
  try {
    const sourceStat = await fs.stat(job.sourcePath);
    if (!sourceStat.isFile()) {
      missingSources.push(`${job.citationKey}: ${job.sourcePath}`);
    }
  } catch (error) {
    if (error.code === "ENOENT") {
      missingSources.push(`${job.citationKey}: ${job.sourcePath}`);
    } else {
      throw error;
    }
  }
}
if (missingSources.length > 0) {
  throw new Error(`Missing PDF sources:\n${missingSources.join("\n")}`);
}

await fs.mkdir(pdfDirectory, { recursive: true });

let copiedCount = 0;
let unchangedCount = 0;
for (const job of jobs) {
  const samePath = path.resolve(job.sourcePath) === path.resolve(job.destinationPath);
  if (samePath || (await filesMatch(job.sourcePath, job.destinationPath))) {
    unchangedCount += 1;
  } else {
    await fs.copyFile(job.sourcePath, job.destinationPath);
    copiedCount += 1;
  }
  job.bytes = (await fs.stat(job.destinationPath)).size;
  job.sha256 = await sha256(job.destinationPath);
  job.localPath = portablePath(job.destinationPath);
}

let rewrittenBibliography = bibliography;
for (const entry of [...entries].reverse()) {
  rewrittenBibliography =
    rewrittenBibliography.slice(0, entry.start) +
    entry.rewrittenText +
    rewrittenBibliography.slice(entry.end);
}

if (rewrittenBibliography !== bibliography) {
  await atomicWrite(bibliographyPath, rewrittenBibliography);
}

const sortedJobs = [...jobs].sort((left, right) =>
  left.citationKey.localeCompare(right.citationKey, "en"),
);
const generatedAt = new Date().toISOString();
const totalBytes = jobs.reduce((sum, job) => sum + job.bytes, 0);

const manifestLines = [
  "citation_key\tdate\ttitle\tdoi\tpdf_path\tsha256\tbytes",
  ...sortedJobs.map((job) =>
    [
      tsvCell(job.citationKey),
      tsvCell(job.date),
      tsvCell(job.title),
      tsvCell(job.doi),
      job.localPath,
      job.sha256,
      job.bytes,
    ].join("\t"),
  ),
];
await atomicWrite(manifestPath, `${manifestLines.join("\n")}\n`);

const indexLines = [
  "# Reference PDF index",
  "",
  "This file is generated by `src/scripts/sync_reference_pdfs.mjs` from `references/library.bib`.",
  "The BibLaTeX citation key is the canonical identifier shared by the bibliography, manifest, and PDF filename.",
  "",
  `Generated: ${generatedAt}`,
  "",
  "| Citation key | Date | Reference | PDF |",
  "| --- | --- | --- | --- |",
  ...sortedJobs.map((job) => {
    const pdfLabel = job.pdfNumber === 1 ? "PDF" : `PDF ${job.pdfNumber}`;
    return `| \`${job.citationKey}\` | ${markdownCell(job.date)} | ${markdownCell(job.title)} | [${pdfLabel}](${job.localPath}) |`;
  }),
  "",
];
await atomicWrite(indexPath, `${indexLines.join("\n")}\n`);

const expectedFiles = new Set(jobs.map((job) => path.basename(job.destinationPath)));
const orphanFiles = (await fs.readdir(pdfDirectory))
  .filter((fileName) => fileName.toLowerCase().endsWith(".pdf"))
  .filter((fileName) => !expectedFiles.has(fileName));

console.log(`Bibliography entries: ${entries.length}`);
console.log(`Entries with PDFs: ${entries.length - entriesWithoutPdfs.length}`);
console.log(`Entries without PDFs: ${entriesWithoutPdfs.length}`);
console.log(`PDF attachments: ${jobs.length}`);
console.log(`Copied or updated: ${copiedCount}`);
console.log(`Already current: ${unchangedCount}`);
console.log(`Total size: ${(totalBytes / 1024 / 1024).toFixed(1)} MiB`);
console.log(`Bibliography: ${bibliographyPath}`);
console.log(`PDF directory: ${pdfDirectory}`);
console.log(`Manifest: ${manifestPath}`);
console.log(`Index: ${indexPath}`);
if (orphanFiles.length > 0) {
  console.warn(`Orphan PDFs left untouched: ${orphanFiles.join(", ")}`);
}
