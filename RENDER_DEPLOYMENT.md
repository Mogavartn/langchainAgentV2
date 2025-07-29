# 🚀 Render Deployment Guide - JAK Company RAG API v2.4

## Overview
This guide will help you deploy the JAK Company RAG API Performance-Optimized v2.4 on Render.com. The application is now fully configured for seamless Render deployment.

## 📋 Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub Repository**: Your code should be in a GitHub repository
3. **OpenAI API Key**: Required for the AI functionality

## 🛠️ Deployment Steps

### Step 1: Connect Your Repository

1. Log in to your Render dashboard
2. Click **"New +"** → **"Web Service"**
3. Connect your GitHub repository containing this code
4. Select the repository and branch (usually `main` or `master`)

### Step 2: Configure Service Settings

Render will automatically detect the `render.yaml` file, but you can also configure manually:

**Basic Settings:**
- **Name**: `jak-company-rag-api` (or your preferred name)
- **Region**: `Oregon` (recommended for better performance)
- **Branch**: `main` (or your default branch)
- **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
- **Start Command**: `python process.py`

**Advanced Settings:**
- **Plan**: Start with `Starter` ($7/month) or `Hobby` (free with limitations)
- **Python Version**: `3.11.7` (specified in `runtime.txt`)
- **Health Check Path**: `/health`

### Step 3: Set Environment Variables

**Required Environment Variables:**
```bash
OPENAI_API_KEY=your_openai_api_key_here
```

**Optional Performance Variables (already set in render.yaml):**
```bash
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
DISABLE_ACCESS_LOG=true
MAX_MEMORY_SESSIONS=1000
SESSION_TTL_SECONDS=3600
CACHE_TTL_SECONDS=1800
```

### Step 4: Deploy

1. Click **"Create Web Service"**
2. Render will start building and deploying your application
3. The build process typically takes 2-5 minutes
4. Once deployed, you'll get a URL like: `https://your-service-name.onrender.com`

## 🔍 Verification

After deployment, test these endpoints:

1. **Health Check**: `GET https://your-app.onrender.com/health`
2. **Performance Metrics**: `GET https://your-app.onrender.com/performance_metrics`
3. **Memory Status**: `GET https://your-app.onrender.com/memory_status`
4. **Main API**: `POST https://your-app.onrender.com/optimize_rag`

### Sample API Test
```bash
curl -X POST "https://your-app.onrender.com/optimize_rag" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "C'\''est quoi un ambassadeur ?",
    "session_id": "test_session"
  }'
```

## 🎯 Performance Optimizations

The application includes several optimizations for Render deployment:

- **Memory Management**: TTL-based caching with automatic cleanup
- **Async Operations**: Full async/await implementation for better concurrency
- **Keyword Optimization**: O(1) frozenset-based keyword matching
- **Response Caching**: 30-minute TTL for frequently asked questions
- **Health Monitoring**: Built-in health checks and performance metrics

## 🔧 Configuration Files

### `render.yaml`
Complete service configuration including:
- Build and start commands
- Environment variables
- Health check configuration
- Resource allocation

### `runtime.txt`
Specifies Python version: `python-3.11.7`

### `requirements.txt`
All dependencies with compatible versions for Render

### `Procfile`
Alternative deployment configuration (backup)

## 🚨 Troubleshooting

### Common Issues and Solutions

**1. Build Fails with Dependency Errors**
```bash
# Solution: Check requirements.txt compatibility
pip install -r requirements.txt  # Test locally first
```

**2. Application Won't Start**
- Check the logs in Render dashboard
- Verify `OPENAI_API_KEY` is set correctly
- Ensure `PORT` environment variable is available (Render sets this automatically)

**3. Health Check Fails**
- Verify `/health` endpoint is accessible
- Check if the application is binding to `0.0.0.0:$PORT`

**4. Performance Issues**
- Monitor `/performance_metrics` endpoint
- Check memory usage via `/memory_status`
- Consider upgrading to a higher Render plan

**5. OpenAI API Errors**
- Verify your OpenAI API key is valid and has credits
- Check OpenAI usage limits and quotas

### Viewing Logs
```bash
# In Render dashboard:
1. Go to your service
2. Click on "Logs" tab
3. Monitor real-time logs for errors
```

## 📊 Monitoring

### Built-in Endpoints for Monitoring

1. **Health Check**: `/health`
   - Service status and performance metrics
   - Memory utilization information
   - Feature availability status

2. **Performance Metrics**: `/performance_metrics`
   - Optimization status
   - Performance improvements data
   - Feature status indicators

3. **Memory Status**: `/memory_status`
   - Active sessions count
   - Memory utilization percentage
   - TTL and caching information

### Performance Targets
- Response Time: < 100ms for regular requests
- Cache Hits: < 10ms processing time
- Memory Utilization: < 90%
- Error Rate: < 1%

## 🔄 Updates and Maintenance

### Updating the Application
1. Push changes to your GitHub repository
2. Render will automatically redeploy (if auto-deploy is enabled)
3. Monitor the deployment in the Render dashboard

### Scaling
- **Horizontal Scaling**: Upgrade to higher plans for more resources
- **Vertical Scaling**: Use Render's auto-scaling features
- **Load Balancing**: Render handles this automatically

## 🔐 Security Considerations

1. **Environment Variables**: Never commit API keys to your repository
2. **HTTPS**: Render provides SSL certificates automatically
3. **CORS**: Configured to allow necessary origins
4. **Rate Limiting**: Consider implementing rate limiting for production use

## 💰 Cost Optimization

### Render Plans
- **Hobby Plan**: Free (with limitations - sleeps after 15 minutes of inactivity)
- **Starter Plan**: $7/month (recommended for development)
- **Standard Plan**: $25/month (recommended for production)
- **Pro Plan**: $85/month (high-traffic applications)

### Cost-Saving Tips
1. Use the Hobby plan for testing and development
2. Monitor usage to choose the right plan
3. Implement efficient caching to reduce compute time
4. Use the built-in performance optimizations

## 📞 Support

### Getting Help
1. **Render Documentation**: [render.com/docs](https://render.com/docs)
2. **Render Community**: [community.render.com](https://community.render.com)
3. **Application Logs**: Use `/health` and `/performance_metrics` endpoints

### Performance Issues
If you experience performance issues:
1. Check `/performance_metrics` for bottlenecks
2. Monitor memory usage via `/memory_status`
3. Review application logs in Render dashboard
4. Consider upgrading your Render plan

---

## ✅ Deployment Checklist

- [ ] Repository connected to Render
- [ ] `OPENAI_API_KEY` environment variable set
- [ ] Service builds successfully
- [ ] Health check passes at `/health`
- [ ] API responds correctly to test requests
- [ ] Performance metrics are accessible
- [ ] Monitoring endpoints are working
- [ ] Application logs show no critical errors

**Your JAK Company RAG API v2.4 is now ready for production on Render! 🎉**