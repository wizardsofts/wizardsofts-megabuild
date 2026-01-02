import asyncio
import logging
from datetime import datetime, time, timezone
from typing import Dict, Optional
import pytz
import sys
from pathlib import Path
# Add the app directory to Python path to allow imports
sys.path.append(str(Path(__file__).parent))

from config_model import load_and_validate_config

logger = logging.getLogger(__name__)

class BusinessHoursScheduler:
    def __init__(self):
        self.config = None
        self.business_start: Optional[time] = None
        self.business_end: Optional[time] = None
        self.timezone = None
        self.is_initialized = False
        
    async def initialize(self):
        """Initialize the business hours scheduler"""
        try:
            # Use the validated config model instead of loading raw YAML
            validated_config = load_and_validate_config('/opt/autoscaler/config.yaml')
            
            # Extract business hours configuration from the validated model
            business_config = validated_config.autoscaler.business_hours
            
            start_str = business_config.start
            end_str = business_config.end
            tz_str = business_config.timezone
            
            # Parse times
            self.business_start = datetime.strptime(start_str, '%H:%M').time()
            self.business_end = datetime.strptime(end_str, '%H:%M').time()
            
            # Set timezone
            try:
                self.timezone = pytz.timezone(tz_str)
            except:
                logger.warning(f"Invalid timezone '{tz_str}', defaulting to UTC")
                self.timezone = pytz.UTC
            
            logger.info(f"Business hours set: {self.business_start} - {self.business_end} {self.timezone}")
            
            self.is_initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize BusinessHoursScheduler: {e}")
            raise
    
    async def is_business_hours(self) -> bool:
        """Check if current time is within business hours"""
        if not self.is_initialized:
            raise Exception("BusinessHoursScheduler not initialized")
        
        # Get current time in the configured timezone
        now = datetime.now(self.timezone)
        current_time = now.time()
        
        # Check if current time is within business hours
        # Handle case where business hours span midnight (not common but possible)
        if self.business_end > self.business_start:
            # Normal case: business hours don't cross midnight
            is_business_hour = self.business_start <= current_time <= self.business_end
        else:
            # Edge case: business hours cross midnight (e.g. 22:00 to 06:00)
            is_business_hour = current_time >= self.business_start or current_time <= self.business_end
        
        logger.debug(f"Current time: {current_time}, Business hours: {self.business_start}-{self.business_end}, Is business hours: {is_business_hour}")
        
        return is_business_hour
    
    async def is_weekend(self) -> bool:
        """Check if current day is weekend"""
        now = datetime.now(self.timezone)
        return now.weekday() >= 5  # Saturday is 5, Sunday is 6
    
    async def is_holiday(self, date: Optional[datetime] = None) -> bool:
        """Check if a date is a holiday (placeholder - implement as needed)"""
        # This is a placeholder implementation
        # In a real system, you'd have a list of holidays
        if date is None:
            date = datetime.now(self.timezone)
        
        # Placeholder - no holidays by default
        return False
    
    async def is_business_day(self) -> bool:
        """Check if current day is a business day (not weekend or holiday)"""
        is_weekend = await self.is_weekend()
        is_holiday = await self.is_holiday()
        
        return not (is_weekend or is_holiday)
    
    async def get_time_until_business_hours(self) -> int:
        """Get the number of seconds until the next business hours start"""
        if not self.is_initialized:
            raise Exception("BusinessHoursScheduler not initialized")
        
        now = datetime.now(self.timezone)
        current_time = now.time()
        
        # If currently in business hours, return 0
        if await self.is_business_hours() and await self.is_business_day():
            return 0
        
        # Calculate when the next business day starts
        if await self.is_business_day() and current_time < self.business_start:
            # Business hours for today haven't started yet
            next_business_start = now.replace(
                hour=self.business_start.hour,
                minute=self.business_start.minute,
                second=0,
                microsecond=0
            )
        else:
            # Use the next business day
            next_day = now.date()
            days_added = 0
            
            while True:
                next_day = now.date().replace(day=now.date().day + days_added + 1)
                next_business_day = datetime.combine(
                    next_day, 
                    self.business_start
                ).astimezone(self.timezone)
                
                # Check if this day is a business day (not weekend or holiday)
                if not await self.is_weekend() and not await self.is_holiday(next_business_day):
                    next_business_start = next_business_day
                    break
                
                days_added += 1
        
        # Calculate seconds until next business start
        time_delta = next_business_start - now
        return max(0, int(time_delta.total_seconds()))
    
    async def get_time_until_business_ends(self) -> int:
        """Get the number of seconds until the current business day ends"""
        if not self.is_initialized:
            raise Exception("BusinessHoursScheduler not initialized")
        
        if not await self.is_business_day() or not await self.is_business_hours():
            return 0
        
        now = datetime.now(self.timezone)
        
        # Calculate when business hours end today
        business_end_today = now.replace(
            hour=self.business_end.hour,
            minute=self.business_end.minute,
            second=0,
            microsecond=0
        )
        
        time_delta = business_end_today - now
        return max(0, int(time_delta.total_seconds()))
    
    async def wait_until_business_hours(self):
        """Wait until the next business hours start"""
        while not (await self.is_business_hours() and await self.is_business_day()):
            seconds_until = await self.get_time_until_business_hours()
            if seconds_until > 0:
                logger.info(f"Waiting {seconds_until} seconds until next business hours")
                await asyncio.sleep(min(seconds_until, 300))  # Sleep max 5 minutes at a time
            else:
                await asyncio.sleep(10)  # Brief sleep to prevent tight loop