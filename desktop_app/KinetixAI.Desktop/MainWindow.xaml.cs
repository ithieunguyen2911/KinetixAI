using System;
using System.Collections.ObjectModel;
using System.Diagnostics;
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
    private readonly DispatcherTimer _playheadTimer = new() { Interval = TimeSpan.FromMilliseconds(100) };
    private Process? _backendProcess;
    private ProjectResponseDto? _currentProject;
    private int _knownProjectCount;
    private bool _isPlaying;
    private double _videoDurationSeconds = 6.0;

    public ObservableCollection<SubtitleSegmentDto> SubtitleItems { get; } = new();
    public ObservableCollection<ProjectResponseDto> ProjectItems { get; } = new();

    public MainWindow()
    {
        InitializeComponent();
        GridSubtitles.ItemsSource = SubtitleItems;
        LstProjects.ItemsSource = ProjectItems;
        _mcpSyncTimer.Tick += McpSyncTimer_Tick;
        _playheadTimer.Tick += PlayheadTimer_Tick;
        Loaded += MainWindow_Loaded;
        Closed += MainWindow_Closed;
    }

    private async void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        AppendLog("Workstation initialized. Verifying Core Orchestrator & MCP bridge...");
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
        var total = VideoPlayer.NaturalDuration.TimeSpan.TotalSeconds;
        SliderScrub.Value = pos;
        TxtTimecode.Text = $"{pos:00.00}s / {total:00.00}s";
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
            TxtBackendStatus.Text = "Core API: 127.0.0.1:8000 (Online)";
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
                    TxtBackendStatus.Text = "Core API: 127.0.0.1:8000 (Online)";
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

            TxtProjectCount.Text = $"{list.Length} projects";

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
        TxtTemplateId.Text = project.TemplateId;
        CmbEngineType.SelectedIndex = project.EngineType == "hyperframes" ? 1 : 0;
        TxtStepStatus.Text = project.CurrentStep;
        TxtProgressPercent.Text = $"{project.ProgressPercent}%";
        PbPipeline.Value = project.ProgressPercent;
        TxtOutputPath.Text = string.IsNullOrWhiteSpace(project.FinalOutputPath)
            ? string.Empty
            : project.FinalOutputPath;
        TxtStatusRight.Text = $"Active Project: {project.ProjectId} [{project.EngineUpper}]";

        SubtitleItems.Clear();
        foreach (var seg in project.Subtitles)
        {
            SubtitleItems.Add(seg);
        }

        LoadVideoIntoMonitor(project.FinalOutputPath);
        await LoadMediaProbeSpecsAsync(project.ProjectId);
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
            TxtTrimEnd.Text = $"{probe.DurationSeconds:0.0}";
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
        SliderScrub.Value = 0;
        TxtTimecode.Text = $"00.00s / {_videoDurationSeconds:00.00}s";
    }

    private void SliderScrub_PreviewMouseLeftButtonUp(object sender, MouseButtonEventArgs e)
    {
        if (VideoPlayer.Source == null) return;
        VideoPlayer.Position = TimeSpan.FromSeconds(SliderScrub.Value);
    }

    private string GetSelectedEngine()
    {
        if (CmbEngineType.SelectedItem is ComboBoxItem item && item.Content is string s)
        {
            return s.Trim().ToLowerInvariant();
        }
        return "remotion";
    }

    private async void BtnRunAiCommand_Click(object sender, RoutedEventArgs e)
    {
        BtnRunAiCommand.IsEnabled = false;
        try
        {
            await EnsureBackendRunningAsync();
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
            // Release file lock on video player before overwriting the same project's MP4
            VideoPlayer.Stop();
            VideoPlayer.Source = null;

            var engine = GetSelectedEngine();
            var req = new CreateProjectRequestDto
            {
                ProjectId = TxtProjectId.Text.Trim(),
                SourceUrl = TxtSourceUrl.Text.Trim(),
                EngineType = engine,
                TemplateId = TxtTemplateId.Text.Trim(),
                ScriptText = TxtScriptText.Text.Trim(),
            };

            TxtStepStatus.Text = $"Running 5-Step Pipeline ({engine.ToUpperInvariant()})...";
            PbPipeline.Value = 25;
            AppendLog($"Starting pipeline for '{req.ProjectId}' [engine={req.EngineType}, source={req.SourceUrl}]...");

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

        BtnRerenderSubtitles.IsEnabled = false;
        try
        {
            VideoPlayer.Stop();
            VideoPlayer.Source = null;

            var engine = GetSelectedEngine();
            var req = new UpdateSubtitlesRequestDto
            {
                EngineType = engine,
                Subtitles = SubtitleItems.ToList(),
            };
            AppendLog($"Re-rendering '{_currentProject.ProjectId}' overlay with {engine.ToUpperInvariant()}...");
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
        if (!double.TryParse(TxtTrimStart.Text, out double startSec) ||
            !double.TryParse(TxtTrimEnd.Text, out double endSec) ||
            endSec <= startSec)
        {
            MessageBox.Show("Enter valid Start and End seconds (End > Start).", "Invalid Trim Range", MessageBoxButton.OK, MessageBoxImage.Warning);
            return;
        }

        BtnTrimVideo.IsEnabled = false;
        try
        {
            VideoPlayer.Stop();
            VideoPlayer.Source = null;

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

    private void BtnAddSubtitleRow_Click(object sender, RoutedEventArgs e)
    {
        double lastEnd = SubtitleItems.Count > 0 ? SubtitleItems.Max(s => s.EndTime) : 0.0;
        SubtitleItems.Add(new SubtitleSegmentDto
        {
            StartTime = Math.Round(lastEnd, 2),
            EndTime = Math.Round(lastEnd + 2.0, 2),
            Text = "New caption segment",
        });
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
