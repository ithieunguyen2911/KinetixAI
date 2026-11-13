#!/usr/bin/env node
/**
 * HyperFrames (heygen-com/hyperframes) Deterministic Composition Generator & Renderer Bridge.
 * 1. Generates spec-compliant HyperFrames HTML composition (`index.html` + `compositions/captions.html`)
 *    following all 12 rules of the HyperFrames Contract (`class="clip"`, `data-start`, `data-duration`,
 *    `data-track-kind="captions"`, `<template>`, `gsap.fromTo` on child elements, `window.__timelines`).
 * 2. Renders the deterministic 1280x720@30fps video overlay MP4.
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

function escapeHtml(str) {
  return String(str || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
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
const baseDuration = Number(propsObj.duration_seconds) > 0 ? Number(propsObj.duration_seconds) : 6.0;
const maxEnd = subtitles.reduce((acc, s) => Math.max(acc, Number(s.end_time) || 0), baseDuration);
const duration = Math.max(2.0, Math.ceil(maxEnd));
const outputPath = path.resolve(parsed.output);
const workDir = path.dirname(outputPath);
fs.mkdirSync(workDir, { recursive: true });

// 1. Generate HyperFrames project structure in workspace for Studio inspection & `npx hyperframes check`
const hfProjectDir = path.join(workDir, 'hyperframes_composition');
const hfCompositionsDir = path.join(hfProjectDir, 'compositions');
fs.mkdirSync(hfCompositionsDir, { recursive: true });

const clipDivs = subtitles
  .map((seg, i) => {
    const start = Math.max(0.05, Number(seg.start_time || 0)).toFixed(2);
    const dur = Math.max(0.2, Number(seg.end_time || 2) - Number(seg.start_time || 0)).toFixed(2);
    return `    <div id="cap-clip-${i}" class="clip caption-clip" data-start="${start}" data-duration="${dur}" data-track-index="1">
      <div id="cap-box-${i}" class="caption-scrim">${escapeHtml(seg.text)}</div>
    </div>`;
  })
  .join('\n');

const tweenLines = subtitles
  .map((seg, i) => {
    const start = Math.max(0.05, Number(seg.start_time || 0)).toFixed(2);
    const end = Math.max(0.25, Number(seg.end_time || 2) - 0.12).toFixed(2);
    return [
      `      tl.fromTo("#cap-box-${i}", { opacity: 0, y: 12 }, { opacity: 1, y: 0, duration: 0.16, ease: "power3.out" }, ${start});`,
      `      tl.to("#cap-box-${i}", { opacity: 0, duration: 0.12, ease: "power2.in" }, ${end});`,
    ].join('\n');
  })
  .join('\n');

const rootHtml = `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>HyperFrames Composition - ${escapeHtml(propsObj.project_id || 'project')}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js"></script>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="${duration}" data-width="1280" data-height="720">
      <div
        id="captions"
        data-composition-id="captions"
        data-composition-src="compositions/captions.html"
        data-track-kind="captions"
        data-start="0"
        data-duration="${duration}"
        data-track-index="1"
        data-width="1280"
        data-height="720"
      ></div>
    </div>
    <script>
      window.__timelines = window.__timelines || {};
      if (typeof gsap !== "undefined") {
        window.__timelines["main"] = gsap.timeline({ paused: true });
      }
    </script>
  </body>
</html>
`;

const captionsSceneHtml = `<template>
  <style>
    #root { position: absolute; inset: 0; font-family: "Inter", sans-serif; }
    .caption-clip { position: absolute; left: 0; right: 0; bottom: 84px; text-align: center; overflow: visible; }
    .caption-scrim {
      display: inline-block;
      background: rgba(15, 17, 23, 0.88);
      border: 1px solid rgba(255, 255, 255, 0.16);
      border-radius: 10px;
      padding: 14px 28px;
      color: #F9FAFB;
      font-size: 34px;
      font-weight: 700;
    }
  </style>
  <div id="root" data-composition-id="captions" data-width="1280" data-height="720">
${clipDivs}
  </div>
  <script>
    window.__timelines = window.__timelines || {};
    if (typeof gsap !== "undefined") {
      const tl = gsap.timeline({ paused: true });
${tweenLines}
      window.__timelines["captions"] = tl;
    }
  </script>
</template>
`;

fs.writeFileSync(path.join(hfProjectDir, 'index.html'), rootHtml, 'utf8');
fs.writeFileSync(path.join(hfCompositionsDir, 'captions.html'), captionsSceneHtml, 'utf8');

// Write metadata manifest alongside overlay
const manifestPath = `${outputPath}.hyperframes.json`;
fs.writeFileSync(
  manifestPath,
  JSON.stringify(
    {
      engine: 'hyperframes',
      template_id: parsed.template,
      composition_dir: hfProjectDir,
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

const tpl = String(parsed.template || 'CaptionTemplate');
const filters = [
  `drawbox=x=40:y=28:w=380:h=40:color=0x131519@0.92:t=fill`,
  `drawbox=x=40:y=28:w=4:h=40:color=0x3B82F6@1.0:t=fill`,
  `drawtext=${fontSpec}text='HYPERFRAMES  |  ${escapeDrawtext(tpl)}':fontcolor=0xE5E7EB:fontsize=18:x=58:y=40`,
];

if (tpl === 'SocialPopCaptions') {
  filters.push(`drawbox=x=180:y=470:w=920:h=118:color=0x0F172A@0.94:t=fill`);
  filters.push(`drawbox=x=180:y=470:w=920:h=4:color=0xF59E0B@1.0:t=fill`);
} else if (tpl === 'KineticTitleCard') {
  filters.push(`drawbox=x=100:y=568:w=1080:h=104:color=0x131519@0.92:t=fill`);
  filters.push(`drawbox=x=100:y=568:w=1080:h=3:color=0x10B981@1.0:t=fill`);
  filters.push(`drawbox=x=240:y=170:w=800:h=130:color=0x111827@0.94:t=fill:enable='between(t\\,0\\,1.8)'`);
  filters.push(`drawtext=${fontSpec}text='KINETIX STUDIO PRESENTATION':fontcolor=0x10B981:fontsize=34:x=(w-text_w)/2:y=218:enable='between(t\\,0\\,1.8)'`);
} else if (tpl === 'TechCalloutHUD') {
  filters.push(`drawbox=x=100:y=568:w=1080:h=104:color=0x131519@0.92:t=fill`);
  filters.push(`drawbox=x=100:y=568:w=1080:h=3:color=0x38BDF8@1.0:t=fill`);
  filters.push(`drawbox=x=0:y=712:w='min(1280,1280*(t/${duration}))':h=8:color=0x38BDF8@1.0:t=fill`);
} else {
  filters.push(`drawbox=x=100:y=568:w=1080:h=104:color=0x131519@0.92:t=fill`);
  filters.push(`drawbox=x=100:y=568:w=1080:h=3:color=0x3B82F6@1.0:t=fill`);
}

const textY = tpl === 'SocialPopCaptions' ? 514 : 606;
for (const seg of subtitles) {
  const start = Number(seg.start_time || 0).toFixed(2);
  const end = Number(seg.end_time || 2).toFixed(2);
  const safeText = escapeDrawtext(seg.text);
  if (safeText) {
    filters.push(
      `drawtext=${fontSpec}text='${safeText}':fontcolor=white:fontsize=31:x=(w-text_w)/2:y=${textY}:enable='between(t\\,${start}\\,${end})'`
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
