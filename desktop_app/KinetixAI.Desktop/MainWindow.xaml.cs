using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
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
    private bool _suppressProjectSelectionChanged;
    private double _videoDurationSeconds = 6.0;
    private string? _selectedClipId;

    public ObservableCollection<SubtitleSegmentDto> SubtitleItems { get; } = new();
    public ObservableCollection<ProjectResponseDto> ProjectItems { get; } = new();
    public ObservableCollection<StorySceneDto> SceneItems { get; } = new();
    public ObservableCollection<CharacterProfileDto> CharacterItems { get; } = new();
    public ObservableCollection<AuditLogEntryDto> AuditLogItems { get; } = new();
    public ObservableCollection<TimelineClipBlockVm> TimelineV2Blocks { get; } = new();
    public ObservableCollection<TimelineClipBlockVm> TimelineV1Blocks { get; } = new();
    public ObservableCollection<TimelineClipBlockVm> TimelineSubtitleBlocks { get; } = new();
    public ObservableCollection<TimelineClipBlockVm> TimelineA1Blocks { get; } = new();
    public ObservableCollection<TimelineClipBlockVm> TimelineBeatMarkers { get; } = new();

    public MainWindow()
    {
        InitializeComponent();
        GridSubtitles.ItemsSource = SubtitleItems;
        GridScenes.ItemsSource = SceneItems;
        GridCharacters.ItemsSource = CharacterItems;
        GridAuditLogs.ItemsSource = AuditLogItems;
        LstProjects.ItemsSource = ProjectItems;
        IcTimelineV2.ItemsSource = TimelineV2Blocks;
        IcTimelineV1.ItemsSource = TimelineV1Blocks;
        IcTimelineSubtitles.ItemsSource = TimelineSubtitleBlocks;
        IcTimelineA1.ItemsSource = TimelineA1Blocks;
        IcTimelineBeats.ItemsSource = TimelineBeatMarkers;

        _mcpSyncTimer.Tick += McpSyncTimer_Tick;
        _playheadTimer.Tick += PlayheadTimer_Tick;
        Loaded += MainWindow_Loaded;
        Closed += MainWindow_Closed;
    }

    private async void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        AppendLog("Kinetix Studio v5.0 initialized (Interactive Timeline CRUD, Podcast AI, VoiceStudio Cloning/Design).");
        await EnsureBackendRunningAsync();
        await RefreshCustomVoicesAsync();
        await RefreshProjectsAsync(selectLatestIfNew: true, forceReloadList: true);
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
        double maxClipEnd = _currentProject?.TimelineClips?.Count > 0
            ? _currentProject.TimelineClips.Max(c => c.EndTime)
            : 0.0;
        double totalDur = Math.Max(1.0, Math.Max(_videoDurationSeconds, maxClipEnd));
        double trackWidth = Math.Max(200.0, TimelineTrackArea.ActualWidth);

        TxtRuler1.Text = $"00:{(totalDur * 0.2):00.0}";
        TxtRuler2.Text = $"00:{(totalDur * 0.4):00.0}";
        TxtRuler3.Text = $"00:{(totalDur * 0.6):00.0}";
        TxtRuler4.Text = $"00:{(totalDur * 0.8):00.0}";
        TxtRuler5.Text = $"00:{totalDur:00.0}";

        TimelineV2Blocks.Clear();
        TimelineV1Blocks.Clear();
        TimelineSubtitleBlocks.Clear();
        TimelineA1Blocks.Clear();
        TimelineBeatMarkers.Clear();

        var clips = _currentProject?.TimelineClips;
        if (clips != null && clips.Count > 0)
        {
            foreach (var c in clips)
            {
                double left = (c.StartTime / totalDur) * trackWidth;
                double width = Math.Max(22.0, ((c.EndTime - c.StartTime) / totalDur) * trackWidth - 2);
                bool sel = string.Equals(c.ClipId, _selectedClipId, StringComparison.OrdinalIgnoreCase);

                var (bg, border) = c.TrackId.ToUpperInvariant() switch
                {
                    "V2" => ("#172554", sel ? "#FFFFFF" : "#3B82F6"),
                    "V1" => ("#064E3B", sel ? "#FFFFFF" : "#10B981"),
                    "S1" => ("#422006", sel ? "#FFFFFF" : "#F59E0B"),
                    "A1" => ("#2E1065", sel ? "#FFFFFF" : "#8B5CF6"),
                    _ => ("#0C4A6E", sel ? "#FFFFFF" : "#38BDF8"),
                };

                var vm = new TimelineClipBlockVm
                {
                    ClipId = c.ClipId,
                    TrackId = c.TrackId.ToUpperInvariant(),
                    Label = c.TrackId.Equals("S1", StringComparison.OrdinalIgnoreCase)
                        ? $"{c.StartTime:0.0}s: {c.Label}"
                        : c.Label,
                    StartTime = c.StartTime,
                    EndTime = c.EndTime,
                    LeftPx = Math.Max(0, left),
                    WidthPx = width,
                    BackgroundHex = bg,
                    BorderHex = border,
                    BorderThicknessStr = sel ? "2" : "1",
                };

                switch (vm.TrackId)
                {
                    case "V2": TimelineV2Blocks.Add(vm); break;
                    case "V1": TimelineV1Blocks.Add(vm); break;
                    case "S1": TimelineSubtitleBlocks.Add(vm); break;
                    case "A1": TimelineA1Blocks.Add(vm); break;
                    case "B1":
                        vm.WidthPx = 9;
                        vm.LeftPx = Math.Max(0, left - 4);
                        TimelineBeatMarkers.Add(vm);
                        break;
                }
            }
        }
        else if (_currentProject != null)
        {
            TimelineV2Blocks.Add(new TimelineClipBlockVm { ClipId = "v2_overlay_01", TrackId = "V2", Label = $"{_currentProject.EngineUpper} | {_currentProject.TemplateId}", StartTime = 0, EndTime = totalDur, LeftPx = 0, WidthPx = Math.Max(40, trackWidth - 2), BackgroundHex = "#172554", BorderHex = "#3B82F6" });
            TimelineV1Blocks.Add(new TimelineClipBlockVm { ClipId = "v1_video_01", TrackId = "V1", Label = $"MASTER VIDEO ({totalDur:0.0}s)", StartTime = 0, EndTime = totalDur, LeftPx = 0, WidthPx = Math.Max(40, trackWidth - 2), BackgroundHex = "#064E3B", BorderHex = "#10B981" });
            TimelineA1Blocks.Add(new TimelineClipBlockVm { ClipId = "a1_audio_01", TrackId = "A1", Label = $"AUDIO + VOICE ({_currentProject.VoiceId})", StartTime = 0, EndTime = totalDur, LeftPx = 0, WidthPx = Math.Max(40, trackWidth - 2), BackgroundHex = "#2E1065", BorderHex = "#8B5CF6" });

            int idx = 1;
            foreach (var seg in SubtitleItems)
            {
                double left = (seg.StartTime / totalDur) * trackWidth;
                double width = Math.Max(22.0, ((seg.EndTime - seg.StartTime) / totalDur) * trackWidth - 2);
                TimelineSubtitleBlocks.Add(new TimelineClipBlockVm
                {
                    ClipId = $"s1_sub_{idx++:00}",
                    TrackId = "S1",
                    Label = $"{seg.StartTime:0.0}s: {seg.Text}",
                    StartTime = seg.StartTime,
                    EndTime = seg.EndTime,
                    LeftPx = Math.Max(0, left),
                    WidthPx = width,
                    BackgroundHex = "#422006",
                    BorderHex = "#F59E0B",
                });
            }
        }
    }

    private void TimelineTrackArea_SizeChanged(object sender, SizeChangedEventArgs e) => RebuildVisualTimeline();

    private void TimelineCanvas_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        double width = Math.Max(1.0, TimelineTrackArea.ActualWidth);
        var pt = e.GetPosition(TimelineTrackArea);
        double targetSec = Math.Clamp(pt.X / width, 0.0, 1.0) * _videoDurationSeconds;
        SeekMonitorTo(targetSec);
    }

    private void TimelineClipBlock_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (sender is FrameworkElement fe && fe.DataContext is TimelineClipBlockVm block)
        {
            _selectedClipId = block.ClipId;
            SelectComboByTag(CmbClipTrack, block.TrackId);
            TxtClipStart.Text = block.StartTime.ToString("0.00", CultureInfo.InvariantCulture);
            TxtClipEnd.Text = block.EndTime.ToString("0.00", CultureInfo.InvariantCulture);

            // Strip visual "0.0s: " prefix when loading S1 into editor box
            var rawDto = _currentProject?.TimelineClips?.FirstOrDefault(x => x.ClipId == block.ClipId);
            TxtClipLabel.Text = rawDto?.Label ?? block.Label;

            SeekMonitorTo(block.StartTime);
            RebuildVisualTimeline();
            AppendLog($"Selected clip [{block.TrackId}] '{block.ClipId}' ({block.StartTime:0.00}s - {block.EndTime:0.00}s).");
            e.Handled = true;
        }
    }

    private void SeekMonitorTo(double seconds)
    {
        double clamped = Math.Clamp(seconds, 0.0, _videoDurationSeconds);
        SliderScrub.Value = clamped;
        TxtTimecode.Text = $"{clamped:00.00}s / {_videoDurationSeconds:00.00}s";
        TxtSfxTimestamp.Text = clamped.ToString("0.00", CultureInfo.InvariantCulture);
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
        var venvPython = Path.Combine(repoRoot, ".venv", "Scripts", "python.exe");
        bool useVenvPython = File.Exists(venvPython);
        AppendLog($"Starting Python FastAPI Core Orchestrator in {repoRoot} ({(useVenvPython ? ".venv python" : "uv")})...");
        try
        {
            var psi = new ProcessStartInfo
            {
                FileName = useVenvPython ? venvPython : "uv",
                Arguments = useVenvPython
                    ? "-m uvicorn src.presentation.api.main:app --host 127.0.0.1 --port 8000"
                    : "run uvicorn src.presentation.api.main:app --host 127.0.0.1 --port 8000",
                WorkingDirectory = repoRoot,
                UseShellExecute = false,
                CreateNoWindow = true,
            };
            _backendProcess = Process.Start(psi);

            for (int i = 0; i < 40; i++)
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
            AppendLog($"Warning: Could not auto-start FastAPI backend: {ex.Message}");
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

    private async Task RefreshCustomVoicesAsync()
    {
        try
        {
            var profiles = await _http.GetFromJsonAsync<VoiceProfileDto[]>("/api/v1/voices/profiles");
            if (profiles == null) return;
            foreach (var p in profiles)
            {
                var vid = !string.IsNullOrWhiteSpace(p.VoiceId) ? p.VoiceId : p.ProfileId;
                if (string.IsNullOrWhiteSpace(vid)) continue;
                EnsureVoiceInCombo(CmbVoiceId, p.Name, vid);
                EnsureVoiceInCombo(CmbPodcastHostVoice, $"Host: {p.Name}", vid);
                EnsureVoiceInCombo(CmbPodcastGuestVoice, $"Guest: {p.Name}", vid);
            }
        }
        catch
        {
            // Ignore when backend is starting up
        }
    }

    private static void EnsureVoiceInCombo(ComboBox combo, string label, string tagValue)
    {
        for (int i = 0; i < combo.Items.Count; i++)
        {
            if (combo.Items[i] is ComboBoxItem item && string.Equals(item.Tag?.ToString(), tagValue, StringComparison.OrdinalIgnoreCase))
            {
                return;
            }
        }
        combo.Items.Add(new ComboBoxItem { Content = label, Tag = tagValue });
    }

    private async Task RefreshProjectsAsync(bool selectLatestIfNew = false, bool forceReloadList = false)
    {
        try
        {
            var list = await _http.GetFromJsonAsync<ProjectResponseDto[]>("/api/v1/projects");
            if (list == null) return;

            TxtProjectCount.Text = $" ({list.Length})";

            bool countChanged = forceReloadList || list.Length != ProjectItems.Count;
            if (countChanged)
            {
                _suppressProjectSelectionChanged = true;
                try
                {
                    ProjectItems.Clear();
                    foreach (var item in list.Reverse())
                    {
                        ProjectItems.Add(item);
                    }
                    if (_currentProject != null)
                    {
                        LstProjects.SelectedItem = ProjectItems.FirstOrDefault(p => p.ProjectId == _currentProject.ProjectId);
                    }
                }
                finally
                {
                    _suppressProjectSelectionChanged = false;
                }
            }

            if (list.Length > 0 && (_currentProject == null || (selectLatestIfNew && list.Length > _knownProjectCount)))
            {
                var newest = _currentProject == null
                    ? (list.LastOrDefault(p => !string.IsNullOrWhiteSpace(p.FinalOutputPath) && File.Exists(p.FinalOutputPath)) ?? list.Last())
                    : list.Last();
                if (_knownProjectCount > 0 && list.Length > _knownProjectCount)
                {
                    AppendLog($"[MCP Sync] New project synced: '{newest.ProjectId}' ({newest.EngineUpper})");
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

    private static void SelectComboByTag(ComboBox combo, string? tagValue)
    {
        if (string.IsNullOrWhiteSpace(tagValue)) return;
        for (int i = 0; i < combo.Items.Count; i++)
        {
            if (combo.Items[i] is ComboBoxItem item &&
                string.Equals(item.Tag?.ToString(), tagValue, StringComparison.OrdinalIgnoreCase))
            {
                combo.SelectedIndex = i;
                return;
            }
        }
    }

    private static string GetComboTag(ComboBox combo, string fallback)
    {
        if (combo.SelectedItem is ComboBoxItem item && item.Tag is string tag && !string.IsNullOrWhiteSpace(tag))
        {
            return tag.Trim();
        }
        return fallback;
    }

    private async Task BindProjectAsync(ProjectResponseDto project)
    {
        _currentProject = project;
        _suppressProjectSelectionChanged = true;
        try
        {
            LstProjects.SelectedItem = ProjectItems.FirstOrDefault(p => p.ProjectId == _currentProject?.ProjectId);
        }
        finally
        {
            _suppressProjectSelectionChanged = false;
        }
        TxtProjectId.Text = project.ProjectId;
        TxtSourceUrl.Text = project.SourceUrl;
        CmbEngineType.SelectedIndex = project.EngineType == "hyperframes" ? 1 : 0;
        SelectComboByTag(CmbTemplateId, project.TemplateId);
        SelectComboByTag(CmbTransitionPreset, project.TransitionPreset);
        SelectComboByTag(CmbAnimationPreset, project.AnimationPreset);
        SelectComboByTag(CmbVoiceId, project.VoiceId);
        SelectComboByTag(CmbBgmPreset, project.BgmPreset);

        TxtStepStatus.Text = project.CurrentStep;
        TxtProgressPercent.Text = $"{project.ProgressPercent}%";
        PbPipeline.Value = project.ProgressPercent;
        TxtOutputPath.Text = project.FinalOutputPath ?? string.Empty;
        TxtStatusRight.Text = $"Active: {project.ProjectId} [{project.EngineUpper} | {project.TemplateId} | {project.VoiceId}]";

        SubtitleItems.Clear();
        foreach (var seg in project.Subtitles) SubtitleItems.Add(seg);

        var ctx = project.SceneContext ?? new SceneContextDto();
        TxtWorldSetting.Text = ctx.WorldSetting;
        TxtVisualStyle.Text = ctx.VisualStyle;
        TxtLightingMood.Text = ctx.LightingMood;

        SceneItems.Clear();
        foreach (var sc in project.Scenes) SceneItems.Add(sc);

        CharacterItems.Clear();
        foreach (var ch in project.Characters) CharacterItems.Add(ch);

        AuditLogItems.Clear();
        foreach (var log in project.AuditLogs.AsEnumerable().Reverse()) AuditLogItems.Add(log);

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
            TxtTimelineSummary.Text = $"{_currentProject?.TimelineClips?.Count ?? 4} Clips | {probe.Resolution} @ {probe.Fps:0.00} fps";
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
        SeekMonitorTo(Math.Max(0.0, SliderScrub.Value - (1.0 / 30.0)));
    }

    private void BtnStepForward_Click(object sender, RoutedEventArgs e)
    {
        if (VideoPlayer.Source == null) return;
        VideoPlayer.Pause();
        _isPlaying = false;
        BtnPlayPause.Content = "Play";
        SeekMonitorTo(Math.Min(_videoDurationSeconds, SliderScrub.Value + (1.0 / 30.0)));
    }

    private void BtnMarkIn_Click(object sender, RoutedEventArgs e)
    {
        TxtTrimStart.Text = SliderScrub.Value.ToString("0.00", CultureInfo.InvariantCulture);
        TxtClipStart.Text = TxtTrimStart.Text;
        AppendLog($"Marked IN at {SliderScrub.Value:0.00}s");
    }

    private void BtnMarkOut_Click(object sender, RoutedEventArgs e)
    {
        TxtTrimEnd.Text = SliderScrub.Value.ToString("0.00", CultureInfo.InvariantCulture);
        TxtClipEnd.Text = TxtTrimEnd.Text;
        AppendLog($"Marked OUT at {SliderScrub.Value:0.00}s");
    }

    private void SliderScrub_PreviewMouseLeftButtonUp(object sender, MouseButtonEventArgs e) => SeekMonitorTo(SliderScrub.Value);

    private string GetSelectedEngine()
    {
        if (CmbEngineType.SelectedItem is ComboBoxItem item && item.Content is string s)
        {
            return s.Trim().ToLowerInvariant();
        }
        return "remotion";
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

    // ==========================================================
    // INTERACTIVE MULTI-TRACK TIMELINE CLIP CRUD (ADD / EDIT / SPLIT / CLONE / DELETE / RENDER)
    // ==========================================================

    private async Task ExecuteTimelineActionAsync(string action, bool renderTimeline = false)
    {
        if (_currentProject == null) return;
        if (!double.TryParse(TxtClipStart.Text, NumberStyles.Any, CultureInfo.InvariantCulture, out double st)) st = 0.0;
        if (!double.TryParse(TxtClipEnd.Text, NumberStyles.Any, CultureInfo.InvariantCulture, out double en)) en = Math.Max(st + 2.0, 2.0);
        if (en <= st) en = st + 0.5;

        try
        {
            if (renderTimeline || action == "render")
            {
                await ReleaseVideoPlayerLockAsync();
            }
            var req = new ManageTimelineClipRequestDto
            {
                Action = action,
                ClipId = _selectedClipId,
                SplitTime = SliderScrub.Value,
                RenderTimeline = renderTimeline,
                Clip = new TimelineClipDto
                {
                    ClipId = _selectedClipId ?? string.Empty,
                    TrackId = GetComboTag(CmbClipTrack, "S1"),
                    Label = TxtClipLabel.Text.Trim(),
                    StartTime = st,
                    EndTime = en,
                    SourceStart = st,
                    SourceEnd = en,
                },
            };

            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/timeline-clips", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                await BindProjectAsync(updated);
                AppendLog($"Timeline [{action.ToUpperInvariant()}] completed ({updated.TimelineClips.Count} clips).");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Timeline {action} error: {ex.Message}");
            MessageBox.Show(ex.Message, "Timeline Edit Error", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
    }

    private async void BtnTimelineAddClip_Click(object sender, RoutedEventArgs e) => await ExecuteTimelineActionAsync("add");
    private async void BtnTimelineSaveClip_Click(object sender, RoutedEventArgs e) => await ExecuteTimelineActionAsync("update");
    private async void BtnTimelineSplitClip_Click(object sender, RoutedEventArgs e) => await ExecuteTimelineActionAsync("split");
    private async void BtnTimelineCloneClip_Click(object sender, RoutedEventArgs e) => await ExecuteTimelineActionAsync("clone");
    private async void BtnTimelineDeleteClip_Click(object sender, RoutedEventArgs e) => await ExecuteTimelineActionAsync("delete");
    private async void BtnTimelineRenderVideo_Click(object sender, RoutedEventArgs e) => await ExecuteTimelineActionAsync("render", renderTimeline: true);

    // ==========================================================
    // USER GUIDE BUTTON (OPEN GENERATED HTML OR DOCX)
    // ==========================================================

    private void BtnOpenUserGuide_Click(object sender, RoutedEventArgs e)
    {
        var repoRoot = FindRepositoryRoot();
        var docsDir = Path.Combine(repoRoot, "docs");
        string[] candidates =
        {
            Path.Combine(docsDir, "Tai_lieu_huong_dan_su_dung_Kinetix_Studio_v5.0.html"),
            Path.Combine(docsDir, "Tai_lieu_huong_dan_su_dung_Kinetix_Studio_v4.0.html"),
            Path.Combine(docsDir, "Tai_lieu_huong_dan_su_dung_Kinetix_Studio_v5.0.docx"),
            Path.Combine(docsDir, "Tai_lieu_huong_dan_su_dung_Kinetix_Studio_v4.0.docx"),
        };

        var existing = candidates.FirstOrDefault(File.Exists);
        if (existing != null)
        {
            Process.Start(new ProcessStartInfo(existing) { UseShellExecute = true });
            AppendLog($"Opened Enterprise User Guide: {existing}");
        }
        else
        {
            MessageBox.Show($"User Guide not found in {docsDir}", "User Guide", MessageBoxButton.OK, MessageBoxImage.Information);
        }
    }

    // ==========================================================
    // PODCAST & VOICESTUDIO AI (GENERATION / DESIGN / CLONE / DUBBING)
    // ==========================================================

    private void BtnLoadSamplePodcast_Click(object sender, RoutedEventArgs e)
    {
        var repoRoot = FindRepositoryRoot();
        var samplePath = Path.Combine(repoRoot, "docs", "sample_podcast_tap_01_tuoi_30.txt");
        if (!File.Exists(samplePath))
        {
            AppendLog($"Sample podcast script not found: {samplePath}");
            MessageBox.Show($"Sample podcast script not found:\n{samplePath}", "Sample Script Missing", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        TxtPodcastContent.Text = File.ReadAllText(samplePath, System.Text.Encoding.UTF8).Trim();
        TxtProjectId.Text = "tap_01_tuoi_30_podcast";
        SelectComboByTag(CmbPodcastGenre, "late_night_story");
        SelectComboByTag(CmbPodcastHostVoice, "vi-VN-NamMinhNeural");
        AppendLog($"Loaded Episode 1 sample podcast ('tap_01_tuoi_30_podcast', genre=late_night_story, host=vi-VN-NamMinhNeural) from {samplePath}.");
    }

    private async void BtnGeneratePodcast_Click(object sender, RoutedEventArgs e)
    {
        BtnGeneratePodcast.IsEnabled = false;
        try
        {
            await EnsureBackendRunningAsync();
            await ReleaseVideoPlayerLockAsync();
            var typedId = TxtProjectId.Text.Trim();
            var targetProj = !string.IsNullOrWhiteSpace(typedId)
                ? typedId
                : (_currentProject?.ProjectId ?? "kinetix_podcast_01");

            var genre = GetComboTag(CmbPodcastGenre, "podcast_dialogue");
            var hostVoice = GetComboTag(CmbPodcastHostVoice, "vi-VN-HoaiMyNeural");
            var guestVoice = GetComboTag(CmbPodcastGuestVoice, "vi-VN-NamMinhNeural");

            var req = new PodcastRequestDto
            {
                RawContent = TxtPodcastContent.Text.Trim(),
                Genre = genre,
                HostVoiceId = hostVoice,
                GuestVoiceId = guestVoice,
                BgmVolume = 0.14,
            };
            AppendLog($"Generating Multi-Voice Podcast '{targetProj}' [genre={genre}, host={hostVoice}, guest={guestVoice}]...");
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{targetProj}/podcast", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                await RefreshProjectsAsync(forceReloadList: true);
                await BindProjectAsync(updated);
                AppendLog($"Podcast exported: {updated.FinalOutputPath} ({updated.PodcastTurns.Count} turns).");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Podcast error: {ex.Message}");
            MessageBox.Show(ex.Message, "Podcast Studio Error", MessageBoxButton.OK, MessageBoxImage.Error);
        }
        finally
        {
            BtnGeneratePodcast.IsEnabled = true;
        }
    }

    private async void BtnDesignVoice_Click(object sender, RoutedEventArgs e)
    {
        BtnDesignVoice.IsEnabled = false;
        try
        {
            await EnsureBackendRunningAsync();
            var req = new VoiceDesignRequestDto
            {
                Name = TxtVoiceDesignName.Text.Trim(),
                PromptDescription = TxtVoiceDesignPrompt.Text.Trim(),
                Seed = 42,
                Language = "vi-VN",
            };
            AppendLog($"Designing synthetic voice profile '{req.Name}' (VoiceStudio Voice Design)...");
            var response = await _http.PostAsJsonAsync("/api/v1/voices/design", req);
            response.EnsureSuccessStatusCode();
            var profile = await response.Content.ReadFromJsonAsync<VoiceProfileDto>();
            await RefreshCustomVoicesAsync();
            AppendLog($"Voice Designed & Saved: id='{profile?.ProfileId}', name='{profile?.Name}'. Added to Voice dropdowns!");
        }
        catch (Exception ex)
        {
            AppendLog($"Voice design error: {ex.Message}");
            MessageBox.Show(ex.Message, "Voice Design Error", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
        finally
        {
            BtnDesignVoice.IsEnabled = true;
        }
    }

    private void BtnBrowseCloneAudio_Click(object sender, RoutedEventArgs e)
    {
        var dlg = new OpenFileDialog
        {
            Filter = "Audio Files (*.wav;*.mp3;*.m4a)|*.wav;*.mp3;*.m4a|All Files (*.*)|*.*",
            Title = "Select Clean Reference Voice Recording (With Speaker Consent)"
        };
        if (dlg.ShowDialog() == true)
        {
            TxtCloneRefAudioPath.Text = dlg.FileName;
        }
    }

    private async void BtnCloneVoice_Click(object sender, RoutedEventArgs e)
    {
        if (ChkCloneConsent.IsChecked != true)
        {
            MessageBox.Show(
                "Per VoiceStudio ethics policy, you MUST verify explicit speaker consent before cloning a voice.",
                "Consent Verification Required",
                MessageBoxButton.OK,
                MessageBoxImage.Warning
            );
            return;
        }

        BtnCloneVoice.IsEnabled = false;
        try
        {
            await EnsureBackendRunningAsync();
            var req = new VoiceCloneRequestDto
            {
                Name = TxtCloneVoiceName.Text.Trim(),
                ReferenceAudioPath = TxtCloneRefAudioPath.Text.Trim(),
                ConsentVerified = true,
                Language = "vi-VN",
            };
            AppendLog($"Cloning voice '{req.Name}' from '{req.ReferenceAudioPath}'...");
            var response = await _http.PostAsJsonAsync("/api/v1/voices/clone", req);
            if (!response.IsSuccessStatusCode)
            {
                var err = await response.Content.ReadAsStringAsync();
                throw new Exception(err);
            }
            var profile = await response.Content.ReadFromJsonAsync<VoiceProfileDto>();
            await RefreshCustomVoicesAsync();
            AppendLog($"Cloned Voice Saved: id='{profile?.ProfileId}', name='{profile?.Name}'.");
        }
        catch (Exception ex)
        {
            AppendLog($"Voice clone error: {ex.Message}");
            MessageBox.Show(ex.Message, "Voice Clone Error", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
        finally
        {
            BtnCloneVoice.IsEnabled = true;
        }
    }

    private async void BtnDubVideo_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        BtnDubVideo.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            var voiceId = GetComboTag(CmbPodcastHostVoice, "vi-VN-HoaiMyNeural");
            var req = new DubbingRequestDto
            {
                TargetLanguage = voiceId.StartsWith("en", StringComparison.OrdinalIgnoreCase) ? "en-US" : "vi-VN",
                VoiceId = voiceId,
            };
            AppendLog($"Auto-Dubbing '{_currentProject.ProjectId}' with time-aligned '{voiceId}'...");
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/dubbing", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                await BindProjectAsync(updated);
                AppendLog($"Video Dubbed: {updated.FinalOutputPath}");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Dubbing error: {ex.Message}");
        }
        finally
        {
            BtnDubVideo.IsEnabled = true;
        }
    }

    // ==========================================================
    // LEFT DOCK: INGEST, PIPELINE & PROJECT CLONE / DELETE
    // ==========================================================

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
                AppendLog($"Source inspected: title='{meta.Title}', type={meta.SourceType}, res={meta.Resolution}, dur={meta.Duration:0.00}s");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Source inspect error: {ex.Message}");
        }
        finally
        {
            BtnInspectSource.IsEnabled = true;
        }
    }

    private void BtnClearScript_Click(object sender, RoutedEventArgs e)
    {
        TxtScriptText.Text = string.Empty;
        AppendLog("Script cleared. Pipeline will use automatic Whisper / Windows STT transcription.");
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
            var req = new AiMcpCommandRequestDto { Prompt = prompt, SourceUrl = TxtSourceUrl.Text.Trim() };
            var response = await _http.PostAsJsonAsync("/api/v1/mcp/command", req);
            response.EnsureSuccessStatusCode();
            var project = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (project != null)
            {
                await BindProjectAsync(project);
                AppendLog($"[MCP Dispatch] Completed '{project.ProjectId}' -> {project.FinalOutputPath}");
                await RefreshProjectsAsync(forceReloadList: true);
            }
        }
        catch (Exception ex)
        {
            AppendLog($"MCP Command Error: {ex.Message}");
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
            var template = GetComboTag(CmbTemplateId, "CaptionTemplate");
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
            AppendLog($"Starting pipeline '{req.ProjectId}' [{req.EngineType}/{template}]...");

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
                await RefreshProjectsAsync(forceReloadList: true);
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

    private async void BtnCloneProject_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        BtnCloneProject.IsEnabled = false;
        try
        {
            AppendLog($"Cloning project '{_currentProject.ProjectId}'...");
            var response = await _http.PostAsJsonAsync(
                $"/api/v1/projects/{_currentProject.ProjectId}/clone",
                new CloneProjectRequestDto()
            );
            response.EnsureSuccessStatusCode();
            var cloned = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (cloned != null)
            {
                await RefreshProjectsAsync(forceReloadList: true);
                await BindProjectAsync(cloned);
                AppendLog($"Cloned project created: '{cloned.ProjectId}'.");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Clone project error: {ex.Message}");
        }
        finally
        {
            BtnCloneProject.IsEnabled = true;
        }
    }

    private async void BtnDeleteProject_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        var targetId = _currentProject.ProjectId;
        var confirm = MessageBox.Show(
            $"Delete project '{targetId}' and its workspace files?",
            "Confirm Delete Project",
            MessageBoxButton.YesNo,
            MessageBoxImage.Question
        );
        if (confirm != MessageBoxResult.Yes) return;

        BtnDeleteProject.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            var response = await _http.DeleteAsync($"/api/v1/projects/{targetId}");
            response.EnsureSuccessStatusCode();
            _currentProject = null;
            AppendLog($"Deleted project '{targetId}'.");
            await RefreshProjectsAsync(forceReloadList: true);
        }
        catch (Exception ex)
        {
            AppendLog($"Delete project error: {ex.Message}");
        }
        finally
        {
            BtnDeleteProject.IsEnabled = true;
        }
    }

    // ==========================================================
    // SUBTITLES TAB (ADD / CLONE / SPLIT / EXPORT / REMOVE)
    // ==========================================================

    private async void BtnRerenderSubtitles_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        GridSubtitles.CommitEdit(DataGridEditingUnit.Cell, true);
        GridSubtitles.CommitEdit(DataGridEditingUnit.Row, true);

        BtnRerenderSubtitles.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            var engine = GetSelectedEngine();
            var template = GetComboTag(CmbTemplateId, "CaptionTemplate");
            var req = new UpdateSubtitlesRequestDto
            {
                EngineType = engine,
                TemplateId = template,
                Subtitles = SubtitleItems.ToList(),
            };
            AppendLog($"Re-rendering '{_currentProject.ProjectId}' ({engine}/{template})...");
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/subtitles", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                await BindProjectAsync(updated);
                AppendLog($"Re-render complete: {updated.FinalOutputPath}");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Re-render error: {ex.Message}");
        }
        finally
        {
            BtnRerenderSubtitles.IsEnabled = true;
        }
    }

    private void BtnAddSubtitleRow_Click(object sender, RoutedEventArgs e)
    {
        double lastEnd = SubtitleItems.Count > 0 ? SubtitleItems.Max(s => s.EndTime) : 0.0;
        SubtitleItems.Add(new SubtitleSegmentDto
        {
            StartTime = Math.Round(lastEnd, 2),
            EndTime = Math.Round(lastEnd + 2.0, 2),
            Text = "New caption cue",
        });
        RebuildVisualTimeline();
    }

    private void BtnCloneSubtitleRow_Click(object sender, RoutedEventArgs e)
    {
        var source = GridSubtitles.SelectedItem as SubtitleSegmentDto ?? SubtitleItems.LastOrDefault();
        if (source == null) return;
        double dur = Math.Max(0.5, source.EndTime - source.StartTime);
        double newStart = Math.Round(source.EndTime, 2);
        SubtitleItems.Add(new SubtitleSegmentDto
        {
            StartTime = newStart,
            EndTime = Math.Round(newStart + dur, 2),
            Text = $"{source.Text} (Copy)",
        });
        RebuildVisualTimeline();
    }

    private void BtnSplitSubtitleCue_Click(object sender, RoutedEventArgs e)
    {
        double playhead = SliderScrub.Value;
        var targetCue = SubtitleItems.FirstOrDefault(s => playhead > s.StartTime + 0.2 && playhead < s.EndTime - 0.2)
                        ?? GridSubtitles.SelectedItem as SubtitleSegmentDto;
        if (targetCue == null) return;

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
        AppendLog($"Split subtitle cue at {splitPoint:0.00}s.");
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
            AppendLog($"Exported .srt, .vtt & .transcript.json for '{_currentProject.ProjectId}'.");
        }
        catch (Exception ex)
        {
            AppendLog($"Subtitle export error: {ex.Message}");
        }
        finally
        {
            BtnExportSubtitles.IsEnabled = true;
        }
    }

    // ==========================================================
    // CONTEXT, SCENES, CHARACTERS, SOUND LIBRARY, FX & BEAT-CUT
    // ==========================================================

    private async void BtnSaveContext_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        BtnSaveContext.IsEnabled = false;
        try
        {
            var dto = new SceneContextDto
            {
                WorldSetting = TxtWorldSetting.Text.Trim(),
                VisualStyle = TxtVisualStyle.Text.Trim(),
                LightingMood = TxtLightingMood.Text.Trim(),
                CameraLens = _currentProject.SceneContext?.CameraLens ?? "35mm Anamorphic",
                ContinuityNotes = _currentProject.SceneContext?.ContinuityNotes ?? "Consistent character & style.",
            };
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/context", dto);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                _currentProject = updated;
                AuditLogItems.Clear();
                foreach (var l in updated.AuditLogs.AsEnumerable().Reverse()) AuditLogItems.Add(l);
                AppendLog("Saved Scene Context Bible.");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Save context error: {ex.Message}");
        }
        finally
        {
            BtnSaveContext.IsEnabled = true;
        }
    }

    private void BtnAddScene_Click(object sender, RoutedEventArgs e)
    {
        double nextStart = SceneItems.Count > 0 ? SceneItems.Max(s => s.StartTime + s.DurationSec) : 0.0;
        int num = SceneItems.Count + 1;
        SceneItems.Add(new StorySceneDto
        {
            SceneId = $"scene_{num:00}",
            Title = $"Scene {num:00}",
            CharacterId = CharacterItems.FirstOrDefault()?.CharacterId ?? "char_host",
            StartTime = Math.Round(nextStart, 2),
            DurationSec = 2.0,
            TransitionIn = GetComboTag(CmbTransitionPreset, "fade_black"),
            AnimationPreset = GetComboTag(CmbAnimationPreset, "spring_pop"),
            SfxId = "sfx_whoosh_fast",
            NarrationText = "New storyboard scene dialogue...",
        });
    }

    private void BtnCloneScene_Click(object sender, RoutedEventArgs e)
    {
        var selected = GridScenes.SelectedItem as StorySceneDto ?? SceneItems.LastOrDefault();
        if (selected == null) return;
        SceneItems.Add(new StorySceneDto
        {
            SceneId = $"{selected.SceneId}_copy",
            Title = $"{selected.Title} (Copy)",
            SettingContext = selected.SettingContext,
            CharacterId = selected.CharacterId,
            NarrationText = selected.NarrationText,
            StartTime = Math.Round(selected.StartTime + selected.DurationSec, 2),
            DurationSec = selected.DurationSec,
            TransitionIn = selected.TransitionIn,
            AnimationPreset = selected.AnimationPreset,
            SfxId = selected.SfxId,
        });
    }

    private void BtnDeleteScene_Click(object sender, RoutedEventArgs e)
    {
        if (GridScenes.SelectedItem is StorySceneDto selected) SceneItems.Remove(selected);
        else if (SceneItems.Count > 0) SceneItems.RemoveAt(SceneItems.Count - 1);
    }

    private async void BtnSaveScenes_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        GridScenes.CommitEdit(DataGridEditingUnit.Cell, true);
        GridScenes.CommitEdit(DataGridEditingUnit.Row, true);
        BtnSaveScenes.IsEnabled = false;
        try
        {
            var req = new ManageSceneRequestDto { Action = "replace_all", Scenes = SceneItems.ToList() };
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/scenes", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                _currentProject = updated;
                AuditLogItems.Clear();
                foreach (var l in updated.AuditLogs.AsEnumerable().Reverse()) AuditLogItems.Add(l);
                AppendLog($"Saved {updated.Scenes.Count} storyboard scenes.");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Save scenes error: {ex.Message}");
        }
        finally
        {
            BtnSaveScenes.IsEnabled = true;
        }
    }

    private void BtnAddCharacter_Click(object sender, RoutedEventArgs e)
    {
        int n = CharacterItems.Count + 1;
        CharacterItems.Add(new CharacterProfileDto
        {
            CharacterId = $"char_{n:00}",
            Name = $"Character {n}",
            Role = "Co-Host",
            VoiceId = "en-US-AriaNeural",
            AvatarBadge = $"CH{n}",
            ThemeColor = "#F59E0B",
            VisualDescription = "Studio attire with amber glow accent badge",
        });
    }

    private void BtnCloneCharacter_Click(object sender, RoutedEventArgs e)
    {
        var selected = GridCharacters.SelectedItem as CharacterProfileDto ?? CharacterItems.LastOrDefault();
        if (selected == null) return;
        CharacterItems.Add(new CharacterProfileDto
        {
            CharacterId = $"{selected.CharacterId}_clone",
            Name = $"{selected.Name} (Clone)",
            Role = selected.Role,
            VoiceId = selected.VoiceId,
            AvatarBadge = selected.AvatarBadge,
            ThemeColor = selected.ThemeColor,
            VisualDescription = selected.VisualDescription,
        });
    }

    private void BtnDeleteCharacter_Click(object sender, RoutedEventArgs e)
    {
        if (GridCharacters.SelectedItem is CharacterProfileDto selected) CharacterItems.Remove(selected);
        else if (CharacterItems.Count > 0) CharacterItems.RemoveAt(CharacterItems.Count - 1);
    }

    private async void BtnSaveCharacters_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        GridCharacters.CommitEdit(DataGridEditingUnit.Cell, true);
        GridCharacters.CommitEdit(DataGridEditingUnit.Row, true);
        BtnSaveCharacters.IsEnabled = false;
        try
        {
            var req = new ManageCharacterRequestDto { Action = "replace_all", Characters = CharacterItems.ToList() };
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/characters", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                _currentProject = updated;
                AuditLogItems.Clear();
                foreach (var l in updated.AuditLogs.AsEnumerable().Reverse()) AuditLogItems.Add(l);
                AppendLog($"Saved {updated.Characters.Count} consistent character profiles.");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Save characters error: {ex.Message}");
        }
        finally
        {
            BtnSaveCharacters.IsEnabled = true;
        }
    }

    private async void BtnGenerateVoiceover_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        BtnGenerateVoiceover.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            var voiceId = GetComboTag(CmbVoiceId, "vi-VN-HoaiMyNeural");
            var req = new VoiceoverRequestDto
            {
                VoiceId = voiceId,
                Rate = Math.Round(SliderVoiceRate.Value, 2),
                Text = string.Join(". ", SubtitleItems.Select(s => s.Text)),
            };
            AppendLog($"Synthesizing Voiceover ({voiceId}, rate={req.Rate:0.00}x)...");
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/voiceover", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null)
            {
                await BindProjectAsync(updated);
                AppendLog($"Voiceover applied: {updated.FinalOutputPath}");
            }
        }
        catch (Exception ex)
        {
            AppendLog($"Voiceover error: {ex.Message}");
        }
        finally
        {
            BtnGenerateVoiceover.IsEnabled = true;
        }
    }

    private async void BtnApplyBgm_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        BtnApplyBgm.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            var bgmId = GetComboTag(CmbBgmPreset, "bgm_ambient_pad");
            var req = new SoundLibraryRequestDto { BgmPreset = bgmId, BgmVolume = Math.Round(SliderBgmVolume.Value, 2) };
            AppendLog($"Mixing BGM preset '{bgmId}'...");
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/sound-library", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null) await BindProjectAsync(updated);
        }
        catch (Exception ex)
        {
            AppendLog($"BGM mix error: {ex.Message}");
        }
        finally
        {
            BtnApplyBgm.IsEnabled = true;
        }
    }

    private async void BtnInsertSfx_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        if (!double.TryParse(TxtSfxTimestamp.Text, NumberStyles.Any, CultureInfo.InvariantCulture, out double ts)) ts = SliderScrub.Value;
        BtnInsertSfx.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            var sfxId = GetComboTag(CmbSfxPreset, "sfx_whoosh_fast");
            var req = new SoundLibraryRequestDto { SfxId = sfxId, SfxTimestamp = Math.Max(0.0, ts), SfxVolume = 0.70 };
            AppendLog($"Inserting SFX '{sfxId}' at {req.SfxTimestamp:0.00}s...");
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/sound-library", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null) await BindProjectAsync(updated);
        }
        catch (Exception ex)
        {
            AppendLog($"SFX insert error: {ex.Message}");
        }
        finally
        {
            BtnInsertSfx.IsEnabled = true;
        }
    }

    private async void BtnApplyBeatCut_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        int bpm = 120;
        if (CmbBeatBpm.SelectedItem is ComboBoxItem item && int.TryParse(item.Tag?.ToString(), out int parsed)) bpm = parsed;
        BtnApplyBeatCut.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            var req = new BeatCutRequestDto { Bpm = bpm, AlignSubtitles = ChkSnapSubtitles.IsChecked == true, PulseFlash = ChkBeatPulse.IsChecked == true };
            AppendLog($"Running Auto Beat-Cut at {bpm} BPM...");
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/beat-cut", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null) await BindProjectAsync(updated);
        }
        catch (Exception ex)
        {
            AppendLog($"Beat-Cut error: {ex.Message}");
        }
        finally
        {
            BtnApplyBeatCut.IsEnabled = true;
        }
    }

    private async void BtnApplyFxMotion_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        BtnApplyFxMotion.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            var transition = GetComboTag(CmbTransitionPreset, "fade_black");
            var animation = GetComboTag(CmbAnimationPreset, "spring_pop");
            var req = new FxMotionRequestDto { TransitionPreset = transition, AnimationPreset = animation };
            AppendLog($"Applying Transition '{transition}' + Animation '{animation}'...");
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/fx-motion", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null) await BindProjectAsync(updated);
        }
        catch (Exception ex)
        {
            AppendLog($"FX Motion error: {ex.Message}");
        }
        finally
        {
            BtnApplyFxMotion.IsEnabled = true;
        }
    }

    private void BtnExportAuditLog_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        try
        {
            var repoRoot = FindRepositoryRoot();
            var outDir = Path.Combine(repoRoot, "workspace", _currentProject.ProjectId);
            Directory.CreateDirectory(outDir);
            var outFile = Path.Combine(outDir, $"{_currentProject.ProjectId}_audit_logs.json");
            File.WriteAllText(outFile, JsonSerializer.Serialize(_currentProject.AuditLogs, new JsonSerializerOptions { WriteIndented = true }));
            AppendLog($"Exported Audit Logs -> {outFile}");
            Process.Start(new ProcessStartInfo(outFile) { UseShellExecute = true });
        }
        catch (Exception ex)
        {
            AppendLog($"Export audit log error: {ex.Message}");
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
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/trim", new TrimVideoRequestDto { StartTime = startSec, EndTime = endSec });
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null) await BindProjectAsync(updated);
        }
        catch (Exception ex)
        {
            AppendLog($"Trim error: {ex.Message}");
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
            double.TryParse(item.Tag?.ToString(), NumberStyles.Any, CultureInfo.InvariantCulture, out double parsed)) speed = parsed;

        BtnApplySpeed.IsEnabled = false;
        try
        {
            await ReleaseVideoPlayerLockAsync();
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/speed", new SpeedChangeRequestDto { SpeedFactor = speed });
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null) await BindProjectAsync(updated);
        }
        catch (Exception ex)
        {
            AppendLog($"Speed change error: {ex.Message}");
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
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/reframe", new ReframeRequestDto { AspectRatio = aspectRatio });
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null) await BindProjectAsync(updated);
        }
        catch (Exception ex)
        {
            AppendLog($"Reframe error: {ex.Message}");
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
        string preset = GetComboTag(CmbColorPreset, "natural");
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
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/color-grade", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null) await BindProjectAsync(updated);
        }
        catch (Exception ex)
        {
            AppendLog($"Color grade error: {ex.Message}");
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
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/audio-master", req);
            response.EnsureSuccessStatusCode();
            var updated = await response.Content.ReadFromJsonAsync<ProjectResponseDto>();
            if (updated != null) await BindProjectAsync(updated);
        }
        catch (Exception ex)
        {
            AppendLog($"Audio master error: {ex.Message}");
        }
        finally
        {
            BtnMasterAudio.IsEnabled = true;
        }
    }

    private async void BtnSnapshot_Click(object sender, RoutedEventArgs e)
    {
        if (_currentProject == null) return;
        BtnSnapshot.IsEnabled = false;
        try
        {
            double ts = Math.Max(0.0, SliderScrub.Value);
            var response = await _http.PostAsJsonAsync($"/api/v1/projects/{_currentProject.ProjectId}/snapshot", new SnapshotRequestDto { TimestampSec = ts });
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

    private void BtnBrowseFile_Click(object sender, RoutedEventArgs e)
    {
        var dlg = new OpenFileDialog
        {
            Filter = "Video Files (*.mp4;*.mov;*.mkv;*.webm)|*.mp4;*.mov;*.mkv;*.webm|All Files (*.*)|*.*",
            Title = "Select Source Video File"
        };
        if (dlg.ShowDialog() == true) TxtSourceUrl.Text = dlg.FileName;
    }

    private async void BtnRefreshProjects_Click(object sender, RoutedEventArgs e)
    {
        await EnsureBackendRunningAsync();
        await RefreshCustomVoicesAsync();
        await RefreshProjectsAsync(forceReloadList: true);
    }

    private async void LstProjects_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (_suppressProjectSelectionChanged) return;
        if (LstProjects.SelectedItem is not ProjectResponseDto selected) return;
        if (_currentProject != null && string.Equals(_currentProject.ProjectId, selected.ProjectId, StringComparison.Ordinal)) return;
        try
        {
            var proj = await _http.GetFromJsonAsync<ProjectResponseDto>($"/api/v1/projects/{selected.ProjectId}");
            if (proj != null) await BindProjectAsync(proj);
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
