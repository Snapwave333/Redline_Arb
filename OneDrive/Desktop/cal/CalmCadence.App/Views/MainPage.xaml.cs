using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;
using CalmCadence.App.ViewModels;

namespace CalmCadence.App.Views
{
    /// <summary>
    /// The main dashboard page displaying Daily Studio status and navigation options.
    /// </summary>
    public partial class MainPage : Page
    {
        private readonly MainPageViewModel _viewModel;

        public MainPage()
        {
            this.InitializeComponent();
            _viewModel = new MainPageViewModel();
            DataContext = _viewModel;
        }

        protected override async void OnNavigatedTo(NavigationEventArgs e)
        {
            base.OnNavigatedTo(e);
            await _viewModel.LoadStatusAsync();
        }

        private void OnGoogleIntegrationClicked(object sender, RoutedEventArgs e)
        {
            Frame?.Navigate(typeof(GoogleIntegrationPage));
        }

        private void OnDailyStudioClicked(object sender, RoutedEventArgs e)
        {
            Frame?.Navigate(typeof(DailyStudioPage));
        }

        private void OnManageRoutinesClicked(object sender, RoutedEventArgs e)
        {
            Frame?.Navigate(typeof(RoutineListPage));
        }
    }
}
