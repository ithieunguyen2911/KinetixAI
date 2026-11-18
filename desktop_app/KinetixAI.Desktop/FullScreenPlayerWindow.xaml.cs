using System;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;
using System.Windows.Media.Animation;
using System.Windows.Threading;

namespace KinetixAI.Desktop;

/// <summary>
/// Dedicated borderless, maximized Cinema FullScreen Player for high-resolution video preview.
/// Features synchronized playhead, auto-hiding glass HUD, and pro NLE keyboard shortcuts.
/// </summary>
public partial class FullScreenPlayerWindow : Window
{
    private readonly string _mediaPath;
    private readonly TimeSpan _initialPosition;
    private readonly bool _startPlaying;
    private readonly string _projectTitle;

    private readonly DispatcherTimer _playheadTimer;
    private readonly DispatcherTimer _hudIdleTimer;

    private bool _isPlaying;
    private bool _isMuted;
    private double _previousVolume = 1.0;
    private double _videoDurationSeconds = 6.0;

    /// <summary>
    /// Playhead position when exiting fullscreen to synchronize back to MainWindow.
    /// </summary>
    public TimeSpan ExitPosition { get; private set; } = TimeSpan.Zero;

    /// <summary>
    /// Playback state when exiting fullscreen.
    /// </summary>
    public bool WasPlaying { get; private set; }

    public FullScreenPlayerWindow(
        string mediaPath,
        TimeSpan initialPosition,
        bool isPlaying = true,
        double initialVolume = 1.0,
        string projectTitle = "Kinetix Studio Video")
    {
        InitializeComponent();

        _mediaPath = mediaPath;
        _initialPosition = initialPosition;
        _startPlaying = isPlaying;
        _previousVolume = Math.Clamp(initialVolume, 0.0, 1.0);
        _projectTitle = string.IsNullOrWhiteSpace(projectTitle) ? "Kinetix Studio" : projectTitle;

        _playheadTimer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(40) };
        _playheadTimer.Tick += PlayheadTimer_Tick;

        _hudIdleTimer = new DispatcherTimer { Interval = TimeSpan.FromSeconds(2.5) };
        _hudIdleTimer.Tick += HudIdleTimer_Tick;

