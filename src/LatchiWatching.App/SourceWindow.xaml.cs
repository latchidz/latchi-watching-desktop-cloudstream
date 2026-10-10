using System.IO;
using System.Windows;
using System.Windows.Input;
using System.Windows.Threading;
using Microsoft.Web.WebView2.Core;
using LatchiWatching.Core;
namespace LatchiWatching.App;
// Based on the working LATCHI PLAY full-screen player, generalized to an explicitly selected website.
public partial class SourceWindow : Window
{
    private readonly CoreWebView2Environment _env;
    private readonly string _url;
    private DispatcherTimer? _safety;
    public TaskCompletionSource<bool> Ready {get;} = new(TaskCreationOptions.RunContinuationsAsynchronously);
    public int BlockedPopups {get;private set;}
    public SourceWindow(CoreWebView2Environment env,string url,string title)
    {
        if(!Sources.IsSafeWebsite(url) && !(App.IsTest && url=="https://test.local/index.html")) throw new ArgumentException("Invalid website");
        InitializeComponent();_env=env;_url=url;Title=title+" — LATCHI WATCHING";
        Activated+=(_,_)=>Topmost=true;Deactivated+=(_,_)=>Topmost=false;
        Loaded+=async (_,_)=>await InitAsync();
        Closed+=(_,_)=>{_safety?.Stop();PlayerWeb.Dispose();};
    }
    private async Task InitAsync()
    {
        try
        {
            await PlayerWeb.EnsureCoreWebView2Async(_env);var core=PlayerWeb.CoreWebView2;
            if(App.IsTest) core.SetVirtualHostNameToFolderMapping("test.local",App.TestFixture!,CoreWebView2HostResourceAccessKind.DenyCors);
            core.Settings.AreDefaultContextMenusEnabled=false;core.Settings.AreDevToolsEnabled=false;core.Settings.IsStatusBarEnabled=false;
            core.Settings.IsZoomControlEnabled=false;core.Settings.AreDefaultScriptDialogsEnabled=false;core.Settings.IsBuiltInErrorPageEnabled=false;
            core.NewWindowRequested+=(_,ev)=>{BlockedPopups++;ev.Handled=true;};
            core.DownloadStarting+=(_,ev)=>{ev.Cancel=true;};
            core.PermissionRequested+=(_,ev)=>{ev.State=CoreWebView2PermissionState.Deny;};
            core.NavigationStarting+=(_,ev)=>{if(!Sources.IsSafeWebsite(ev.Uri) && !(App.IsTest && ev.Uri.StartsWith("https://test.local/"))) ev.Cancel=true;};
            await core.AddScriptToExecuteOnDocumentCreatedAsync(WebGuards.PlayerGuardScript);
            // WPF does not expose CoreWebView2Controller. Route iframe exit messages
            // through the public frame API instead of an unavailable controller property.
            core.FrameCreated+=(_,created)=>
            {
                created.Frame.WebMessageReceived+=(_,ev)=>{try{if(ev.TryGetWebMessageAsString()=="latchi-player-exit")Dispatcher.BeginInvoke(new Action(ClosePlayer));}catch{}};
            };
            core.WebMessageReceived+=(_,ev)=>{try{if(ev.TryGetWebMessageAsString()=="latchi-player-exit")ClosePlayer();}catch{}};
            core.NavigationCompleted+=(_,ev)=>
            {
                _safety?.Stop();
                if(ev.IsSuccess){LoadingOverlay.Visibility=Visibility.Collapsed;PlayerWeb.Visibility=Visibility.Visible;Ready.TrySetResult(true);}
                else{ShowError("تعذّر الاتصال بالمصدر. قد يكون الموقع متوقفًا أو محجوبًا؛ جرّب لاحقًا أو عدّل عنوانه من الإعدادات.");Ready.TrySetResult(false);}
            };
            _safety=new DispatcherTimer{Interval=TimeSpan.FromSeconds(20)};
            _safety.Tick+=(_,_)=>{_safety.Stop();LoadingOverlay.Visibility=Visibility.Collapsed;PlayerWeb.Visibility=Visibility.Visible;};_safety.Start();
            core.Navigate(_url);
        }
        catch(Exception ex){App.Log(ex);ShowError("تعذّر بدء WebView2. تحقّق من تثبيت Runtime ثم أعد المحاولة.");Ready.TrySetResult(false);}
    }
    private void ShowError(string text){PlayerWeb.Visibility=Visibility.Hidden;LoadingOverlay.Visibility=Visibility.Collapsed;ErrorText.Text=text;ErrorOverlay.Visibility=Visibility.Visible;}
    public async Task<string> ExecuteAsync(string script)=>await PlayerWeb.CoreWebView2.ExecuteScriptAsync(script);
    public async Task CaptureAsync(string path){await using var f=File.Create(path);await PlayerWeb.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png,f);}
    public void ClosePlayer(){try{_ = PlayerWeb.CoreWebView2?.ExecuteScriptAsync("try{document.querySelectorAll('video,audio').forEach(v=>v.pause());if(document.pictureInPictureElement)document.exitPictureInPicture();}catch(e){}");}catch{}Close();}
    private void OnExitClick(object sender,RoutedEventArgs e)=>ClosePlayer();
    private void OnWindowKeyDown(object sender,KeyEventArgs e){if(e.Key==Key.Escape){e.Handled=true;ClosePlayer();}}
}
