package com.wizardsofts.gibd.gateway_service.exception;

import com.wizardsofts.gibd.gateway_service.audit.SecurityAuditLogger;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.oauth2.jwt.JwtException;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.server.ResponseStatusException;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;

/**
 * Global exception handler for the gateway.
 *
 * Provides consistent error responses for:
 * - Validation errors
 * - Authentication/Authorization failures
 * - Business logic errors
 * - Unexpected exceptions
 *
 * All errors are logged appropriately and formatted for API consumers.
 */
@Slf4j
@RestControllerAdvice
@RequiredArgsConstructor
public class GlobalExceptionHandler {

    private final SecurityAuditLogger auditLogger;

    /**
     * Standard error response format.
     */
    public record ErrorResponse(
        Instant timestamp,
        int status,
        String error,
        String message,
        String path,
        Map<String, String> details
    ) {
        public static ErrorResponse of(HttpStatus status, String message, String path) {
            return new ErrorResponse(
                Instant.now(),
                status.value(),
                status.getReasonPhrase(),
                message,
                path,
                null
            );
        }

        public static ErrorResponse of(HttpStatus status, String message, String path, Map<String, String> details) {
            return new ErrorResponse(
                Instant.now(),
                status.value(),
                status.getReasonPhrase(),
                message,
                path,
                details
            );
        }
    }

    /**
     * Handles validation errors.
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ErrorResponse> handleValidationException(
            MethodArgumentNotValidException ex) {

        Map<String, String> errors = new HashMap<>();
        ex.getBindingResult().getAllErrors().forEach(error -> {
            String fieldName = error instanceof FieldError fe ? fe.getField() : error.getObjectName();
            String errorMessage = error.getDefaultMessage();
            errors.put(fieldName, errorMessage);
        });

        log.debug("Validation failed: {}", errors);

        ErrorResponse response = ErrorResponse.of(
            HttpStatus.BAD_REQUEST,
            "Validation failed",
            null,
            errors
        );

        return ResponseEntity.badRequest().body(response);
    }

    /**
     * Handles JWT authentication errors.
     */
    @ExceptionHandler(JwtException.class)
    public ResponseEntity<ErrorResponse> handleJwtException(JwtException ex) {
        log.warn("JWT error: {}", ex.getMessage());

        auditLogger.logTokenValidation(null, null, false, ex.getMessage(), null);

        ErrorResponse response = ErrorResponse.of(
            HttpStatus.UNAUTHORIZED,
            "Invalid or expired token",
            null
        );

        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
    }

    /**
     * Handles authentication errors.
     */
    @ExceptionHandler(AuthenticationException.class)
    public ResponseEntity<ErrorResponse> handleAuthenticationException(AuthenticationException ex) {
        log.warn("Authentication error: {}", ex.getMessage());

        auditLogger.logAuthFailure(null, null, ex.getMessage(), null);

        ErrorResponse response = ErrorResponse.of(
            HttpStatus.UNAUTHORIZED,
            "Authentication required",
            null
        );

        return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
    }

    /**
     * Handles access denied errors.
     */
    @ExceptionHandler(AccessDeniedException.class)
    public ResponseEntity<ErrorResponse> handleAccessDeniedException(AccessDeniedException ex) {
        log.warn("Access denied: {}", ex.getMessage());

        auditLogger.logAccessDenied(null, null, null, ex.getMessage(), null);

        ErrorResponse response = ErrorResponse.of(
            HttpStatus.FORBIDDEN,
            "Access denied",
            null
        );

        return ResponseEntity.status(HttpStatus.FORBIDDEN).body(response);
    }

    /**
     * Handles business logic errors (IllegalArgumentException).
     */
    @ExceptionHandler(IllegalArgumentException.class)
    public ResponseEntity<ErrorResponse> handleIllegalArgumentException(IllegalArgumentException ex) {
        log.debug("Bad request: {}", ex.getMessage());

        ErrorResponse response = ErrorResponse.of(
            HttpStatus.BAD_REQUEST,
            ex.getMessage(),
            null
        );

        return ResponseEntity.badRequest().body(response);
    }

    /**
     * Handles state errors (IllegalStateException).
     */
    @ExceptionHandler(IllegalStateException.class)
    public ResponseEntity<ErrorResponse> handleIllegalStateException(IllegalStateException ex) {
        log.warn("State error: {}", ex.getMessage());

        ErrorResponse response = ErrorResponse.of(
            HttpStatus.CONFLICT,
            ex.getMessage(),
            null
        );

        return ResponseEntity.status(HttpStatus.CONFLICT).body(response);
    }

    /**
     * Handles ResponseStatusException.
     */
    @ExceptionHandler(ResponseStatusException.class)
    public ResponseEntity<ErrorResponse> handleResponseStatusException(ResponseStatusException ex) {
        log.debug("Response status: {} - {}", ex.getStatusCode(), ex.getReason());

        ErrorResponse response = ErrorResponse.of(
            HttpStatus.valueOf(ex.getStatusCode().value()),
            ex.getReason() != null ? ex.getReason() : "Request failed",
            null
        );

        return ResponseEntity.status(ex.getStatusCode()).body(response);
    }

    /**
     * Handles all other unexpected exceptions.
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ErrorResponse> handleGenericException(Exception ex) {
        log.error("Unexpected error: {}", ex.getMessage(), ex);

        ErrorResponse response = ErrorResponse.of(
            HttpStatus.INTERNAL_SERVER_ERROR,
            "An unexpected error occurred",
            null
        );

        return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(response);
    }
}
