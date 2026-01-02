#!/bin/bash
# GIBD-News Deployment Script
set -e

cd /opt/wizardsofts-megabuild/apps/gibd-news

# Create .env if not exists
if [ ! -f .env ]; then
    cat > .env << 'EOF'
ACTIVE_PROFILE=docker
GIBD_DEEPSEEK_API_KEY=
GIBD_EMAIL_SENDER=
GIBD_EMAIL_PASSWORD=
EOF
fi

# Build Docker image
echo "Building Docker images..."
docker-compose build --no-cache

# Start the metrics exporter service (runs continuously)
echo "Starting metrics exporter service..."
docker-compose up -d metrics
echo "Metrics exporter running at http://localhost:9090/metrics"

# Set up crontab for scheduled scraping
echo "Setting up crontab..."
CRON_FILE=/tmp/gibd-news-cron

# Create cron entries
cat > $CRON_FILE << 'CRON'
# GIBD-News Scrapers - Auto-generated
# News URL scrapers - every 2 hours
0 */2 * * * cd /opt/wizardsofts-megabuild/apps/gibd-news && docker-compose run --rm fetch-financialexpress >> /opt/wizardsofts-megabuild/apps/gibd-news/logs/cron_fe.log 2>&1
15 */2 * * * cd /opt/wizardsofts-megabuild/apps/gibd-news && docker-compose run --rm fetch-tbsnews >> /opt/wizardsofts-megabuild/apps/gibd-news/logs/cron_tbs.log 2>&1
30 */2 * * * cd /opt/wizardsofts-megabuild/apps/gibd-news && docker-compose run --rm fetch-dailystar >> /opt/wizardsofts-megabuild/apps/gibd-news/logs/cron_ds.log 2>&1

# News details fetcher - 45 minutes after URL scrapers
45 */2 * * * cd /opt/wizardsofts-megabuild/apps/gibd-news && docker-compose run --rm fetch-news-details >> /opt/wizardsofts-megabuild/apps/gibd-news/logs/cron_details.log 2>&1

# DSE stock data - once daily at 4 PM (after market close, Bangladesh time = UTC+6)
0 10 * * 1-5 cd /opt/wizardsofts-megabuild/apps/gibd-news && docker-compose run --rm fetch-stock-data >> /opt/wizardsofts-megabuild/apps/gibd-news/logs/cron_stock.log 2>&1

# DSE share price - every 5 min during trading hours (9:30 AM - 3:00 PM Bangladesh = 3:30-9:00 UTC)
*/5 3-9 * * 1-5 cd /opt/wizardsofts-megabuild/apps/gibd-news && docker-compose run --rm scrape-share-price >> /opt/wizardsofts-megabuild/apps/gibd-news/logs/cron_price.log 2>&1

# Existing DNS update script
*/5 * * * * /home/wizardsofts/scripts/update_dns/venv/bin/python /home/wizardsofts/scripts/update_dns/update_dns_boto3.py >> /home/wizardsofts/scripts/update_dns/cron.log 2>&1
CRON

# Install new crontab
crontab $CRON_FILE

# Create logs directory
mkdir -p /opt/wizardsofts-megabuild/apps/gibd-news/logs

echo "Deployment complete!"
echo "Crontab installed:"
crontab -l
