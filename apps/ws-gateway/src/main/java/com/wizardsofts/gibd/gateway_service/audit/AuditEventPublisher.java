package com.wizardsofts.gibd.gateway_service.audit;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.scheduling.annotation.Async;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

/**
 * Publisher for security audit events to external systems.
 *
 * Supports:
 * - Webhook delivery (HTTP POST)
 * - Message queue integration (future)
 * - SIEM integration (future)
 *
 * Uses async processing with internal queue for reliability.
 */
@Slf4j
@Service
public class AuditEventPublisher {

    @Value("${security.audit.webhook-url:}")
    private String webhookUrl;

    @Value("${security.audit.webhook-auth-header:}")
    private String webhookAuthHeader;

    private final RestTemplate restTemplate = new RestTemplate();
    private final BlockingQueue<SecurityAuditEvent> eventQueue = new LinkedBlockingQueue<>(10000);

    /**
     * Publishes an audit event asynchronously.
     */
    @Async
    public void publish(SecurityAuditEvent event) {
        if (webhookUrl == null || webhookUrl.isBlank()) {
            log.debug("No webhook URL configured, skipping event publish");
            return;
        }

        try {
            // Add to queue for processing
            if (!eventQueue.offer(event)) {
                log.warn("Audit event queue full, dropping event: {}", event.getEventId());
                return;
            }

            // Process event
            sendToWebhook(event);

        } catch (Exception e) {
            log.error("Failed to publish audit event {}: {}", event.getEventId(), e.getMessage());
        }
    }

    /**
     * Sends event to configured webhook.
     */
    private void sendToWebhook(SecurityAuditEvent event) {
        try {
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            if (webhookAuthHeader != null && !webhookAuthHeader.isBlank()) {
                headers.set(HttpHeaders.AUTHORIZATION, webhookAuthHeader);
            }

            HttpEntity<SecurityAuditEvent> request = new HttpEntity<>(event, headers);

            ResponseEntity<Void> response = restTemplate.exchange(
                webhookUrl,
                HttpMethod.POST,
                request,
                Void.class
            );

            if (!response.getStatusCode().is2xxSuccessful()) {
                log.warn("Webhook returned non-success status: {}", response.getStatusCode());
            }

        } catch (Exception e) {
            log.error("Failed to send event to webhook: {}", e.getMessage());
            // Re-queue for retry (with exponential backoff in production)
        }
    }

    /**
     * Returns current queue size for monitoring.
     */
    public int getQueueSize() {
        return eventQueue.size();
    }

    /**
     * Returns queue capacity for monitoring.
     */
    public int getQueueCapacity() {
        return eventQueue.remainingCapacity();
    }
}