        Loaded += FullScreenPlayerWindow_Loaded;
        Closing += FullScreenPlayerWindow_Closing;
    }

    private void FullScreenPlayerWindow_Loaded(object sender, RoutedEventArgs e)
    {
        TxtFsTitle.Text = _projectTitle;

        if (File.Exists(_mediaPath))
        {
            FsPlayer.Source = new Uri(_mediaPath, UriKind.Absolute);
            FsPlayer.Volume = _previousVolume;
            FsVolumeSlider.Value = _previousVolume;

            FsPlayer.Position = _initialPosition;
            if (_startPlaying)
            {
                FsPlayer.Play();
                _isPlaying = true;
                BtnFsPlayPause.Content = "Pause ⏸";
                _playheadTimer.Start();
            }
            else
            {
                FsPlayer.Pause();
                _isPlaying = false;
                BtnFsPlayPause.Content = "Play ⏵";
            }
        }
        else
        {
            MessageBox.Show(
                $"Không tìm thấy file video: {_mediaPath}",
                "Lỗi Video",
                MessageBoxButton.OK,
                MessageBoxImage.Warning);
            Close();
            return;
        }

        _hudIdleTimer.Start();
    }

    private void FullScreenPlayerWindow_Closing(object? sender, System.ComponentModel.CancelEventArgs e)
    {
        ExitPosition = FsPlayer.Position;
        WasPlaying = _isPlaying;

        _playheadTimer.Stop();
        _hudIdleTimer.Stop();

        try
        {
            FsPlayer.Stop();
            FsPlayer.Close();
        }
        catch
        {
            // Ignore clean teardown warnings
        }

        Mouse.OverrideCursor = null;
    }

    #region MediaElement Lifecycle & Playhead

    private void FsPlayer_MediaOpened(object sender, RoutedEventArgs e)
    {
        if (FsPlayer.NaturalDuration.HasTimeSpan)
        {
            _videoDurationSeconds = Math.Max(0.5, FsPlayer.NaturalDuration.TimeSpan.TotalSeconds);
            FsSliderScrub.Maximum = _videoDurationSeconds;

            var w = FsPlayer.NaturalVideoWidth;
            var h = FsPlayer.NaturalVideoHeight;
            if (w > 0 && h > 0)
            {
                TxtFsSpecs.Text = $"•  {w}x{h}  •  30 fps  •  Stereo Audio";
            }

            if (_initialPosition.TotalSeconds > 0 && _initialPosition.TotalSeconds <= _videoDurationSeconds)
            {
                FsPlayer.Position = _initialPosition;
                FsSliderScrub.Value = _initialPosition.TotalSeconds;
            }

            UpdateFsTimecodeDisplay(FsPlayer.Position.TotalSeconds, _videoDurationSeconds);
        }
    }

    private void FsPlayer_MediaEnded(object sender, RoutedEventArgs e)
    {
        FsPlayer.Position = TimeSpan.Zero;
        FsSliderScrub.Value = 0;
        _isPlaying = false;
        BtnFsPlayPause.Content = "Play ⏵";
        _playheadTimer.Stop();
        UpdateFsTimecodeDisplay(0.0, _videoDurationSeconds);
        FadeInHud();
    }

    private void PlayheadTimer_Tick(object? sender, EventArgs e)
    {
        if (!_isPlaying || !FsPlayer.NaturalDuration.HasTimeSpan) return;

        var pos = FsPlayer.Position.TotalSeconds;
        FsSliderScrub.Value = pos;
        UpdateFsTimecodeDisplay(pos, _videoDurationSeconds);
    }

    private void UpdateFsTimecodeDisplay(double currentSec, double totalSec)
    {
        var curSpan = TimeSpan.FromSeconds(Math.Max(0, currentSec));
        var totSpan = TimeSpan.FromSeconds(Math.Max(0, totalSec));

        var curFmt = curSpan.TotalHours >= 1
            ? curSpan.ToString(@"hh\:mm\:ss\.ff")
            : curSpan.ToString(@"mm\:ss\.ff");

        var totFmt = totSpan.TotalHours >= 1
            ? totSpan.ToString(@"hh\:mm\:ss\.ff")
            : totSpan.ToString(@"mm\:ss\.ff");

        TxtFsTimecode.Text = $"{curFmt} / {totFmt}";
    }

    private void SeekTo(double targetSeconds)
    {
        var clamped = Math.Clamp(targetSeconds, 0.0, _videoDurationSeconds);
        FsPlayer.Position = TimeSpan.FromSeconds(clamped);
        FsSliderScrub.Value = clamped;
        UpdateFsTimecodeDisplay(clamped, _videoDurationSeconds);
    }

    #endregion

    #region Auto-Hiding Glass HUD Engine

    private void HudIdleTimer_Tick(object? sender, EventArgs e)
    {
        if (_isPlaying)
        {
            FadeOutHud();
        }
    }

    private void FadeOutHud()
    {
        if (HudContainer.Opacity > 0.05)
        {
            var anim = new DoubleAnimation(0.0, TimeSpan.FromMilliseconds(450))
            {
                EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseOut }
            };
            HudContainer.BeginAnimation(UIElement.OpacityProperty, anim);
            Mouse.OverrideCursor = Cursors.None;
        }
    }

    private void FadeInHud()
    {
        if (HudContainer.Opacity < 0.95)
        {
            var anim = new DoubleAnimation(1.0, TimeSpan.FromMilliseconds(180))
            {
                EasingFunction = new QuadraticEase { EasingMode = EasingMode.EaseIn }
            };
            HudContainer.BeginAnimation(UIElement.OpacityProperty, anim);
            Mouse.OverrideCursor = null;
        }
    }

    private void Window_MouseMove(object sender, MouseEventArgs e)
    {
        FadeInHud();
        _hudIdleTimer.Stop();
        _hudIdleTimer.Start();
    }

    private void Window_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
    {
        if (e.ClickCount == 2)
        {
            Close();
        }
    }

    #endregion

    #region Transport Controls & Actions

    private void BtnFsPlayPause_Click(object sender, RoutedEventArgs e)
    {
        TogglePlayPause();
    }

    private void TogglePlayPause()
    {
        if (_isPlaying)
        {
            FsPlayer.Pause();
            _isPlaying = false;
            BtnFsPlayPause.Content = "Play ⏵";
            FadeInHud();
        }
        else
        {
            FsPlayer.Play();
            _isPlaying = true;
            BtnFsPlayPause.Content = "Pause ⏸";
            _playheadTimer.Start();
            _hudIdleTimer.Stop();
            _hudIdleTimer.Start();
        }
    }

    private void BtnFsReplay5s_Click(object sender, RoutedEventArgs e)
    {
        SeekTo(FsPlayer.Position.TotalSeconds - 5.0);
    }

    private void BtnFsForward5s_Click(object sender, RoutedEventArgs e)
    {
        SeekTo(FsPlayer.Position.TotalSeconds + 5.0);
    }

    private void BtnFsStop_Click(object sender, RoutedEventArgs e)
    {
        FsPlayer.Stop();
        _isPlaying = false;
        BtnFsPlayPause.Content = "Play ⏵";
        SeekTo(0.0);
        FadeInHud();
    }

    private void FsSliderScrub_PreviewMouseLeftButtonUp(object sender, MouseButtonEventArgs e)
    {
        SeekTo(FsSliderScrub.Value);
    }

    private void FsVolumeSlider_ValueChanged(object sender, RoutedPropertyChangedEventArgs<double> e)
    {
        if (FsPlayer != null)
        {
            FsPlayer.Volume = e.NewValue;
            _previousVolume = e.NewValue;
            BtnFsMute.Content = e.NewValue <= 0.001 ? "🔇" : "🔊";
            _isMuted = e.NewValue <= 0.001;
        }
    }

    private void BtnFsMute_Click(object sender, RoutedEventArgs e)
    {
        if (_isMuted)
        {
            _isMuted = false;
            var restore = _previousVolume > 0.05 ? _previousVolume : 0.8;
            FsPlayer.Volume = restore;
            FsVolumeSlider.Value = restore;
            BtnFsMute.Content = "🔊";
        }
        else
        {
            _isMuted = true;
            _previousVolume = FsVolumeSlider.Value;
            FsPlayer.Volume = 0.0;
            FsVolumeSlider.Value = 0.0;
            BtnFsMute.Content = "🔇";
        }
    }

    private void BtnFsExit_Click(object sender, RoutedEventArgs e)
    {
        Close();
    }

    private void Window_KeyDown(object sender, KeyEventArgs e)
    {
        switch (e.Key)
        {
            case Key.Space:
                TogglePlayPause();
                e.Handled = true;
                break;

            case Key.Escape:
            case Key.F11:
            case Key.F:
                Close();
                e.Handled = true;
                break;

            case Key.Left:
                SeekTo(FsPlayer.Position.TotalSeconds - 5.0);
                e.Handled = true;
                break;

            case Key.Right:
                SeekTo(FsPlayer.Position.TotalSeconds + 5.0);
                e.Handled = true;
                break;

            case Key.M:
                BtnFsMute_Click(this, new RoutedEventArgs());
                e.Handled = true;
                break;

            case Key.Home:
                SeekTo(0.0);
                e.Handled = true;
                break;

            case Key.End:
                SeekTo(_videoDurationSeconds);
                e.Handled = true;
                break;
        }
    }

    #endregion
}
