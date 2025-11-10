using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;
using Microsoft.UI.Xaml.Navigation;
using CalmCadence.App.ViewModels;

namespace CalmCadence.App.Views;

public sealed partial class GoogleIntegrationPage : Page
{
    private readonly GoogleIntegrationPageViewModel _viewModel;

    public GoogleIntegrationPage()
    {
        this.InitializeComponent();
        _viewModel = new GoogleIntegrationPageViewModel();
        DataContext = _viewModel;
    }

    protected override async void OnNavigatedTo(NavigationEventArgs e)
    {
        base.OnNavigatedTo(e);
        await _viewModel.LoadSettingsAsync();
    }

    private async void SignInButton_Click(object sender, RoutedEventArgs e)
    {
        await _viewModel.SignInAsync();
    }

    private async void SignOutButton_Click(object sender, RoutedEventArgs e)
    {
        await _viewModel.SignOutAsync();
    }

    private async void SyncButton_Click(object sender, RoutedEventArgs e)
    {
        await _viewModel.SyncNowAsync();
    }
}
