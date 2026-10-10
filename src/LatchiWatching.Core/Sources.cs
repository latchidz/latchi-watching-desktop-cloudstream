using System.Text.Json;
namespace LatchiWatching.Core;
public sealed record SourceDefinition(string Id,string Arabic,string English,string Image,string Url);
public static class Sources
{
    public static readonly IReadOnlyList<SourceDefinition> All = new SourceDefinition[] {
        new("3isk", "قصة عشق ١", "3isk", "assets/sources/qissat-eshq-1.jpg", "https://3esk.onl"),
        new("eseek", "قصة عشق ٢", "Eseek", "assets/sources/qissat-eshq-2.jpg", "https://qeseh.net"),
        new("Krmzy", "قرمزي", "Krmzy", "assets/sources/krmzy.jpg", "https://krmzi.org"),
        new("MyCimaProvider", "ماي سيما", "MyCima", "assets/sources/mycima.jpg", "https://mycima.living"),
        new("Topcinema", "توب سينما", "TopCinema", "assets/sources/topcinema.jpg", "https://web8.topcinema.cam"),
        new("TukTukcima", "توك توك سيما", "TukTukCima", "assets/sources/tuktukcima.jpg", "https://tuktukhd.com"),
        new("Tuniflix", "تونيفليكس", "TuniFlix", "assets/sources/tuniflix.jpg", "https://tuniflix.site"),
        new("Wecima", "وي سيما", "WeCima", "assets/sources/wecima.jpg", "https://wecima.ac")
    };
    public static SourceDefinition? Find(string? id) => All.FirstOrDefault(x => x.Id == id);
    public static bool IsSafeWebsite(string? value)
    {
        if (value is null || value.Length > 2048 || !Uri.TryCreate(value,UriKind.Absolute,out var u)) return false;
        if (u.Scheme != "https" || u.Port != 443 || u.UserInfo.Length != 0 || u.IsLoopback || u.HostNameType != UriHostNameType.Dns) return false;
        var host=u.IdnHost.ToLowerInvariant();
        return host.Contains('.') && !host.EndsWith('.') && !new[]{".local",".localhost",".internal",".test"}.Any(host.EndsWith);
    }
    public static bool IsAppOrigin(string? value) => Uri.TryCreate(value,UriKind.Absolute,out var u) && u.Scheme=="https" && u.Host=="app.local" && u.Port==443;
    public static Dictionary<string,string> ValidateOverrides(IReadOnlyDictionary<string,string> input)
    {
        var result=new Dictionary<string,string>();
        foreach(var (id,url) in input) { if(Find(id) is null || !IsSafeWebsite(url)) throw new ArgumentException("Invalid source URL"); result[id]=url; }
        return result;
    }
}
