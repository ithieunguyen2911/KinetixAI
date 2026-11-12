import React from 'react';
import { AbsoluteFill, Sequence, useCurrentFrame, useVideoConfig, interpolate, spring } from 'remotion';

export interface WordTimestampItem {
  word: string;
  start_time: number;
  end_time: number;
}

export interface SubtitleItem {
  start_time: number;
  end_time: number;
  text: string;
  words?: WordTimestampItem[];
}

export interface CaptionTemplateProps {
  subtitles: SubtitleItem[];
  project_id?: string;
}

const CaptionCard: React.FC<{ segment: SubtitleItem; currentTime: number }> = ({
  segment,
  currentTime,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const translateY = spring({
    frame,
    fps,
    config: { damping: 18, stiffness: 180 },
  });

  const opacity = interpolate(frame, [0, 5], [0, 1], {
    extrapolateRight: 'clamp',
  });

  const hasWords = Array.isArray(segment.words) && segment.words.length > 0;

  return (
    <div
      style={{
        transform: `translateY(${(1 - translateY) * 14}px)`,
        opacity,
        backgroundColor: 'rgba(19, 21, 25, 0.90)',
        borderTop: '2px solid #2563EB',
        borderRadius: 10,
        padding: '16px 32px',
        color: '#F9FAFB',
        fontFamily: 'Inter, Segoe UI, sans-serif',
        fontSize: 34,
        fontWeight: 700,
        textAlign: 'center',
        maxWidth: 1040,
      }}
    >
      {hasWords
        ? segment.words!.map((w, idx) => {
            const isActive = currentTime >= w.start_time && currentTime <= w.end_time;
            return (
              <span
                key={idx}
                style={{
                  color: isActive ? '#60A5FA' : '#F9FAFB',
                  marginRight: 8,
                  transition: 'color 80ms ease',
                }}
              >
                {w.word}
              </span>
            );
          })
        : segment.text}
    </div>
  );
};

export const CaptionTemplate: React.FC<CaptionTemplateProps> = ({ subtitles = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: 'transparent',
        justifyContent: 'flex-end',
        alignItems: 'center',
        paddingBottom: 72,
      }}
    >
      {subtitles.map((seg, index) => {
        const fromFrame = Math.max(0, Math.round(seg.start_time * fps));
        const durationInFrames = Math.max(1, Math.round((seg.end_time - seg.start_time) * fps));
        return (
          <Sequence
            key={index}
            from={fromFrame}
            durationInFrames={durationInFrames}
            layout="none"
          >
            <CaptionCard segment={seg} currentTime={currentTime} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
