package com.wizardsofts.gibd.gateway_service.service;

import com.wizardsofts.gibd.gateway_service.audit.SecurityAuditLogger;
import com.wizardsofts.gibd.gateway_service.model.Tenant;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.Instant;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * In-memory rate limiting service.
 *
 * Implements sliding window rate limiting per:
 * - Tenant ID
 * - User ID
 * - IP address
 *
 * Rate limits are configurable per subscription tier.
 * For production, consider using Redis for distributed rate limiting.
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class RateLimitService {

    private final SecurityAuditLogger auditLogger;

    // Rate limit windows (in-memory, per instance)
    private final Map<String, RateLimitWindow> windows = new ConcurrentHashMap<>();

    @Value("${rate-limit.window-seconds:60}")
    private int windowSeconds;

    @Value("${rate-limit.cleanup-interval-seconds:300}")
    private int cleanupIntervalSeconds;

    // Tier-based limits (requests per window)
    private static final Map<Tenant.SubscriptionTier, Integer> TIER_LIMITS = Map.of(
        Tenant.SubscriptionTier.FREE, 100,
        Tenant.SubscriptionTier.STARTER, 1000,
        Tenant.SubscriptionTier.PROFESSIONAL, 10000,
        Tenant.SubscriptionTier.ENTERPRISE, 100000
    );

    // Default limit for unauthenticated requests
    private static final int DEFAULT_LIMIT = 50;

    /**
     * Rate limit check result.
     */
    public record RateLimitResult(
        boolean allowed,
        int limit,
        int remaining,
        long resetAt,
        String retryAfter
    ) {
        public static RateLimitResult allowed(int limit, int remaining, long resetAt) {
            return new RateLimitResult(true, limit, remaining, resetAt, null);
        }

        public static RateLimitResult denied(int limit, long resetAt, String retryAfter) {
            return new RateLimitResult(false, limit, 0, resetAt, retryAfter);
        }
    }

    /**
     * Checks and records a request against rate limits.
     *
     * @param tenantId Tenant ID (optional)
     * @param userId User ID (optional)
     * @param tier Subscription tier (optional)
     * @param clientIp Client IP address
     * @return Rate limit result
     */
    public RateLimitResult checkRateLimit(
            String tenantId,
            String userId,
            Tenant.SubscriptionTier tier,
            String clientIp) {

        // Determine the rate limit key and limit
        String key;
        int limit;

        if (tenantId != null) {
            key = "tenant:" + tenantId;
            limit = TIER_LIMITS.getOrDefault(tier, DEFAULT_LIMIT);
        } else if (userId != null) {
            key = "user:" + userId;
            limit = DEFAULT_LIMIT * 2; // Authenticated users get more
        } else {
            key = "ip:" + clientIp;
            limit = DEFAULT_LIMIT;
        }

        // Get or create window
        RateLimitWindow window = windows.computeIfAbsent(key,
            k -> new RateLimitWindow(Instant.now(), windowSeconds));

        // Check if window has expired
        if (window.isExpired()) {
            window.reset();
        }

        // Increment counter
        int currentCount = window.increment();

        long resetAt = window.getResetAt().getEpochSecond();
        int remaining = Math.max(0, limit - currentCount);

        if (currentCount > limit) {
            // Rate limit exceeded
            Duration retryAfter = Duration.between(Instant.now(), window.getResetAt());
            String retryAfterSeconds = String.valueOf(retryAfter.getSeconds());

            log.warn("Rate limit exceeded for {}: {} requests (limit: {})", key, currentCount, limit);
            auditLogger.logRateLimitExceeded(
                userId != null ? userId : "anonymous",
                clientIp,
                key,
                null
            );

            return RateLimitResult.denied(limit, resetAt, retryAfterSeconds);
        }

        return RateLimitResult.allowed(limit, remaining, resetAt);
    }

    /**
     * Gets current usage for a key without incrementing.
     */
    public int getCurrentUsage(String key) {
        RateLimitWindow window = windows.get(key);
        if (window == null || window.isExpired()) {
            return 0;
        }
        return window.getCount();
    }

    /**
     * Cleans up expired windows.
     * Should be called periodically.
     */
    public void cleanup() {
        Instant now = Instant.now();
        int removed = 0;

        var iterator = windows.entrySet().iterator();
        while (iterator.hasNext()) {
            var entry = iterator.next();
            if (entry.getValue().isExpiredFor(Duration.ofSeconds(cleanupIntervalSeconds))) {
                iterator.remove();
                removed++;
            }
        }

        if (removed > 0) {
            log.debug("Cleaned up {} expired rate limit windows", removed);
        }
    }

    /**
     * Gets the limit for a tier.
     */
    public int getLimitForTier(Tenant.SubscriptionTier tier) {
        return TIER_LIMITS.getOrDefault(tier, DEFAULT_LIMIT);
    }

    /**
     * Sliding window counter.
     */
    private static class RateLimitWindow {
        private Instant windowStart;
        private final int windowSeconds;
        private final AtomicInteger counter = new AtomicInteger(0);

        RateLimitWindow(Instant start, int windowSeconds) {
            this.windowStart = start;
            this.windowSeconds = windowSeconds;
        }

        int increment() {
            return counter.incrementAndGet();
        }

        int getCount() {
            return counter.get();
        }

        boolean isExpired() {
            return Instant.now().isAfter(windowStart.plusSeconds(windowSeconds));
        }

        boolean isExpiredFor(Duration duration) {
            return Instant.now().isAfter(windowStart.plusSeconds(windowSeconds).plus(duration));
        }

        void reset() {
            windowStart = Instant.now();
            counter.set(0);
        }

        Instant getResetAt() {
            return windowStart.plusSeconds(windowSeconds);
        }
    }
}
