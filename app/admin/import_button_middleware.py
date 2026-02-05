"""Middleware to inject Import button into SQLAdmin pages."""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class ImportButtonMiddleware(BaseHTTPMiddleware):
    """Middleware to add Import button next to Export button in admin."""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Only inject into admin list pages
        if (request.url.path.startswith("/admin/") and 
            "/list" in request.url.path and
            response.status_code == 200 and
            response.headers.get("content-type", "").startswith("text/html")):
            
            # Get the identity from URL (e.g., /admin/player/list -> player)
            path_parts = request.url.path.split("/")
            if len(path_parts) >= 3:
                identity = path_parts[2]
                
                # Read response body
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                
                body_str = body.decode("utf-8")
                
                # Inject Import button JavaScript
                import_js = f"""
                <script>
                document.addEventListener('DOMContentLoaded', function() {{
                    setTimeout(function() {{
                        // Find the Export button
                        const exportBtn = document.querySelector('a.btn[href*="export"]');
                        if (exportBtn && !document.querySelector('.import-btn-custom')) {{
                            // Create Import button
                            const importBtn = document.createElement('a');
                            importBtn.href = '/admin/{identity}/import';
                            importBtn.className = 'btn btn-primary import-btn-custom';
                            importBtn.style.marginLeft = '10px';
                            importBtn.innerHTML = '<i class="fa fa-upload"></i> Import';
                            
                            // Insert after Export button
                            exportBtn.parentNode.insertBefore(importBtn, exportBtn.nextSibling);
                        }}
                    }}, 100);
                }});
                </script>
                """
                
                # Inject before closing body tag
                if "</body>" in body_str:
                    body_str = body_str.replace("</body>", import_js + "</body>")
                    body = body_str.encode("utf-8")
                
                # Create new response with modified body
                # Update Content-Length header
                headers = dict(response.headers)
                headers['content-length'] = str(len(body))
                
                return Response(
                    content=body,
                    status_code=response.status_code,
                    headers=headers,
                    media_type=response.media_type
                )
        
        return response
