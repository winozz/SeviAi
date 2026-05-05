# Web Directory - User Interfaces

## Purpose
Interactive web interfaces for chatting and analytics.

## Files

| File | Purpose |
|------|---------|
| `web_interface.html` | Real-time chat UI |
| `logs_dashboard.html` | Analytics and metrics dashboard |

## Web Interface

### web_interface.html
Beautiful, responsive chat interface for users.

**Features**:
- Real-time message sending/receiving
- User ID tracking
- Intent classification display
- Confidence score display
- Response time metrics
- Conversation history
- Message styling and formatting

**Usage**:
1. **Direct**: Open in browser
   ```bash
   open web_interface.html
   ```

2. **Hosted on API**: Place in static folder
   ```bash
   cp web/*.html /path/to/static/
   ```

3. **Via CDN**: Upload to CDN and reference

**Connection**:
- Default: http://localhost:8000
- Configurable in HTML (change `API_URL` constant)

**Features**:
- ✓ Real-time chat
- ✓ Intent display
- ✓ Confidence scores
- ✓ Response timing
- ✓ Message history
- ✓ Mobile responsive
- ✓ Dark/Light theme ready

### logs_dashboard.html
Real-time analytics and monitoring dashboard.

**Metrics**:
- Total messages today
- Unique users
- Most common intents
- Average confidence
- Top intents
- Intent performance over time

**Tabs**:
1. **Overview** - Daily statistics
2. **Messages** - Message log
3. **Intents** - Intent usage breakdown
4. **Sessions** - Session analytics
5. **Users** - User statistics

**Usage**:
1. Open in browser
   ```bash
   open web_interface.html
   ```

2. Dashboard auto-refreshes every 5 seconds

3. Data source: `/logs/today` endpoint

## Hosting Options

### Option 1: Direct File Access
```bash
open web_interface.html
```

Simple for local development.

### Option 2: Web Server
```bash
# Python built-in
python -m http.server 8080 --directory web/

# Node.js
npx http-server web/

# nginx
# Copy to /var/www/html/
# Access at http://localhost
```

### Option 3: API Integration
Serve from FastAPI:

```python
# In api/app.py
from fastapi.staticfiles import StaticFiles

app.mount("/web", StaticFiles(directory="web"), name="web")
```

Then access:
- Chat: http://localhost:8000/web/web_interface.html
- Dashboard: http://localhost:8000/web/logs_dashboard.html

### Option 4: CDN
Upload to AWS S3, Azure Blob, or similar:

1. Build with API URL pointing to your server
2. Upload HTML files
3. Access via CDN URL

## Customization

### Change API URL
Edit in HTML:
```javascript
const API_URL = "http://your-api-domain.com";
```

### Customize Colors
Edit CSS variables:
```css
:root {
  --primary-color: #2563eb;
  --secondary-color: #1e40af;
  --background: #ffffff;
}
```

### Change Refresh Rate
Edit in logs_dashboard.html:
```javascript
setInterval(refreshMetrics, 5000); // 5 seconds
```

## API Dependencies

Both interfaces require these API endpoints:

### web_interface.html
- `POST /chat` - Send message

### logs_dashboard.html
- `GET /logs/today` - Daily stats
- `GET /logs/intents` - Intent breakdown
- `GET /model/info` - Model info

Ensure API is running:
```bash
python -m uvicorn api.app:app --port 8000
```

## Troubleshooting

### "Failed to fetch from API"
1. Check API is running
   ```bash
   curl http://localhost:8000/health
   ```

2. Check CORS is enabled in API

3. Verify API URL in HTML matches actual URL

### Dashboard Shows No Data
1. Ensure API is running
2. Send test message to populate logs
3. Check browser console for errors
4. Verify `/logs/today` endpoint works
   ```bash
   curl http://localhost:8000/logs/today
   ```

### Styling Issues
1. Clear browser cache
2. Check CSS loads correctly
3. Verify file paths are correct
4. Try different browser

## Development

### Local Testing
```bash
# Start API
python -m uvicorn api.app:app --port 8000

# Open interfaces
open web/web_interface.html
open web/logs_dashboard.html

# Send test messages
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "user_id": "test_user"}'
```

### Browser DevTools
1. Open DevTools (F12)
2. Check Console for errors
3. Check Network tab for API calls
4. Monitor Application storage

## Production Deployment

### Before Going Live
1. [ ] Test all API endpoints
2. [ ] Verify CORS settings
3. [ ] Change API URL to production
4. [ ] Test on multiple browsers
5. [ ] Test on mobile devices
6. [ ] Set up HTTPS
7. [ ] Configure web server
8. [ ] Set up monitoring
9. [ ] Create backup

### Nginx Configuration
```nginx
server {
    listen 443 ssl;
    server_name chat.cvsu.edu.ph;
    
    ssl_certificate /etc/letsencrypt/live/chat.cvsu.edu.ph/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/chat.cvsu.edu.ph/privkey.pem;
    
    root /var/www/html/web;
    index web_interface.html;
    
    location / {
        try_files $uri $uri/ =404;
    }
    
    location /api {
        proxy_pass http://api-server:8000;
    }
}
```

## Performance

### Load Times
- web_interface.html: <1s
- logs_dashboard.html: <2s (includes data fetch)

### Network Usage
- Initial load: ~100KB
- Per chat: ~2KB
- Per dashboard refresh: ~5KB

### Browser Support
- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- IE11: Not supported

## Security Notes

- No API keys exposed in HTML
- CORS configured on API side
- Input validation by API
- SSL/TLS recommended for production
- Consider rate limiting on API
- Monitor for unusual access patterns

## Analytics Integration

### Google Analytics
Add to HTML head:
```html
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_ID');
</script>
```

### Custom Analytics
Track events:
```javascript
trackEvent('chat_sent', {'intent': intent, 'confidence': confidence});
trackEvent('page_view', {'page': 'dashboard'});
```

## Related Documentation

- **Integration**: `docs/INTEGRATION_GUIDE.md`
- **API**: `docs/API_README.md`
- **Deployment**: `docs/DOCKER_DEPLOYMENT.md`
