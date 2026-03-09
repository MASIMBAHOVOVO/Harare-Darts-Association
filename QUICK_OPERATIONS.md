# HDA Quick Operations Guide

## 1. Remove Duplicate Player Names

Run this script to remove duplicate player names from the database, keeping the player with the most associated game data:

```bash
cd "c:\Users\masim\Desktop\HDA - Copy\Harare Darts Assiciation"
python scripts/remove_duplicate_players.py
```

**What it does:**
- Identifies all players with duplicate names (case-insensitive)
- Keeps the player with the most data (game week stats, match details)
- Deletes duplicate players and transfers all their match/game data to the kept player
- Shows detailed before/after information

### Optional: Also Remove Duplicate Team Names

If you also have duplicate team names, run:
```bash
python scripts/remove_duplicate_teams.py
```

---

## 2. Player Edit/Delete Now Stays on Current Page

✅ **Already implemented!**

When users edit or delete a player, they will now stay on the same page/dashboard instead of being redirected to the teams view.

**Changes made:**
- Updated edit and delete player routes to accept a `referrer` URL parameter
- Modified the secretary_dashboard.html to send the current page URL when saving/deleting
- JavaScript now captures `window.location.href` when opening edit modal

---

## 3. Concurrency Improvements for 100+ Users

### Quick Setup (Development)
Just run the app normally - it now uses threaded mode:
```bash
python run.py
```
This handles ~50 concurrent users.

### Production Setup (100+ users)
For 100+ users, use Gunicorn WSGI server:

```bash
# Install (if not already in requirements.txt)
pip install gunicorn

# Run with optimal settings for ~4 core machine
gunicorn --workers 9 --worker-class sync --threads 2 --timeout 60 --bind 0.0.0.0:5000 run:app
```

**Automatic scaling formula:**
- Workers needed = `(2 × CPU_cores) + 1`
- For 4 cores: 9 workers
- For 8 cores: 17 workers
- For 2 cores: 5 workers

**Database:**
- Connection pool automatically optimized (20 base + 40 overflow = 60 max)
- Connections recycle every 4.5 minutes to prevent staleness
- Pre-ping ensures dead connections are detected immediately

---

## Configuration Summary

### config.py (Database Pooling)
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 20,          # Base connections
    'max_overflow': 40,       # Overflow connections
    'pool_recycle': 280,      # Recycle interval
    'pool_pre_ping': True,    # Test before use
    'pool_timeout': 30,       # Wait timeout
}
```

### run.py (Threading)
```python
app.run(
    debug=True,
    port=5000,
    threaded=True,  # ✅ NEW: Enable threading
)
```

---

## Next Steps (Optional Enhancements)

1. **Add Nginx Reverse Proxy** - Distribute load, handle SSL certificates
2. **Enable Caching** - Use Redis for session storage and query caching
3. **Database Optimization** - Index frequently queried columns
4. **Monitoring** - Set up logging and performance monitoring (New Relic, Datadog)
5. **Load Testing** - Test with Apache Bench or Locust to verify capacity

See `DEPLOYMENT.md` for detailed production deployment instructions.

---

## Files Modified

- `app/config.py` - Enhanced database connection pooling
- `app/admin.py` - Player edit/delete routes now preserve referrer
- `templates/secretary_dashboard.html` - Added referrer tracking
- `run.py` - Enabled threading mode
- `requirements.txt` - Added gunicorn and waitress

## Files Created

- `scripts/remove_duplicate_players.py` - Duplicate player removal script
- `scripts/remove_duplicate_teams.py` - Duplicate team removal script (if needed)
- `DEPLOYMENT.md` - Comprehensive production deployment guide
- `QUICK_OPERATIONS.md` - This file
