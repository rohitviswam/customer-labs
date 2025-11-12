# Next Steps - Your 72-Hour Roadmap

This document provides a day-by-day plan to complete the attribution dashboard project.

## Current Status ✅

You now have:
- ✅ Complete project structure
- ✅ All dbt models (staging, intermediate, marts)
- ✅ Streaming pipeline script
- ✅ Dashboard application
- ✅ Comprehensive documentation
- ✅ Git repository initialized with 2 commits

## What You Need to Do

### Day 1 (Hours 0-24) - Today

#### 1. Set Up Your Environment (2-3 hours)

```bash
# Get BigQuery access
# Option A: Use your own GCP account
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Option B: Create free trial account
# Visit: https://cloud.google.com/free

# Install dependencies
pip install dbt-bigquery google-cloud-bigquery streamlit plotly pandas
```

#### 2. Configure dbt (1 hour)

```bash
cd dbt_attribution

# Edit profiles.yml with YOUR details
nano ~/.dbt/profiles.yml

# Update:
# - project: YOUR_PROJECT_ID
# - dataset: attribution_dev (or your choice)
# - keyfile: path/to/credentials.json

# Test connection
dbt debug
```

#### 3. Run dbt Models (2 hours)

```bash
# First run (will take 5-10 minutes)
dbt run

# Run tests
dbt test

# Generate documentation
dbt docs generate
dbt docs serve
```

**Expected Output:**
- All models should succeed
- Most tests should pass (some may warn on empty public dataset)
- Documentation site opens in browser

#### 4. Update Worklog (15 mins)

Edit `worklog.md` with your actual times and experiences.

#### 5. Make Git Commits

```bash
git add -A
git commit -m "Configure dbt for my GCP project"
```

### Day 2 (Hours 24-48)

#### 1. Test Streaming Pipeline (2 hours)

```bash
cd streaming

# Stream sample events
python stream_events.py \
    --project YOUR_PROJECT_ID \
    --dataset attribution_dev \
    --num-users 5 \
    --events-per-user 5 \
    --test-dedup

# Verify in BigQuery console:
# Check events_streaming table
```

#### 2. Refresh dbt Models (30 mins)

```bash
cd ../dbt_attribution

# Rerun to pick up streamed events
dbt run --select +marts
```

#### 3. Launch Dashboard (1 hour)

```bash
cd ../dashboard

# Start dashboard
streamlit run app.py

# In sidebar, enter:
# - Your GCP Project ID
# - Dataset: attribution_dev
```

**Test all 4 dashboard sections:**
- [ ] Metrics display
- [ ] Time series charts load
- [ ] Channel breakdown shows
- [ ] Live events feed works

#### 4. Create Hand-Drawn Sketches (1 hour)

**Sketch 1: Architecture Diagram**
- Draw system components
- Show data flow arrows
- Label each component
- Take photo, save to `sketches/architecture_sketch.jpg`

**Sketch 2: Attribution Logic**
- Draw example user journey
- Show first-click vs last-click calculation
- Annotate decision points
- Take photo, save to `sketches/attribution_logic_sketch.jpg`

#### 5. Update Worklog (30 mins)

Add Day 2 entries to `worklog.md`.

#### 6. Make Git Commits

```bash
git add sketches/
git commit -m "Add hand-drawn architecture and logic sketches"

git add worklog.md
git commit -m "Update worklog with Day 2 progress"
```

### Day 3 (Hours 48-72)

#### 1. Testing & Validation (2 hours)

**Test Full Pipeline:**
```bash
# 1. Stream new events
python streaming/stream_events.py --project YOUR_PROJECT --num-users 3

# 2. Refresh dbt
dbt run --select +marts

# 3. Check dashboard updates
streamlit run dashboard/app.py
```

**Verify:**
- [ ] Events appear in dashboard within 30 seconds
- [ ] Attribution calculations are correct
- [ ] All metrics update properly

#### 2. Record Demo Video (2 hours)

**Option A: Screencast (Recommended)**

Use Loom, Quicktime, or OBS to record:

1. **Introduction (30s)**
   - Your name
   - Project overview

2. **Architecture Walkthrough (1 min)**
   - Show architecture diagram
   - Explain data flow
   - Mention key design decisions

3. **dbt Models (2 min)**
   - Show staging models
   - Explain intermediate layer
   - Walk through attribution logic in marts

4. **Streaming Demo (1.5 min)**
   - Run streaming script
   - Show events in BigQuery
   - Explain deduplication

5. **Dashboard Tour (2 min)**
   - Show all 4 sections
   - Highlight real-time updates
   - Explain attribution comparison

6. **Wrap-up (30s)**
   - Key accomplishments
   - Future enhancements

**Option B: Be Ready for Live Demo**

Practice 10-15 minute walkthrough covering same topics.

#### 3. Finalize Documentation (2 hours)

