# Alibaba Cloud ECS Deployment Guide: CivicPulse AI / CleanCity Copilot

This guide provides end-to-end instructions for deploying the **CivicPulse AI & CleanCity Copilot** container stack on **Alibaba Cloud ECS (Elastic Compute Service)** or any Linux VPS.

---

## 1. Alibaba Cloud ECS Instance Specifications

- **OS Recommendation**: `Alibaba Cloud Linux 3` or `Ubuntu 22.04 LTS` / `24.04 LTS` (64-bit)
- **Minimum Specs**: 2 vCPUs, 2 GB RAM (e.g. `ecs.e-c1m1.large` or `ecs.t6-c1m2.large` or higher)
- **Disk**: 40 GB ESSD

---

## 2. Configure Security Group Rules (Firewall)

In the [Alibaba Cloud ECS Console](https://ecs.console.aliyun.com/):
1. Navigate to **Network & Security** > **Security Groups**.
2. Click **Add Rules** under your ECS instance's security group.
3. Add the following **Inbound** rules:

| Protocol | Port Range | Source | Purpose |
| :--- | :--- | :--- | :--- |
| **TCP** | `22` | `0.0.0.0/0` | SSH Remote Access |
| **TCP** | `80` | `0.0.0.0/0` | Web Portal & API Gateway (HTTP) |
| **TCP** | `443` | `0.0.0.0/0` | Secure Portal Gateway (HTTPS) |
| **TCP** | `8000` | `0.0.0.0/0` | Direct FastAPI Backend & OpenAPI Docs |
| **TCP** | `8501` | `0.0.0.0/0` | Direct Streamlit Citizen & Admin UI |

---

## 3. Transfer Files to Your ECS Server

### Option A: Transfer Pre-Packaged Archive via SCP (Fastest - 3 seconds)
From your local Windows terminal (PowerShell or Git Bash) in this project folder:
```powershell
# 1. Generate package (already pre-built)
python package_for_deploy.py

# 2. Upload tarball to your Alibaba Cloud ECS
scp cleancity_deploy.tar.gz root@<YOUR_ECS_PUBLIC_IP>:/root/
```

Then SSH into your ECS server:
```bash
ssh root@<YOUR_ECS_PUBLIC_IP>

# Extract the archive
mkdir -p /root/cleancity && tar -xzf /root/cleancity_deploy.tar.gz -C /root/cleancity
cd /root/cleancity
```

### Option B: Clone via Git
If you push this repository to GitHub or Alibaba Cloud Codeup:
```bash
ssh root@<YOUR_ECS_PUBLIC_IP>
git clone <YOUR_GIT_REPO_URL> cleancity
cd cleancity
```

---

## 4. Run One-Command Automated Deployment

Inside `/root/cleancity`, run:
```bash
chmod +x deploy.sh
./deploy.sh
```

### What `deploy.sh` does automatically:
1. Detects OS and installs **Docker Engine** & **Docker Compose** plugin if missing.
2. Starts and enables the Docker system service.
3. Automatically opens firewall ports (80, 443, 8000, 8501, 22) in UFW / Firewalld.
4. Mounts persistent storage volumes for civic photos (`app_media`) and database (`app_db`).
5. Copies and verifies seeded database records (`cleancity.db`).
6. Builds Docker images and boots `nginx`, `backend`, and `frontend` containers.
7. Performs automated health check against `http://localhost:8000/api/health`.
8. Queries public Elastic IP and prints live URLs.

---

## 5. Live Verification Endpoints

Once `deploy.sh` finishes, you can access:

| Service | URL | Description |
| :--- | :--- | :--- |
| **CivicPulse Municipal Portal** | `http://<YOUR_ECS_IP>/` | Citizen reporting, heatmap, verification |
| **Swagger OpenAPI Documentation** | `http://<YOUR_ECS_IP>:8000/docs` | 27 interactive REST endpoints |
| **Streamlit Citizen & Admin UI** | `http://<YOUR_ECS_IP>:8501/` | Live analytics, dispatch triage, ticketing |
| **Backend Health Check** | `http://<YOUR_ECS_IP>:8000/api/health` | Container health probe |

---

## 6. (Optional) Custom Domain & Free Let's Encrypt SSL

If you have a domain name (e.g. `civic.yourdomain.com`):
1. Create an **A Record** pointing `civic.yourdomain.com` to your ECS Public IP.
2. Run:
```bash
sudo ./deploy/enable_ssl.sh civic.yourdomain.com your-email@domain.com
```
Your portal will now automatically redirect to `https://civic.yourdomain.com/` with an A+ SSL security rating.

---

## 7. Helpful Commands

```bash
# View live logs of all services
docker compose logs -f

# View logs for backend only
docker compose logs -f backend

# Restart all services
docker compose restart

# Stop all services
docker compose down

# Check running status
docker compose ps
```
