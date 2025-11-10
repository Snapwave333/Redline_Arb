using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;
using CalmCadence.App.ViewModels;

namespace CalmCadence.App.Views
{
    public partial class RoutineDetailPage : Page
    {
        private RoutineDetailViewModel _viewModel;

        public RoutineDetailPage()
        {
            this.InitializeComponent();
            _viewModel = new RoutineDetailViewModel();
            DataContext = _viewModel;
        }

        protected override async void OnNavigatedTo(NavigationEventArgs e)
        {
            base.OnNavigatedTo(e);

            if (e.Parameter is Guid routineId)
            {
                // Edit existing routine
                await _viewModel.LoadRoutineAsync(routineId);
            }
            else
            {
                // Create new routine
                _viewModel.InitializeNewRoutine();
            }
        }

        private void OnBackClicked(object sender, RoutedEventArgs e)
        {
            if (_viewModel.HasUnsavedChanges)
            {
                ShowUnsavedChangesDialog();
            }
            else
            {
                Frame?.GoBack();
            }
        }

        private async void ShowUnsavedChangesDialog()
        {
            var dialog = new ContentDialog
            {
                Title = "Unsaved Changes",
                Content = "You have unsaved changes. Do you want to save them before leaving?",
                PrimaryButtonText = "Save",
                SecondaryButtonText = "Discard",
                CloseButtonText = "Cancel",
                XamlRoot = this.XamlRoot
            };

            var result = await dialog.ShowAsync();
            switch (result)
            {
                case ContentDialogResult.Primary:
                    await OnSaveClicked(this, new RoutedEventArgs());
                    break;
                case ContentDialogResult.Secondary:
                    Frame?.GoBack();
                    break;
            }
        }

        private void OnAddStepClicked(object sender, RoutedEventArgs e)
        {
            _viewModel.AddNewStep();
        }

        private async void OnSaveClicked(object sender, RoutedEventArgs e)
        {
            var success = await _viewModel.SaveRoutineAsync();
            if (success)
            {
                Frame?.GoBack();
            }
        }

        private void OnCancelClicked(object sender, RoutedEventArgs e)
        {
            if (_viewModel.HasUnsavedChanges)
            {
                ShowUnsavedChangesDialog();
            }
            else
            {
                Frame?.GoBack();
            }
        }
    }
}
