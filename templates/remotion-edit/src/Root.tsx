import React from 'react';
import {Composition, registerRoot} from 'remotion';
import {AiEdit} from './AiEdit';
import {Compare} from './Compare';
import edit from './edit.json';

const Root: React.FC = () => (
  <>
    <Composition id="AiEdit" component={AiEdit} durationInFrames={edit.durationInFrames} fps={30} width={1080} height={1920} />
    <Composition id="Compare" component={Compare} durationInFrames={edit.durationInFrames} fps={30} width={1080} height={1920} />
  </>
);
registerRoot(Root);
