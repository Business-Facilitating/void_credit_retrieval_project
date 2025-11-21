# GSR Automation - Deployment Options Comparison

**Author:** Gabriel Jerdhy Lapuz
**Project:** gsr_automation
**Last Updated:** 2025-11-20

---

## 📊 Quick Comparison

| Feature              | Option 1: Persistent VM | Option 2: Ephemeral VM ⭐ |
| -------------------- | ----------------------- | ------------------------- |
| **Cost/Month**       | ~$25-30                 | ~$0.50-1                  |
| **Savings**          | Baseline                | **95% cheaper**           |
| **VM Uptime**        | 24/7 (720 hours)        | ~4 hours/month            |
| **Setup Complexity** | Medium                  | Low (automated script)    |
| **Maintenance**      | Manual updates          | Auto-fresh environment    |
| **Best For**         | Frequent runs           | Infrequent runs           |
| **Scalability**      | Limited                 | Excellent                 |
| **Environment**      | Can drift over time     | Always fresh              |
| **Browser Mode**     | Headed (GUI-enabled)    | Headed (GUI-enabled)      |

> **Note:** Both deployment options now use **headed mode** (visible browser with GUI) for better reliability with UPS automation. The browser runs on a virtual X11 display (Xvfb) with XFCE window manager.

---

## 💰 Detailed Cost Breakdown

### Option 1: Persistent VM with Cron

**Monthly Costs:**

- Compute Engine (e2-medium, 24/7): $24.27
- Storage (20GB boot disk): $0.80
- Network egress: ~$0.50
- **Total: ~$25-30/month**

**Annual Cost:** ~$300-360/year

### Option 2: Ephemeral VM with Cloud Scheduler

**Monthly Costs (15 runs):**

- Compute Engine (15 runs × 15 min): $0.25
- Cloud Function (15 invocations): $0.01
- Cloud Scheduler (1 job): $0.10
- Cloud Storage (5GB): $0.10
- Secret Manager (15 accesses): $0.01
- Network egress: ~$0.03
- **Total: ~$0.50-1/month**

**Annual Cost:** ~$6-12/year

**Savings:** $294-348/year (95% reduction)

---

## 🎯 Use Case Recommendations

### Choose Option 1 (Persistent VM) If:

✅ You need to run the pipeline **multiple times per day**  
✅ You have **complex dependencies** that take long to install  
✅ You need **real-time monitoring** and manual intervention  
✅ You want to **SSH into the VM** for debugging  
✅ You have **other workloads** to run on the same VM

### Choose Option 2 (Ephemeral VM) If: ⭐

✅ You run the pipeline **infrequently** (daily, every other day, weekly)  
✅ You want **minimal maintenance** and auto-updates  
✅ You want to **minimize costs** significantly  
✅ You prefer **serverless/managed** infrastructure  
✅ You want **isolated, reproducible** runs  
✅ You want **automatic cleanup** and no VM management

**For your use case (every other day):** **Option 2 is strongly recommended!**

---

## 🏗️ Architecture Comparison

### Option 1: Persistent VM Architecture

```
┌─────────────────────────────────────┐
│      Persistent Compute Engine VM    │
│         (Running 24/7)               │
│                                      │
│  ┌────────────────────────────────┐ │
│  │         Cron Daemon            │ │
│  │   (Checks schedule every min)  │ │
│  └────────────┬───────────────────┘ │
│               │                      │
│               ▼                      │
│  ┌────────────────────────────────┐ │
│  │      Make Pipeline Full        │ │
│  │  (Runs every other day)        │ │
│  └────────────┬───────────────────┘ │
│               │                      │
│               ▼                      │
│  ┌────────────────────────────────┐ │
│  │    3-Step Pipeline             │ │
│  │  • ClickHouse Extract          │ │
│  │  • Filter Label-Only           │ │
│  │  • UPS Web Login               │ │
│  └────────────┬───────────────────┘ │
│               │                      │
│               ▼                      │
│  ┌────────────────────────────────┐ │
│  │    Local Storage               │ │
│  │  data/output/, logs/           │ │
│  └────────────────────────────────┘ │
└─────────────────────────────────────┘

Cost: VM runs 24/7 even when idle
```

### Option 2: Ephemeral VM Architecture

```
┌─────────────────────────────────────┐
│       Cloud Scheduler               │
│   (Every other day at 2:00 AM)      │
└────────────┬────────────────────────┘
             │ HTTP Trigger
             ▼
┌─────────────────────────────────────┐
│       Cloud Function                │
│   (Runs for ~1 second)              │
│   • Creates VM                      │
│   • Returns immediately             │
└────────────┬────────────────────────┘
             │ API Call
             ▼
┌─────────────────────────────────────┐
│    Ephemeral Compute Engine VM      │
│      (Created on-demand)            │
│                                     │
│  Startup Script:                    │
│  1. Install dependencies            │
│  2. Clone repo                      │
│  3. Fetch .env from Secret Manager  │
│  4. Run pipeline                    │
│  5. Upload to Cloud Storage         │
│  6. VM auto-terminates              │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│      Cloud Storage Bucket           │
│   (Persistent results storage)      │
│   • /runs/TIMESTAMP/                │
│   • /logs/TIMESTAMP/                │
└─────────────────────────────────────┘

Cost: Only pay for ~15 minutes of compute
```

---

## 🔧 Setup Comparison

### Option 1 Setup Steps

1. Create GCP VM manually
2. SSH into VM
3. Install system dependencies
4. Install Poetry
5. Clone repository
6. Setup .env file
7. Install project dependencies
8. Install Playwright
9. Test pipeline
10. Configure crontab
11. Monitor and maintain

