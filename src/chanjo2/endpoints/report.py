from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

# @app.get("/report/", response_class=HTMLResponse)
# async def report(request: Request, id: str):
#   return templates.TemplateResponse("item.html", {"request": request, "id": id})
