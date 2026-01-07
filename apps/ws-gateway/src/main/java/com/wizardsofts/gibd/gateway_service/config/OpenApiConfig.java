package com.wizardsofts.gibd.gateway_service.config;

import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.security.OAuthFlow;
import io.swagger.v3.oas.models.security.OAuthFlows;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

/**
 * OpenAPI/Swagger configuration for API documentation.
 *
 * Provides:
 * - API metadata (title, version, description)
 * - OAuth2/Bearer token security scheme
 * - Server URLs for different environments
 *
 * Access Swagger UI at: /swagger-ui.html
 * Access OpenAPI spec at: /v3/api-docs
 */
@Configuration
public class OpenApiConfig {

    @Value("${spring.application.name:ws-gateway}")
    private String applicationName;

    @Value("${keycloak.issuer-uri:https://id.wizardsofts.com/realms/wizardsofts}")
    private String keycloakIssuer;

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(apiInfo())
            .servers(servers())
            .components(securityComponents())
            .addSecurityItem(new SecurityRequirement().addList("bearer-jwt"));
    }

    private Info apiInfo() {
        return new Info()
            .title("WizardSofts API Gateway")
            .version("1.0.0")
            .description("""
                API Gateway for WizardSofts GIBD Platform.

                ## Authentication

                All API endpoints require OAuth2 Bearer token authentication.
                Obtain a token from Keycloak using:
                - Authorization Code flow (for web applications)
                - Client Credentials flow (for service-to-service)

                ## Tenant Context

                Multi-tenant endpoints require a valid `tenant_id` claim in the JWT.
                The gateway extracts tenant context and propagates it to downstream services.

                ## Rate Limiting

                API rate limits are enforced per tenant/user. Check response headers for:
                - `X-RateLimit-Limit`: Maximum requests allowed
                - `X-RateLimit-Remaining`: Requests remaining in window
                - `X-RateLimit-Reset`: Unix timestamp when limit resets
                """)
            .contact(new Contact()
                .name("WizardSofts")
                .email("support@wizardsofts.com")
                .url("https://wizardsofts.com"))
            .license(new License()
                .name("Proprietary")
                .url("https://wizardsofts.com/terms"));
    }

    private List<Server> servers() {
        return List.of(
            new Server()
                .url("https://api.wizardsofts.com")
                .description("Production"),
            new Server()
                .url("https://api-staging.wizardsofts.com")
                .description("Staging"),
            new Server()
                .url("http://localhost:8080")
                .description("Local Development")
        );
    }

    private Components securityComponents() {
        return new Components()
            .addSecuritySchemes("bearer-jwt", new SecurityScheme()
                .type(SecurityScheme.Type.HTTP)
                .scheme("bearer")
                .bearerFormat("JWT")
                .description("JWT Bearer token from Keycloak"))
            .addSecuritySchemes("oauth2", new SecurityScheme()
                .type(SecurityScheme.Type.OAUTH2)
                .description("OAuth2 with Keycloak")
                .flows(new OAuthFlows()
                    .authorizationCode(new OAuthFlow()
                        .authorizationUrl(keycloakIssuer + "/protocol/openid-connect/auth")
                        .tokenUrl(keycloakIssuer + "/protocol/openid-connect/token")
                        .refreshUrl(keycloakIssuer + "/protocol/openid-connect/token"))
                    .clientCredentials(new OAuthFlow()
                        .tokenUrl(keycloakIssuer + "/protocol/openid-connect/token"))));
    }
}
