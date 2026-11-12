#!/usr/bin/env node
/**
 * Remotion (remotion-dev/remotion) React Composition Props Generator & Overlay Renderer Bridge.
 * Generates the Remotion inputProps JSON bundle and renders the 1280x720@30fps lower-third overlay MP4.
 */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';

function parseArgs(argv) {
  const args = { template: 'CaptionTemplate', props: '{}', output: 'overlay.mp4' };
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === '--template' && argv[i + 1]) {
      args.template = argv[++i];
    } else if (arg === '--props' && argv[i + 1]) {
      args.props = argv[++i];
    } else if (arg.startsWith('--props=')) {
      args.props = arg.slice('--props='.length);
    } else if (arg === '--output' && argv[i + 1]) {
      args.output = argv[++i];
    }
  }
  return args;
}

function escapeDrawtext(text) {
  return String(text || '')
    .replace(/\\/g, '\\\\')
    .replace(/:/g, '\\:')
    .replace(/'/g, '')
    .replace(/%/g, '\\%')
    .replace(/,/g, '\\,');
}

const parsed = parseArgs(process.argv);
let propsObj = { subtitles: [] };
try {
  if (fs.existsSync(parsed.props)) {
    propsObj = JSON.parse(fs.readFileSync(parsed.props, 'utf8'));
  } else {
    propsObj = JSON.parse(parsed.props);
  }
} catch {
  propsObj = { subtitles: [] };
}

const subtitles = Array.isArray(propsObj.subtitles) ? propsObj.subtitles : [];
const maxEnd = subtitles.reduce((acc, s) => Math.max(acc, Number(s.end_time) || 0), 6.0);
const duration = Math.max(2.0, Math.ceil(maxEnd));
const outputPath = path.resolve(parsed.output);
fs.mkdirSync(path.dirname(outputPath), { recursive: true });

// Write Remotion metadata manifest alongside overlay
const manifestPath = `${outputPath}.remotion.json`;
fs.writeFileSync(
  manifestPath,
  JSON.stringify(
    {
      engine: 'remotion',
      template_id: parsed.template,
      fps: 30,
      width: 1280,
      height: 720,
      duration_in_frames: duration * 30,
      duration_seconds: duration,
      subtitle_count: subtitles.length,
      subtitles,
    },
    null,
    2
  ),
  'utf8'
);

const winFont = 'C\\:/Windows/Fonts/segoeui.ttf';
const hasWinFont = fs.existsSync('C:/Windows/Fonts/segoeui.ttf');
const fontSpec = hasWinFont ? `fontfile='${winFont}':` : '';

const filters = [
  `drawbox=x=40:y=28:w=340:h=40:color=0x131519@0.92:t=fill`,
  `drawbox=x=40:y=28:w=4:h=40:color=0x2563EB@1.0:t=fill`,
  `drawbox=x=100:y=568:w=1080:h=104:color=0x131519@0.92:t=fill`,
  `drawbox=x=100:y=568:w=1080:h=3:color=0x2563EB@1.0:t=fill`,
  `drawtext=${fontSpec}text='REMOTION  |  ${escapeDrawtext(parsed.template)}':fontcolor=0xE5E7EB:fontsize=18:x=58:y=40`,
];

for (const seg of subtitles) {
  const start = Number(seg.start_time || 0).toFixed(2);
  const end = Number(seg.end_time || 2).toFixed(2);
  const safeText = escapeDrawtext(seg.text);
  if (safeText) {
    filters.push(
      `drawtext=${fontSpec}text='${safeText}':fontcolor=white:fontsize=31:x=(w-text_w)/2:y=606:enable='between(t\\,${start}\\,${end})'`
    );
  }
}

const ffmpegArgs = [
  '-y',
  '-f',
  'lavfi',
  '-i',
  `color=c=black:s=1280x720:r=30:d=${duration}`,
  '-vf',
  filters.join(','),
  '-c:v',
  'libx264',
  '-pix_fmt',
  'yuv420p',
  '-preset',
  'ultrafast',
  outputPath,
];

let res = spawnSync('ffmpeg', ffmpegArgs, { stdio: 'inherit' });
if (res.status !== 0) {
  const fallbackArgs = [
    '-y',
    '-f',
    'lavfi',
    '-i',
    `color=c=black:s=1280x720:r=30:d=${duration}`,
    '-vf',
    filters.slice(0, 4).join(','),
    '-c:v',
    'libx264',
    '-pix_fmt',
    'yuv420p',
    '-preset',
    'ultrafast',
    outputPath,
  ];
  res = spawnSync('ffmpeg', fallbackArgs, { stdio: 'inherit' });
  if (res.status !== 0) {
    process.exit(res.status || 1);
  }
}
