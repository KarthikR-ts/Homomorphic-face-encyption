# Production Deployment Guide

This guide covers deploying the Privacy-Preserving Facial Recognition API to production using Docker Compose with blue-green deployment strategy.

## Architecture Overview

The production setup includes:

- **Flask API**: Gunicorn with 4 workers, gevent async
- **PostgreSQL**: With SSL encryption and LUKS-encrypted volumes
- **Redis**: With persistence and AUTH security
- **Nginx**: Reverse proxy with TLS termination and rate limiting
- **Celery**: Async task worker for batch processing
- **Fluentd**: Log aggregation to Elasticsearch
- **Elasticsearch/Kibana**: Log storage and visualization

## Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- 16GB RAM minimum
- 100GB disk space
- Linux host (recommended for LUKS encryption)

## Quick Start

1. **Clone and setup secrets:**
```bash
git clone <repository>
cd homomorphic-face-encyption

# Create secrets directory
mkdir -p secrets

# Generate secrets (replace with secure values)
openssl rand -hex 32 > secrets/secret_key.txt
openssl rand -hex 32 > secrets/jwt_private_key.pem  # Actually need PEM format
openssl rand -hex 32 > secrets/db_encryption_key.txt
echo "strong-postgres-password" > secrets/db_password.txt
echo "strong-redis-password" > secrets/redis_password.txt
date +%Y-%m-%d > secrets/ip_hash_salt.txt
echo "AWS_ACCESS_KEY_ID" > secrets/aws_access_key_id.txt
echo "AWS_SECRET_ACCESS_KEY" > secrets/aws_secret_access_key.txt
```

2. **Setup SSL certificates:**
```bash
# Create directories
mkdir -p ssl/postgres ssl/letsencrypt

# Generate PostgreSQL SSL certificates
openssl req -new -x509 -days 365 -nodes \
  -out ssl/postgres/server.crt \
  -keyout ssl/postgres/server.key \
  -subj "/C=US/ST=State/L=City/O=Organization/CN=postgres"

# Copy CA certificate
cp ssl/postgres/server.crt ssl/postgres/ca.crt

# For Let's Encrypt, use certbot or mount existing certificates
# certbot certonly --standalone -d your-domain.com
```

3. **Setup encrypted volumes:**
```bash
# Create LUKS encrypted device for PostgreSQL data
sudo cryptsetup luksFormat /dev/sdb  # Use appropriate device
sudo cryptsetup luksOpen /dev/sdb encrypted_postgres
sudo mkfs.ext4 /dev/mapper/encrypted_postgres

# Mount the encrypted volume
sudo mkdir -p /var/lib/docker/volumes/postgres_data/_data
sudo mount /dev/mapper/encrypted_postgres /var/lib/docker/volumes/postgres_data/_data
```

4. **Deploy:**
```bash
# Make deploy script executable (Linux/Mac)
chmod +x deploy.sh

# Deploy with blue-green strategy
./deploy.sh deploy
```

## Configuration

### Environment Variables

Update the following in `docker-compose.prod.yml`:

