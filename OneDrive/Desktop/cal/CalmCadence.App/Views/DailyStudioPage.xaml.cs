using System;
using System.Collections.ObjectModel;
using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using CalmCadence.Core.Interfaces;
using CalmCadence.Core.Models;
using Microsoft.Extensions.DependencyInjection;
using System.IO;
using Windows.Media.Core;

namespace CalmCadence.App.Views;

public sealed partial class DailyStudioPage : Page
{
    private IDailyStudioService _dailyStudioService;
    private ObservableCollection<DailyMedia> _dailyBriefs = new();

    public DailyStudioPage()
    {
        this.InitializeComponent();

        // Get service from DI
        _dailyStudioService = App.AppHost?.Services.GetRequiredService<IDailyStudioService>()
            ?? throw new InvalidOperationException("DailyStudioService not available");

        // Setup controls
        btnGenerateBrief.Click += BtnGenerateBrief_Click;
        btnSettings.Click += BtnSettings_Click;
        lstDailyBriefs.SelectionChanged += LstDailyBriefs_SelectionChanged;

        // Load data
        LoadDailyBriefs();
        UpdateCurrentDate();
    }

    private void UpdateCurrentDate()
    {
        txtCurrentDate.Text = DateTimeOffset.Now.ToString("dddd, MMMM d, yyyy");
    }

    private async void LoadDailyBriefs()
    {
        try
        {
            // Load last 30 days of briefs
            var startDate = DateTimeOffset.Now.AddDays(-30);
            var briefs = new ObservableCollection<DailyMedia>();

            for (int i = 0; i < 30; i++)
            {
                var date = startDate.AddDays(i);
                var media = await _dailyStudioService.GetDailyMediaAsync(date);
                if (media != null)
                {
                    briefs.Add(media);
                }
            }

            _dailyBriefs = briefs;
            lstDailyBriefs.ItemsSource = _dailyBriefs;
        }
        catch (Exception ex)
        {
            // TODO: Show error message
            System.Diagnostics.Debug.WriteLine($"Failed to load daily briefs: {ex.Message}");
        }
    }

    private async void BtnGenerateBrief_Click(object sender, RoutedEventArgs e)
    {
        try
        {
            btnGenerateBrief.IsEnabled = false;
            btnGenerateBrief.Content = "Generating...";

            var today = DateTimeOffset.Now.Date;
            var media = await _dailyStudioService.GenerateDailyBriefAsync(today);

            if (media != null)
            {
                // Refresh the list
                LoadDailyBriefs();

                // Auto-select the newly generated brief
                var newItem = _dailyBriefs.FirstOrDefault(m => m.Date.Date == today.Date);
                if (newItem != null)
                {
                    lstDailyBriefs.SelectedItem = newItem;
                }
            }
        }
        catch (Exception ex)
        {
            // TODO: Show error message
            System.Diagnostics.Debug.WriteLine($"Failed to generate brief: {ex.Message}");
        }
        finally
        {
            btnGenerateBrief.IsEnabled = true;
            btnGenerateBrief.Content = "Generate Today's Brief";
        }
    }

    private void BtnSettings_Click(object sender, RoutedEventArgs e)
    {
        // TODO: Navigate to settings page
    }

    private void LstDailyBriefs_SelectionChanged(object sender, SelectionChangedEventArgs e)
    {
        if (lstDailyBriefs.SelectedItem is DailyMedia media)
        {
            try
            {
                // Prefer video if available, otherwise fall back to audio
                if (!string.IsNullOrEmpty(media.VideoFilePath) && File.Exists(media.VideoFilePath))
                {
                    mediaPlayer.Source = MediaSource.CreateFromUri(new Uri(media.VideoFilePath));
                }
                else if (!string.IsNullOrEmpty(media.AudioFilePath) && File.Exists(media.AudioFilePath))
                {
                    mediaPlayer.Source = MediaSource.CreateFromUri(new Uri(media.AudioFilePath));
                }
                else
                {
                    mediaPlayer.Source = null;
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"Failed to load media: {ex.Message}");
            }
        }
    }
}
