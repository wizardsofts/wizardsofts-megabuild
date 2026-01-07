package com.wizardsofts.gibd.gateway_service.integration;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.wizardsofts.gibd.gateway_service.dto.TenantRegistrationRequest;
import com.wizardsofts.gibd.gateway_service.model.Tenant;
import com.wizardsofts.gibd.gateway_service.repository.TenantRepository;
import org.junit.jupiter.api.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.AutoConfigureMockMvc;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.http.MediaType;
import org.springframework.security.test.context.support.WithMockUser;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * Integration tests for Tenant Onboarding API.
 *
 * Tests the complete flow of:
 * - Tenant registration
 * - Tenant lookup
 * - Admin operations (suspend, reactivate, delete)
 *
 * Uses H2 in-memory database and mocked security context.
 */
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@TestMethodOrder(MethodOrderer.OrderAnnotation.class)
@DisplayName("Tenant Onboarding Integration Tests")
public class TenantOnboardingIntegrationTest {

    @Autowired
    private MockMvc mockMvc;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private TenantRepository tenantRepository;

    private static final String TENANT_SLUG = "test-tenant";
    private static final String OWNER_EMAIL = "owner@test.com";

    @BeforeEach
    void setUp() {
        // Clean up any existing test data
        tenantRepository.findBySlugIgnoreCase(TENANT_SLUG)
            .ifPresent(tenant -> tenantRepository.delete(tenant));
    }