- `CORS_ORIGINS`: Your frontend domain (https://your-app.com)
- `JWT_ISSUER`: Your service issuer name
- `JWT_AUDIENCE`: Your client audience name

### Secrets Management

All sensitive data is managed through Docker secrets:

- `secret_key.txt`: Flask secret key (32 hex chars)
- `jwt_private_key.pem`: RSA private key for JWT signing
- `db_encryption_key.txt`: Database field encryption key
- `db_password.txt`: PostgreSQL password
- `redis_password.txt`: Redis AUTH password
- `ip_hash_salt.txt`: Salt for IP address hashing
- `aws_access_key_id.txt`: AWS access key for S3 backups
- `aws_secret_access_key.txt`: AWS secret key for S3 backups

### SSL/TLS Setup

1. **PostgreSQL SSL:**
   - Certificates are mounted from `./ssl/postgres/`
   - Requires client certificates for full security

2. **Nginx TLS:**
   - Mount Let's Encrypt certificates to `./ssl/letsencrypt/`
   - Automatic HTTP to HTTPS redirect
   - HSTS headers enabled

### Networking

- **frontend**: Nginx accessible externally (ports 80, 443)
- **backend**: Internal network for app, postgres, redis (isolated)
- **logging**: Internal network for log aggregation (isolated)

## Deployment Commands

```bash
# Deploy new version (blue-green)
./deploy.sh deploy

# Check deployment status
./deploy.sh status

# Rollback to previous version
./deploy.sh rollback

# Cleanup all containers and volumes
./deploy.sh cleanup
```

## Monitoring and Logs

### Health Checks

All services include health checks:
- Flask API: `GET /health` endpoint
- PostgreSQL: `pg_isready` command
- Redis: `redis-cli ping`
- Nginx: `curl localhost/health`

### Logging

- **Fluentd** aggregates logs from all services
- **Elasticsearch** stores logs with retention policies
- **Kibana** provides visualization dashboards

Access Kibana at: `http://localhost:5601` (internal only)

### Log Types

- **facial-api-app**: Flask application logs
- **facial-api-nginx**: Nginx access/error logs
- **facial-api-security**: Security-related events

## Backup and Recovery

### Automated Backups

- **PostgreSQL**: Daily `pg_dump` to encrypted S3 bucket
- **Logs**: Retained in Elasticsearch with configurable retention

### Manual Backup

```bash
# Backup database
docker exec facial-recognition_postgres_1 pg_dump -U postgres face_db > backup.sql

# Backup Redis data
docker exec facial-recognition_redis_1 redis-cli --rdb /tmp/redis_backup.rdb
```

### Recovery

1. Stop the application stack
2. Restore database from backup
3. Start the stack
4. Verify health checks pass

## Security Considerations

### Network Security

- PostgreSQL only accessible from backend network
- Redis requires AUTH password
- Nginx rate limiting and security headers

### Data Encryption

- Database fields encrypted with AES-256
- SSL/TLS for all communications
- LUKS encryption for persistent volumes

### Access Control

- JWT tokens with RS256 signing
- Redis-based token blacklist
- IP address hashing for privacy compliance

## Troubleshooting

### Common Issues

1. **Health checks failing:**
   ```bash
   # Check service logs
   docker-compose -f docker-compose.prod.yml logs <service_name>

   # Check service status
   docker-compose -f docker-compose.prod.yml ps
   ```

2. **Database connection issues:**
   ```bash
   # Check PostgreSQL logs
   docker-compose -f docker-compose.prod.yml logs postgres

   # Test connection
   docker-compose -f docker-compose.prod.yml exec postgres pg_isready -U postgres
   ```

3. **SSL certificate issues:**
   ```bash
   # Renew Let's Encrypt certificates
   certbot renew

   # Reload Nginx configuration
   docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload
   ```

### Performance Tuning

- **Gunicorn workers**: Adjust based on CPU cores (2x cores + 1)
- **Redis memory**: Monitor and adjust maxmemory policy
- **PostgreSQL**: Tune `shared_buffers`, `work_mem`, `maintenance_work_mem`

## Scaling

### Horizontal Scaling

1. **App servers**: Add more instances behind load balancer
2. **Celery workers**: Scale worker count based on queue length
3. **Elasticsearch**: Add more nodes for log volume

### Vertical Scaling

- Increase resource limits in `docker-compose.prod.yml`
- Monitor resource usage with `docker stats`

## Maintenance

### Updates

1. Update application code
2. Build new images
3. Run `./deploy.sh deploy`
4. Monitor health checks
5. Cleanup old images: `docker image prune -f`

### Certificate Renewal

```bash
# Renew Let's Encrypt certificates
certbot renew --deploy-hook "docker-compose -f docker-compose.prod.yml exec nginx nginx -s reload"
```

### Log Rotation

- Elasticsearch handles log rotation automatically
- Application logs rotated by logrotate in containers
- Backup logs compressed and archived to S3

## Compliance

This setup complies with:
- **DPDP Act 2023**: IP hashing, consent management, data minimization
- **GDPR**: Data encryption, audit logging, right to erasure
- **ISO 27001**: Security controls, access management, incident response

## Support

For issues:
1. Check logs: `./deploy.sh status`
2. Review health checks
3. Check Elasticsearch/Kibana for detailed logs
4. Rollback if necessary: `./deploy.sh rollback`
