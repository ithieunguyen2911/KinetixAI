using System;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Threading;
using KinetixAI.Desktop.Models;
using Microsoft.Win32;

namespace KinetixAI.Desktop;

public partial class MainWindow : Window
{
    private readonly HttpClient _http = new() { BaseAddress = new Uri("http://127.0.0.1:8000"), Timeout = TimeSpan.FromMinutes(5) };
    private readonly DispatcherTimer _mcpSyncTimer = new() { Interval = TimeSpan.FromSeconds(3) };
    private readonly DispatcherTimer _playheadTimer = new() { Interval = TimeSpan.FromMilliseconds(50) };
    private Process? _backendProcess;
    private ProjectResponseDto? _currentProject;
    private int _knownProjectCount;
    private bool _isPlaying;
    private double _videoDurationSeconds = 6.0;

    public ObservableCollection<SubtitleSegmentDto> SubtitleItems { get; } = new();
    public ObservableCollection<ProjectResponseDto> ProjectItems { get; } = new();
    public ObservableCollection<TimelineClipBlockVm> TimelineSubtitleBlocks { get; } = new();

    public MainWindow()
    {
        InitializeComponent();
        GridSubtitles.ItemsSource = SubtitleItems;
        LstProjects.ItemsSource = ProjectItems;
        IcTimelineSubtitles.ItemsSource = TimelineSubtitleBlocks;
        _mcpSyncTimer.Tick += McpSyncTimer_Tick;
        _playheadTimer.Tick += PlayheadTimer_Tick;
        Loaded += MainWindow_Loaded;
        Closed += MainWindow_Closed;
    }

