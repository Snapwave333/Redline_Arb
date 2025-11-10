using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;
using CalmCadence.App.ViewModels;

namespace CalmCadence.App.Views
{
    public partial class RoutineListPage : Page
    {
        private RoutineListViewModel _viewModel;

        public RoutineListPage()
        {
            this.InitializeComponent();
            _viewModel = new RoutineListViewModel();
            DataContext = _viewModel;
        }

        protected override async void OnNavigatedTo(NavigationEventArgs e)
        {
            base.OnNavigatedTo(e);
            await _viewModel.LoadRoutinesAsync();
        }

        private void OnBackClicked(object sender, RoutedEventArgs e)
        {
            Frame?.GoBack();
        }

        private void OnAddRoutineClicked(object sender, RoutedEventArgs e)
        {
            Frame?.Navigate(typeof(RoutineDetailPage), null);
        }

        private void OnRefreshClicked(object sender, RoutedEventArgs e)
        {
            _ = _viewModel.LoadRoutinesAsync();
        }

        private async void OnRunRoutineClicked(object sender, RoutedEventArgs e)
        {
            if (sender is Button button && button.Tag is Guid routineId)
            {
                await _viewModel.RunRoutineAsync(routineId);
            }
        }

        private void OnEditRoutineClicked(object sender, RoutedEventArgs e)
        {
            if (sender is Button button && button.Tag is Guid routineId)
            {
                Frame?.Navigate(typeof(RoutineDetailPage), routineId);
            }
        }

        private async void OnDuplicateRoutineClicked(object sender, RoutedEventArgs e)
        {
            if (sender is MenuFlyoutItem menuItem && menuItem.Tag is Guid routineId)
            {
                await _viewModel.DuplicateRoutineAsync(routineId);
            }
        }

        private async void OnDeleteRoutineClicked(object sender, RoutedEventArgs e)
        {
            if (sender is MenuFlyoutItem menuItem && menuItem.Tag is Guid routineId)
            {
                var dialog = new ContentDialog
                {
                    Title = "Delete Routine",
                    Content = "Are you sure you want to delete this routine? This action cannot be undone.",
                    PrimaryButtonText = "Delete",
                    CloseButtonText = "Cancel",
                    XamlRoot = this.XamlRoot
                };

                var result = await dialog.ShowAsync();
                if (result == ContentDialogResult.Primary)
                {
                    await _viewModel.DeleteRoutineAsync(routineId);
                }
            }
        }
    }
}