**Time:** ~30-60 minutes  
**Complexity:** Medium  
**Ongoing:** Manual updates and maintenance

### Option 2 Setup Steps

1. Update `deploy_ephemeral.sh` configuration
2. Run `./deploy_ephemeral.sh`
3. Done!

**Time:** ~5-10 minutes (mostly automated)  
**Complexity:** Low  
**Ongoing:** Zero maintenance (auto-fresh environment)

---

## 📈 Scalability Comparison

### Option 1: Scaling Challenges

- Need to manually create/manage multiple VMs
- Cron jobs can conflict if runs overlap
- Resource contention on single VM
- Manual load balancing required

### Option 2: Scaling Advantages

- Easily run multiple accounts in parallel
- Each run gets isolated VM
- No resource contention
- Simple: Just add more scheduler jobs
- Auto-scales with demand

**Example: Running 5 different accounts**

| Approach | Cost                         | Complexity |
| -------- | ---------------------------- | ---------- |
| Option 1 | 5 VMs × $25 = **$125/month** | High       |
| Option 2 | 5 jobs × $1 = **$5/month**   | Low        |

---

## 🔒 Security Comparison

### Option 1: Security Considerations

- ⚠️ .env file stored on VM disk
- ⚠️ VM accessible via SSH (attack surface)
- ⚠️ Need to manage OS updates
- ⚠️ Credentials can be exposed if VM compromised
- ✅ Can use firewall rules
- ✅ Can use private networking

### Option 2: Security Advantages

- ✅ Credentials in Secret Manager (encrypted)
- ✅ No SSH access needed
- ✅ Fresh OS every run (auto-patched)
- ✅ VM exists only during execution
- ✅ IAM-based access control
- ✅ Audit logs for all operations
- ✅ No persistent attack surface

---

## 🐛 Troubleshooting Comparison

### Option 1: Debugging

**Pros:**

- Can SSH into VM
- Can run commands interactively
- Can inspect files directly

**Cons:**

- Need to maintain SSH access
- Environment can drift
- Harder to reproduce issues

### Option 2: Debugging

**Pros:**

- Serial console logs available
- Cloud Storage has all results
- Reproducible (same environment every time)
- Cloud Function logs show all triggers

**Cons:**

- Can't SSH into ephemeral VM (but can view serial output)
- Need to trigger new run to test changes

---

## 📊 Performance Comparison

| Metric               | Option 1           | Option 2               |
| -------------------- | ------------------ | ---------------------- |
| **Pipeline Runtime** | 5-15 min           | 5-15 min (same)        |
| **Startup Time**     | Instant (VM ready) | +2-3 min (VM creation) |
| **Total Time**       | 5-15 min           | 7-18 min               |
| **Consistency**      | Can vary (drift)   | Always consistent      |

**Note:** Option 2 adds 2-3 minutes for VM creation, but this is negligible for infrequent runs.

---

## ✅ Decision Matrix

### Choose Option 1 If:

- [ ] Running **more than 3 times per day**
- [ ] Need **interactive debugging** frequently
- [ ] Have **other workloads** on same VM
- [ ] Startup time is **critical** (need instant execution)
- [ ] Prefer **traditional** infrastructure

### Choose Option 2 If: ⭐

- [x] Running **3 times per day or less**
- [x] Want **95% cost savings**
- [x] Prefer **zero maintenance**
- [x] Want **reproducible** environments
- [x] Value **security** and isolation
- [x] Want **serverless** architecture

**For your use case (every other day): Option 2 is the clear winner!**

---

## 🎯 Migration Path

### Already Using Option 1? Migrate to Option 2:

1. **Backup your .env file**

   ```bash
   scp your-vm:.env ./env-backup
   ```

2. **Run Option 2 deployment**

   ```bash
   ./deploy_ephemeral.sh
   ```

3. **Test Option 2**

   ```bash
   gcloud scheduler jobs run gsr-automation-scheduler --location=us-central1
   ```

4. **Verify results**

   ```bash
   gsutil ls gs://gsr-automation-results/runs/
   ```

5. **Delete persistent VM**

   ```bash
   gcloud compute instances delete your-vm-name --zone=your-zone
   ```

6. **Save $25-30/month!** 🎉

---

## 📚 Documentation Links

### Option 1 Documentation

- [Deployment Quick Reference](docs/DEPLOYMENT_QUICK_REFERENCE.md)
- [Makefile & Cron Guide](docs/MAKEFILE_CRON_DEPLOYMENT.md)
- [Deployment Summary](docs/DEPLOYMENT_SUMMARY.md)

### Option 2 Documentation

- [Quick Start Guide](OPTION2_QUICK_START.md) ⭐ **Start here!**
- [Detailed Guide](docs/GCP_EPHEMERAL_VM_DEPLOYMENT.md)
- [Cloud Function Code](cloud_function/main.py)
- [Deployment Script](deploy_ephemeral.sh)

---

## 🎉 Recommendation

**For your use case (running every other day):**

# Choose Option 2: Ephemeral VM with Cloud Scheduler ⭐

**Why:**

- ✅ **95% cost savings** ($25-30/month → $0.50-1/month)
- ✅ **Zero maintenance** (auto-fresh environment)
- ✅ **Better security** (Secret Manager, no persistent VM)
- ✅ **Easier setup** (one script does everything)
- ✅ **More scalable** (easy to add more accounts)
- ✅ **Reproducible** (same environment every time)

**Get started:** [OPTION2_QUICK_START.md](OPTION2_QUICK_START.md)

---

**Questions?** Check the documentation or run `./deploy_ephemeral.sh` to get started!