    private async void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        AppendLog("Kinetix Studio NLE v2.0 initialized. Verifying Core Orchestrator & MCP bridge...");
        await EnsureBackendRunningAsync();
        await RefreshProjectsAsync(selectLatestIfNew: true);
        _mcpSyncTimer.Start();
    }

    private void MainWindow_Closed(object? sender, EventArgs e)
    {
        _mcpSyncTimer.Stop();
        _playheadTimer.Stop();
        try
        {
            VideoPlayer.Stop();
            VideoPlayer.Close();
            if (_backendProcess is { HasExited: false })
            {
                _backendProcess.Kill(entireProcessTree: true);
            }
        }
        catch
        {
            // Ignore shutdown cleanup errors
        }
    }

    private async void McpSyncTimer_Tick(object? sender, EventArgs e)
    {
        await RefreshProjectsAsync(selectLatestIfNew: true);
    }

    private void PlayheadTimer_Tick(object? sender, EventArgs e)
    {
        if (!_isPlaying || !VideoPlayer.NaturalDuration.HasTimeSpan) return;
        var pos = VideoPlayer.Position.TotalSeconds;
        var total = Math.Max(0.5, VideoPlayer.NaturalDuration.TimeSpan.TotalSeconds);
        SliderScrub.Value = pos;
        TxtTimecode.Text = $"{pos:00.00}s / {total:00.00}s";
        UpdatePlayheadCursorPosition(pos, total);
    }

    private void UpdatePlayheadCursorPosition(double currentSec, double totalSec)
    {
        double trackWidth = Math.Max(100.0, TimelineTrackArea.ActualWidth);
        double ratio = Math.Clamp(currentSec / Math.Max(0.5, totalSec), 0.0, 1.0);
        Canvas.SetLeft(PlayheadLine, ratio * (trackWidth - 2));
    }

    private void RebuildVisualTimeline()
    {
        double totalDur = Math.Max(1.0, _videoDurationSeconds);
        double trackWidth = Math.Max(200.0, TimelineTrackArea.ActualWidth);

        TxtRuler1.Text = $"00:{(totalDur * 0.2):00.0}";
        TxtRuler2.Text = $"00:{(totalDur * 0.4):00.0}";
        TxtRuler3.Text = $"00:{(totalDur * 0.6):00.0}";
        TxtRuler4.Text = $"00:{(totalDur * 0.8):00.0}";
        TxtRuler5.Text = $"00:{totalDur:00.0}";

        TimelineSubtitleBlocks.Clear();
        foreach (var seg in SubtitleItems)
        {
            double left = (seg.StartTime / totalDur) * trackWidth;
            double width = Math.Max(24.0, ((seg.EndTime - seg.StartTime) / totalDur) * trackWidth - 2);
            TimelineSubtitleBlocks.Add(new TimelineClipBlockVm
            {
                Label = $"{seg.StartTime:0.0}s: {seg.Text}",
                StartTime = seg.StartTime,
                EndTime = seg.EndTime,
                LeftPx = Math.Max(0, left),
                WidthPx = width,
            });
        }

        if (_currentProject != null)
        {
            TxtTrackV2.Text = $"{_currentProject.EngineUpper} OVERLAY  |  {_currentProject.TemplateId}  ({SubtitleItems.Count} cues)";
        }
    }

    private void TimelineTrackArea_SizeChanged(object sender, SizeChangedEventArgs e)
    {
        RebuildVisualTimeline();
    }

    private void TimelineCanvas_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        double width = Math.Max(1.0, TimelineTrackArea.ActualWidth);
        var pt = e.GetPosition(TimelineTrackArea);
        double targetSec = Math.Clamp(pt.X / width, 0.0, 1.0) * _videoDurationSeconds;
        SeekMonitorTo(targetSec);
    }

    private void SubtitleTimelineBlock_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (sender is FrameworkElement fe && fe.DataContext is TimelineClipBlockVm block)
        {
            SeekMonitorTo(block.StartTime);
            e.Handled = true;
        }
    }

    private void SeekMonitorTo(double seconds)
    {
        double clamped = Math.Clamp(seconds, 0.0, _videoDurationSeconds);
        SliderScrub.Value = clamped;
        TxtTimecode.Text = $"{clamped:00.00}s / {_videoDurationSeconds:00.00}s";
        UpdatePlayheadCursorPosition(clamped, _videoDurationSeconds);
        if (VideoPlayer.Source != null)
        {
            VideoPlayer.Position = TimeSpan.FromSeconds(clamped);
        }
    }

    private string FindRepositoryRoot()
    {
        var dir = new DirectoryInfo(AppDomain.CurrentDomain.BaseDirectory);
        while (dir != null)
        {
            if (File.Exists(Path.Combine(dir.FullName, "pyproject.toml")))
            {
                return dir.FullName;
            }
            dir = dir.Parent;
        }
        return Directory.GetCurrentDirectory();
    }

    private async Task EnsureBackendRunningAsync()
    {
        if (await IsBackendHealthyAsync())
        {
            TxtBackendStatus.Text = "Core API: Online";
            DotBackend.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#10B981"));
            return;
        }

        var repoRoot = FindRepositoryRoot();
        AppendLog($"Starting Python FastAPI Core Orchestrator in {repoRoot}...");
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = "uv",
                Arguments = "run uvicorn src.presentation.api.main:app --host 127.0.0.1 --port 8000",
                WorkingDirectory = repoRoot,
                UseShellExecute = false,
                CreateNoWindow = true,
            };
            _backendProcess = Process.Start(psi);

            for (int i = 0; i < 20; i++)
            {
                await Task.Delay(500);
                if (await IsBackendHealthyAsync())
                {
                    TxtBackendStatus.Text = "Core API: Online";
                    DotBackend.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#10B981"));
                    AppendLog("FastAPI Core Orchestrator online at http://127.0.0.1:8000.");
                    return;
                }
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Warning: Could not auto-start FastAPI via uv: {ex.Message}");
        }

        TxtBackendStatus.Text = "Core API: Offline";
        DotBackend.Fill = new SolidColorBrush((Color)ColorConverter.ConvertFromString("#EF4444"));
    }

    private async Task<bool> IsBackendHealthyAsync()
    {
        try
        {
            var health = await _http.GetFromJsonAsync<HealthResponseDto>("/api/v1/health");
            return health?.Status == "ok";
        }
        catch
        {
            return false;
        }
    }

    private async Task RefreshProjectsAsync(bool selectLatestIfNew = false)
    {
        try
        {
            var list = await _http.GetFromJsonAsync<ProjectResponseDto[]>("/api/v1/projects");
            if (list == null) return;

            TxtProjectCount.Text = $"{list.Length} items";

            bool countChanged = list.Length != ProjectItems.Count;
            if (countChanged)
            {
                ProjectItems.Clear();
                foreach (var item in list.Reverse())
                {
                    ProjectItems.Add(item);
                }
            }

            if (list.Length > 0 && (_currentProject == null || (selectLatestIfNew && list.Length > _knownProjectCount)))
            {
                var newest = list.Last();
                if (_knownProjectCount > 0 && list.Length > _knownProjectCount)
                {
                    AppendLog($"[MCP Sync] New project synced: '{newest.ProjectId}' ({newest.EngineUpper}) -> {newest.FinalOutputPath}");
                }
                _knownProjectCount = list.Length;
                await BindProjectAsync(newest);
            }
            else
            {
                _knownProjectCount = list.Length;
            }
        }
        catch
        {
            // Silent during background polling
        }
    }

    private async Task BindProjectAsync(ProjectResponseDto project)
    {
        _currentProject = project;
        TxtProjectId.Text = project.ProjectId;
        TxtSourceUrl.Text = project.SourceUrl;
        CmbEngineType.SelectedIndex = project.EngineType == "hyperframes" ? 1 : 0;

        for (int i = 0; i < CmbTemplateId.Items.Count; i++)
        {
            if (CmbTemplateId.Items[i] is ComboBoxItem item &&
                string.Equals(item.Tag?.ToString(), project.TemplateId, StringComparison.OrdinalIgnoreCase))
            {
                CmbTemplateId.SelectedIndex = i;
                break;
            }
        }

        TxtStepStatus.Text = project.CurrentStep;
        TxtProgressPercent.Text = $"{project.ProgressPercent}%";
        PbPipeline.Value = project.ProgressPercent;
        TxtOutputPath.Text = string.IsNullOrWhiteSpace(project.FinalOutputPath)
            ? string.Empty
            : project.FinalOutputPath;
        TxtStatusRight.Text = $"Active Project: {project.ProjectId} [{project.EngineUpper} | {project.TemplateId}]";

        SubtitleItems.Clear();
        foreach (var seg in project.Subtitles)
        {
            SubtitleItems.Add(seg);
        }

        await LoadMediaProbeSpecsAsync(project.ProjectId);
        RebuildVisualTimeline();
        LoadVideoIntoMonitor(project.FinalOutputPath);
    }

    private void LoadVideoIntoMonitor(string? videoPath)
    {
        try
        {
            _playheadTimer.Stop();
            _isPlaying = false;
            BtnPlayPause.Content = "Play";
            VideoPlayer.Stop();
            VideoPlayer.Source = null;

            if (!string.IsNullOrWhiteSpace(videoPath) && File.Exists(videoPath))
            {
                TxtVideoPlaceholder.Visibility = Visibility.Collapsed;
                VideoPlayer.Source = new Uri(videoPath, UriKind.Absolute);
                VideoPlayer.Play();
                _isPlaying = true;
                BtnPlayPause.Content = "Pause";
                _playheadTimer.Start();
            }
            else
            {
                TxtVideoPlaceholder.Visibility = Visibility.Visible;
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Monitor warning: {ex.Message}");
        }
    }

    private async Task LoadMediaProbeSpecsAsync(string projectId)
    {
        try
        {
            var probe = await _http.GetFromJsonAsync<MediaProbeDto>($"/api/v1/projects/{projectId}/probe");
            if (probe == null) return;
            _videoDurationSeconds = probe.DurationSeconds > 0 ? probe.DurationSeconds : 6.0;
            SliderScrub.Maximum = _videoDurationSeconds;
            TxtSpecResolution.Text = $"RES: {probe.Resolution}";
            TxtSpecFps.Text = $"FPS: {probe.Fps:0.00}";
            TxtSpecCodec.Text = $"VID: {probe.VideoCodec}";
            TxtSpecAudio.Text = $"AUD: {probe.AudioCodec} / {probe.SampleRate}Hz";
            TxtSpecDuration.Text = $"DUR: {probe.DurationSeconds:0.00}s";
            TxtSpecSize.Text = $"SIZE: {(probe.SizeBytes / 1024.0):0.0} KB";
            TxtTrimEnd.Text = probe.DurationSeconds.ToString("0.00", CultureInfo.InvariantCulture);
            TxtTrackV1.Text = $"MASTER VIDEO STREAM ({probe.VideoCodec} • {probe.Resolution} • {probe.Fps:0.00} fps • {probe.DurationSeconds:0.00}s)";
            TxtTrackA1.Text = $"AUDIO STREAM  ▂▄▆█▄▂▅▇▃▂▆█▄▂▅▇▃▂▆█▄▂  ({probe.AudioCodec.ToUpperInvariant()} / {probe.SampleRate}Hz)";
            TxtTimelineSummary.Text = $"4 Tracks Active (V2, V1, S1, A1) | {probe.Resolution} @ {probe.Fps:0.00} fps";
        }
        catch
        {
            // Ignore probe errors if video not yet built
        }
    }

    private void VideoPlayer_MediaOpened(object sender, RoutedEventArgs e)
    {
        if (VideoPlayer.NaturalDuration.HasTimeSpan)
        {
            _videoDurationSeconds = VideoPlayer.NaturalDuration.TimeSpan.TotalSeconds;
            SliderScrub.Maximum = _videoDurationSeconds;
            TxtTimecode.Text = $"00.00s / {_videoDurationSeconds:00.00}s";
            RebuildVisualTimeline();
        }
    }

    private void VideoPlayer_MediaEnded(object sender, RoutedEventArgs e)
    {
        VideoPlayer.Position = TimeSpan.Zero;
        VideoPlayer.Play();
    }

    private void BtnPlayPause_Click(object sender, RoutedEventArgs e)
    {
        if (VideoPlayer.Source == null) return;
        if (_isPlaying)
        {
            VideoPlayer.Pause();
            _isPlaying = false;
            BtnPlayPause.Content = "Play";
        }
        else
        {
            VideoPlayer.Play();
            _isPlaying = true;
            BtnPlayPause.Content = "Pause";
            _playheadTimer.Start();
        }
    }

    private void BtnStopVideo_Click(object sender, RoutedEventArgs e)
    {
        if (VideoPlayer.Source == null) return;
        VideoPlayer.Stop();
        _isPlaying = false;
        BtnPlayPause.Content = "Play";
        SeekMonitorTo(0.0);
    }

    private void BtnStepBack_Click(object sender, RoutedEventArgs e)
    {
        if (VideoPlayer.Source == null) return;
        VideoPlayer.Pause();
        _isPlaying = false;
        BtnPlayPause.Content = "Play";
        double target = Math.Max(0.0, SliderScrub.Value - (1.0 / 30.0));
        SeekMonitorTo(target);
    }

    private void BtnStepForward_Click(object sender, RoutedEventArgs e)
    {
        if (VideoPlayer.Source == null) return;
        VideoPlayer.Pause();
        _isPlaying = false;
        BtnPlayPause.Content = "Play";
        double target = Math.Min(_videoDurationSeconds, SliderScrub.Value + (1.0 / 30.0));
        SeekMonitorTo(target);
    }

    private void BtnMarkIn_Click(object sender, RoutedEventArgs e)
    {
        TxtTrimStart.Text = SliderScrub.Value.ToString("0.00", CultureInfo.InvariantCulture);
        AppendLog($"Marked Trim IN at {SliderScrub.Value:0.00}s");
    }

    private void BtnMarkOut_Click(object sender, RoutedEventArgs e)
    {
        TxtTrimEnd.Text = SliderScrub.Value.ToString("0.00", CultureInfo.InvariantCulture);
        AppendLog($"Marked Trim OUT at {SliderScrub.Value:0.00}s");
    }

    private void SliderScrub_PreviewMouseLeftButtonUp(object sender, MouseButtonEventArgs e)
    {
        SeekMonitorTo(SliderScrub.Value);
    }

    private string GetSelectedEngine()
    {
        if (CmbEngineType.SelectedItem is ComboBoxItem item && item.Content is string s)
        {
            return s.Trim().ToLowerInvariant();
        }
        return "remotion";
    }

    private string GetSelectedTemplate()
    {
        if (CmbTemplateId.SelectedItem is ComboBoxItem item && item.Tag is string t)
        {
            return t.Trim();
        }
        return "CaptionTemplate";
    }

    private async Task ReleaseVideoPlayerLockAsync()
    {
        try
        {
            _playheadTimer.Stop();
            _isPlaying = false;
            BtnPlayPause.Content = "Play";
            VideoPlayer.Stop();
            VideoPlayer.Source = null;
            VideoPlayer.Close();
            await Task.Delay(120);
        }
        catch
        {
            // Ignore media release warnings
        }
    }

    private async void BtnInspectSource_Click(object sender, RoutedEventArgs e)
    {
        BtnInspectSource.IsEnabled = false;
        try
        {
            await EnsureBackendRunningAsync();
            var url = TxtSourceUrl.Text.Trim();
            if (string.IsNullOrWhiteSpace(url)) return;

            AppendLog($"Inspecting source metadata via yt-dlp / ffprobe: {url}...");
            var response = await _http.PostAsJsonAsync("/api/v1/sources/inspect", new InspectSourceRequestDto { SourceUrl = url });
            response.EnsureSuccessStatusCode();
            var meta = await response.Content.ReadFromJsonAsync<SourceMetadataDto>();
            if (meta != null)
            {
                TxtSpecResolution.Text = $"RES: {meta.Resolution}";
                TxtSpecFps.Text = $"FPS: {meta.Fps:0.00}";
                TxtSpecDuration.Text = $"DUR: {meta.Duration:0.00}s";
                AppendLog($"Source inspected: title='{meta.Title}', type={meta.SourceType}, res={meta.Resolution}, duration={meta.Duration:0.00}s");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Source inspect error: {ex.Message}");
            MessageBox.Show(ex.Message, "Inspect Source Error", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
        finally
        {
            BtnInspectSource.IsEnabled = true;
        }
    }

    private void BtnClearScript_Click(object sender, RoutedEventArgs e)
    {
        TxtScriptText.Text = string.Empty;
        AppendLog("Script cleared. Pipeline will use automatic speech-to-text transcription (Whisper / Windows Speech STT) on the extracted WAV audio.");
    }

    private async void BtnRunAiCommand_Click(object sender, RoutedEventArgs e)
    {
        BtnRunAiCommand.IsEnabled = false;
        try
        {
            await EnsureBackendRunningAsync();
            await ReleaseVideoPlayerLockAsync();
            var prompt = TxtAiCommand.Text.Trim();
            if (string.IsNullOrWhiteSpace(prompt)) return;

            AppendLog($"[MCP Dispatch] Executing command: \"{prompt}\"");
            TxtStepStatus.Text = "Executing MCP video command...";
            PbPipeline.Value = 30;

            var req = new AiMcpCommandRequestDto
            {
                Prompt = prompt,
                SourceUrl = TxtSourceUrl.Text.Trim(),
            };
            var response = await _http.PostAsJsonAsync("/api/v1/mcp/command", req);
            response.EnsureSuccessStatusCode();
            var project = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (project != null)
            {
                await BindProjectAsync(project);
                AppendLog($"[MCP Dispatch] Completed '{project.ProjectId}' -> {project.FinalOutputPath}");
                await RefreshProjectsAsync();
            }
        }
        catch (Exception ex)
        {
            AppendLog($"MCP Command Error: {ex.Message}");
            MessageBox.Show(ex.Message, "MCP Command Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            BtnRunAiCommand.IsEnabled = true;
        }
    }

    private async void BtnRunPipeline_Click(object sender, RoutedEventArgs e)
    {
        BtnRunPipeline.IsEnabled = false;
        try
        {
            await EnsureBackendRunningAsync();
            await ReleaseVideoPlayerLockAsync();

            var engine = GetSelectedEngine();
            var template = GetSelectedTemplate();
            var scriptVal = TxtScriptText.Text.Trim();
            var req = new CreateProjectRequestDto
            {
                ProjectId = TxtProjectId.Text.Trim(),
                SourceUrl = TxtSourceUrl.Text.Trim(),
                EngineType = engine,
                TemplateId = template,
                ScriptText = string.IsNullOrWhiteSpace(scriptVal) ? null : scriptVal,
            };

            TxtStepStatus.Text = $"Running 5-Step Pipeline ({engine.ToUpperInvariant()} / {template})...";
            PbPipeline.Value = 25;
            AppendLog($"Starting pipeline for '{req.ProjectId}' [engine={req.EngineType}, template={template}, source={req.SourceUrl}]...");

            var response = await _http.PostAsJsonAsync("/api/v1/projects", req);
            if (!response.IsSuccessStatusCode)
            {
                var err = await response.Content.ReadAsStringAsync();
                AppendLog($"Pipeline error: {err}");
                MessageBox.Show(err, "Pipeline Error", MessageBoxButton.OK, MessageBoxImage.Error);
                return;
            }

            var project = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (project != null)
            {
                await BindProjectAsync(project);
                AppendLog($"Completed! Master MP4 exported: {project.FinalOutputPath}");
                await RefreshProjectsAsync();
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Execution exception: {ex.Message}");
            MessageBox.Show(ex.Message, "Execution Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            BtnRunPipeline.IsEnabled = true;
        }
    }

    private async void BtnRerenderSubtitles_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null)
        {
            MessageBox.Show("Select or execute a project first.", "No Project Active", MessageBoxButton.OK, MessageBoxImage.Information);
            return;
        }

        GridSubtitles.CommitEdit(DataGridEditingUnit.Cell, true);
        GridSubtitles.CommitEdit(DataGridEditingUnit.Row, true);

        BtnRerenderSubtitles.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();

            var engine = GetSelectedEngine();
            var template = GetSelectedTemplate();
            var req = new UpdateSubtitlesRequestDto
            {
                EngineType = engine,
                TemplateId = template,
                Subtitles = SubtitleItems.ToList(),
            };
            AppendLog($"Re-rendering '{_currentProject.ProjectId}' overlay with {engine.ToUpperInvariant()} ({template})...");
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/subtitles", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                await BindProjectAsync(updated);
                AppendLog($"Re-render complete: {updated.FinalOutputPath}");
                await RefreshProjectsAsync();
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Re-render error: {ex.Message}");
            MessageBox.Show(ex.Message, "Re-Render Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            BtnRerenderSubtitles.IsEnabled = true;
        }
    }

    private async void BtnTrimVideo_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        if (!double.TryParse(TxtTrimStart.Text, NumberStyles.Any, CultureInfo.InvariantCulture, out double startSec) ||
            !double.TryParse(TxtTrimEnd.Text, NumberStyles.Any, CultureInfo.InvariantCulture, out double endSec) ||
            endSec <= startSec)
        {
            MessageBox.Show("Enter valid Start and End seconds (End > Start).", "Invalid Trim Range", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        BtnTrimVideo.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();

            AppendLog($"Trimming '{_currentProject.ProjectId}' from {startSec:0.00}s to {endSec:0.00}s via FFmpeg...");
            var response = await _http.PostAsJsonAsync(
                $"/api/v1/projects/{_currentProject.ProjectId}/trim",
                new TrimVideoRequestDto { StartTime = startSec, EndTime = endSec }
            );
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                await BindProjectAsync(updated);
                AppendLog($"Trimmed MP4 saved: {updated.FinalOutputPath}");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Trim error: {ex.Message}");
            MessageBox.Show(ex.Message, "Trim Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            BtnTrimVideo.IsEnabled = true;
        }
    }

    private async void BtnApplySpeed_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        double speed = 1.0;
        if (CmbSpeedFactor.SelectedItem is ComboBoxItem item &&
            double.TryParse(item.Tag?.ToString(), NumberStyles.Any, CultureInfo.InvariantCulture, out double parsed))
        {
            speed = parsed;
        }

        BtnApplySpeed.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            AppendLog($"Applying playback speed {speed:0.00}x to '{_currentProject.ProjectId}' via FFmpeg (setpts + atempo)...");
            var response = await _http.PostAsJsonAsync(
                $"/api/v1/projects/{_currentProject.ProjectId}/speed",
                new SpeedChangeRequestDto { SpeedFactor = speed }
            );
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                await BindProjectAsync(updated);
                AppendLog($"Speed ramping ({speed:0.00}x) complete: {updated.FinalOutputPath}");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Speed change error: {ex.Message}");
            MessageBox.Show(ex.Message, "Speed Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            BtnApplySpeed.IsEnabled = true;
        }
    }

    private async Task ApplyAspectRatioAsync(string aspectRatio)
    {
        if (_currentProject == null) return;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            AppendLog($"Reframing '{_currentProject.ProjectId}' to {aspectRatio} via FFmpeg...");
            var response = await _http.PostAsJsonAsync(
                $"/api/v1/projects/{_currentProject.ProjectId}/reframe",
                new ReframeRequestDto { AspectRatio = aspectRatio }
            );
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                await BindProjectAsync(updated);
                AppendLog($"Reframed ({aspectRatio}) saved: {updated.FinalOutputPath}");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Reframe error: {ex.Message}");
            MessageBox.Show(ex.Message, "Reframe Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
    }

    private async void BtnAspect16x9_Click(object sender, RoutedEventArgs e) => await ApplyAspectRatioAsync("16:9");
    private async void BtnAspect9x16_Click(object sender, RoutedEventArgs e) => await ApplyAspectRatioAsync("9:16");
    private async void BtnAspect1x1_Click(object sender, RoutedEventArgs e) => await ApplyAspectRatioAsync("1:1");

    private void BtnResetColor_Click(object sender, RoutedEventArgs e)
    {
        CmbColorPreset.SelectedIndex = 0;
        SliderBrightness.Value = 0.0;
        SliderContrast.Value = 1.0;
        SliderSaturation.Value = 1.0;
    }

    private async void BtnApplyColorGrade_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        string preset = "natural";
        if (CmbColorPreset.SelectedItem is ComboBoxItem item && item.Tag is string tag)
        {
            preset = tag;
        }

        BtnApplyColorGrade.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            var req = new ColorGradeRequestDto
            {
                Preset = preset,
                Brightness = Math.Round(SliderBrightness.Value, 2),
                Contrast = Math.Round(SliderContrast.Value, 2),
                Saturation = Math.Round(SliderSaturation.Value, 2),
                Gamma = 1.0,
            };
            AppendLog($"Applying Color Grade '{preset}' (B={req.Brightness}, C={req.Contrast}, S={req.Saturation}) via FFmpeg...");
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/color-grade", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                await BindProjectAsync(updated);
                AppendLog($"Color Grade applied: {updated.FinalOutputPath}");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Color grade error: {ex.Message}");
            MessageBox.Show(ex.Message, "Color Grade Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            BtnApplyColorGrade.IsEnabled = true;
        }
    }

    private async void BtnMasterAudio_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        BtnMasterAudio.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            var req = new AudioMasterRequestDto
            {
                RemoveSilence = ChkSilenceCut.IsChecked == true,
                NormalizeLoudness = ChkLoudnorm.IsChecked == true,
                MixBgm = ChkMixBgm.IsChecked == true,
                BgmSource = "demo://bgm",
                BgVolume = 0.18,
            };
            AppendLog($"Executing Audio Mastering (SilenceCut={req.RemoveSilence}, Loudnorm={req.NormalizeLoudness}, MixBGM={req.MixBgm})...");
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/audio-master", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                await BindProjectAsync(updated);
                AppendLog($"Audio Mastering complete: {updated.FinalOutputPath}");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Audio master error: {ex.Message}");
            MessageBox.Show(ex.Message, "Audio Mastering Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            BtnMasterAudio.IsEnabled = true;
        }
    }

    private async void BtnExportSubtitles_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        BtnExportSubtitles.IsEnabled = false;
        try
        {
            var srtRes = await _http.GetAsync($"/api/v1/projects/{_currentProject.ProjectId}/subtitles/export?fmt=srt");
            var vttRes = await _http.GetAsync($"/api/v1/projects/{_currentProject.ProjectId}/subtitles/export?fmt=vtt");
            var jsonRes = await _http.GetAsync($"/api/v1/projects/{_currentProject.ProjectId}/subtitles/export?fmt=json");
            srtRes.EnsureSuccessStatusCode();
            vttRes.EnsureSuccessStatusCode();
            jsonRes.EnsureSuccessStatusCode();
            AppendLog($"Exported multi-format subtitles (.srt, .vtt, .transcript.json) for '{_currentProject.ProjectId}'.");
        }
        catch (Exception ex)
        {
            AppendLog($"Subtitle export error: {ex.Message}");
            MessageBox.Show(ex.Message, "Export Subtitles Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            BtnExportSubtitles.IsEnabled = true;
        }
    }

    private async void BtnSnapshot_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        BtnSnapshot.IsEnabled = false;
        try
        {
            double ts = Math.Max(0.0, SliderScrub.Value);
            var response = await _http.PostAsJsonAsync(
                $"/api/v1/projects/{_currentProject.ProjectId}/snapshot",
                new SnapshotRequestDto { TimestampSec = ts }
            );
            response.EnsureSuccessStatusCode();
            var snap = await response.Content.ReadFromJsonAsync<SnapshotResponseDto>();
            if (snap != null && File.Exists(snap.SnapshotPath))
            {
                AppendLog($"Snapshot PNG captured at {snap.TimestampSec:0.00}s -> {snap.SnapshotPath}");
                Process.Start(new ProcessStartInfo(snap.SnapshotPath) { UseShellExecute = true });
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Snapshot error: {ex.Message}");
        }
        finally
        {
            BtnSnapshot.IsEnabled = true;
        }
    }

    private void BtnAddSubtitleRow_Click(object sender, RoutedEventArgs e)
    {
        double lastEnd = SubtitleItems.Count > 0 ? SubtitleItems.Max(s => s.EndTime) : 0.0;
        SubtitleItems.Add(new SubtitleSegmentDto
        {
            StartTime = Math.Round(lastEnd, 2),
            EndTime = Math.Round(lastEnd + 2.0, 2),
            Text = "New caption segment",
        });
        RebuildVisualTimeline();
    }

    private void BtnSplitSubtitleCue_Click(object sender, RoutedEventArgs e)
    {
        double playhead = SliderScrub.Value;
        var targetCue = SubtitleItems.FirstOrDefault(s => playhead > s.StartTime + 0.2 && playhead < s.EndTime - 0.2)
                        ?? GridSubtitles.SelectedItem as SubtitleSegmentDto;
        if (targetCue == null)
        {
            AppendLog("Move playhead inside a subtitle cue (or select a cue) to split it.");
            return;
        }

        double splitPoint = (playhead > targetCue.StartTime + 0.2 && playhead < targetCue.EndTime - 0.2)
            ? Math.Round(playhead, 2)
            : Math.Round((targetCue.StartTime + targetCue.EndTime) / 2.0, 2);

        var words = targetCue.Text.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        int midIdx = Math.Max(1, words.Length / 2);
        string firstText = words.Length > 1 ? string.Join(" ", words.Take(midIdx)) : targetCue.Text + " (1)";
        string secondText = words.Length > 1 ? string.Join(" ", words.Skip(midIdx)) : targetCue.Text + " (2)";

        double origEnd = targetCue.EndTime;
        targetCue.EndTime = splitPoint;
        targetCue.Text = firstText;

        int insertIdx = SubtitleItems.IndexOf(targetCue) + 1;
        SubtitleItems.Insert(insertIdx, new SubtitleSegmentDto
        {
            StartTime = splitPoint,
            EndTime = origEnd,
            Text = secondText,
        });
        GridSubtitles.Items.Refresh();
        RebuildVisualTimeline();
        AppendLog($"Split subtitle cue at {splitPoint:0.00}s into two cues.");
    }

    private void BtnRemoveSubtitleRow_Click(object sender, RoutedEventArgs e)
    {
        if (GridSubtitles.SelectedItem is SubtitleSegmentDto selected)
        {
            SubtitleItems.Remove(selected);
        }
        else if (SubtitleItems.Count > 0)
        {
            SubtitleItems.RemoveAt(SubtitleItems.Count - 1);
        }
        RebuildVisualTimeline();
    }

    private void BtnBrowseFile_Click(object sender, RoutedEventArgs e)
    {
        var dlg = new OpenFileDialog
        {
            Filter = "Video Files (*.mp4;*.mov;*.mkv;*.webm)|*.mp4;*.mov;*.mkv;*.webm|All Files (*.*)|*.*",
            Title = "Select Source Video File"
        };
        if (dlg.ShowDialog() == true)
        {
            TxtSourceUrl.Text = dlg.FileName;
        }
    }

    private async void BtnRefreshProjects_Click(object sender, RoutedEventArgs e)
    {
        await EnsureBackendRunningAsync();
        await RefreshProjectsAsync();
    }

    private async void LstProjects_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (LstProjects.SelectedItem is not ProjectResponseDto selected) return;
        try
        {
            var proj = await _http.GetFromJsonAsync<ProjectResponseDto>($"/api/v1/projects/{selected.ProjectId}");
            if (proj != null)
            {
                await BindProjectAsync(proj);
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Failed to load project '{selected.ProjectId}': {ex.Message}");
        }
    }

    private void BtnOpenVideo_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject?.FinalOutputPath is string path && File.Exists(path))
        {
            Process.Start(new ProcessStartInfo(path) { UseShellExecute = true });
        }
        else
        {
            MessageBox.Show("Final MP4 file does not exist yet. Run the pipeline first.", "File Not Found", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    private void BtnOpenFolder_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject?.FinalOutputPath is string path && File.Exists(path))
        {
            var dir = Path.GetDirectoryName(path);
            if (!string.IsNullOrEmpty(dir))
            {
                Process.Start(new ProcessStartInfo("explorer.exe", dir) { UseShellExecute = true });
                return;
            }
        }
        var repoRoot = FindRepositoryRoot();
        Process.Start(new ProcessStartInfo("explorer.exe", Path.Combine(repoRoot, "workspace")) { UseShellExecute = true });
    }

    private void AppendLog(string message)
    {
        TxtLogs.AppendText($"[{DateTime.Now:HH:mm:ss}] {message}{Environment.NewLine}");
        TxtLogs.ScrollToEnd();
    }
}
