import React from 'react';
import { Composition } from 'remotion';
import { CaptionTemplate } from './CaptionTemplate';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="CaptionTemplate"
        component={CaptionTemplate}
        durationInFrames={180}
        fps={30}
        width={1280}
        height={720}
        defaultProps={{
          subtitles: [
            { start_time: 0, end_time: 2, text: 'KinetixAI Remotion Engine' },
            { start_time: 2, end_time: 4, text: 'Clean Architecture + SOLID' },
            { start_time: 4, end_time: 6, text: 'Automated Video Pipeline' },
          ],
        }}
      />
    </>
  );
};
