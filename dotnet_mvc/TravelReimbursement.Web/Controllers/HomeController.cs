using Microsoft.AspNetCore.Mvc;
using System.Text.Json;

namespace TravelReimbursement.Web.Controllers;

public class HomeController : Controller
{
    private readonly IHttpClientFactory _factory;
    public HomeController(IHttpClientFactory factory) => _factory = factory;

    public async Task<IActionResult> Index()
    {
        try
        {
            var client = _factory.CreateClient("ReimbursementApi");
            var json = await client.GetStringAsync("/api/claims/sample");
            ViewBag.SampleJson = JsonDocument.Parse(json).RootElement.ToString();
            ViewBag.ApiAvailable = true;
        }
        catch
        {
            ViewBag.SampleJson = "Python API is unavailable. Start FastAPI on http://localhost:8000.";
            ViewBag.ApiAvailable = false;
        }
        return View();
    }
}
