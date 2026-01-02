import { NextAuthOptions } from 'next-auth';
import KeycloakProvider from 'next-auth/providers/keycloak';
import { JWT } from 'next-auth/jwt';

/**
 * Extended JWT type with Keycloak-specific claims
 */
interface KeycloakJWT extends JWT {
  accessToken?: string;
  refreshToken?: string;
  accessTokenExpires?: number;
  error?: string;
  tenantId?: string;
  roles?: string[];
}

/**
 * Refresh token function for Keycloak
 * Handles token rotation per OAuth 2.1 best practices
 */
async function refreshAccessToken(token: KeycloakJWT): Promise<KeycloakJWT> {
  try {
    const issuerUri = process.env.KEYCLOAK_ISSUER;
    if (!issuerUri) {
      throw new Error('KEYCLOAK_ISSUER not configured');
    }

    const tokenEndpoint = `${issuerUri}/protocol/openid-connect/token`;

    const response = await fetch(tokenEndpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        grant_type: 'refresh_token',
        client_id: process.env.KEYCLOAK_CLIENT_ID!,
        refresh_token: token.refreshToken!,
      }),
    });

    const refreshedTokens = await response.json();

    if (!response.ok) {
      console.error('Token refresh failed:', refreshedTokens);
      throw new Error('RefreshTokenError');
    }

    return {
      ...token,
      accessToken: refreshedTokens.access_token,
      refreshToken: refreshedTokens.refresh_token ?? token.refreshToken,
      accessTokenExpires: Date.now() + refreshedTokens.expires_in * 1000,
    };
  } catch (error) {
    console.error('Error refreshing access token:', error);
    return {
      ...token,
      error: 'RefreshTokenError',
    };
  }
}

/**
 * Extract roles from Keycloak token
 */
function extractRoles(accessToken: string): string[] {
  try {
    // Decode JWT payload (second part)
    const payload = JSON.parse(
      Buffer.from(accessToken.split('.')[1], 'base64').toString()
    );

    const realmRoles = payload.realm_access?.roles || [];
    return realmRoles;
  } catch (error) {
    console.error('Error extracting roles:', error);
    return [];
  }
}

/**
 * Extract tenant_id from Keycloak token
 */
function extractTenantId(accessToken: string): string | undefined {
  try {
    const payload = JSON.parse(
      Buffer.from(accessToken.split('.')[1], 'base64').toString()
    );
    return payload.tenant_id;
  } catch (error) {
    console.error('Error extracting tenant_id:', error);
    return undefined;
  }
}

/**
 * NextAuth.js configuration for Keycloak OIDC
 *
 * Security features:
 * - PKCE is enforced by Keycloak (public client)
 * - Token refresh with rotation
 * - Role extraction for authorization
 * - Tenant context for multi-tenancy
 */
export const authOptions: NextAuthOptions = {
  providers: [
    KeycloakProvider({
      clientId: process.env.KEYCLOAK_CLIENT_ID!,
      clientSecret: '', // Public client - no secret
      issuer: process.env.KEYCLOAK_ISSUER!,
      authorization: {
        params: {
          // Request offline access for refresh tokens
          scope: 'openid profile email offline_access',
        },
      },
    }),
  ],

  callbacks: {
    /**
     * JWT callback - runs on sign in and token refresh
     */
    async jwt({ token, account, user }) {
      const keycloakToken = token as KeycloakJWT;

      // Initial sign in
      if (account && user) {
        return {
          ...token,
          accessToken: account.access_token,
          refreshToken: account.refresh_token,
          accessTokenExpires: account.expires_at
            ? account.expires_at * 1000
            : Date.now() + 300000, // 5 min default
          tenantId: account.access_token
            ? extractTenantId(account.access_token)
            : undefined,
          roles: account.access_token
            ? extractRoles(account.access_token)
            : [],
        };
      }

      // Return token if not expired
      if (
        keycloakToken.accessTokenExpires &&
        Date.now() < keycloakToken.accessTokenExpires - 60000
      ) {
        return token;
      }

      // Token expired, refresh it
      return refreshAccessToken(keycloakToken);
    },

    /**
     * Session callback - makes data available to client
     */
    async session({ session, token }) {
      const keycloakToken = token as KeycloakJWT;

      return {
        ...session,
        accessToken: keycloakToken.accessToken,
        error: keycloakToken.error,
        user: {
          ...session.user,
          tenantId: keycloakToken.tenantId,
          roles: keycloakToken.roles || [],
        },
      };
    },
  },

  pages: {
    signIn: '/auth/signin',
    error: '/auth/error',
  },

  session: {
    strategy: 'jwt',
    maxAge: 30 * 24 * 60 * 60, // 30 days
  },

  events: {
    async signOut({ token }) {
      // Perform Keycloak logout (end session)
      const keycloakToken = token as KeycloakJWT;
      if (keycloakToken.accessToken) {
        try {
          const issuerUri = process.env.KEYCLOAK_ISSUER;
          const logoutUrl = `${issuerUri}/protocol/openid-connect/logout`;

          await fetch(logoutUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: new URLSearchParams({
              client_id: process.env.KEYCLOAK_CLIENT_ID!,
              refresh_token: keycloakToken.refreshToken || '',
            }),
          });
        } catch (error) {
          console.error('Keycloak logout error:', error);
        }
      }
    },
  },

  debug: process.env.NODE_ENV === 'development',
};

/**
 * Type declarations for extended session
 */
declare module 'next-auth' {
  interface Session {
    accessToken?: string;
    error?: string;
    user: {
      name?: string | null;
      email?: string | null;
      image?: string | null;
      tenantId?: string;
      roles?: string[];
    };
  }
}

declare module 'next-auth/jwt' {
  interface JWT {
    accessToken?: string;
    refreshToken?: string;
    accessTokenExpires?: number;
    error?: string;
    tenantId?: string;
    roles?: string[];
  }
}
