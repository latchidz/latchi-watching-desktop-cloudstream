using System.IO;
using System.Text.Json;
using System.Windows;
using Microsoft.Web.WebView2.Core;
using LatchiWatching.Core;
namespace LatchiWatching.App;
public partial class MainWindow : Window
{
    private CoreWebView2Environment? _env;
    private SourceWindow? _source;
    private readonly string _data=Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"LATCHI","WatchingWindows");
    private Dictionary<string,string> _overrides=new();
    public MainWindow(){InitializeComponent();MaxHeight=SystemParameters.WorkArea.Height+10;Loaded+=async (_,_)=>await InitAsync();Closed+=(_,_)=>{_source?.Close();Web.Dispose();};}
    private async Task InitAsync()
    {
        try
        {
            Directory.CreateDirectory(_data);
            var file=Path.Combine(_data,"sources.json");
            if(File.Exists(file))try{_overrides=Sources.ValidateOverrides(JsonSerializer.Deserialize<Dictionary<string,string>>(File.ReadAllText(file))??new());}catch{_overrides=new();}
            var profile=App.IsTest?Path.Combine(App.TestOutput!,"profile"):Path.Combine(_data,"WebView2");
            _env=await CoreWebView2Environment.CreateAsync(null,profile,new CoreWebView2EnvironmentOptions{AdditionalBrowserArguments="--autoplay-policy=no-user-gesture-required"+(App.IsTest?" --disable-gpu":"")});
            await Web.EnsureCoreWebView2Async(_env);var core=Web.CoreWebView2;
            core.Settings.AreDevToolsEnabled=false;core.Settings.AreDefaultContextMenusEnabled=false;core.Settings.IsStatusBarEnabled=false;core.Settings.IsZoomControlEnabled=false;core.Settings.AreDefaultScriptDialogsEnabled=false;
            core.NewWindowRequested+=(_,ev)=>ev.Handled=true;core.DownloadStarting+=(_,ev)=>ev.Cancel=true;
            core.NavigationStarting+=(_,ev)=>{if(!Sources.IsAppOrigin(ev.Uri)&&ev.Uri!="about:blank")ev.Cancel=true;};
            await core.AddScriptToExecuteOnDocumentCreatedAsync(WebGuards.PopupBlockScript);
            core.SetVirtualHostNameToFolderMapping("app.local",Path.Combine(AppContext.BaseDirectory,"wwwroot"),CoreWebView2HostResourceAccessKind.DenyCors);
            core.WebMessageReceived+=Handle;
            core.NavigationCompleted+=async (_,ev)=>{if(ev.IsSuccess&&App.IsTest)await RunSelfTestAsync();};
            core.Navigate("https://app.local/index.html");
        }
        catch(Exception ex){App.Log(ex);if(App.IsTest){await WriteFailureAsync(ex.Message);Application.Current.Shutdown(2);}else{MessageBox.Show("يحتاج التطبيق Microsoft Edge WebView2 Runtime. ثبّته من موقع Microsoft ثم أعد فتح التطبيق.","LATCHI WATCHING");Close();}}
    }
    private void Post(object data)=>Web.CoreWebView2.PostWebMessageAsJson(JsonSerializer.Serialize(data));
    private void Handle(object? sender,CoreWebView2WebMessageReceivedEventArgs ev)
    {
        if(!Sources.IsAppOrigin(ev.Source))return;
        try
        {
            using var doc=JsonDocument.Parse(ev.WebMessageAsJson);var root=doc.RootElement;var action=root.GetProperty("action").GetString();
            switch(action)
            {
                case "ready":Post(new{type="sources",sources=Sources.All.Select(s=>new{id=s.Id,arabic=s.Arabic,english=s.English,image=s.Image,url=_overrides.GetValueOrDefault(s.Id,s.Url)})});break;
                case "open":var item=Sources.Find(root.GetProperty("id").GetString());if(item is not null&&_env is not null&&_source is null){_source=new SourceWindow(_env,_overrides.GetValueOrDefault(item.Id,item.Url),item.Arabic);_source.Closed+=(_,_)=>{_source=null;Show();Activate();};_source.Show();}break;
                case "min":WindowState=WindowState.Minimized;break;
                case "max":WindowState=WindowState==WindowState.Maximized?WindowState.Normal:WindowState.Maximized;break;
                case "close":Close();break;
                case "drag":try{DragMove();}catch{}break;
                case "save":var urls=JsonSerializer.Deserialize<Dictionary<string,string>>(root.GetProperty("urls").GetRawText())??new();_overrides=Sources.ValidateOverrides(urls);var path=Path.Combine(_data,"sources.json");File.WriteAllText(path+".tmp",JsonSerializer.Serialize(_overrides));File.Move(path+".tmp",path,true);Post(new{type="saved"});break;
            }
        }
        catch(Exception ex){Post(new{type="error",message="تعذّر تنفيذ الطلب: تحقّق من العناوين وأعد المحاولة."});App.Log(ex);}
    }
    private async Task WriteFailureAsync(string message){if(App.TestOutput is not null)await File.WriteAllTextAsync(Path.Combine(App.TestOutput,"ui-report.json"),JsonSerializer.Serialize(new{passed=false,error=message}));}
    private async Task RunSelfTestAsync()
    {
        try
        {
            await Task.Delay(1400);
            var menu=JsonDocument.Parse(await Web.CoreWebView2.ExecuteScriptAsync("JSON.stringify({count:document.querySelectorAll('.source-card').length,images:[...document.querySelectorAll('.source-card img')].map(i=>({width:i.naturalWidth,height:i.naturalHeight})),popupBlocked:window.open('about:blank')===null})"));
            var menuJson=JsonDocument.Parse(menu.RootElement.GetString()!);
            if(menuJson.RootElement.GetProperty("count").GetInt32()!=8||!menuJson.RootElement.GetProperty("popupBlocked").GetBoolean())throw new Exception("Home/popup assertion failed");
            foreach(var im in menuJson.RootElement.GetProperty("images").EnumerateArray())if(im.GetProperty("width").GetInt32()!=1800||im.GetProperty("height").GetInt32()!=600)throw new Exception("Source images must be exact 3:1");
            await using(var image=File.Create(Path.Combine(App.TestOutput!,"LATCHI-WATCHING-Home-Windows.png")))await Web.CoreWebView2.CapturePreviewAsync(CoreWebView2CapturePreviewImageFormat.Png,image);
            var player=new SourceWindow(_env!,"https://test.local/index.html","اختبار فيديو قانوني");player.Show();
            if(!await player.Ready.Task.WaitAsync(TimeSpan.FromSeconds(45)))throw new Exception("Local player navigation failed");
            await Task.Delay(1800);
            var videoRaw=await player.ExecuteAsync("JSON.stringify({time:document.querySelector('video').currentTime,ready:document.querySelector('video').readyState,colors:(()=>{let c=document.createElement('canvas');c.width=64;c.height=36;let x=c.getContext('2d');x.drawImage(document.querySelector('video'),0,0,64,36);let p=x.getImageData(0,0,64,36).data,s=new Set();for(let i=0;i<p.length;i+=4)s.add(p[i]+','+p[i+1]+','+p[i+2]);return s.size})(),popupBlocked:window.open('https://example.com')===null})");
            var video=JsonDocument.Parse(JsonDocument.Parse(videoRaw).RootElement.GetString()!);
            if(video.RootElement.GetProperty("time").GetDouble()<0.3||video.RootElement.GetProperty("ready").GetInt32()<2||video.RootElement.GetProperty("colors").GetInt32()<8||!video.RootElement.GetProperty("popupBlocked").GetBoolean())throw new Exception("Video decode/render/popup assertions failed");
            await player.CaptureAsync(Path.Combine(App.TestOutput!,"Local-Video-Windows.png"));
            await player.ExecuteAsync("document.querySelector('video').pause();document.querySelector('video').currentTime=2;");await Task.Delay(500);
            var seek=JsonDocument.Parse(await player.ExecuteAsync("({paused:document.querySelector('video').paused,time:document.querySelector('video').currentTime})"));
            if(!seek.RootElement.GetProperty("paused").GetBoolean()||seek.RootElement.GetProperty("time").GetDouble()<1.8)throw new Exception("Pause/seek failed");
            var fullscreen=player.WindowState==WindowState.Maximized&&player.WindowStyle==WindowStyle.None;
            if(!fullscreen)throw new Exception("Full-screen source window not active");
            player.ClosePlayer();
            await File.WriteAllTextAsync(Path.Combine(App.TestOutput!,"ui-report.json"),JsonSerializer.Serialize(new{passed=true,source_cards=8,all_nine_images_ratio="3:1",local_video_decoded=true,local_video_colors=video.RootElement.GetProperty("colors").GetInt32(),pause_seek_passed=true,fullscreen_passed=fullscreen,popup_script_blocked=true,physical_audio_tested=false,live_provider_video_tested=false},new JsonSerializerOptions{WriteIndented=true}));
            Application.Current.Shutdown(0);
        }
        catch(Exception ex){await WriteFailureAsync(ex.ToString());Application.Current.Shutdown(2);}
    }
}
