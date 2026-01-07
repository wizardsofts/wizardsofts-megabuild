package com.wizardsofts.gibd.gateway_service.service;

import com.wizardsofts.gibd.gateway_service.model.Tenant;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.*;

/**
 * Service for provisioning tenants in Keycloak.
 *
 * Creates:
 * - Keycloak group for the tenant
 * - Default roles within the tenant group
 * - Assigns owner to the tenant group with admin role
 *
 * Requires Keycloak Admin API access via service account.
 */
@Slf4j
@Service
public class KeycloakTenantProvisioningService {

    @Value("${keycloak.admin.base-url:${KEYCLOAK_ISSUER_URI:https://id.wizardsofts.com}}")
    private String keycloakBaseUrl;

    @Value("${keycloak.admin.realm:wizardsofts}")
    private String realm;

    private final OAuth2ClientService oauth2ClientService;
    private final RestTemplate restTemplate;

    // Default roles to create for each tenant
    private static final List<String> DEFAULT_TENANT_ROLES = Arrays.asList(
        "tenant-admin",
        "tenant-member",
        "tenant-viewer"
    );

    public KeycloakTenantProvisioningService(OAuth2ClientService oauth2ClientService) {
        this.oauth2ClientService = oauth2ClientService;
        this.restTemplate = new RestTemplate();
    }

    /**
     * Provisions a tenant in Keycloak.
     *
     * @param tenant The tenant to provision
     * @return The Keycloak group ID created for the tenant
     * @throws RuntimeException if provisioning fails
     */
    public String provisionTenant(Tenant tenant) {
        log.info("Starting Keycloak provisioning for tenant: {}", tenant.getSlug());

        try {
            // Step 1: Create tenant group
            String groupId = createTenantGroup(tenant);
            log.info("Created Keycloak group {} for tenant {}", groupId, tenant.getSlug());

            // Step 2: Create default roles as subgroups
            createTenantRoles(groupId, tenant.getSlug());
            log.info("Created default roles for tenant {}", tenant.getSlug());

            // Step 3: Assign owner to tenant-admin role
            assignOwnerToAdminRole(tenant.getOwnerEmail(), groupId);
            log.info("Assigned owner {} to tenant-admin role", tenant.getOwnerEmail());

            return groupId;

        } catch (Exception e) {
            log.error("Failed to provision tenant {} in Keycloak: {}", tenant.getSlug(), e.getMessage());
            throw new RuntimeException("Keycloak provisioning failed: " + e.getMessage(), e);
        }
    }

    /**
     * Creates the main tenant group in Keycloak.
     */
    private String createTenantGroup(Tenant tenant) {
        String url = keycloakBaseUrl + "/admin/realms/" + realm + "/groups";

        HttpHeaders headers = oauth2ClientService.createAuthHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, Object> groupBody = new HashMap<>();
        groupBody.put("name", "tenant:" + tenant.getSlug());
        groupBody.put("attributes", Map.of(
            "tenant_id", List.of(tenant.getId().toString()),
            "tier", List.of(tenant.getTier().name()),
            "owner_email", List.of(tenant.getOwnerEmail())
        ));

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(groupBody, headers);

        ResponseEntity<Void> response = restTemplate.exchange(
            url,
            HttpMethod.POST,
            request,
            Void.class
        );

        if (response.getStatusCode() == HttpStatus.CREATED) {
            // Extract group ID from Location header
            String location = response.getHeaders().getFirst(HttpHeaders.LOCATION);
            if (location != null) {
                return location.substring(location.lastIndexOf('/') + 1);
            }
        }

        throw new RuntimeException("Failed to create tenant group, status: " + response.getStatusCode());
    }

    /**
     * Creates default role subgroups within the tenant group.
     */
    private void createTenantRoles(String parentGroupId, String tenantSlug) {
        String url = keycloakBaseUrl + "/admin/realms/" + realm + "/groups/" + parentGroupId + "/children";

        HttpHeaders headers = oauth2ClientService.createAuthHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        for (String role : DEFAULT_TENANT_ROLES) {
            Map<String, Object> roleBody = new HashMap<>();
            roleBody.put("name", role);

            HttpEntity<Map<String, Object>> request = new HttpEntity<>(roleBody, headers);

            try {
                restTemplate.exchange(url, HttpMethod.POST, request, Void.class);
                log.debug("Created role {} for tenant {}", role, tenantSlug);
            } catch (Exception e) {
                log.warn("Failed to create role {} for tenant {}: {}", role, tenantSlug, e.getMessage());
            }
        }
    }

    /**
     * Assigns the owner to the tenant-admin role group.
     */
    private void assignOwnerToAdminRole(String ownerEmail, String parentGroupId) {
        // First, find the user by email
        String userSearchUrl = keycloakBaseUrl + "/admin/realms/" + realm + "/users?email=" + ownerEmail;

        HttpHeaders headers = oauth2ClientService.createAuthHeaders();
        HttpEntity<Void> request = new HttpEntity<>(headers);

        ResponseEntity<List> userResponse = restTemplate.exchange(
            userSearchUrl,
            HttpMethod.GET,
            request,
            List.class
        );

        if (userResponse.getBody() == null || userResponse.getBody().isEmpty()) {
            log.warn("User {} not found in Keycloak, will be assigned on first login", ownerEmail);
            return;
        }

        @SuppressWarnings("unchecked")
        Map<String, Object> user = (Map<String, Object>) userResponse.getBody().get(0);
        String userId = (String) user.get("id");

        // Find tenant-admin subgroup
        String groupsUrl = keycloakBaseUrl + "/admin/realms/" + realm + "/groups/" + parentGroupId + "/children";
        ResponseEntity<List> groupsResponse = restTemplate.exchange(
            groupsUrl,
            HttpMethod.GET,
            request,
            List.class
        );

        if (groupsResponse.getBody() != null) {
            for (Object group : groupsResponse.getBody()) {
                @SuppressWarnings("unchecked")
                Map<String, Object> groupMap = (Map<String, Object>) group;
                if ("tenant-admin".equals(groupMap.get("name"))) {
                    String adminGroupId = (String) groupMap.get("id");

                    // Assign user to group
                    String assignUrl = keycloakBaseUrl + "/admin/realms/" + realm
                        + "/users/" + userId + "/groups/" + adminGroupId;
                    restTemplate.exchange(assignUrl, HttpMethod.PUT, request, Void.class);
                    log.info("Assigned user {} to tenant-admin group", ownerEmail);
                    break;
                }
            }
        }
    }

    /**
     * Deletes a tenant group from Keycloak.
     */
    public void deprovisionTenant(String keycloakGroupId) {
        log.info("Deprovisioning tenant group: {}", keycloakGroupId);

        String url = keycloakBaseUrl + "/admin/realms/" + realm + "/groups/" + keycloakGroupId;

        HttpHeaders headers = oauth2ClientService.createAuthHeaders();
        HttpEntity<Void> request = new HttpEntity<>(headers);

        try {
            restTemplate.exchange(url, HttpMethod.DELETE, request, Void.class);
            log.info("Successfully deleted Keycloak group: {}", keycloakGroupId);
        } catch (Exception e) {
            log.error("Failed to delete Keycloak group {}: {}", keycloakGroupId, e.getMessage());
            throw new RuntimeException("Failed to deprovision tenant", e);
        }
    }
}