    @Test
    @Order(1)
    @DisplayName("Should register new tenant successfully")
    void shouldRegisterNewTenant() throws Exception {
        TenantRegistrationRequest request = TenantRegistrationRequest.builder()
            .organizationName("Test Organization")
            .slug(TENANT_SLUG)
            .ownerEmail(OWNER_EMAIL)
            .subscriptionTier("FREE")
            .build();

        MvcResult result = mockMvc.perform(post("/api/v1/tenants")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.slug").value(TENANT_SLUG))
            .andExpect(jsonPath("$.organizationName").value("Test Organization"))
            .andExpect(jsonPath("$.status").value("PENDING"))
            .andReturn();

        // Verify tenant was created in database
        Tenant tenant = tenantRepository.findBySlugIgnoreCase(TENANT_SLUG).orElseThrow();
        assertThat(tenant.getName()).isEqualTo("Test Organization");
        assertThat(tenant.getOwnerEmail()).isEqualTo(OWNER_EMAIL);
    }

    @Test
    @Order(2)
    @DisplayName("Should reject duplicate slug")
    void shouldRejectDuplicateSlug() throws Exception {
        // First, create a tenant
        Tenant existingTenant = Tenant.builder()
            .slug(TENANT_SLUG)
            .name("Existing Tenant")
            .ownerEmail("existing@test.com")
            .status(Tenant.TenantStatus.ACTIVE)
            .tier(Tenant.SubscriptionTier.FREE)
            .build();
        tenantRepository.save(existingTenant);

        // Try to register with same slug
        TenantRegistrationRequest request = TenantRegistrationRequest.builder()
            .organizationName("New Organization")
            .slug(TENANT_SLUG)
            .ownerEmail(OWNER_EMAIL)
            .build();

        mockMvc.perform(post("/api/v1/tenants")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest())
            .andExpect(jsonPath("$.message").value("Slug '" + TENANT_SLUG + "' is already taken"));
    }

    @Test
    @Order(3)
    @DisplayName("Should validate slug format")
    void shouldValidateSlugFormat() throws Exception {
        TenantRegistrationRequest request = TenantRegistrationRequest.builder()
            .organizationName("Test Organization")
            .slug("Invalid Slug!") // Invalid characters
            .ownerEmail(OWNER_EMAIL)
            .build();

        mockMvc.perform(post("/api/v1/tenants")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest());
    }

    @Test
    @Order(4)
    @DisplayName("Should validate email format")
    void shouldValidateEmailFormat() throws Exception {
        TenantRegistrationRequest request = TenantRegistrationRequest.builder()
            .organizationName("Test Organization")
            .slug("valid-slug")
            .ownerEmail("invalid-email")
            .build();

        mockMvc.perform(post("/api/v1/tenants")
                .contentType(MediaType.APPLICATION_JSON)
                .content(objectMapper.writeValueAsString(request)))
            .andExpect(status().isBadRequest());
    }

    @Test
    @Order(5)
    @WithMockUser(roles = "ADMIN")
    @DisplayName("Admin should be able to get tenant by ID")
    void adminShouldGetTenantById() throws Exception {
        // Create a tenant
        Tenant tenant = Tenant.builder()
            .slug(TENANT_SLUG)
            .name("Test Tenant")
            .ownerEmail(OWNER_EMAIL)
            .status(Tenant.TenantStatus.ACTIVE)
            .tier(Tenant.SubscriptionTier.FREE)
            .build();
        tenant = tenantRepository.save(tenant);

        mockMvc.perform(get("/api/v1/tenants/" + tenant.getId()))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.slug").value(TENANT_SLUG));
    }

    @Test
    @Order(6)
    @WithMockUser(roles = "ADMIN")
    @DisplayName("Admin should be able to suspend tenant")
    void adminShouldSuspendTenant() throws Exception {
        // Create an active tenant
        Tenant tenant = Tenant.builder()
            .slug(TENANT_SLUG)
            .name("Test Tenant")
            .ownerEmail(OWNER_EMAIL)
            .status(Tenant.TenantStatus.ACTIVE)
            .tier(Tenant.SubscriptionTier.FREE)
            .build();
        tenant = tenantRepository.save(tenant);

        mockMvc.perform(put("/api/v1/tenants/" + tenant.getId() + "/suspend")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"reason\": \"Test suspension\"}"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("SUSPENDED"));

        // Verify in database
        Tenant suspended = tenantRepository.findById(tenant.getId()).orElseThrow();
        assertThat(suspended.getStatus()).isEqualTo(Tenant.TenantStatus.SUSPENDED);
        assertThat(suspended.getSuspendedAt()).isNotNull();
    }

    @Test
    @Order(7)
    @WithMockUser(roles = "ADMIN")
    @DisplayName("Admin should be able to reactivate suspended tenant")
    void adminShouldReactivateTenant() throws Exception {
        // Create a suspended tenant
        Tenant tenant = Tenant.builder()
            .slug(TENANT_SLUG)
            .name("Test Tenant")
            .ownerEmail(OWNER_EMAIL)
            .status(Tenant.TenantStatus.SUSPENDED)
            .tier(Tenant.SubscriptionTier.FREE)
            .build();
        tenant = tenantRepository.save(tenant);

        mockMvc.perform(put("/api/v1/tenants/" + tenant.getId() + "/reactivate"))
            .andExpect(status().isOk())
            .andExpect(jsonPath("$.status").value("ACTIVE"));
    }

    @Test
    @Order(8)
    @WithMockUser(roles = "ADMIN")
    @DisplayName("Admin should be able to delete tenant")
    void adminShouldDeleteTenant() throws Exception {
        // Create a tenant
        Tenant tenant = Tenant.builder()
            .slug(TENANT_SLUG)
            .name("Test Tenant")
            .ownerEmail(OWNER_EMAIL)
            .status(Tenant.TenantStatus.ACTIVE)
            .tier(Tenant.SubscriptionTier.FREE)
            .build();
        tenant = tenantRepository.save(tenant);

        mockMvc.perform(delete("/api/v1/tenants/" + tenant.getId()))
            .andExpect(status().isNoContent());

        // Verify soft delete
        Tenant deleted = tenantRepository.findById(tenant.getId()).orElseThrow();
        assertThat(deleted.getStatus()).isEqualTo(Tenant.TenantStatus.DELETED);
    }

    @Test
    @Order(9)
    @DisplayName("Non-admin should not be able to suspend tenant")
    @WithMockUser(roles = "USER")
    void nonAdminShouldNotSuspendTenant() throws Exception {
        Tenant tenant = Tenant.builder()
            .slug(TENANT_SLUG)
            .name("Test Tenant")
            .ownerEmail(OWNER_EMAIL)
            .status(Tenant.TenantStatus.ACTIVE)
            .tier(Tenant.SubscriptionTier.FREE)
            .build();
        tenant = tenantRepository.save(tenant);

        mockMvc.perform(put("/api/v1/tenants/" + tenant.getId() + "/suspend")
                .contentType(MediaType.APPLICATION_JSON)
                .content("{\"reason\": \"Test\"}"))
            .andExpect(status().isForbidden());
    }
}