**Review and Update:**
- [ ] README.md - accurate and complete
- [ ] docs/assumptions.md - all edge cases covered
- [ ] docs/runbook.md - operational procedures clear
- [ ] worklog.md - 6-10 entries with insights
- [ ] SUBMISSION_CHECKLIST.md - all boxes checked

**Create 1-Page Summary** (docs/submission_summary.md):
```markdown
# Project Summary

## Dataset
bigquery-public-data.ga4_obfuscated_sample_ecommerce

## Key Decisions
- Lookback window: 14 days
- Session timeout: 30 minutes  
- Identity: user_pseudo_id
- Conversion events: purchase, begin_checkout

## Technical Stack
- BigQuery: Data warehouse
- dbt: Transformation (staging → intermediate → marts)
- Python: Streaming pipeline
- Streamlit: Dashboard

## Metrics
- X dbt models
- Y tests passing
- Z second latency
- $N estimated monthly cost

## Edge Cases Handled
1. Direct conversions (no prior touchpoints)
2. Multiple conversions per user
3. Duplicate event deduplication
4. Missing/null field handling

## Future Enhancements
- Multi-touch attribution models
- Campaign-level granularity
- Cross-device tracking
- ML-based attribution
```

#### 4. Final Git Commits

```bash
# Commit any changes
git add -A
git commit -m "Finalize documentation and testing"

# Create clean commit history
git log --oneline  # Review commits

# If needed, clean up with interactive rebase
# git rebase -i HEAD~5
```

#### 5. Prepare Submission (1 hour)

**Option A: GitHub**
```bash
# Create GitHub repo
# Visit: https://github.com/new

# Push your code
git remote add origin https://github.com/YOUR_USERNAME/attribution-dashboard.git
git branch -M main
git push -u origin main
```

**Option B: GitLab/Bitbucket**

Similar process - create repo and push.

**Option C: ZIP file**
```bash
cd ..
zip -r attribution-dashboard.zip "customer labs" -x "*.git*" "*/target/*" "*/dbt_packages/*"
```

#### 6. Submit! 🚀

Use the email template from `SUBMISSION_CHECKLIST.md`.

**Include:**
- Repository URL or ZIP file
- Dashboard link or demo video
- 1-page summary
- Highlight key features

### After Submission

#### Prepare for Interview

**Live Walkthrough (10-15 mins)**
- Practice explaining architecture
- Be ready to navigate code
- Prepare to discuss design decisions

**Live SQL Edit (15 mins)**

Practice these potential tasks:
1. Add new attribution model (linear attribution)
2. Add campaign-level granularity
3. Filter out test traffic
4. Add conversion funnel metrics
5. Optimize slow query

Example preparation:
```sql
-- Practice: Add linear attribution
-- Modify mart_first_click_attribution.sql to distribute credit evenly

WITH journeys AS (
  SELECT *,
    conversion_value / total_touchpoints as attributed_value
  FROM {{ ref('int_user_journeys') }}
)
SELECT
  channel,
  SUM(attributed_value) as total_attributed_value
FROM journeys
GROUP BY channel
```

## Tips & Best Practices

### Time Management
- Don't over-optimize - working is better than perfect
- If stuck > 30 mins, document assumption and move on
- Leave buffer time for unexpected issues

### Git Commits
- Commit every 1-2 hours
- Use descriptive messages
- Show incremental progress

### Worklog Entries
- Add entry after each major milestone
- Include challenges and solutions
- Note time spent and decisions made

### Documentation
- Write as you go, not at the end
- Include screenshots where helpful
- Test all setup instructions

### Demo Video
- Keep it concise (5-8 mins max)
- Show, don't just tell
- Highlight unique aspects

## Common Pitfalls to Avoid

1. ❌ Forgetting to commit regularly
   ✅ Commit every major change

2. ❌ Not testing on fresh environment
   ✅ Have someone else try your setup instructions

3. ❌ Incomplete worklog
   ✅ Write entries as you work, not retroactively

4. ❌ Missing hand-drawn sketches
   ✅ Actually draw and photograph them

5. ❌ Not handling edge cases
   ✅ Document assumptions and limitations

6. ❌ Dashboard doesn't work without data
   ✅ Add graceful error handling

7. ❌ Submitting with credentials in repo
   ✅ Use .gitignore and check before pushing

## Support Resources

- **dbt Docs**: https://docs.getdbt.com
- **BigQuery Docs**: https://cloud.google.com/bigquery/docs
- **Streamlit Docs**: https://docs.streamlit.io
- **GA4 Schema**: Search "GA4 BigQuery export schema"

## Questions?

If you have clarifying questions (up to 5 in first 24 hours):
- Review `docs/assumptions.md` first
- Check if edge case is already documented
- Email: jobs@customerlabs.co

## You've Got This! 💪

You have all the code and documentation you need. Now just:
1. Configure with your credentials
2. Test everything works
3. Create your sketches
4. Record demo
5. Submit

The hard part (designing and coding) is done. You're set up for success!

---

**Good luck!** 🎉
