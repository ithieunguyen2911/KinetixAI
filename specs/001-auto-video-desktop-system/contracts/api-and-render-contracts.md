# Interface & API Contracts: KinetixAI (FlowVids-AI) v3.0 Studio Expansion

## 1. New Domain Interfaces (`src/domain/interfaces/`)
- `IVoiceSynthesizer(ABC)`: `list_voices()`, `synthesize(text, output_path, voice_id, rate, pitch_hz) -> Path`
- `IAudioAssetLibrary(ABC)`: `list_bgm_presets()`, `list_sfx_presets()`, `resolve_bgm(preset_id, output_dir, duration_sec) -> Path`, `resolve_sfx(sfx_id, output_dir) -> Path`
- `IVideoProcessor(ABC)` extensions:
  - `apply_transition_and_animation(video_path, output_path, transition_preset, animation_preset) -> Path`
  - `detect_beats_and_cut(video_path, output_path, bpm, pulse_flash) -> Tuple[Path, List[float]]`
  - `insert_sfx_track(video_path, sfx_path, output_path, timestamp_sec, volume) -> Path`

## 2. New v3.0 FastAPI REST Endpoints
| Method | Endpoint | Purpose |
| :--- | :--- | :--- |
| `GET` | `/api/v1/catalog/studio` | List voices, BGM presets, SFX presets, transitions, and animations |
| `POST` | `/api/v1/projects/{id}/clone` | Clone (duplicate) project assets, scenes, characters, and subtitles |
| `DELETE` | `/api/v1/projects/{id}` | Delete project workspace & metadata |
| `POST` | `/api/v1/projects/{id}/context` | Update global `SceneContext` (World/Visual/Lighting/Camera/Continuity) |
| `POST` | `/api/v1/projects/{id}/scenes` | Add, Update, Clone, or Delete a `StoryScene` (`action`: `upsert\|clone\|delete`) |
| `POST` | `/api/v1/projects/{id}/characters` | Add, Update, Clone, or Delete a `CharacterProfile` (`action`: `upsert\|clone\|delete`) |
| `POST` | `/api/v1/projects/{id}/voiceover` | Generate TTS voiceover audio track and mux onto project video |
| `POST` | `/api/v1/projects/{id}/sound-library` | Mix curated BGM preset and/or insert timestamped SFX cue |
| `POST` | `/api/v1/projects/{id}/fx-motion` | Apply `transition_preset` and `animation_preset` via FFmpeg + Motion Engines |
| `POST` | `/api/v1/projects/{id}/beat-cut` | Generate BPM beat grid (`.beats.json`), align subtitles to beats, and apply pulse FX |
| `POST` | `/api/v1/projects/{id}/timeline-clips` | Add, Update, Split, Clone, Delete, or Render interactive Multi-Track Timeline clips |
| `POST` | `/api/v1/projects/{id}/podcast` | Generate multi-voice expressive Podcast/Storytelling MP4 across 6 genres |
| `POST` | `/api/v1/projects/{id}/dubbing` | Time-aligned AI Video Dubbing into target language |
| `POST` | `/api/v1/voices/design` | Design synthetic VoiceProfile from prompt description & seed |
| `POST` | `/api/v1/voices/clone` | Consent-gated Voice Cloning from clean reference audio |
| `GET` | `/api/v1/voices/profiles` | List all built-in + custom designed/cloned VoiceProfiles |

---

## 3. v6.1 FullScreen Cinema Interaction & Keybinding Contract (US14)

### 3.1 UI Navigation & Interaction Mappings
| Trigger / Event | Source Control | Action / Contract |
| :--- | :--- | :--- |
| **Click `BtnFullScreen`** | Transport Deck (`MainWindow.xaml`) | Pauses `VideoPlayer`, transfers active media URI & position, opens `FullScreenPlayerWindow`. |
| **Double-Click Monitor** | `VideoPlayer` / `MonitorBorder` | Toggles Fullscreen Cinema View. |
| **`F11` or `F` Key** | Global Window `KeyDown` | Toggles between normal NLE layout and FullScreen Cinema mode. |
| **`Space` Key** | `KeyDown` (Cinema Window) | Toggles Play / Pause of the active media stream. |
| **`Esc` Key** | `KeyDown` (Cinema Window) | Closes Cinema Window, passes `ExitPosition` back to `MainWindow`, and restores NLE state. |
| **`Left Arrow` (`←`)** | `KeyDown` (Cinema Window) | Jumps backward 5.0 seconds (`Position = Position - 5s`). |
| **`Right Arrow` (`→`)** | `KeyDown` (Cinema Window) | Jumps forward 5.0 seconds (`Position = Position + 5s`). |
| **`M` Key** | `KeyDown` (Cinema Window) | Toggles audio mute state. |
| **Mouse Move** | Root Canvas (`FullScreenPlayerWindow`) | Restores Glass HUD opacity to `1.0` and resets the 2.5s idle countdown timer. |
| **Mouse Idle (2.5s)** | `DispatcherTimer` Tick | Fades Glass HUD opacity to `0.0` for 100% unobstructed cinema view. |

### 3.2 WPF Window Constructor Contract
```csharp
public partial class FullScreenPlayerWindow : Window
{
    public FullScreenPlayerWindow(string mediaPath, TimeSpan initialPosition, bool isPlaying, double volume);
    public TimeSpan ExitPosition { get; }
    public bool WasPlaying { get; }
}
```
