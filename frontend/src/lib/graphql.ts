import { apiClient } from './api';
import type { QueryClient } from '@tanstack/react-query';

export interface GraphQLVariables {
  [key: string]: any;
}

export interface GraphQLResponse<T> {
  data: T;
  errors?: ReadonlyArray<{ message: string; path?: (string | number)[] }>;
  extensions?: Record<string, any>;
}

export interface GraphQLOptions {
  variables?: GraphQLVariables;
  fetchPolicy?: 'cache-first' | 'cache-only' | 'network-only' | 'cache-and-network' | 'no-cache';
  errorPolicy?: 'ignore' | 'omit' | 'throw';
  context?: any;
}

const defaultOptions: Required<Omit<GraphQLOptions, 'variables'>> = {
  fetchPolicy: 'cache-first',
  errorPolicy: 'throw',
  context: undefined,
};

let defaultFetchPolicy: GraphQLOptions['fetchPolicy'] = 'cache-first';
let defaultErrorPolicy: GraphQLOptions['errorPolicy'] = 'throw';

export function setGraphQLDefaults(options: {
  fetchPolicy?: GraphQLOptions['fetchPolicy'];
  errorPolicy?: GraphQLOptions['errorPolicy'];
}): void {
  if (options.fetchPolicy !== undefined) {
    defaultFetchPolicy = options.fetchPolicy;
  }
  if (options.errorPolicy !== undefined) {
    defaultErrorPolicy = options.errorPolicy;
  }
}

export async function executeGraphQLQuery<T = any>(
  query: string,
  variables?: GraphQLVariables,
  options: GraphQLOptions = {}
): Promise<GraphQLResponse<T>> {
  const opts = {
    ...defaultOptions,
    ...options,
  };

  try {
    const response = await apiClient.post<GraphQLResponse<T>>('/graphql', {
      query,
      variables,
    });

    if (response.data.errors && response.data.errors.length > 0) {
      const errorMessage = response.data.errors.map(e => e.message).join('; ');
      
      if (opts.errorPolicy === 'ignore' || opts.errorPolicy === 'omit') {
        return response.data;
      }
      
      throw new Error(`GraphQL Error: ${errorMessage}`);
    }

    return response.data;
  } catch (error) {
    if (opts.errorPolicy === 'ignore' || opts.errorPolicy === 'omit') {
      return { data: null as T };
    }
    
    throw error;
  }
}

/**
 * Batch execute multiple GraphQL operations
 */
export async function executeGraphQLBatch(
  operations: Array<{
    id: string;
    query: string;
    variables?: GraphQLVariables;
  }>
): Promise<Map<string, GraphQLResponse<any>>> {
  const results = new Map<string, GraphQLResponse<any>>();

  const promises = operations.map(async ({ id, query, variables }) => {
    try {
      const response = await executeGraphQLQuery(query, variables);
      results.set(id, response);
    } catch (error) {
      results.set(id, {
        data: null,
        errors: error instanceof Error 
          ? [{ message: error.message }]
          : [{ message: String(error) }],
      });
    }
  });

  await Promise.all(promises);
  return results;
}

/**
 * Generate GraphQL query string from field list
 */
export function buildGraphQLQuery(
  operation: string,
  fields: string | string[],
  variables?: string
): string {
  const fieldsStr = Array.isArray(fields) 
    ? fields.join('\\n') 
    : fields;
  
  const varStr = variables ? `(${variables})` : '';
  
  return `
    operation ${operation}${varStr} {
      ${operation}${varStr} {
        ${fieldsStr}
      }
    }
  `.trim();
}

/**
 * Generate GraphQL fragment
 */
export function buildGraphQLFragment(
  name: string,
  type: string,
  fields: string | string[]
): string {
  const fieldsStr = Array.isArray(fields) 
    ? fields.join('\\n') 
    : fields;
  
  return `
    fragment ${name} on ${type} {
      ${fieldsStr}
    }
  `.trim();
}

/**
 * GraphQL schema types (auto-generated from introspection)
 */
export const GraphQLSchema = {
  types: {
    Stock: {
      fields: ['symbol', 'name', 'price', 'change', 'changePercent', 'volume', 'marketCap'],
    },
    Crypto: {
      fields: ['id', 'symbol', 'name', 'price', 'change', 'changePercent', 'volume', 'marketCap', 'supply'],
    },
    User: {
      fields: ['id', 'username', 'email', 'profile', 'preferences'],
    },
    Portfolio: {
      fields: ['id', 'name', 'assets', 'totalValue', 'performance'],
    },
    FundamentalData: {
      fields: ['symbol', 'metrics', 'ratios', 'scores', 'timestamp'],
    },
  },
} as const;