declare module "@tanstack/react-query" {
  export interface UseQueryOptions<TData = unknown, TError = Error, TSelectData = TData> {
    queryKey?: readonly unknown[];
    queryFn?: () => Promise<TData> | TData;
    enabled?: boolean;
    staleTime?: number;
    gcTime?: number;
    retry?: boolean | number;
    refetchOnWindowFocus?: boolean;
    refetchInterval?: number | false;
    placeholderData?: TData | (() => TData);
    select?: (data: TData) => TSelectData;
  }

  export interface UseQueryResult<TData = unknown, TError = Error> {
    data: TData | undefined;
    error: TError | null;
    isError: boolean;
    isPending: boolean;
    isLoading: boolean;
    isSuccess: boolean;
    isFetching: boolean;
    isRefetching: boolean;
    refetch: () => Promise<UseQueryResult<TData, TError>>;
    status: "pending" | "error" | "success";
    fetchStatus: "fetching" | "idle" | "paused";
  }

  export interface UseMutationOptions<TData = unknown, TError = Error, TVariables = void> {
    mutationFn?: (variables: TVariables) => Promise<TData>;
    mutationKey?: readonly unknown[];
    onSuccess?: (data: TData, variables: TVariables) => void;
    onError?: (error: TError, variables: TVariables) => void;
    onSettled?: (data: TData | undefined, error: TError | null, variables: TVariables) => void;
  }

  export interface UseMutationResult<TData = unknown, TError = Error, TVariables = void> {
    data: TData | undefined;
    error: TError | null;
    isError: boolean;
    isPending: boolean;
    isLoading: boolean;
    isSuccess: boolean;
    isIdle: boolean;
    mutate: (variables: TVariables) => void;
    mutateAsync: (variables: TVariables) => Promise<TData>;
    reset: () => void;
    status: "idle" | "pending" | "error" | "success";
  }

  export interface QueryClientConfig {
    defaultOptions?: {
      queries?: {
        staleTime?: number;
        gcTime?: number;
        retry?: boolean | number;
        refetchOnWindowFocus?: boolean;
      };
      mutations?: {
        retry?: boolean | number;
      };
    };
  }

  export class QueryClient {
    constructor(config?: QueryClientConfig);
    invalidateQueries(filters?: { queryKey?: readonly unknown[]; exact?: boolean }): Promise<void>;
    refetchQueries(filters?: { queryKey?: readonly unknown[]; exact?: boolean }): Promise<void>;
    cancelQueries(filters?: { queryKey?: readonly unknown[]; exact?: boolean }): Promise<void>;
    clear(): void;
    getQueryData<TData>(queryKey: readonly unknown[]): TData | undefined;
    setQueryData<TData>(queryKey: readonly unknown[], data: TData | ((old: TData | undefined) => TData)): TData;
    prefetchQuery<TData>(options: UseQueryOptions<TData>): Promise<TData>;
  }

  // Overload: with select (returns selected type)
  export function useQuery<TData = unknown, TError = Error, TSelectData = TData>(
    options: UseQueryOptions<TData, TError, TSelectData> & { select: (data: TData) => TSelectData },
  ): UseQueryResult<TSelectData, TError>;

  // Overload: without select (returns query data type)
  export function useQuery<TData = unknown, TError = Error>(
    options: UseQueryOptions<TData, TError>,
  ): UseQueryResult<TData, TError>;

  export function useMutation<TData = unknown, TError = Error, TVariables = void>(
    options: UseMutationOptions<TData, TError, TVariables>,
  ): UseMutationResult<TData, TError, TVariables>;

  export function useQueryClient(): QueryClient;

  export function QueryClientProvider(props: {
    client: QueryClient;
    children: React.ReactNode;
  }): React.JSX.Element;

  export function HydrationBoundary(props: {
    state: unknown;
    children: React.ReactNode;
  }): React.JSX.Element;

  export function useIsFetching(): number;
  export function useIsMutating(): number;
}
